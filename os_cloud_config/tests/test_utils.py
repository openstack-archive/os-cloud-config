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
import testtools

from os_cloud_config import exception
from os_cloud_config.tests import base
from os_cloud_config import utils
from os_cloud_config.utils import _clients as clients


class UtilsTest(base.TestCase):

    @mock.patch.dict('os.environ', {})
    def test_ensure_environment_missing_all(self):
        message = ("OS_AUTH_URL, OS_PASSWORD, OS_TENANT_NAME, OS_USERNAME "
                   "environment variables are required to be set.")
        with testtools.ExpectedException(exception.MissingEnvironment,
                                         message):
            utils._ensure_environment()

    @mock.patch.dict('os.environ', {'OS_PASSWORD': 'a', 'OS_AUTH_URL': 'a',
                     'OS_TENANT_NAME': 'a'})
    def test_ensure_environment_missing_username(self):
        message = "OS_USERNAME environment variable is required to be set."
        with testtools.ExpectedException(exception.MissingEnvironment,
                                         message):
            utils._ensure_environment()

    @mock.patch.dict('os.environ', {'OS_PASSWORD': 'a', 'OS_AUTH_URL': 'a',
                     'OS_TENANT_NAME': 'a', 'OS_USERNAME': 'a'})
    def test_ensure_environment_missing_none(self):
        self.assertIs(None, utils._ensure_environment())

    @mock.patch('os.environ')
    @mock.patch('ironicclient.client.get_client')
    def test_get_ironic_client(self, client_mock, environ):
        clients.get_ironic_client()
        client_mock.assert_called_once_with(
            1, os_username=environ["OS_USERNAME"],
            os_password=environ["OS_PASSWORD"],
            os_auth_url=environ["OS_AUTH_URL"],
            os_tenant_name=environ["OS_TENANT_NAME"])

    @mock.patch('os.environ')
    @mock.patch('novaclient.v1_1.client.Client')
    def test_get_nova_bm_client(self, client_mock, environ):
        clients.get_nova_bm_client()
        client_mock.assert_called_once_with(environ["OS_USERNAME"],
                                            environ["OS_PASSWORD"],
                                            environ["OS_AUTH_URL"],
                                            environ["OS_TENANT_NAME"],
                                            extensions=[mock.ANY])

    @mock.patch('os.environ')
    @mock.patch('keystoneclient.v2_0.client.Client')
    def test_get_keystone_client(self, client_mock, environ):
        clients.get_keystone_client()
        client_mock.assert_called_once_with(
            username=environ["OS_USERNAME"],
            password=environ["OS_PASSWORD"],
            auth_url=environ["OS_AUTH_URL"],
            tenant_name=environ["OS_TENANT_NAME"])
