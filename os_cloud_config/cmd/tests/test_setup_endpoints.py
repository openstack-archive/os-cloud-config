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

import mock
import os
import sys

from os_cloud_config.cmd import setup_endpoints
from os_cloud_config.tests import base


class SetupEndpointsTest(base.TestCase):

    @mock.patch('os_cloud_config.cmd.setup_endpoints.setup_endpoints')
    @mock.patch.object(
        sys, 'argv',
        ['setup-endpoints', '-s', '{"nova": {"password": "123"}}',
         '-p', '192.0.2.28', '-r', 'EC'])
    @mock.patch.object(os, 'environ', {"OS_USERNAME": "admin",
                                       "OS_PASSWORD": "password",
                                       "OS_TENANT_NAME": "admin",
                                       "OS_AUTH_URL": "http://localhost:5000"})
    def test_script(self, setup_endpoints_mock):
        pass
        setup_endpoints.main()
        setup_endpoints_mock.assert_called_once_with(
            {'nova': {'password': '123'}},
            public_host='192.0.2.28',
            region='EC',
            os_username="admin",
            os_password="password",
            os_tenant_name="admin",
            os_auth_url="http://localhost:5000")
