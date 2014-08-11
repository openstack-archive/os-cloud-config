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
import textwrap

import json

from os_cloud_config import neutron
from os_cloud_config import utils


def parse_args():
    description = textwrap.dedent("""
    Setup neutron for a new cloud.

    The JSON describing the network(s) to create is expected to be of the
    following form:

    {
      "physical": {
        "gateway": "192.0.2.1",
        "metadata_server": "192.0.2.1",
        "cidr": "192.0.2.0/24",
        "allocation_end": "192.0.2.20",
        "allocation_start": "192.0.2.2",
        "name": "ctlplane"
      },
      "float": {
        "allocation_start": "10.0.0.2",
        "allocation_end": "10.0.0.100",
        "name": "default-net"
        "cidr": "10.0.0.0/8"
      }
    }

    At least one network of the type 'physical' or 'float' is required. cidr
    and name are always required for each network, and physical networks
    also require metadata_server.
    """)
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=description)
    parser.add_argument('-n', '--network-json', dest='json',
                        help='JSON formatted description of the network(s) to '
                        'create', required=True)
    return parser.parse_args()


def main():
    args = parse_args()

    try:
        utils._ensure_environment()
        with open(args.json, 'r') as jsonfile:
            network_desc = json.load(jsonfile)
        neutron.initialize_neutron(network_desc)
    except Exception as e:
        print(str(e))
        return 1
    return 0
