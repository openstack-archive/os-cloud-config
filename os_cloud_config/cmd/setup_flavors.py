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
    return parser.parse_args()


def main():
    args = parse_args()
    try:
        utils._ensure_environment()
        flavors.cleanup_flavors()
        if args.nodes:
            with open(args.nodes, 'r') as nodes_file:
                nodes_list = json.load(nodes_file)
            flavors.create_flavors_from_nodes(None, nodes_list, args.kernel,
                                              args.ramdisk)
        elif args.flavors:
            with open(args.flavors, 'r') as flavors_file:
                flavors_list = json.load(flavors_file)
            flavors.create_flavors_from_list(None, flavors_list, args.kernel,
                                             args.ramdisk)
    except Exception as e:
        print(str(e))
        return 1
    return 0
