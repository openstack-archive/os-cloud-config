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

import keystoneclient.v3.client as ksclient

LOG = logging.getLogger(__name__)


def initialize(host, admin_token, admin_email, admin_password):
    """Perform post-heat initialization of Keystone.

    :param host: ip/hostname of node where Keystone is running
    :param admin_token: admin token to use with Keystone's admin endpoint
    :param admin_email: admin user's e-mail address to be set
    :param admin_password: admin user's password to be set
    """

    keystone = _create_admin_client(host, admin_token)

    _create_roles(keystone)
    _create_projects(keystone)
    _create_admin_user(keystone, admin_email, admin_password)


def initialize_for_swift(auth_url, username, password):
    """Create roles in Keystone for use with Swift.

    :param auth_url: URI pointing to a running Keystone
    :param username: Username to authenticate to Keystone with
    :param password: Password to authenticate to Keystone with
    """
    keystone = _create_client(auth_url, username, password)

    LOG.debug('Creating swiftoperator role.')
    keystone.roles.create('swiftoperator')
    LOG.debug('Creating ResellerAdmin role.')
    keystone.roles.create('ResellerAdmin')


def initialize_for_heat(auth_url, username, password, domain_admin_password):
    """Create Heat domain and an admin user for it.

    :param auth_url: URI pointing to a running Keystone
    :param username: Username to authenticate to Keystone with
    :param password: Password to authenticate to Keystone with
    :param domain_admin_password: heat domain admin's password to be set
    """
    keystone = _create_client(auth_url, username, password)
    admin_role = keystone.roles.find(name='admin')

    LOG.debug('Creating heat domain.')
    heat_domain = keystone.domains.create(
        'heat',
        description='Owns users and projects created by heat'
    )
    LOG.debug('Creating heat_domain_admin user.')
    heat_admin = keystone.users.create(
        'heat_domain_admin',
        description='Manages users and projects created by heat',
        domain=heat_domain,
        password=domain_admin_password,
    )
    LOG.debug('Granting admin role to heat_domain_admin user on heat domain.')
    keystone.roles.grant(admin_role,
                         user=heat_admin,
                         domain=heat_domain)


def _create_admin_client(host, admin_token):
    """Create Keystone v3 client for admin endpoint.

    :param host: ip/hostname of node where Keystone is running
    :param admin_token: admin token to use with Keystone's admin endpoint
    """
    admin_url = "http://%s:35357/v3" % host
    return ksclient.Client(endpoint=admin_url, token=admin_token)


def _create_client(auth_url, username, password):
    """Create Keystone client for a given URL, username and password.

    :param auth_url: URI pointing to a running Keystone
    :param username: Username to authenticate to Keystone with
    :param password: Password to authenticate to Keystone with
    """
    return ksclient.Client(endpoint=auth_url, username=username,
                           password=password)

def _create_roles(keystone):
    """Create initial roles in Keystone.

    :param keystone: keystone v3 client
    """
    LOG.debug('Creating admin role.')
    keystone.roles.create('admin')
    LOG.debug('Creating Member role.')
    keystone.roles.create('Member')


def _create_projects(keystone):
    """Create initial projects in Keystone.

    :param keystone: keystone v3 client
    """
    LOG.debug('Creating admin project.')
    keystone.projects.create('admin', None)
    LOG.debug('Creating service project.')
    keystone.projects.create('service', None)


def _create_admin_user(keystone, admin_email, admin_password):
    """Create admin user in Keystone.

    :param keystone: keystone v3 client
    :param admin_email: admin user's e-mail address to be set
    :param admin_password: admin user's password to be set
    """
    admin_project = keystone.projects.find(name='admin')
    admin_role = keystone.roles.find(name='admin')

    LOG.debug('Creating admin user.')
    admin_user = keystone.users.create('admin',
                                       email=admin_email,
                                       password=admin_password,
                                       project=admin_project)
    LOG.debug('Granting admin role to admin user on admin project.')
    keystone.roles.grant(admin_role,
                         user=admin_user,
                         project=admin_project)
