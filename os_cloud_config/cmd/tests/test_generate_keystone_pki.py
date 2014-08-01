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

from os_cloud_config.cmd import generate_keystone_pki
from os_cloud_config.tests import base


class GenerateKeystonePKITest(base.TestCase):

    @mock.patch('os_cloud_config.keystone_pki.generate_certs_into_json')
    @mock.patch.object(sys, 'argv', ['generate-keystone-pki', '-j',
                       'foo.json', '-s'])
    def test_with_heatenv(self, generate_mock):
        generate_keystone_pki.main()
        generate_mock.assert_called_once_with('foo.json', True)

    @mock.patch('os_cloud_config.keystone_pki.create_and_write_ca_'
                'and_signing_pairs')
    @mock.patch.object(sys, 'argv', ['generate-keystone-pki', '-d', 'bar'])
    def test_without_heatenv(self, create_mock):
        generate_keystone_pki.main()
        create_mock.assert_called_once_with('bar')
