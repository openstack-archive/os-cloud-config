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

from os_cloud_config.cmd.utils import environment
from os_cloud_config import exception
from os_cloud_config.tests import base


class CMDEnviromentTest(base.TestCase):

    @mock.patch.dict('os.environ', {})
    def test_ensure_environment_missing_all(self):
        message = ("OS_AUTH_URL, OS_PASSWORD, OS_TENANT_NAME, OS_USERNAME "
                   "environment variables are required to be set.")
        with testtools.ExpectedException(exception.MissingEnvironment,
                                         message):
            environment._ensure()

    @mock.patch.dict('os.environ', {'OS_PASSWORD': 'a', 'OS_AUTH_URL': 'a',
                     'OS_TENANT_NAME': 'a'})
    def test_ensure_environment_missing_username(self):
        message = "OS_USERNAME environment variable is required to be set."
        with testtools.ExpectedException(exception.MissingEnvironment,
                                         message):
            environment._ensure()

    @mock.patch.dict('os.environ', {'OS_PASSWORD': 'a', 'OS_AUTH_URL': 'a',
                     'OS_TENANT_NAME': 'a', 'OS_USERNAME': 'a'})
    def test_ensure_environment_missing_none(self):
        self.assertIs(None, environment._ensure())
