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

from os_cloud_config.cmd import upload_kernel_ramdisk
from os_cloud_config.tests import base


class UploadKernelRamdiskTest(base.TestCase):

    @mock.patch('os_cloud_config.cmd.utils._clients.get_glance_client',
                return_value='glance_client_mock')
    @mock.patch('os_cloud_config.glance.create_or_find_kernel_and_ramdisk')
    @mock.patch.dict('os.environ', {'OS_USERNAME': 'a', 'OS_PASSWORD': 'a',
                     'OS_TENANT_NAME': 'a', 'OS_AUTH_URL': 'a'})
    @mock.patch.object(sys, 'argv', ['upload_kernel_ramdisk', '-k',
                                     'bm-kernel', '-r', 'bm-ramdisk', '-l',
                                     'kernel-file', '-s', 'ramdisk-file'])
    def test_with_arguments(self, create_or_find_mock, glanceclient_mock):
        upload_kernel_ramdisk.main()
        create_or_find_mock.assert_called_once_with(
            'glance_client_mock', 'bm-kernel', 'bm-ramdisk',
            kernel_path='kernel-file', ramdisk_path='ramdisk-file')
