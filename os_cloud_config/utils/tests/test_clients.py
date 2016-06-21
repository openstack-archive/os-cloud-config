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

from os_cloud_config.tests import base
from os_cloud_config.utils import clients


class ClientsTest(base.TestCase):

    @mock.patch('ironicclient.client.get_client')
    def test_get_ironic_client(self, client_mock):
        clients.get_ironic_client('username', 'password', 'tenant_name',
                                  'auth_url')
        client_mock.assert_called_once_with(
            1, os_username='username',
            os_password='password',
            os_auth_url='auth_url',
            os_tenant_name='tenant_name',
            ca_file=None)

    @mock.patch('novaclient.client.Client')
    def test_get_nova_bm_client(self, client_mock):
        clients.get_nova_bm_client('username', 'password', 'tenant_name',
                                   'auth_url')
        client_mock.assert_called_once_with('2', 'username',
                                            'password',
                                            'tenant_name',
                                            'auth_url',
                                            cacert=None,
                                            extensions=[mock.ANY])

    @mock.patch('keystoneclient.v2_0.client.Client')
    def test_get_keystone_client(self, client_mock):
        clients.get_keystone_client('username', 'password', 'tenant_name',
                                    'auth_url')
        client_mock.assert_called_once_with(
            username='username',
            password='password',
            auth_url='auth_url',
            tenant_name='tenant_name',
            cacert=None)

    @mock.patch('keystoneclient.v3.client.Client')
    def test_get_keystone_v3_client_with_v2_url(self, client_mock):
        clients.get_keystone_v3_client('username', 'password', 'tenant_name',
                                       'auth_url/v2.0')
        client_mock.assert_called_once_with(
            username='username',
            password='password',
            auth_url='auth_url/v3',
            tenant_name='tenant_name',
            cacert=None)

    @mock.patch('keystoneclient.v3.client.Client')
    def test_get_keystone_v3_client_with_v3_url(self, client_mock):
        clients.get_keystone_v3_client('username', 'password', 'tenant_name',
                                       'auth_url/v3')
        client_mock.assert_called_once_with(
            username='username',
            password='password',
            auth_url='auth_url/v3',
            tenant_name='tenant_name',
            cacert=None)

    @mock.patch('neutronclient.neutron.client.Client')
    def test_get_neutron_client(self, client_mock):
        clients.get_neutron_client('username', 'password', 'tenant_name',
                                   'auth_url')
        client_mock.assert_called_once_with(
            '2.0', username='username',
            password='password',
            auth_url='auth_url',
            tenant_name='tenant_name',
            ca_cert=None)

    @mock.patch('keystoneclient.session.Session')
    @mock.patch('keystoneclient.auth.identity.v2.Password')
    @mock.patch('glanceclient.Client')
    def test_get_glance_client(self, client_mock, password_mock, session_mock):
        clients.get_glance_client('username', 'password', 'tenant_name',
                                  'auth_url')
        password_mock.assert_called_once_with(auth_url='auth_url',
                                              username='username',
                                              password='password',
                                              tenant_name='tenant_name')
        session_mock.assert_called_once_with(auth=password_mock.return_value)
        session_mock.return_value.get_endpoint.assert_called_once_with(
            service_type='image', interface='public', region_name='regionOne')
        session_mock.return_value.get_token.assert_called_once_with()
        client_mock.assert_called_once_with(
            '1', endpoint=session_mock.return_value.get_endpoint.return_value,
            token=session_mock.return_value.get_token.return_value,
            cacert=None)
