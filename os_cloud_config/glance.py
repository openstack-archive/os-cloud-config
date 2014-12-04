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

import logging

from glanceclient.openstack.common.apiclient import exceptions

LOG = logging.getLogger(__name__)


def create_or_find_kernel_and_ramdisk(glanceclient, kernel_name, ramdisk_name,
                                      kernel_path=None, ramdisk_path=None):
    """Find or create a given kernel and ramdisk in Glance.

    If either kernel_path or ramdisk_path is None, they will not be created,
    and an exception will be raised if it does not exist in Glance.

    :param glanceclient: A client for Glance.
    :param kernel_name: Name to search for or create for the kernel.
    :param ramdisk_name: Name to search for or create for the ramdisk.
    :param kernel_path: Path to the kernel on disk.
    :param ramdisk_path: Path to the ramdisk on disk.

    :returns: A dictionary mapping kernel or ramdisk to the ID in Glance.
    """
    try:
        kernel_image = glanceclient.images.find(name=kernel_name,
                                                disk_format='aki')
    except exceptions.NotFound:
        if kernel_path:
            kernel_image = glanceclient.images.create(
                name=kernel_name, disk_format='aki', is_public=True,
                data=open(kernel_path, 'rb'))
        else:
            raise ValueError("Kernel image not found in Glance, and no path "
                             "specified.")
    try:
        ramdisk_image = glanceclient.images.find(name=ramdisk_name,
                                                 disk_format='ari')
    except exceptions.NotFound:
        if ramdisk_path:
            # public, type=ari
            ramdisk_image = glanceclient.images.create(
                name=ramdisk_name, disk_format='ari', is_public=True,
                data=open(ramdisk_path, 'rb'))
        else:
            raise ValueError("Ramdisk image not found in Glance, and no path "
                             "specified.")
    return {'kernel': kernel_image.id, 'ramdisk': ramdisk_image.id}
