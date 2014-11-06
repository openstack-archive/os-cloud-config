# Copyright (c) 2014 Hewlett-Packard Development Company, L.P.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import sys
import tempfile

import mock

from os_cloud_config.cmd import register_nodes
from os_cloud_config.tests import base


class RegisterNodesTest(base.TestCase):

    @mock.patch('os_cloud_config.cmd.utils._clients.get_nova_bm_client',
                return_value='nova_bm_client_mock')
    @mock.patch('os_cloud_config.cmd.utils._clients.get_keystone_client',
                return_value='keystone_client_mock')
    @mock.patch('os_cloud_config.nodes.using_ironic', return_value=False)
    @mock.patch('os_cloud_config.nodes.register_all_nodes')
    @mock.patch.dict('os.environ', {'OS_USERNAME': 'a', 'OS_PASSWORD': 'a',
                     'OS_TENANT_NAME': 'a', 'OS_AUTH_URL': 'a'})
    @mock.patch.object(sys, 'argv', ['register-nodes', '--service-host',
                       'seed', '--nodes'])
    def test_with_arguments_nova_baremetal(self, register_mock,
                                           using_ironic_mock,
                                           get_keystone_client_mock,
                                           get_nova_bm_client_mock):
        with tempfile.NamedTemporaryFile() as f:
            f.write(u'{}\n'.encode('utf-8'))
            f.flush()
            sys.argv.append(f.name)
            return_code = register_nodes.main()

        register_mock.assert_called_once_with(
            "seed", {}, client='nova_bm_client_mock', remove=False,
            blocking=True, keystone_client='keystone_client_mock')
        using_ironic_mock.assert_called_once_with(
            keystone='keystone_client_mock')
        get_keystone_client_mock.assert_called_once_with()
        get_nova_bm_client_mock.assert_called_once_with()

        self.assertEqual(0, return_code)

    @mock.patch('os_cloud_config.cmd.utils._clients.get_ironic_client',
                return_value='ironic_client_mock')
    @mock.patch('os_cloud_config.cmd.utils._clients.get_keystone_client',
                return_value='keystone_client_mock')
    @mock.patch('os_cloud_config.nodes.using_ironic', return_value=True)
    @mock.patch('os_cloud_config.nodes.register_all_nodes')
    @mock.patch.dict('os.environ', {'OS_USERNAME': 'a', 'OS_PASSWORD': 'a',
                     'OS_TENANT_NAME': 'a', 'OS_AUTH_URL': 'a'})
    @mock.patch.object(sys, 'argv', ['register-nodes', '--service-host',
                       'seed', '--nodes'])
    def test_with_arguments_ironic(self, register_mock,
                                   using_ironic_mock,
                                   get_keystone_client_mock,
                                   get_ironic_client_mock):
        with tempfile.NamedTemporaryFile() as f:
            f.write(u'{}\n'.encode('utf-8'))
            f.flush()
            sys.argv.append(f.name)
            return_code = register_nodes.main()

        register_mock.assert_called_once_with(
            "seed", {}, client='ironic_client_mock', remove=False,
            blocking=True, keystone_client='keystone_client_mock')
        using_ironic_mock.assert_called_once_with(
            keystone='keystone_client_mock')
        get_keystone_client_mock.assert_called_once_with()
        get_ironic_client_mock.assert_called_once_with()

        self.assertEqual(0, return_code)

    @mock.patch('os_cloud_config.nodes.register_all_nodes')
    @mock.patch.dict('os.environ', {'OS_USERNAME': 'a', 'OS_PASSWORD': 'a',
                     'OS_TENANT_NAME': 'a', 'OS_AUTH_URL': 'a'})
    @mock.patch.object(sys, 'argv', ['register-nodes', '--service-host',
                       'seed', '--nodes'])
    def test_with_exception(self, register_mock):
        register_mock.side_effect = ValueError
        with tempfile.NamedTemporaryFile() as f:
            f.write(u'{}\n'.encode('utf-8'))
            f.flush()
            sys.argv.append(f.name)
            return_code = register_nodes.main()
        self.assertEqual(1, return_code)
