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

import os
import sys
import tempfile

import mock

from os_cloud_config.cmd import register_nodes
from os_cloud_config.tests import base


class RegisterNodesTest(base.TestCase):

    @mock.patch('os_cloud_config.nodes.register_all_nodes')
    @mock.patch('os_cloud_config.nodes.check_service')
    @mock.patch.object(os, 'environ', {'OS_USERNAME': 'a', 'OS_PASSWORD': 'a',
                       'OS_TENANT_NAME': 'a', 'OS_AUTH_URL': 'a'})
    @mock.patch.object(sys, 'argv', ['register-nodes', '--service-host',
                       'seed', '--nodes'])
    def test_with_arguments(self, register_mock, check_mock):
        with tempfile.NamedTemporaryFile() as f:
            f.write('{}\n')
            f.flush()
            sys.argv.append(f.name)
            register_nodes.main()
        self.assertEqual(1, check_mock.call_count)
        register_mock.has_calls([mock.call("seed", "{}")])

    @mock.patch('os_cloud_config.nodes.check_service')
    @mock.patch.object(os, 'environ', {'OS_USERNAME': 'b'})
    @mock.patch.object(sys, 'argv', ['register-nodes', '--nodes'])
    def test_with_no_environment(self, check_mock):
        with tempfile.NamedTemporaryFile() as f:
            f.write('{}\n')
            f.flush()
            sys.argv.append(f.name)
            register_nodes.main()
        self.assertEqual(0, check_mock.call_count)
