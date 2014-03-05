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

from os_cloud_config.openstack.common import processutils
from os_cloud_config import ssh


LOG = logging.getLogger(__name__)


def initialize(host, ssh_user, ssh_key, admin_token, admin_email,
               admin_password, public_ssl_host=None, region='regionOne'):
    """Perform post-heat initialization of Keystone.

    :param host: ip/hostname of node where Keystone is running
    :param ssh_user: username for ssh connection to Keystone node
    :param ssh_key: key file path for ssh connection to Keystone node
    :param admin_token: admin token to use with Keystone's service endpoint
    :param admin_email: admin user's e-mail address to be set
    :param admin_password: admin user's password to be set
    :param public_ssl_host: Keystone's public URL to be set in service catalog
    :param region: region to use for endpoint registration
    """

    # TODO(jistr): support distros which use "openstack-keystone" user
    keystone_user = 'keystone'

    pki_setup(host, ssh_user, ssh_key, keystone_user)

    # TODO(jistr): rest of the initialization here


def pki_setup(ssh_host, ssh_user, ssh_key, keystone_user):
    """Set up Keystone token signing and verification.

    :param ssh_host: ip/hostname of node where Keystone is present
    :param ssh_user: username for ssh connection to Keystone node
    :param ssh_key: key file path for ssh connection to Keystone node
    :param keystone_user: user account under which Keystone service runs
    """

    setup_command = (
        'sudo keystone-manage pki_setup --keystone-user %s --keystone-group %s'
    ) % (keystone_user, keystone_user)

    connection = ssh.connect(ssh_host, ssh_user, ssh_key)
    stdout, stderr = processutils.ssh_execute(connection, setup_command)
    LOG.debug("Keystone PKI setup stdout: %s" % stdout)
    LOG.debug("Keystone PKI setup stderr: %s" % stderr)
    connection.close()
