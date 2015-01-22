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

from os_cloud_config.cmd import setup_flavors
from os_cloud_config.tests import base


class RegisterNodesTest(base.TestCase):

    @mock.patch('os_cloud_config.cmd.utils._clients.get_nova_bm_client')
    @mock.patch('os_cloud_config.flavors.create_flavors_from_nodes')
    @mock.patch.dict('os.environ', {'OS_USERNAME': 'a', 'OS_PASSWORD': 'a',
                     'OS_TENANT_NAME': 'a', 'OS_AUTH_URL': 'a'})
    @mock.patch.object(sys, 'argv', ['setup-flavors', '--nodes', '-k', 'aaa',
                       '-r', 'zzz'])
    def test_with_arguments_nodes(self, create_flavors_mock,
                                  get_nova_bm_client_mock):
        with tempfile.NamedTemporaryFile() as f:
            f.write(u'{}\n'.encode('utf-8'))
            f.flush()
            sys.argv.insert(2, f.name)
            return_code = setup_flavors.main()

        create_flavors_mock.assert_called_once_with(
            get_nova_bm_client_mock(), {}, 'aaa', 'zzz', None)

        self.assertEqual(0, return_code)

    @mock.patch('os_cloud_config.cmd.utils._clients.get_nova_bm_client')
    @mock.patch('os_cloud_config.flavors.create_flavors_from_nodes')
    @mock.patch.dict('os.environ', {'OS_USERNAME': 'a', 'OS_PASSWORD': 'a',
                                    'OS_TENANT_NAME': 'a', 'OS_AUTH_URL': 'a',
                                    'ROOT_DISK': '10'})
    @mock.patch.object(sys, 'argv', ['setup-flavors', '--nodes', '-k', 'aaa',
                       '-r', 'zzz'])
    def test_with_arguments_nodes_root_disk(self, create_flavors_mock,
                                            get_nova_bm_client_mock):
        with tempfile.NamedTemporaryFile() as f:
            f.write(u'{}\n'.encode('utf-8'))
            f.flush()
            sys.argv.insert(2, f.name)
            return_code = setup_flavors.main()

        create_flavors_mock.assert_called_once_with(
            get_nova_bm_client_mock(), {}, 'aaa', 'zzz', '10')

        self.assertEqual(0, return_code)

    @mock.patch('os_cloud_config.cmd.utils._clients.get_nova_bm_client')
    @mock.patch('os_cloud_config.flavors.create_flavors_from_list')
    @mock.patch.dict('os.environ', {'OS_USERNAME': 'a', 'OS_PASSWORD': 'a',
                     'OS_TENANT_NAME': 'a', 'OS_AUTH_URL': 'a'})
    @mock.patch.object(sys, 'argv', ['setup-flavors', '--flavors', '-k', 'aaa',
                       '-r', 'zzz'])
    def test_with_arguments_flavors(self, create_flavors_mock,
                                    get_nova_bm_client_mock):
        with tempfile.NamedTemporaryFile() as f:
            f.write(u'{}\n'.encode('utf-8'))
            f.flush()
            sys.argv.insert(2, f.name)
            return_code = setup_flavors.main()

        create_flavors_mock.assert_called_once_with(
            get_nova_bm_client_mock(), {}, 'aaa', 'zzz')

        self.assertEqual(0, return_code)

    @mock.patch('os_cloud_config.cmd.utils._clients.get_nova_bm_client',
                return_value='nova_bm_client_mock')
    @mock.patch('os_cloud_config.flavors.create_flavors_from_nodes')
    @mock.patch.dict('os.environ', {'OS_USERNAME': 'a', 'OS_PASSWORD': 'a',
                     'OS_TENANT_NAME': 'a', 'OS_AUTH_URL': 'a'})
    @mock.patch.object(sys, 'argv', ['setup-flavors', '--nodes', '-k', 'aaa',
                       '-r', 'zzz'])
    def test_with_exception(self, create_flavors_mock,
                            get_nova_bm_client_mock):
        create_flavors_mock.side_effect = ValueError
        with tempfile.NamedTemporaryFile() as f:
            f.write(u'{}\n'.encode('utf-8'))
            f.flush()
            sys.argv.insert(2, f.name)
            return_code = setup_flavors.main()
        self.assertEqual(1, return_code)
