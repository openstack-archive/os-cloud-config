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

import mock

from os_cloud_config.cmd.utils import _clients as clients
from os_cloud_config.tests import base


class CMDClientsTest(base.TestCase):

    @mock.patch.dict('os.environ', {'OS_USERNAME': 'username',
                                    'OS_PASSWORD': 'password',
                                    'OS_TENANT_NAME': 'tenant',
                                    'OS_AUTH_URL': 'auth_url',
                                    'OS_CACERT': 'cacert'})
    def test___get_client_args(self):
        result = clients._get_client_args()
        expected = ("username", "password", "tenant", "auth_url", "cacert")
        self.assertEqual(result, expected)

    @mock.patch('os.environ')
    @mock.patch('ironicclient.client.get_client')
    def test_get_ironic_client(self, client_mock, environ):
        clients.get_ironic_client()
        client_mock.assert_called_once_with(
            1, os_username=environ["OS_USERNAME"],
            os_password=environ["OS_PASSWORD"],
            os_auth_url=environ["OS_AUTH_URL"],
            os_tenant_name=environ["OS_TENANT_NAME"],
            ca_file=environ.get("OS_CACERT"))

    @mock.patch('os.environ')
    @mock.patch('novaclient.client.Client')
    def test_get_nova_bm_client(self, client_mock, environ):
        clients.get_nova_bm_client()
        client_mock.assert_called_once_with("2", environ["OS_USERNAME"],
                                            environ["OS_PASSWORD"],
                                            environ["OS_AUTH_URL"],
                                            environ["OS_TENANT_NAME"],
                                            cacert=environ.get("OS_CACERT"),
                                            extensions=[mock.ANY])

    @mock.patch('os.environ')
    @mock.patch('keystoneclient.v2_0.client.Client')
    def test_get_keystone_client(self, client_mock, environ):
        clients.get_keystone_client()
        client_mock.assert_called_once_with(
            username=environ["OS_USERNAME"],
            password=environ["OS_PASSWORD"],
            auth_url=environ["OS_AUTH_URL"],
            tenant_name=environ["OS_TENANT_NAME"],
            cacert=environ.get("OS_CACERT"))

    @mock.patch('os.environ')
    @mock.patch('keystoneclient.v3.client.Client')
    def test_get_keystone_v3_client(self, client_mock, environ):
        clients.get_keystone_v3_client()
        client_mock.assert_called_once_with(
            username=environ["OS_USERNAME"],
            password=environ["OS_PASSWORD"],
            auth_url=environ["OS_AUTH_URL"].replace('v2.0', 'v3'),
            tenant_name=environ["OS_TENANT_NAME"],
            cacert=environ.get("OS_CACERT"))

    @mock.patch('os.environ')
    @mock.patch('neutronclient.neutron.client.Client')
    def test_get_neutron_client(self, client_mock, environ):
        clients.get_neutron_client()
        client_mock.assert_called_once_with(
            '2.0', username=environ["OS_USERNAME"],
            password=environ["OS_PASSWORD"],
            auth_url=environ["OS_AUTH_URL"],
            tenant_name=environ["OS_TENANT_NAME"],
            ca_cert=environ.get("OS_CACERT"))

    @mock.patch('os.environ')
    @mock.patch('keystoneclient.session.Session')
    @mock.patch('keystoneclient.auth.identity.v2.Password')
    @mock.patch('glanceclient.Client')
    def test_get_glance_client(self, client_mock, password_mock, session_mock,
                               environ):
        clients.get_glance_client()
        tenant_name = environ["OS_TENANT_NAME"]
        password_mock.assert_called_once_with(auth_url=environ["OS_AUTH_URL"],
                                              username=environ["OS_USERNAME"],
                                              password=environ["OS_PASSWORD"],
                                              tenant_name=tenant_name)
        session_mock.assert_called_once_with(auth=password_mock.return_value)
        session_mock.return_value.get_endpoint.assert_called_once_with(
            service_type='image', interface='public', region_name='regionOne')
        session_mock.return_value.get_token.assert_called_once_with()
        client_mock.assert_called_once_with(
            '1', endpoint=session_mock.return_value.get_endpoint.return_value,
            token=session_mock.return_value.get_token.return_value,
            cacert=environ.get('OS_CACERT'))
