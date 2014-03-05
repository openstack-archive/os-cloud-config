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

import paramiko

from os_cloud_config import exception
from os_cloud_config.openstack.common.gettextutils import _


LOG = logging.getLogger(__name__)
CONNECTION_TIMEOUT = 60


def connect(host, user, keyfile):
    """Establish an SSH connection.

    :param host: ip/hostname to connect to
    :param user: user to connect as
    :param keyfile: path to a file with a private key to use

    :return: an established ssh connection
    :rtype: paramiko.SSHClient
    """
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(host,
                    username=user,
                    key_filename=keyfile,
                    timeout=CONNECTION_TIMEOUT)

        LOG.debug("SSH connection with %s established successfully." % host)

        # send TCP keepalive packets every 20 seconds
        ssh.get_transport().set_keepalive(20)

        return ssh
    except Exception:
        LOG.exception(_('Connection error'))
        raise exception.SSHConnectionFailed()
