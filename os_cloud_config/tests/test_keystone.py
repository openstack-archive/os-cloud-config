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

        self.client.tenants.create.assert_has_calls(
            [mock.call('admin', None), mock.call('service', None)])

        self.client.tenants.find.assert_called_once_with(name='admin')
        self.client.roles.find.assert_called_once_with(name='admin')
        self.client.users.create.assert_called_once_with(
            'admin', email='admin@example.org', password='adminpasswd',
            tenant_id=self.client.tenants.find.return_value.id)

        self.client.roles.find.assert_called_once_with(name='admin')
        self.client.roles.add_user_role.assert_called_once_with(
            self.client.users.create.return_value,
            self.client.roles.find.return_value,
            self.client.tenants.find.return_value)

        self.client.services.create.assert_called_once_with(
            'keystone', 'identity', description='Keystone Identity Service')
        self.client.endpoints.create.assert_called_once_with(
            'regionOne', self.client.services.create.return_value.id,
            'http://192.0.0.3:5000/v2.0', 'http://192.0.0.3:35357/v2.0',
            'http://192.0.0.3:5000/v2.0')

    def test_initialize_for_swift(self):
        self._patch_client()

        keystone.initialize_for_swift('192.0.0.3', 'mytoken')

        self.client.roles.create.assert_has_calls(
            [mock.call('swiftoperator'), mock.call('ResellerAdmin')])

    def test_initialize_for_heat(self):
        self._patch_client()

        keystone.initialize_for_heat('192.0.0.3', 'mytoken', 'heatadminpasswd')

        self.client.domains.create.assert_called_once_with(
            'heat', description='Owns users and tenants created by heat')
        self.client.users.create.assert_called_once_with(
            'heat_domain_admin',
            description='Manages users and tenants created by heat',
            domain=self.client.domains.create.return_value,
            password='heatadminpasswd')
        self.client.roles.find.assert_called_once_with(name='admin')
        self.client.roles.grant.assert_called_once_with(
            self.client.roles.find.return_value,
            user=self.client.users.create.return_value,
            domain=self.client.domains.create.return_value)

    def test_create_endpoint_options(self):
        self._patch_client()

        keystone._create_endpoint(self.client, '192.0.0.3', 'specialRegion',
                                  'keystone.example.com')
        self.client.services.create.assert_called_once_with(
            'keystone', 'identity', description='Keystone Identity Service')
        self.client.endpoints.create.assert_called_once_with(
            'specialRegion', self.client.services.create.return_value.id,
            'https://keystone.example.com:13000/v2.0',
            'http://192.0.0.3:35357/v2.0', 'http://192.0.0.3:5000/v2.0')

    @mock.patch('os_cloud_config.keystone.ksclient.Client')
    def test_create_admin_client(self, client):
        self.assertEqual(
            client.return_value,
            keystone._create_admin_client('192.0.0.3', 'mytoken'))
        client.assert_called_once_with(endpoint='http://192.0.0.3:35357/v2.0',
                                       token='mytoken')

    def _patch_client(self):
        self.client = mock.MagicMock()
        self.create_admin_client_patcher = mock.patch(
            'os_cloud_config.keystone._create_admin_client')
        create_admin_client = self.create_admin_client_patcher.start()
        self.addCleanup(self._patch_client_cleanup)
        create_admin_client.return_value = self.client

    def _patch_client_cleanup(self):
        self.create_admin_client_patcher.stop()
        self.client = None
