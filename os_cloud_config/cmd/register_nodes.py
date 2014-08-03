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

from __future__ import print_function

import argparse
import json
import textwrap

from os_cloud_config import nodes
from os_cloud_config import utils


def parse_args():
    description = textwrap.dedent("""
    Register nodes with either Ironic or Nova-baremetal.

    The JSON nodes file contains a list of node metadata. Each list item is
    a JSON object describing one node, which has "memory" in KB, "cpu" in
    threads, "arch" (one of i386/amd64/etc), "disk" in GB, "mac" a list of
    MAC addresses for the node, and "pm_type", "pm_user", "pm_addr" and
    "pm_password" describing power management details.

    Ironic will be used if the Ironic service is registered with Keystone.

    This program will wait up to 10 minutes for the baremetal service to
    register a node.
    """)
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=description)
    parser.add_argument('-s', '--service-host', dest='service_host',
                        help='Nova-bm service host to register nodes with')
    parser.add_argument('-n', '--nodes', dest='nodes', required=True,
                        help='A JSON file containing a list of nodes that '
                        'are intended to be registered')
    return parser.parse_args()


def main():
    args = parse_args()

    try:
        with open(args.nodes, 'r') as node_file:
            nodes_list = json.load(node_file)
        utils._ensure_environment()

        # TODO(StevenK): Filter out registered nodes.
        nodes.register_all_nodes(args.service_host, nodes_list)
    except Exception as e:
        print(e.message)
        return 1
    return 0
