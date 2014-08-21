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

import argparse
import json
import logging
import os
import textwrap

from os_cloud_config import flavors
from os_cloud_config import utils


def parse_args():
    description = textwrap.dedent("""
    Create flavors describing the compute resources the cloud has
    available.
    """)

    parser = argparse.ArgumentParser(
        description=description,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-n', '--nodes', dest='nodes',
                       help='nodes to create flavors from')
    group.add_argument('-f', '--flavors', dest='flavors',
                       help='description of flavors to create directly')
    parser.add_argument('-k', '--kernel', dest='kernel',
                        help='ID of the kernel in Glance', required=True)
    parser.add_argument('-r', '--ramdisk', dest='ramdisk',
                        help='ID of the ramdisk in Glance', required=True)
    utils._add_logging_arguments(parser)
    return parser.parse_args()


def main():
    args = parse_args()
    utils._configure_logging(args)
    try:
        utils._ensure_environment()
        flavors.cleanup_flavors()
        root_disk = None
        if os.environ.get('ROOT_DISK'):
            root_disk = os.environ.get('ROOT_DISK')
        if args.nodes:
            with open(args.nodes, 'r') as nodes_file:
                nodes_list = json.load(nodes_file)
            flavors.create_flavors_from_nodes(None, nodes_list, args.kernel,
                                              args.ramdisk, root_disk)
        elif args.flavors:
            with open(args.flavors, 'r') as flavors_file:
                flavors_list = json.load(flavors_file)
            flavors.create_flavors_from_list(None, flavors_list, args.kernel,
                                             args.ramdisk)
    except Exception as e:
        logging.exception("Unexpected error during command execution")
        return 1
    return 0
