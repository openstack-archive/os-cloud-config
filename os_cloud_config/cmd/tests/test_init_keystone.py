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

from os_cloud_config.cmd import init_keystone
from os_cloud_config.tests import base


class InitKeystoneTest(base.TestCase):

    @mock.patch('os_cloud_config.cmd.init_keystone.initialize')
    @mock.patch.object(sys, 'argv', ['init-keystone', '-o', 'hostname', '-t',
                                     'token', '-e', 'admin@example.com', '-p',
                                     'password', '-u', 'root'])
    def test_script(self, initialize_mock):
        init_keystone.main()
        initialize_mock.assert_called_once_with(
            'hostname', 'token', 'admin@example.com', 'password', 'regionOne',
            None, None, 'root', 600, 10, True)
