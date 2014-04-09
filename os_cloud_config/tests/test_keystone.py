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

from os_cloud_config import keystone
from os_cloud_config.tests import base


class KeystoneTest(base.TestCase):

    def test_initialize(self):
        self._patch_client()

        keystone.initialize(
            '192.0.0.3', 'mytoken', 'admin@example.org', 'adminpasswd')

        self.client.roles.create.assert_has_calls(
            [mock.call('admin'), mock.call('Member')])

        self.client.projects.create.assert_has_calls(
            [mock.call('admin', None), mock.call('service', None)])

        self.client.projects.find.assert_called_once_with(name='admin')
        self.client.users.create.assert_called_once_with(
            'admin', email='admin@example.org', password='adminpasswd',
            project=self.client.projects.find.return_value)

        self.client.roles.find.assert_called_once_with(name='admin')
        self.client.roles.grant.assert_called_once_with(
            self.client.roles.find.return_value,
            user=self.client.users.create.return_value,
            project=self.client.projects.find.return_value)

    def test_initialize_for_swift(self):
        self._patch_client(name='_create_client')

        keystone.initialize_for_swift('http://192.0.0.3:5000/', 'admin', '')

        self.client.roles.create.assert_has_calls(
            [mock.call('swiftoperator'), mock.call('ResellerAdmin')])

    def test_initialize_for_heat(self):
        self._patch_client(name='_create_client')

        keystone.initialize_for_heat('http://192.0.0.3:5000/', 'admin', '',
                                     'heatadminpasswd')

        self.client.domains.create.assert_called_once_with(
            'heat', description='Owns users and projects created by heat')
        self.client.users.create.assert_called_once_with(
            'heat_domain_admin',
            description='Manages users and projects created by heat',
            domain=self.client.domains.create.return_value,
            password='heatadminpasswd')
        self.client.roles.find.assert_called_once_with(name='admin')
        self.client.roles.grant.assert_called_once_with(
            self.client.roles.find.return_value,
            user=self.client.users.create.return_value,
            domain=self.client.domains.create.return_value)

    @mock.patch('os_cloud_config.keystone.ksclient.Client')
    def test_create_admin_client(self, client):
        self.assertEqual(
            client.return_value,
            keystone._create_admin_client('192.0.0.3', 'mytoken'))
        client.assert_called_once_with(endpoint='http://192.0.0.3:35357/v3',
                                       token='mytoken')

    def _patch_client(self, name='_create_admin_client'):
        self.client = mock.MagicMock()
        self.create_client_patcher = mock.patch(
            'os_cloud_config.keystone.' + name)
        create_client = self.create_client_patcher.start()
        self.addCleanup(self._patch_client_cleanup)
        create_client.return_value = self.client

    def _patch_client_cleanup(self):
        self.create_client_patcher.stop()
        self.client = None
