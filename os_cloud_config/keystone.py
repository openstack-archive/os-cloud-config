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

from __future__ import print_function

import logging
import socket
import subprocess
import time

from keystoneclient import exceptions
import keystoneclient.v2_0.client as ksclient_v2
import keystoneclient.v3.client as ksclient_v3
from six.moves.urllib.parse import urlparse

from os_cloud_config.utils import clients

LOG = logging.getLogger(__name__)

SERVICES = {
    'heat': {
        'description': 'Heat Service',
        'type': 'orchestration',
        'path': '/v1/%(tenant_id)s',
        'port': 8004,
        'ssl_port': 13004,
    },
    'heatcfn': {
        'description': 'Heat CloudFormation Service',
        'type': 'cloudformation',
        'path': '/v1',
        'port': 8000,
        'ssl_port': 13005,
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
        'path': '/v2.1/$(tenant_id)s',
        'port': 8774,
        'ssl_port': 13774,
    },
    'ceilometer': {
        'description': 'Ceilometer Service',
        'type': 'metering',
        'port': 8777,
        'ssl_port': 13777,
    },
    'gnocchi': {
        'description': 'OpenStack Metric Service',
        'type': 'metric',
        'port': 8041,
        'ssl_port': 13041,
    },
    'aodh': {
        'description': 'OpenStack Alarming Service',
        'type': 'alarming',
        'port': 8042,
        'ssl_port': 13042,
    },
    'cinder': {
        'description': 'Cinder Volume Service',
        'type': 'volume',
        'path': '/v1/%(tenant_id)s',
        'port': 8776,
        'ssl_port': 13776,
    },
    'cinderv2': {
        'description': 'Cinder Volume Service v2',
        'type': 'volumev2',
        'path': '/v2/%(tenant_id)s',
        'port': 8776,
        'ssl_port': 13776,
    },
    'swift': {
        'description': 'Swift Object Storage Service',
        'type': 'object-store',
        'path': '/v1/AUTH_%(tenant_id)s',
        'admin_path': '/v1',
        'port': 8080,
        'ssl_port': 13808,
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
        'port': 6385,
        'ssl_port': 13385,
    },
    'tuskar': {
        'description': 'Tuskar Service',
        'type': 'management',
        'path': '/v2',
        'port': 8585
    },
    'manila': {
        'description': 'Manila Service',
        'type': 'share',
        'path': '/v1/%(tenant_id)s',
        'port': 8786,
        'ssl_port': 13786,
    },
    'sahara': {
        'description': 'Sahara Service',
        'type': 'data-processing',
        'path': '/v1.1/%(tenant_id)s',
        'port': 8386
    },
    'trove': {
        'description': 'Trove Service',
        'type': 'database',
        'path': '/v1.0/%(tenant_id)s',
        'port': 8779
    },
    'congress': {
        'description': 'Congress Service',
        'type': 'policy',
        'path': '/',
        'port': 1789
    }
}


def initialize(host, admin_token, admin_email, admin_password,
               region='regionOne', ssl=None, public=None, user='root',
               timeout=600, poll_interval=10, pki_setup=True, admin=None,
               internal=None, public_port=None, admin_port=None,
               internal_port=None):
    """Perform post-heat initialization of Keystone.

    :param host: ip/hostname of node where Keystone is running
    :param admin_token: admin token to use with Keystone's admin endpoint
    :param admin_email: admin user's e-mail address to be set
    :param admin_password: admin user's password to be set
    :param region: region to create the endpoint in
    :param ssl: ip/hostname to use as the ssl endpoint, if required
    :param public: ip/hostname to use as the public endpoint, if the default
        is not suitable
    :param user: user to use to connect to the node where Keystone is running
    :param timeout: Total seconds to wait for keystone to be running
    :param poll_interval: Seconds to wait between keystone poll attempts
    :param pki_setup: Boolean for running pki_setup conditionally
    :param admin: ip/hostname to use as the admin endpoint, if the
        default is not suitable
    :param internal: ip/hostname to use as the internal endpoint, if the
        default is not suitable
    :param public_port: port to be used for the public endpoint, if default is
        not suitable
    :param admin_port: port to be used for the admin endpoint, if default is
        not suitable
    :param internal_port: port to be used for the internal endpoint, if
        default is not suitable
    """

    keystone_v2 = _create_admin_client_v2(host, admin_token)
    keystone_v3 = _create_admin_client_v3(host, admin_token, ssl)

    _create_roles(keystone_v2, timeout, poll_interval)
    _create_tenants(keystone_v2)
    _create_admin_user(keystone_v2, admin_email, admin_password)
    _grant_admin_user_roles(keystone_v3)
    _create_keystone_endpoint(keystone_v2, host, region, ssl, public, admin,
                              internal, public_port, admin_port, internal_port)
    if pki_setup:
        print("PKI initialization in init-keystone is deprecated and will be "
              "removed.")
        _perform_pki_initialization(host, user)


def initialize_for_swift(host, admin_token, ssl=None, public=None):
    """Create roles in Keystone for use with Swift.

    :param host: ip/hostname of node where Keystone is running
    :param admin_token: admin token to use with Keystone's admin endpoint
    :param ssl: ip/hostname to use as the ssl endpoint, if required
    :param public: ip/hostname to use as the public endpoint, if the default
        is not suitable
    """
    LOG.warning('This function is deprecated.')

    keystone = _create_admin_client_v2(host, admin_token, public)

    LOG.debug('Creating swiftoperator role.')
    keystone.roles.create('swiftoperator')
    LOG.debug('Creating ResellerAdmin role.')
    keystone.roles.create('ResellerAdmin')


def initialize_for_heat(keystone, domain_admin_password):
    """Create Heat domain and an admin user for it.

    :param keystone: A keystone v3 client
    :param domain_admin_password: heat domain admin's password to be set
    """
    try:
        heat_domain = keystone.domains.find(name='heat')
        LOG.debug('Domain heat already exists.')
    except exceptions.NotFound:
        LOG.debug('Creating heat domain.')
        heat_domain = keystone.domains.create(
            'heat',
            description='Owns users and tenants created by heat'
        )
    try:
        heat_admin = keystone.users.find(name='heat_domain_admin')
        LOG.debug('Heat domain admin already exists.')
    except exceptions.NotFound:
        LOG.debug('Creating heat_domain_admin user.')
        heat_admin = keystone.users.create(
            'heat_domain_admin',
            description='Manages users and tenants created by heat',
            domain=heat_domain,
            password=domain_admin_password,
        )
    LOG.debug('Granting admin role to heat_domain_admin user on heat domain.')
    admin_role = keystone.roles.find(name='admin')
    keystone.roles.grant(admin_role, user=heat_admin, domain=heat_domain)


def _create_role(keystone, name):
    """Helper for idempotent creating of role

    :param keystone: keystone v2 client
    :param name: name of the role
    """
    role = keystone.roles.findall(name=name)
    if role:
        LOG.info("Role %s was already created." % name)
    else:
        LOG.debug("Creating %s role." % name)
        keystone.roles.create(name)


def _create_tenant(keystone, name):
    """Helper for idempotent creating of tenant

    :param keystone: keystone v2 client
    :param name: name of the tenant
    """
    tenants = keystone.tenants.findall(name=name)
    if tenants:
        LOG.info("Tenant %s was already created." % name)
    else:
        LOG.debug("Creating %s tenant." % name)
        keystone.tenants.create(name, None)


def _setup_roles(keystone):
    """Create roles in Keystone for all services.

    :param keystone: keystone v2 client
    """
    # Create roles in Keystone for use with Swift.
    _create_role(keystone, 'swiftoperator')
    _create_role(keystone, 'ResellerAdmin')

    # Create Heat role.
    _create_role(keystone, 'heat_stack_user')


def _create_service(keystone, name, service_type, description=""):
    """Helper for idempotent creating of service.

    :param keystone: keystone v2 client
    :param name: service name
    :param service_type: unique service type
    :param description: service description
    :return keystone service object
    """

    existing_services = keystone.services.findall(type=service_type)
    if existing_services:
        LOG.info('Service %s for %s already created.', name, service_type)
        kservice = existing_services[0]
    else:
        LOG.debug('Creating service for %s.', service_type)
        kservice = keystone.services.create(
            name, service_type, description=description)

    return kservice


def _create_endpoint(keystone, region, service_id, public_uri, admin_uri,
                     internal_uri):
    """Helper for idempotent creating of endpoint.

    :param keystone: keystone v2 client
    :param region: endpoint region
    :param service_id: id of associated service
    :param public_uri: endpoint public uri
    :param admin_uri: endpoint admin uri
    :param internal_uri: endpoint internal uri
    """
    if keystone.endpoints.findall(publicurl=public_uri):
        LOG.info('Endpoint for service %s and public uri %s '
                 'already exists.', service_id, public_uri)
    else:
        LOG.debug('Creating endpoint for service %s.', service_id)
        keystone.endpoints.create(
            region, service_id, public_uri, admin_uri, internal_uri)


def setup_endpoints(endpoints, public_host=None, region=None, client=None,
                    os_username=None, os_password=None, os_tenant_name=None,
                    os_auth_url=None):
    """Create services endpoints in Keystone.

    :param endpoints: dict containing endpoints data
    :param public_host: ip/hostname used for public endpoint URI
    :param region: endpoint location
    """

    common_data = {
        'internal_host': urlparse(os_auth_url).hostname,
        'public_host': public_host
    }

    if not client:
        LOG.warning('Creating client inline is deprecated, please pass '
                    'the client as parameter.')
        client = clients.get_keystone_client(
            os_username, os_password, os_tenant_name, os_auth_url)

    # Setup roles first
    _setup_roles(client)

    # Create endpoints
    LOG.debug('Creating service endpoints.')
    for service, data in endpoints.items():
        conf = SERVICES[service].copy()
        conf.update(common_data)
        conf.update(data)
        _register_endpoint(client, service, conf, region)


def is_valid_ipv6_address(address):
    try:
        socket.inet_pton(socket.AF_INET6, address)
    except socket.error:  # not a valid address
        return False
    except TypeError:  # Not a string, e.g. None
        return False
    return True


def _register_endpoint(keystone, service, data, region=None):
    """Create single service endpoint in Keystone.

    :param keystone: keystone v2 client
    :param service: name of service
    :param data: dict containing endpoint configuration
    :param region: endpoint location
    """
    path = data.get('path', '/')
    internal_host = data.get('internal_host')
    if is_valid_ipv6_address(internal_host):
        internal_host = '[{host}]'.format(host=internal_host)
    port = data.get('port')
    internal_uri = 'http://{host}:{port}{path}'.format(
        host=internal_host, port=port, path=path)

    public_host = data.get('public_host')
    if is_valid_ipv6_address(public_host):
        public_host = '[{host}]'.format(host=public_host)
    public_protocol = 'http'
    public_port = port
    if public_host and 'ssl_port' in data:
        public_port = data.get('ssl_port')
        public_protocol = 'https'

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

    kservice = _create_service(
        keystone, name, data.get('type'), description=data.get('description'))

    if kservice:
        _create_endpoint(
            keystone, region or 'regionOne', kservice.id,
            public_uri, admin_uri, internal_uri)


def _create_user_for_service(keystone, name, password):
    """Create service specific user in Keystone.

    :param keystone: keystone v2 client
    :param name: user's name to be set
    :param password: user's password to be set
    """
    try:
        keystone.users.find(name=name)
        LOG.info('User %s already exists', name)
    except ksclient_v2.exceptions.NotFound:
        LOG.debug('Creating user %s.', name)
        service_tenant = keystone.tenants.find(name='service')
        user = keystone.users.create(name,
                                     password,
                                     tenant_id=service_tenant.id,
                                     email='email=nobody@example.com')

        admin_role = keystone.roles.find(name='admin')
        keystone.roles.add_user_role(user, admin_role, service_tenant)
        if name in ['ceilometer', 'gnocchi']:
            reselleradmin_role = keystone.roles.find(name='ResellerAdmin')
            keystone.roles.add_user_role(user, reselleradmin_role,
                                         service_tenant)


def _create_admin_client_v2(host, admin_token, public=None):
    """Create Keystone v2 client for admin endpoint.

    :param host: ip/hostname of node where Keystone is running
    :param admin_token: admin token to use with Keystone's admin endpoint
    :param ssl: ip/hostname to use as the ssl endpoint, if required
    :param public: ip/hostname to use as the public endpoint, if default is
        not suitable
    """
    # It may not be readily obvious that admin v2 is never available
    # via https. The SSL parameter is just the DNS name to use.
    keystone_host = public or host
    if is_valid_ipv6_address(keystone_host):
        keystone_host = '[{host}]'.format(host=keystone_host)
    admin_url = 'http://%s:35357/v2.0' % (keystone_host)
    return ksclient_v2.Client(endpoint=admin_url, token=admin_token)


def _create_admin_client_v3(host, admin_token, ssl=None, public=None):
    """Create Keystone v3 client for admin endpoint.

    :param host: ip/hostname of node where Keystone is running
    :param admin_token: admin token to use with Keystone's admin endpoint
    :param ssl: ip/hostname to use as the ssl endpoint, if required
    :param public: ip/hostname to use as the public endpoint, if default is
        not suitable
    """
    keystone_host = public or host
    if is_valid_ipv6_address(keystone_host):
        keystone_host = '[{host}]'.format(host=keystone_host)
    # TODO(bnemec): This should respect the ssl parameter, but right now we
    # don't support running the admin endpoint behind ssl.  Once that is
    # fixed, this should use ssl when available.
    admin_url = '%s://%s:35357/v3' % ('http', keystone_host)
    return ksclient_v3.Client(endpoint=admin_url, token=admin_token)


def _create_roles(keystone, timeout=600, poll_interval=10):
    """Create initial roles in Keystone.

    :param keystone: keystone v2 client
    :param timeout: total seconds to wait for keystone
    :param poll_interval: seconds to wait between keystone checks
    """
    wait_cycles = int(timeout / poll_interval)
    for count in range(wait_cycles):
        try:
            LOG.debug('Creating admin role, try %d.' % count)
            _create_role(keystone, 'admin')
            break
        except (exceptions.ConnectionRefused, exceptions.ServiceUnavailable):
            LOG.debug('Unable to create, sleeping for %d seconds.'
                      % poll_interval)
            time.sleep(poll_interval)


def _create_tenants(keystone):
    """Create initial tenants in Keystone.

    :param keystone: keystone v2 client
    """
    _create_tenant(keystone, 'admin')
    _create_tenant(keystone, 'service')


def _create_keystone_endpoint(keystone, host, region, ssl, public, admin,
                              internal, public_port=None, admin_port=None,
                              internal_port=None):
    """Create keystone endpoint in Keystone.

    :param keystone: keystone v2 client
    :param host: ip/hostname of node where Keystone is running
    :param region: region to create the endpoint in
    :param ssl: ip/hostname to use as the ssl endpoint, if required
    :param public: ip/hostname to use as the public endpoint, if default is
        not suitable
    :param admin: ip/hostname to use as the admin endpoint, if the
        default is not suitable
    :param internal: ip/hostname to use as the internal endpoint, if the
        default is not suitable
    :param public_port: port to be used for the public endpoint, if default is
        not suitable
    :param admin_port: port to be used for the admin endpoint, if default is
        not suitable
    :param internal_port: port to be used for the internal endpoint, if
        default is not suitable
    """
    LOG.debug('Create keystone public endpoint')
    service = _create_service(keystone, 'keystone', 'identity',
                              description='Keystone Identity Service')

    if is_valid_ipv6_address(host):
        host = '[{host}]'.format(host=host)
    if is_valid_ipv6_address(ssl):
        ssl = '[{host}]'.format(host=ssl)
    if is_valid_ipv6_address(public):
        public = '[{host}]'.format(host=public)
    if is_valid_ipv6_address(admin):
        admin = '[{host}]'.format(host=admin)
    if is_valid_ipv6_address(internal):
        internal = '[{host}]'.format(host=internal)

    url_template = '{proto}://{host}:{port}/v2.0'
    public_url = url_template.format(proto='http', host=host,
                                     port=public_port or 5000)
    if ssl:
        public_url = url_template.format(proto='https', host=ssl,
                                         port=public_port or 13000)
    elif public:
        public_url = url_template.format(proto='http', host=public,
                                         port=public_port or 5000)

    admin_url = url_template.format(proto='http', host=host,
                                    port=admin_port or 35357)
    if admin:
        admin_url = url_template.format(proto='http', host=admin,
                                        port=admin_port or 35357)

    internal_url = url_template.format(proto='http', host=host,
                                       port=internal_port or 5000)
    if internal:
        internal_url = url_template.format(proto='http', host=internal,
                                           port=internal_port or 5000)

    _create_endpoint(keystone, region, service.id, public_url, admin_url,
                     internal_url)


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

    try:
        keystone.users.find(name='admin')
        LOG.info('Admin user already exists, skip creation')
    except exceptions.NotFound:
        LOG.info('Creating admin user.')
        keystone.users.create('admin', email=admin_email,
                              password=admin_password,
                              tenant_id=admin_tenant.id)


def _grant_admin_user_roles(keystone_v3):
    """Grant admin user roles with admin project and default domain.

    :param keystone_v3: keystone v3 client
    """
    admin_role = keystone_v3.roles.list(name='admin')[0]
    # TO-DO(mmagr): Get back to filtering by id as soon as following bug
    # is fixed: https://bugs.launchpad.net/python-keystoneclient/+bug/1452298
    default_domain = keystone_v3.domains.list(name='default')[0]
    admin_user = keystone_v3.users.list(domain=default_domain, name='admin')[0]
    admin_project = keystone_v3.projects.list(domain=default_domain,
                                              name='admin')[0]

    if admin_role in keystone_v3.roles.list(user=admin_user,
                                            project=admin_project):
        LOG.info('Admin user is already granted admin role with admin project')
    else:
        LOG.info('Granting admin role to admin user on admin project.')
        keystone_v3.roles.grant(admin_role, user=admin_user,
                                project=admin_project)

    if admin_role in keystone_v3.roles.list(user=admin_user,
                                            domain=default_domain):
        LOG.info('Admin user is already granted admin role with default '
                 'domain')
    else:
        LOG.info('Granting admin role to admin user on default domain.')
        keystone_v3.roles.grant(admin_role, user=admin_user,
                                domain=default_domain)
