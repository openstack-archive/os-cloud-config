# -*- coding: utf-8 -*-

# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import logging
import os
import subprocess
import time
from urlparse import urlparse

from keystoneclient.openstack.common.apiclient import exceptions
import keystoneclient.v2_0.client as ksclient

LOG = logging.getLogger(__name__)

SERVICES = {
    'heat': {
        'description': 'Heat Service',
        'type': 'orchestration',
        'path': '/v1/%(tenant_id)s',
        'port': 8004,
    },
    'neutron': {
        'description': 'Neutron Service',
        'type': 'network',
        'port': 9696,
        'ssl_port': 13696,
    },
    'glance': {
        'description': 'Glance Image Service',
        'type': 'image',
        'port': 9292,
        'ssl_port': 13292,
    },
    'ec2': {
        'description': 'EC2 Compatibility Layer',
        'type': 'ec2',
        'path': '/services/Cloud',
        'admin_path': '/services/Admin',
        'port': 8773,
        'ssl_port': 13773,
    },
    'nova': {
        'description': 'Nova Compute Service',
        'type': 'compute',
        'path': '/v2/$(tenant_id)s',
        'port': 8774,
        'ssl_port': 13774,
    },
    'novav3': {
        'description': 'Nova Compute Service v3',
        'type': 'computev3',
        'path': '/v3',
        'port': 8774,
        'name': 'nova',
        'ssl_port': 13774,
    },
    'ceilometer': {
        'description': 'Ceilometer Service',
        'type': 'metering',
        'port': 8777,
    },
    'cinder': {
        'description': 'Cinder Volume Service',
        'type': 'volume',
        'path': '/v1/%(tenant_id)s',
        'port': 8776,
        'ssl_port': 13776,
    },
    'swift': {
        'description': 'Swift Object Storage Service',
        'type': 'object-store',
        'port': 8080,
        'ssl_port': 13080,
    },
    'horizon': {
        'description': 'OpenStack Dashboard',
        'type': 'dashboard',
        'nouser': True,
        'path': '/',
        'admin_path': '/admin'
    },
    'ironic': {
        'description': 'Ironic Service',
        'type': 'baremetal',
        'port': 6385
    },
    'tuskar': {
        'description': 'Tuskar Service',
        'type': 'management',
        'port': 8585
    }
}


def initialize(host, admin_token, admin_email, admin_password,
               region='regionOne', ssl=None, user='root'):
    """Perform post-heat initialization of Keystone.

    :param host: ip/hostname of node where Keystone is running
    :param admin_token: admin token to use with Keystone's admin endpoint
    :param admin_email: admin user's e-mail address to be set
    :param admin_password: admin user's password to be set
    :param region: region to create the endpoint in
    :param ssl: ip/hostname to use as the ssl endpoint, if required
    :param user: user to use to connect to the node where Keystone is running
    """

    keystone = _create_admin_client(host, admin_token)

    _create_roles(keystone)
    _create_tenants(keystone)
    _create_admin_user(keystone, admin_email, admin_password)
    _create_endpoint(keystone, host, region, ssl)
    _perform_pki_initialization(host, user)


def initialize_for_swift(host, admin_token):
    """Create roles in Keystone for use with Swift.

    :param host: ip/hostname of node where Keystone is running
    :param admin_token: admin token to use with Keystone's admin endpoint
    """
    keystone = _create_admin_client(host, admin_token)

    LOG.debug('Creating swiftoperator role.')
    keystone.roles.create('swiftoperator')
    LOG.debug('Creating ResellerAdmin role.')
    keystone.roles.create('ResellerAdmin')


def initialize_for_heat(host, admin_token, domain_admin_password):
    """Create Heat domain and an admin user for it.

    :param host: ip/hostname of node where Keystone is running
    :param admin_token: admin token to use with Keystone's admin endpoint
    :param domain_admin_password: heat domain admin's password to be set
    """
    keystone = _create_admin_client(host, admin_token)
    admin_role = keystone.roles.find(name='admin')

    LOG.debug('Creating heat domain.')
    heat_domain = keystone.domains.create(
        'heat',
        description='Owns users and tenants created by heat'
    )
    LOG.debug('Creating heat_domain_admin user.')
    heat_admin = keystone.users.create(
        'heat_domain_admin',
        description='Manages users and tenants created by heat',
        domain=heat_domain,
        password=domain_admin_password,
    )
    LOG.debug('Granting admin role to heat_domain_admin user on heat domain.')
    keystone.roles.grant(admin_role, user=heat_admin, domain=heat_domain)


def setup_endpoints(endpoints, public_host=None, region=None, client=None):
    """Create services endpoints in Keystone.

    :param endpoints: dict containing endpoints data
    :param public_host: ip/hostname used for public endpoint URI
    :param region: endpoint location
    """

    common_data = {
        'internal_host': urlparse(os.environ["OS_AUTH_URL"]).hostname,
        'public_host': public_host
    }

    if not client:
        client = ksclient.Client(username=os.environ["OS_USERNAME"],
                                 password=os.environ["OS_PASSWORD"],
                                 tenant_name=os.environ["OS_TENANT_NAME"],
                                 auth_url=os.environ["OS_AUTH_URL"])

    LOG.debug('Creating service endpoints.')
    for service, data in endpoints.iteritems():
        conf = SERVICES[service].copy()
        conf.update(common_data)
        conf.update(data)
        _register_endpoint(client, service, conf, public_host, region)


def _register_endpoint(keystone, service, data, public_host=None, region=None):
    """Create single service endpoint in Keystone.

    :param keystone: keystone v2 client
    :param service: name of service
    :param data: dict containing endpoint configuration
    :param public_host: ip/hostname used for public endpoint URI
    :param region: endpoint location
    """
    path = data.get('path', '/')
    internal_host = data.get('internal_host')
    port = data.get('port')
    internal_uri = 'http://{host}:{port}{path}'.format(
        host=internal_host, port=port, path=path)

    public_host = data.get('public_host')
    if public_host:
        public_port = data.get('ssl_port', port)
        public_protocol = 'https'
    else:
        public_protocol = 'http'
        public_port = port

    public_uri = '{protocol}://{host}:{port}{path}'.format(
        protocol=public_protocol,
        host=public_host or internal_host,
        port=public_port,
        path=path)

    admin_uri = 'http://{host}:{port}{path}'.format(
        host=internal_host,
        port=data.get('admin_port', port),
        path=data.get('admin_path', path))

    name = data.get('name', service)
    if not data.get('nouser'):
        _create_user_for_service(keystone, name, data.get('password', None))

    LOG.debug('Creating service for %s.', data.get('type'))
    kservice = keystone.services.create(name, data.get('type'),
                                        description=data.get('description'))

    LOG.debug('Creating endpoint for service %s.', service)
    keystone.endpoints.create(region or 'regionOne', kservice.id,
                              public_uri, admin_uri, internal_uri)


def _create_user_for_service(keystone, name, password):
    """Create service specific user in Keystone.

    :param keystone: keystone v2 client
    :param name: user's name to be set
    :param password: user's password to be set
    """
    try:
        keystone.users.find(name=name)
        LOG.debug('User %s already exists', name)
    except ksclient.exceptions.NotFound:
        LOG.debug('Creating user %s.', name)
        service_tenant = keystone.tenants.find(name='service')
        user = keystone.users.create(name,
                                     password,
                                     tenant_id=service_tenant.id,
                                     email='email=nobody@example.com')

        admin_role = keystone.roles.find(name='admin')
        keystone.roles.add_user_role(user, admin_role, service_tenant)
        # Add the admin tenant role for ceilometer user to enable polling
        # services
        if name == 'ceilometer':
            admin_tenant = keystone.tenants.find(name='admin')
            keystone.roles.add_user_role(user, admin_role, admin_tenant)


def _create_admin_client(host, admin_token):
    """Create Keystone v2 client for admin endpoint.

    :param host: ip/hostname of node where Keystone is running
    :param admin_token: admin token to use with Keystone's admin endpoint
    """
    admin_url = "http://%s:35357/v2.0" % host
    return ksclient.Client(endpoint=admin_url, token=admin_token)


def _create_roles(keystone):
    """Create initial roles in Keystone.

    :param keystone: keystone v2 client
    """
    for count in range(60):
        try:
            LOG.debug('Creating admin role, try %d.' % count)
            keystone.roles.create('admin')
            break
        except (exceptions.ConnectionRefused, exceptions.ServiceUnavailable):
            LOG.debug('Unable to create, sleeping for 10 seconds.')
            time.sleep(10)
    LOG.debug('Creating Member role.')
    keystone.roles.create('Member')


def _create_tenants(keystone):
    """Create initial tenants in Keystone.

    :param keystone: keystone v2 client
    """
    LOG.debug('Creating admin tenant.')
    keystone.tenants.create('admin', None)
    LOG.debug('Creating service tenant.')
    keystone.tenants.create('service', None)


def _create_endpoint(keystone, host, region, ssl):
    """Create keystone endpoint in Keystone.

    :param keystone: keystone v2 client
    :param host: ip/hostname of node where Keystone is running
    :param region: region to create the endpoint in
    :param ssl: ip/hostname to use as the ssl endpoint, if required
    """
    LOG.debug('Create keystone public endpoint')
    service = keystone.services.create('keystone', 'identity',
                                       description='Keystone Identity Service')
    public_url = 'http://%s:5000/v2.0' % host
    if ssl:
        public_url = 'https://%s:13000/v2.0' % ssl
    keystone.endpoints.create(region, service.id, public_url,
                              'http://%s:35357/v2.0' % host,
                              'http://%s:5000/v2.0' % host)


def _perform_pki_initialization(host, user):
    """Perform PKI initialization on a host for Keystone.

    :param host: ip/hostname of node where Keystone is running
    """
    subprocess.check_call(["ssh", "-o" "StrictHostKeyChecking=no", "-t",
                           "-l", user, host, "sudo", "keystone-manage",
                           "pki_setup", "--keystone-user",
                           "$(getent passwd | grep '^keystone' | cut -d: -f1)",
                           "--keystone-group",
                           "$(getent group | grep '^keystone' | cut -d: -f1)"])


def _create_admin_user(keystone, admin_email, admin_password):
    """Create admin user in Keystone.

    :param keystone: keystone v2 client
    :param admin_email: admin user's e-mail address to be set
    :param admin_password: admin user's password to be set
    """
    admin_tenant = keystone.tenants.find(name='admin')
    admin_role = keystone.roles.find(name='admin')

    LOG.debug('Creating admin user.')
    admin_user = keystone.users.create('admin', email=admin_email,
                                       password=admin_password,
                                       tenant_id=admin_tenant.id)
    LOG.debug('Granting admin role to admin user on admin tenant.')
    keystone.roles.add_user_role(admin_user, admin_role, admin_tenant)
