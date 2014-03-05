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

import mock

from os_cloud_config import ssh
from os_cloud_config.tests import base


class SSHTest(base.TestCase):

    @mock.patch('paramiko.AutoAddPolicy')
    @mock.patch('paramiko.SSHClient')
    def test_connect(self, ssh_client_class, policy_class):
        client = mock.MagicMock()
        ssh_client_class.return_value = client

        self.assertEqual(client,
                         ssh.connect('192.0.0.3', 'heat-admin', '/fake_key'))
        client.set_missing_host_key_policy.assert_called_with(
            policy_class.return_value)
        client.connect.assert_called_with('192.0.0.3',
                                          username='heat-admin',
                                          key_filename='/fake_key',
                                          timeout=60)
