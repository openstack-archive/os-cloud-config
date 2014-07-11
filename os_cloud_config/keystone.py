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
import subprocess
import time

from keystoneclient.openstack.common.apiclient import exceptions
import keystoneclient.v2_0.client as ksclient

LOG = logging.getLogger(__name__)


def initialize(host, admin_token, admin_email, admin_password,
               region='regionOne', ssl=None, public=None, user='root'):
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
    """

    keystone = _create_admin_client(host, admin_token)

    _create_roles(keystone)
    _create_tenants(keystone)
    _create_admin_user(keystone, admin_email, admin_password)
    _create_endpoint(keystone, host, region, ssl, public)
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


def _create_endpoint(keystone, host, region, ssl, public):
    """Create keystone endpoint in Keystone.

    :param keystone: keystone v2 client
    :param host: ip/hostname of node where Keystone is running
    :param region: region to create the endpoint in
    :param ssl: ip/hostname to use as the ssl endpoint, if required
    :param public: ip/hostname to use as the public endpoint, if default is
        not suitable
    """
    LOG.debug('Create keystone public endpoint')
    service = keystone.services.create('keystone', 'identity',
                                       description='Keystone Identity Service')
    public_url = 'http://%s:5000/v2.0' % host
    if ssl:
        public_url = 'https://%s:13000/v2.0' % ssl
    elif public:
        public_url = 'http://%s:5000/v2.0' % public
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

    try:
        admin_user = keystone.users.find(name='admin')
        LOG.debug('Admin user already exists, skip creation')
    except exceptions.NotFound:
        LOG.debug('Creating admin user.')
        admin_user = keystone.users.create('admin', email=admin_email,
                                           password=admin_password,
                                           tenant_id=admin_tenant.id)
    if admin_role in keystone.roles.roles_for_user(admin_user, admin_tenant):
        LOG.debug('Admin user is already granted admin role with admin tenant')
    else:
        LOG.debug('Granting admin role to admin user on admin tenant.')
        keystone.roles.add_user_role(admin_user, admin_role, admin_tenant)
