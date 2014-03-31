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

from optparse import OptionParser
import simplejson
import sys

from os_cloud_config import nodes


def parse_args(args):
    parser = OptionParser()
    parser.add_option('-s', '--service-host', dest='service_host',
                      help='Nova-bm service host to register nodes with')
    parser.add_option('-n', '--nodes', dest='nodes',
                      help='JSON list of nodes that are intended to be '
                           'registered')
    return parser.parse_args()


def main():
    (options, args) = parse_args(sys.argv)
    if not options.service_host:
        print("A Service Host is required.")
        return 1
    if not options.nodes:
        print("A JSON nodes file is required.")
        return 1

    with open(options.nodes, 'r') as node_file:
        nodes_list = simplejson.loads(node_file)

    nodes.check_service()
    # TODO(StevenK): Filter out registered nodes.
    nodes.register_all_nodes(options.service_host, nodes_list)
