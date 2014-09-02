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
import os
import simplejson
import sys
import textwrap

from os_cloud_config import keystone
from os_cloud_config import utils


def parse_args():
    description = textwrap.dedent("""
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
    name          - create user and service with specified name, service key
                    name is used by default
    nouser        - don't create user for service
    """)
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=description)
    parser.add_argument('-s', '--services', dest='services', required=True,
                        help='a JSON file containing a list of services that '
                             'are intended to be registered')
    parser.add_argument('-p', '--public', dest='public_host',
                        help='ip/hostname used for public endpoint URI, HTTPS '
                             'will be used')
    parser.add_argument('-r', '--region', dest='region',
                        help='represents the geographic location of the '
                             'service endpoint')
    utils._add_logging_arguments(parser)
    return parser.parse_args()


def main(stdout=None):
    args = parse_args()
    utils._configure_logging(args)

    sys.stderr.write(args.services)
    if os.path.isfile(args.services):
        with open(args.services, 'r') as service_file:
            services = simplejson.load(service_file)
    else:
        # we assume it's just JSON string
        services = simplejson.loads(args.services)

    keystone.setup_endpoints(
        services,
        public_host=args.public_host,
        region=args.region,
        os_username=os.environ["OS_USERNAME"],
        os_password=os.environ["OS_PASSWORD"],
        os_tenant_name=os.environ["OS_TENANT_NAME"],
        os_auth_url=os.environ["OS_AUTH_URL"])
