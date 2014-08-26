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

import json
import sys
import tempfile

import mock

from os_cloud_config.cmd import setup_neutron
from os_cloud_config.tests import base


class SetupNeutronTest(base.TestCase):

    @mock.patch('os_cloud_config.cmd.utils._clients.get_keystone_client',
                return_value='keystone_client_mock')
    @mock.patch('os_cloud_config.cmd.utils._clients.get_neutron_client',
                return_value='neutron_client_mock')
    @mock.patch('os_cloud_config.neutron.initialize_neutron')
    @mock.patch.dict('os.environ', {'OS_USERNAME': 'a', 'OS_PASSWORD': 'a',
                     'OS_TENANT_NAME': 'a', 'OS_AUTH_URL': 'a'})
    @mock.patch.object(sys, 'argv', ['setup-neutron', '--network-json'])
    def test_with_arguments(self, initialize_mock, get_neutron_client_mock,
                            get_keystone_client_mock):
        network_desc = {'physical': {'metadata_server': 'foo.bar'}}
        with tempfile.NamedTemporaryFile() as f:
            f.write(json.dumps(network_desc).encode('utf-8'))
            f.flush()
            sys.argv.append(f.name)
            return_code = setup_neutron.main()

        get_keystone_client_mock.assert_called_once_with()
        get_neutron_client_mock.assert_called_once_with()
        initialize_mock.assert_called_once_with(
            network_desc,
            neutron_client='neutron_client_mock',
            keystone_client='keystone_client_mock')
        self.assertEqual(0, return_code)

    @mock.patch('os_cloud_config.neutron.initialize_neutron')
    @mock.patch.dict('os.environ', {'OS_USERNAME': 'a', 'OS_PASSWORD': 'a',
                     'OS_TENANT_NAME': 'a', 'OS_AUTH_URL': 'a'})
    @mock.patch.object(sys, 'argv', ['setup-neutron', '--network-json'])
    def test_with_exception(self, initialize_mock):
        initialize_mock.side_effect = ValueError
        with tempfile.NamedTemporaryFile() as f:
            f.write('{}\n'.encode('utf-8'))
            f.flush()
            sys.argv.append(f.name)
            return_code = setup_neutron.main()
        self.assertEqual(1, return_code)
