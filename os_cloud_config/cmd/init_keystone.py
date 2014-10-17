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

from os_cloud_config.cmd.utils import environment
from os_cloud_config.keystone import initialize


def parse_args():
    description = textwrap.dedent("""
    Perform initial setup of keystone for a new cloud.

    This will create the admin and service tenants, the admin role, the admin
    user, configure certificates and finally register the initial identity
    endpoint, after which Keystone may be used with normal authentication.

    This command will wait for a user-specified amount of time for a Keystone
    service to be running on the specified host.  The default is a 10 minute
    wait time with 10 seconds between poll attempts.
    """)
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=description)
    parser.add_argument('-o', '--host', dest='host', required=True,
                        help="ip/hostname of node where Keystone is running")
    parser.add_argument('-t', '--admin-token', dest='admin_token',
                        help="admin token to use with Keystone's admin "
                        "endpoint", required=True)
    parser.add_argument('-e', '--admin-email', dest='admin_email',
                        help="admin user's e-mail address to be set",
                        required=True)
    parser.add_argument('-p', '--admin-password', dest='admin_password',
                        help="admin user's password to be set",
                        required=True)
    parser.add_argument('-r', '--region', dest='region', default='regionOne',
                        help="region to create the endpoint in")
    endpoint_group = parser.add_mutually_exclusive_group()
    endpoint_group.add_argument('-s', '--ssl', dest='ssl',
                                help="ip/hostname to use as the ssl "
                                "endpoint, if required")
    endpoint_group.add_argument('--public', dest='public',
                                help="ip/hostname to use as the public "
                                "endpoint, if the default is not suitable")
    parser.add_argument('-u', '--user', dest='user',
                        help="user to connect to the Keystone node via ssh, "
                        "required with --pki-setup")
    parser.add_argument('--timeout', dest='timeout', default=600, type=int,
                        help="Total seconds to wait for keystone to be ready")
    parser.add_argument('--poll-interval', dest='pollinterval',
                        default=10, type=int,
                        help="Seconds to wait between keystone checks")
    pki_group = parser.add_mutually_exclusive_group()
    pki_group.add_argument('--pki-setup', dest='pkisetup',
                           action='store_true',
                           help="Perform PKI setup (DEPRECATED)", default=True)
    pki_group.add_argument('--no-pki-setup', dest='pkisetup',
                           action='store_false',
                           help="Do not perform PKI setup")
    environment._add_logging_arguments(parser)
    return parser.parse_args()


def main():
    args = parse_args()
    environment._configure_logging(args)

    if args.pkisetup and not args.user:
        print("User is required if PKI setup will be performed.")
        return 1
    initialize(args.host, args.admin_token, args.admin_email,
               args.admin_password, args.region, args.ssl, args.public,
               args.user, args.timeout, args.pollinterval, args.pkisetup)
