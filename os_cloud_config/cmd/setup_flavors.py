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

from __future__ import print_function

import argparse
import json
import logging
import os
import textwrap

from os_cloud_config.cmd.utils import _clients as clients
from os_cloud_config.cmd.utils import environment
from os_cloud_config import flavors
from os_cloud_config import glance


def parse_args():
    description = textwrap.dedent("""
    Create flavors describing the compute resources the cloud has
    available.

    If the list of flavors is only meant to encompass hardware that the cloud
    has available, a JSON file describing the nodes can be specified, see
    register-nodes for the format.

    If a custom list of flavors is to be created, they can be specified as a
    list of JSON objects. Each list item is a JSON object describing one
    flavor, which has a "name" for the flavor, "memory" in MB, "cpu" in
    threads, "disk" in GB and "arch" as one of i386/amd64/etc.

    If both --kernel and --kernel-name (or --ramdisk and --ramdisk-name),
    --kernel-name (or --ramdisk-name) will trump the passed in ID.
    """)

    parser = argparse.ArgumentParser(
        description=description,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-n', '--nodes', dest='nodes',
                       help='A JSON file containing a list of nodes that '
                       'distinct flavors will be generated and created from')
    group.add_argument('-f', '--flavors', dest='flavors',
                       help='A JSON file containing a list of flavors to '
                       'create directly')
    parser.add_argument('-k', '--kernel', dest='kernel',
                        help='ID of the kernel in Glance')
    parser.add_argument('--kernel-name', dest='kernel_name',
                        help='Name of the kernel registered in Glance')
    parser.add_argument('-r', '--ramdisk', dest='ramdisk',
                        help='ID of the ramdisk in Glance')
    parser.add_argument('--ramdisk-name', dest='ramdisk_name',
                        help='Name of the ramdisk registered in Glance')
    environment._add_logging_arguments(parser)
    return parser.parse_args()


def _find_image_ids(kernel, ramdisk, kernel_name, ramdisk_name):
    if kernel_name or ramdisk_name:
        glance_client = clients.get_glance_client()
        glance_ids = glance.create_or_find_kernel_and_ramdisk(
            glance_client, kernel_name, ramdisk_name, skip_missing=True)
        kernel = glance_ids['kernel'] or kernel
        ramdisk = glance_ids['ramdisk'] or ramdisk
    if not kernel:
        raise ValueError(
            "Can not find kernel with name %s registered in Glance." %
            kernel_name)
    if not ramdisk:
        raise ValueError(
            "Can not find ramdisk with name %s registered in Glance." %
            ramdisk_name)
    return kernel, ramdisk


def main():
    args = parse_args()
    environment._configure_logging(args)
    try:
        environment._ensure()
        client = clients.get_nova_bm_client()
        flavors.cleanup_flavors(client)
        root_disk = os.environ.get('ROOT_DISK', None)
        if not args.kernel and not args.kernel_name:
            print("One of --kernel or --kernel-name is required.")
            return 1
        if not args.ramdisk and not args.ramdisk_name:
            print("One of --ramdisk or --ramdisk-name is required.")
            return 1
        try:
            kernel, ramdisk = _find_image_ids(args.kernel, args.ramdisk,
                                              args.kernel_name,
                                              args.ramdisk_name)
        except ValueError as e:
            print(e)
            return 1
        if args.nodes:
            with open(args.nodes, 'r') as nodes_file:
                nodes_list = json.load(nodes_file)
            flavors.create_flavors_from_nodes(
                client, nodes_list, kernel, ramdisk, root_disk)
        elif args.flavors:
            with open(args.flavors, 'r') as flavors_file:
                flavors_list = json.load(flavors_file)
            flavors.create_flavors_from_list(
                client, flavors_list, kernel, ramdisk)
    except Exception:
        logging.exception("Unexpected error during command execution")
        return 1
    return 0
