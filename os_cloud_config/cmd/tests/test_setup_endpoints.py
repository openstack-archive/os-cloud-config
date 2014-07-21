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

import mock

from os_cloud_config.cmd import setup_endpoints
from os_cloud_config.tests import base


class SetupEndpointsTest(base.TestCase):

    @mock.patch('os_cloud_config.cmd.utils._clients.get_keystone_client',
                return_value='keystone_client_mock')
    @mock.patch('os_cloud_config.keystone.setup_endpoints')
    @mock.patch.object(
        sys, 'argv',
        ['setup-endpoints', '-s', '{"nova": {"password": "123"}}',
         '-p', '192.0.2.28', '-r', 'EC'])
    @mock.patch.dict('os.environ', {
                     'OS_USERNAME': 'admin',
                     'OS_PASSWORD': 'password',
                     'OS_TENANT_NAME': 'admin',
                     'OS_AUTH_URL': 'http://localhost:5000'})
    def test_script(self, setup_endpoints_mock, get_keystone_client_mock):
        setup_endpoints.main()
        get_keystone_client_mock.assert_called_once_with()
        setup_endpoints_mock.assert_called_once_with(
            {'nova': {'password': '123'}},
            public_host='192.0.2.28',
            region='EC',
            os_auth_url="http://localhost:5000",
            client="keystone_client_mock")
