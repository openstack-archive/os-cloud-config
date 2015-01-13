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

import mock

from os_cloud_config.cmd import init_keystone_heat_domain
from os_cloud_config.tests import base


class InitKeystoneHeatDomainTest(base.TestCase):

    @mock.patch('os_cloud_config.cmd.init_keystone_heat_domain.environment')
    @mock.patch('os_cloud_config.cmd.init_keystone_heat_domain'
                '.initialize_for_heat')
    @mock.patch('os_cloud_config.cmd.utils._clients.get_keystone_v3_client',
                return_value='keystone_v3_client_mock')
    @mock.patch.object(sys, 'argv', ['init-keystone', '-d', 'password'])
    def test_script(self, environment_mock, initialize_mock, client_mock):
        init_keystone_heat_domain.main()
        initialize_mock.assert_called_once_with('keystone_v3_client_mock',
                                                'password')
