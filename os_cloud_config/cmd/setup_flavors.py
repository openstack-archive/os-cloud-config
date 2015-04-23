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

from os_cloud_config.cmd.utils import _clients as clients
from os_cloud_config.cmd.utils import environment
from os_cloud_config import flavors


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
    group.add_argument('-i', '--ironic', action='store_true',
                       help='Pull the registered list of nodes from Ironic '
                       'that distinct flavors will be generated and created '
                       'from')
    parser.add_argument('-k', '--kernel', dest='kernel',
                        help='ID of the kernel in Glance', required=True)
    parser.add_argument('-r', '--ramdisk', dest='ramdisk',
                        help='ID of the ramdisk in Glance', required=True)
    environment._add_logging_arguments(parser)
    return parser.parse_args()


def main():
    args = parse_args()
    environment._configure_logging(args)
    try:
        environment._ensure()
        client = clients.get_nova_bm_client()
        flavors.cleanup_flavors(client)
        root_disk = os.environ.get('ROOT_DISK', None)
        if args.nodes:
            with open(args.nodes, 'r') as nodes_file:
                nodes_list = json.load(nodes_file)
            flavors.create_flavors_from_nodes(
                client, nodes_list, args.kernel, args.ramdisk, root_disk)
        elif args.flavors:
            with open(args.flavors, 'r') as flavors_file:
                flavors_list = json.load(flavors_file)
            flavors.create_flavors_from_list(
                client, flavors_list, args.kernel, args.ramdisk)
        elif args.ironic:
            ironic_client = clients.get_ironic_client()
            flavors.create_flavors_from_ironic(
                client, ironic_client, args.kernel, args.ramdisk, root_disk)
    except Exception:
        logging.exception("Unexpected error during command execution")
        return 1
    return 0
