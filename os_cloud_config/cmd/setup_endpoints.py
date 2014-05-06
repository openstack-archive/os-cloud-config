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

from optparse import OptionParser
import simplejson
import sys
import textwrap

from os_cloud_config import keystone


def parse_args(args):
    usage = textwrap.dedent("""
    %prog [options] -s <json-services-file>

    Register endpoints for specified services.

    The JSON services file contains a dict of services metadata. Each item is
    a JSON object describing one service. You can define following keys for
    each service:

    description   - description of service
    type          - type of service
    path          - path part of endpoint URI
    admin_path    - path part of admin endpoint URI
    port          - endpoint's port
    ssl_port      - if 'public' parameter is specified, public endpoint URI
                    is composed of public IP and this SSL port
    password      - password set for service's user
    """)
    parser = OptionParser(usage=usage)
    parser.add_option('-o', '--host', dest='host',
                      help='ip/hostname of node where Keystone is running')
    parser.add_option('-t', '--admin-token', dest='admin_token',
                      help='admin token to use with Keystone\'s admin '
                           'endpoint')
    parser.add_option('-s', '--services', dest='services',
                      help='a JSON file containing a list of services that '
                           'are intended to be registered')
    parser.add_option('-p', '--public', dest='public_host',
                      help='ip/hostname used for public endpoint URI, HTTPS '
                           'will be used')
    parser.add_option('-r', '--region', dest='region',
                      help='represents the geographic location of the '
                           'service endpoint')
    return parser.parse_args()


def main(stdout=None):
    if stdout is None:
        stdout = sys.stdout
    (options, args) = parse_args(sys.argv)
    if not options.services:
        print("The --host, --admin-token and --services options "
              "are required.", file=stdout)
        return 1

    with open(options.services, 'r') as service_file:
        services = simplejson.load(service_file)

    keystone.setup_endpoints(options.host, options.admin_token, services,
                             public_host=options.public_host,
                             region=options.region)
