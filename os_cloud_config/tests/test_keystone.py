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

from keystoneclient import exceptions
import keystoneclient.v2_0.client as ksclient_v2
import mock

from os_cloud_config import keystone
from os_cloud_config.tests import base


class KeystoneTest(base.TestCase):

    def assert_endpoint(self, host, region='regionOne', public_endpoint=None,
                        admin_endpoint=None, internal_endpoint=None):
        self.client.services.create.assert_called_once_with(
            'keystone', 'identity', description='Keystone Identity Service')
        if public_endpoint is None:
            public_endpoint = 'http://%s:5000/v2.0' % host
        if admin_endpoint is None:
            admin_endpoint = 'http://%s:35357/v2.0' % host
        if internal_endpoint is None:
            internal_endpoint = 'http://%s:5000/v2.0' % host
        self.client.endpoints.create.assert_called_once_with(
            region, self.client.services.create.return_value.id,
            public_endpoint, admin_endpoint, internal_endpoint)

    def assert_calls_in_grant_admin_user_roles(self):
        self.client_v3.roles.list.assert_has_calls([mock.call(name='admin')])
        self.client_v3.domains.list.assert_called_once_with(name='default')
        self.client_v3.users.list.assert_called_once_with(
            domain=self.client_v3.domains.list.return_value[0], name='admin')
        self.client_v3.projects.list.assert_called_once_with(
            domain=self.client_v3.domains.list.return_value[0], name='admin')

    @mock.patch('subprocess.check_call')
    def test_initialize(self, check_call_mock):
        self._patch_client()
        self._patch_client_v3()

        self.client.services.findall.return_value = []
        self.client.endpoints.findall.return_value = []
        self.client.roles.findall.return_value = []
        self.client.tenants.findall.return_value = []

        keystone.initialize(
            '192.0.0.3', 'mytoken', 'admin@example.org', 'adminpasswd')

        self.client.tenants.create.assert_has_calls(
            [mock.call('admin', None), mock.call('service', None)])

        self.assert_calls_in_grant_admin_user_roles()

        self.assert_endpoint('192.0.0.3')

        check_call_mock.assert_called_once_with(
            ["ssh", "-o" "StrictHostKeyChecking=no", "-t", "-l", "root",
             "192.0.0.3", "sudo", "keystone-manage", "pki_setup",
             "--keystone-user",
             "$(getent passwd | grep '^keystone' | cut -d: -f1)",
             "--keystone-group",
             "$(getent group | grep '^keystone' | cut -d: -f1)"])

    def test_initialize_for_swift(self):
        self._patch_client()

        keystone.initialize_for_swift('192.0.0.3', 'mytoken')

        self.client.roles.create.assert_has_calls(
            [mock.call('swiftoperator'), mock.call('ResellerAdmin')])

    def test_initialize_for_heat(self):
        client = mock.MagicMock()
        client.domains.find.side_effect = exceptions.NotFound
        client.users.find.side_effect = exceptions.NotFound

        keystone.initialize_for_heat(client, 'heatadminpasswd')

        client.domains.create.assert_called_once_with(
            'heat', description='Owns users and tenants created by heat')
        client.users.create.assert_called_once_with(
            'heat_domain_admin',
            description='Manages users and tenants created by heat',
            domain=client.domains.create.return_value,
            password='heatadminpasswd')
        client.roles.find.assert_called_once_with(name='admin')
        client.roles.grant.assert_called_once_with(
            client.roles.find.return_value,
            user=client.users.create.return_value,
            domain=client.domains.create.return_value)

    @mock.patch('subprocess.check_call')
    def test_idempotent_initialize(self, check_call_mock):
        self._patch_client()
        self._patch_client_v3()

        self.client.services.findall.return_value = mock.MagicMock()
        self.client.endpoints.findall.return_value = mock.MagicMock()
        self.client.roles.findall.return_value = mock.MagicMock()
        self.client.tenants.findall.return_value = mock.MagicMock()

        keystone.initialize(
            '192.0.0.3',
            'mytoken',
            'admin@example.org',
            'adminpasswd')

        self.assertFalse(self.client.roles.create('admin').called)
        self.assertFalse(self.client.roles.create('service').called)

        self.assertFalse(self.client.tenants.create('admin', None).called)
        self.assertFalse(self.client.tenants.create('service', None).called)

        self.assert_calls_in_grant_admin_user_roles()

        check_call_mock.assert_called_once_with(
            ["ssh", "-o" "StrictHostKeyChecking=no", "-t", "-l", "root",
             "192.0.0.3", "sudo", "keystone-manage", "pki_setup",
             "--keystone-user",
             "$(getent passwd | grep '^keystone' | cut -d: -f1)",
             "--keystone-group",
             "$(getent group | grep '^keystone' | cut -d: -f1)"])

    def test_setup_roles(self):
        self._patch_client()

        self.client.roles.findall.return_value = []

        keystone._setup_roles(self.client)

        self.client.roles.findall.assert_has_calls(
            [mock.call(name='swiftoperator'), mock.call(name='ResellerAdmin'),
             mock.call(name='heat_stack_user')])

        self.client.roles.create.assert_has_calls(
            [mock.call('swiftoperator'), mock.call('ResellerAdmin'),
             mock.call('heat_stack_user')])

    def test_idempotent_setup_roles(self):
        self._patch_client()

        self.client.roles.findall.return_value = mock.MagicMock()

        keystone._setup_roles(self.client)

        self.client.roles.findall.assert_has_calls(
            [mock.call(name='swiftoperator'), mock.call(name='ResellerAdmin'),
             mock.call(name='heat_stack_user')], any_order=True)

        self.assertFalse(self.client.roles.create('swiftoperator').called)
        self.assertFalse(self.client.roles.create('ResellerAdmin').called)
        self.assertFalse(self.client.roles.create('heat_stack_user').called)

    def test_create_tenants(self):
        self._patch_client()

        self.client.tenants.findall.return_value = []

        keystone._create_tenants(self.client)

        self.client.tenants.findall.assert_has_calls(
            [mock.call(name='admin'), mock.call(name='service')],
            any_order=True)

        self.client.tenants.create.assert_has_calls(
            [mock.call('admin', None), mock.call('service', None)])

    def test_idempotent_create_tenants(self):
        self._patch_client()

        self.client.tenants.findall.return_value = mock.MagicMock()

        keystone._create_tenants(self.client)

        self.client.tenants.findall.assert_has_calls(
            [mock.call(name='admin'), mock.call(name='service')],
            any_order=True)

        # Test that tenants are not created again if they exists
        self.assertFalse(self.client.tenants.create('admin', None).called)
        self.assertFalse(self.client.tenants.create('service', None).called)

    def test_create_keystone_endpoint_ssl(self):
        self._patch_client()

        self.client.services.findall.return_value = []
        self.client.endpoints.findall.return_value = []

        keystone._create_keystone_endpoint(
            self.client, '192.0.0.3', 'regionOne', 'keystone.example.com',
            None, None, None)
        public_endpoint = 'https://keystone.example.com:13000/v2.0'
        self.assert_endpoint('192.0.0.3', public_endpoint=public_endpoint)

    def test_create_keystone_endpoint_public(self):
        self._patch_client()

        self.client.services.findall.return_value = []
        self.client.endpoints.findall.return_value = []

        keystone._create_keystone_endpoint(
            self.client, '192.0.0.3', 'regionOne', None, 'keystone.public',
            None, None)
        public_endpoint = 'http://keystone.public:5000/v2.0'
        self.assert_endpoint('192.0.0.3', public_endpoint=public_endpoint)

    def test_create_keystone_endpoint_ssl_and_public(self):
        self._patch_client()

        self.client.services.findall.return_value = []
        self.client.endpoints.findall.return_value = []

        keystone._create_keystone_endpoint(
            self.client, '192.0.0.3', 'regionOne', 'keystone.example.com',
            'keystone.public', None, None)
        public_endpoint = 'https://keystone.example.com:13000/v2.0'
        self.assert_endpoint('192.0.0.3', public_endpoint=public_endpoint)

    def test_create_keystone_endpoint_public_and_admin(self):
        self._patch_client()

        self.client.services.findall.return_value = []
        self.client.endpoints.findall.return_value = []

        keystone._create_keystone_endpoint(
            self.client, '192.0.0.3', 'regionOne', None, 'keystone.public',
            'keystone.admin', None)
        public_endpoint = 'http://keystone.public:5000/v2.0'
        admin_endpoint = 'http://keystone.admin:35357/v2.0'
        self.assert_endpoint('192.0.0.3', public_endpoint=public_endpoint,
                             admin_endpoint=admin_endpoint)

    def test_create_keystone_endpoint_ssl_public_and_admin(self):
        self._patch_client()

        self.client.services.findall.return_value = []
        self.client.endpoints.findall.return_value = []

        keystone._create_keystone_endpoint(
            self.client, '192.0.0.3', 'regionOne', 'keystone.example.com',
            'keystone.public', 'keystone.admin', None)
        public_endpoint = 'https://keystone.example.com:13000/v2.0'
        admin_endpoint = 'http://keystone.admin:35357/v2.0'
        self.assert_endpoint('192.0.0.3', public_endpoint=public_endpoint,
                             admin_endpoint=admin_endpoint)

    def test_create_keystone_endpoint_public_admin_and_internal(self):
        self._patch_client()

        self.client.services.findall.return_value = []
        self.client.endpoints.findall.return_value = []

        keystone._create_keystone_endpoint(
            self.client, '192.0.0.3', 'regionOne', None, 'keystone.public',
            'keystone.admin', 'keystone.internal')
        public_endpoint = 'http://keystone.public:5000/v2.0'
        admin_endpoint = 'http://keystone.admin:35357/v2.0'
        internal_endpoint = 'http://keystone.internal:5000/v2.0'
        self.assert_endpoint('192.0.0.3', public_endpoint=public_endpoint,
                             admin_endpoint=admin_endpoint,
                             internal_endpoint=internal_endpoint)

    def test_create_keystone_endpoint_ssl_public_admin_and_internal(self):
        self._patch_client()

        self.client.services.findall.return_value = []
        self.client.endpoints.findall.return_value = []

        keystone._create_keystone_endpoint(
            self.client, '192.0.0.3', 'regionOne', 'keystone.example.com',
            'keystone.public', 'keystone.admin', 'keystone.internal')
        public_endpoint = 'https://keystone.example.com:13000/v2.0'
        admin_endpoint = 'http://keystone.admin:35357/v2.0'
        internal_endpoint = 'http://keystone.internal:5000/v2.0'
        self.assert_endpoint('192.0.0.3', public_endpoint=public_endpoint,
                             admin_endpoint=admin_endpoint,
                             internal_endpoint=internal_endpoint)

    def test_create_keystone_endpoint_region(self):
        self._patch_client()

        self.client.services.findall.return_value = []
        self.client.endpoints.findall.return_value = []

        keystone._create_keystone_endpoint(
            self.client, '192.0.0.3', 'regionTwo', None, None, None, None)
        self.assert_endpoint('192.0.0.3', region='regionTwo')

    def test_create_keystone_endpoint_ipv6(self):
        self._patch_client()

        self.client.services.findall.return_value = []
        self.client.endpoints.findall.return_value = []

        keystone._create_keystone_endpoint(
            self.client, '2001:db8:fd00:1000:f816:3eff:fec2:8e7c',
            'regionOne',
            None,
            '2001:db8:fd00:1000:f816:3eff:fec2:8e7d',
            '2001:db8:fd00:1000:f816:3eff:fec2:8e7e',
            '2001:db8:fd00:1000:f816:3eff:fec2:8e7f')
        pe = 'http://[2001:db8:fd00:1000:f816:3eff:fec2:8e7d]:5000/v2.0'
        ae = 'http://[2001:db8:fd00:1000:f816:3eff:fec2:8e7e]:35357/v2.0'
        ie = 'http://[2001:db8:fd00:1000:f816:3eff:fec2:8e7f]:5000/v2.0'
        self.assert_endpoint(
            '[2001:db8:fd00:1000:f816:3eff:fec2:8e7c]',
            region='regionOne', public_endpoint=pe, admin_endpoint=ae,
            internal_endpoint=ie)

    @mock.patch('time.sleep')
    def test_create_roles_retry(self, sleep):
        self._patch_client()
        side_effect = (exceptions.ConnectionRefused,
                       exceptions.ServiceUnavailable, mock.DEFAULT,
                       mock.DEFAULT)
        self.client.roles.create.side_effect = side_effect
        self.client.roles.findall.return_value = []

        keystone._create_roles(self.client)
        sleep.assert_has_calls([mock.call(10), mock.call(10)])

    def test_setup_endpoints(self):
        self.client = mock.MagicMock()
        self.client.users.find.side_effect = ksclient_v2.exceptions.NotFound()
        self.client.services.findall.return_value = []
        self.client.endpoints.findall.return_value = []

        keystone.setup_endpoints(
            {'nova': {'password': 'pass', 'type': 'compute',
                      'ssl_port': 1234}},
            public_host='192.0.0.4', region='region', client=self.client,
            os_auth_url='https://192.0.0.3')

        self.client.users.find.assert_called_once_with(name='nova')
        self.client.tenants.find.assert_called_once_with(name='service')
        self.client.roles.find.assert_called_once_with(name='admin')
        self.client.services.findall.assert_called_once_with(type='compute')
        self.client.endpoints.findall.assert_called_once_with(
            publicurl='https://192.0.0.4:1234/v2.1/$(tenant_id)s')

        self.client.users.create.assert_called_once_with(
            'nova', 'pass',
            tenant_id=self.client.tenants.find.return_value.id,
            email='email=nobody@example.com')

        self.client.roles.add_user_role.assert_called_once_with(
            self.client.users.create.return_value,
            self.client.roles.find.return_value,
            self.client.tenants.find.return_value)

        self.client.services.create.assert_called_once_with(
            'nova', 'compute', description='Nova Compute Service')
        self.client.endpoints.create.assert_called_once_with(
            'region',
            self.client.services.create.return_value.id,
            'https://192.0.0.4:1234/v2.1/$(tenant_id)s',
            'http://192.0.0.3:8774/v2.1/$(tenant_id)s',
            'http://192.0.0.3:8774/v2.1/$(tenant_id)s')

    def test_setup_endpoints_ipv6(self):
        self.client = mock.MagicMock()
        self.client.users.find.side_effect = ksclient_v2.exceptions.NotFound()
        self.client.services.findall.return_value = []
        self.client.endpoints.findall.return_value = []

        keystone.setup_endpoints(
            {'nova': {'password': 'pass', 'type': 'compute',
                      'ssl_port': 1234}},
            public_host='2001:db8:fd00:1000:f816:3eff:fec2:8e7c',
            region='region', client=self.client,
            os_auth_url='https://[2001:db8:fd00:1000:f816:3eff:fec2:8e7c]')

        self.client.users.find.assert_called_once_with(name='nova')
        self.client.tenants.find.assert_called_once_with(name='service')
        self.client.roles.find.assert_called_once_with(name='admin')
        self.client.services.findall.assert_called_once_with(type='compute')
        self.client.endpoints.findall.assert_called_once_with(
            publicurl='https://[2001:db8:fd00:1000:f816:3eff:fec2:8e7c]'
                      ':1234/v2.1/$(tenant_id)s')

        self.client.users.create.assert_called_once_with(
            'nova', 'pass',
            tenant_id=self.client.tenants.find.return_value.id,
            email='email=nobody@example.com')

        self.client.roles.add_user_role.assert_called_once_with(
            self.client.users.create.return_value,
            self.client.roles.find.return_value,
            self.client.tenants.find.return_value)

        self.client.services.create.assert_called_once_with(
            'nova', 'compute', description='Nova Compute Service')
        ipv6_addr = '2001:db8:fd00:1000:f816:3eff:fec2:8e7c'
        self.client.endpoints.create.assert_called_once_with(
            'region',
            self.client.services.create.return_value.id,
            'https://[%s]:1234/v2.1/$(tenant_id)s' % ipv6_addr,
            'http://[%s]:8774/v2.1/$(tenant_id)s' % ipv6_addr,
            'http://[%s]:8774/v2.1/$(tenant_id)s' % ipv6_addr)

    @mock.patch('os_cloud_config.keystone._create_service')
    def test_create_ssl_endpoint_no_ssl_port(self, mock_create_service):
        client = mock.Mock()
        client.endpoints.findall.return_value = []
        data = {'nouser': True,
                'internal_host': 'internal',
                'public_host': 'public',
                'port': 1234,
                'password': 'password',
                'type': 'compute',
                }
        mock_service = mock.Mock()
        mock_service.id = 1
        mock_create_service.return_value = mock_service
        keystone._register_endpoint(client, 'fake', data)
        client.endpoints.create.assert_called_once_with(
            'regionOne', 1,
            'http://public:1234/',
            'http://internal:1234/',
            'http://internal:1234/')

    def test_idempotent_register_endpoint(self):
        self.client = mock.MagicMock()

        # Explicitly defining that endpoint has been already created
        self.client.users.find.return_value = mock.MagicMock()
        self.client.services.findall.return_value = mock.MagicMock()
        self.client.endpoints.findall.return_value = mock.MagicMock()

        keystone._register_endpoint(
            self.client,
            'nova',
            {'password': 'pass', 'type': 'compute',
             'ssl_port': 1234, 'public_host': '192.0.0.4',
             'internal_host': '192.0.0.3'},
            region=None)

        # Calling just a subset of find APIs
        self.client.users.find.assert_called_once_with(name='nova')
        self.assertFalse(self.client.tenants.find.called)
        self.assertFalse(self.client.roles.find.called)
        self.client.services.findall.assert_called_once_with(type='compute')
        self.client.endpoints.findall.assert_called_once_with(
            publicurl='https://192.0.0.4:1234/')

        # None of creating API calls has been called
        self.assertFalse(self.client.users.create.called)
        self.assertFalse(self.client.roles.add_user_role.called)
        self.assertFalse(self.client.services.create.called)
        self.assertFalse(self.client.endpoints.create.called)

    @mock.patch('os_cloud_config.keystone.ksclient_v2.Client')
    def test_create_admin_client_v2(self, client):
        self.assertEqual(
            client.return_value,
            keystone._create_admin_client_v2('192.0.0.3', 'mytoken'))
        client.assert_called_once_with(endpoint='http://192.0.0.3:35357/v2.0',
                                       token='mytoken')

    def _patch_client(self):
        self.client = mock.MagicMock()
        self.create_admin_client_patcher = mock.patch(
            'os_cloud_config.keystone._create_admin_client_v2')
        create_admin_client = self.create_admin_client_patcher.start()
        self.addCleanup(self._patch_client_cleanup)
        create_admin_client.return_value = self.client

    def _patch_client_cleanup(self):
        self.create_admin_client_patcher.stop()
        self.client = None

    @mock.patch('os_cloud_config.keystone.ksclient_v3.Client')
    def test_create_admin_client_v3(self, client_v3):
        self.assertEqual(
            client_v3.return_value,
            keystone._create_admin_client_v3('192.0.0.3', 'mytoken'))
        client_v3.assert_called_once_with(endpoint='http://192.0.0.3:35357/v3',
                                          token='mytoken')

    def _patch_client_v3(self):
        self.client_v3 = mock.MagicMock()
        self.create_admin_client_patcher_v3 = mock.patch(
            'os_cloud_config.keystone._create_admin_client_v3')
        create_admin_client_v3 = self.create_admin_client_patcher_v3.start()
        self.addCleanup(self._patch_client_cleanup_v3)
        create_admin_client_v3.return_value = self.client_v3

    def _patch_client_cleanup_v3(self):
        self.create_admin_client_patcher_v3.stop()
        self.client_v3 = None

    def test_create_admin_user_user_exists(self):
        self._patch_client()
        keystone._create_admin_user(self.client, 'admin@example.org',
                                    'adminpasswd')
        self.client.tenants.find.assert_called_once_with(name='admin')
        self.client.users.create.assert_not_called()

    def test_create_admin_user_user_does_not_exist(self):
        self._patch_client()
        self.client.users.find.side_effect = exceptions.NotFound()
        keystone._create_admin_user(self.client, 'admin@example.org',
                                    'adminpasswd')
        self.client.tenants.find.assert_called_once_with(name='admin')
        self.client.users.create.assert_called_once_with(
            'admin', email='admin@example.org', password='adminpasswd',
            tenant_id=self.client.tenants.find.return_value.id)

    def test_grant_admin_user_roles_idempotent(self):
        self._patch_client_v3()
        self.client_v3.roles.list.return_value = (
            [self.client_v3.roles.list.return_value['admin']])
        keystone._grant_admin_user_roles(self.client_v3)
        self.assert_calls_in_grant_admin_user_roles()
        self.client_v3.roles.grant.assert_not_called()

    def list_roles_side_effect(self, *args, **kwargs):
        if kwargs.get('name') == 'admin':
            return [self.client_v3.roles.list.return_value[0]]
        else:
            return []

    def test_grant_admin_user_roles(self):
        self._patch_client_v3()
        self.client_v3.roles.list.side_effect = self.list_roles_side_effect
        keystone._grant_admin_user_roles(self.client_v3)
        self.assert_calls_in_grant_admin_user_roles()
        self.client_v3.roles.grant.assert_has_calls([
            mock.call(self.client_v3.roles.list.return_value[0],
                      user=self.client_v3.users.list.return_value[0],
                      project=self.client_v3.projects.list.return_value[0]),
            mock.call(self.client_v3.roles.list.return_value[0],
                      user=self.client_v3.users.list.return_value[0],
                      domain=self.client_v3.domains.list.return_value[0])])
