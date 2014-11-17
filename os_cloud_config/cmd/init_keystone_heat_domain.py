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

import argparse
import logging
import textwrap

import os_cloud_config.cmd.utils._clients as clients
from os_cloud_config.cmd.utils import environment
from os_cloud_config.keystone import initialize_for_heat


def parse_args():
    description = textwrap.dedent("""
    Create a domain for Heat to use, as well as a user to administer it.

    This will create a heat domain in Keystone, as well as an admin user that
    has rights to administer the domain.
    """)
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=description)
    parser.add_argument('-d', '--domain-admin-password',
                        dest='domain_admin_password',
                        help="domain admin user's password to be set",
                        required=True)
    environment._add_logging_arguments(parser)
    return parser.parse_args()


def main():
    args = parse_args()
    environment._configure_logging(args)
    try:
        environment._ensure()
        keystone_client = clients.get_keystone_v3_client()
        initialize_for_heat(keystone_client, args.domain_admin_password)
    except Exception:
        logging.exception("Unexpected error during command execution")
        return 1
    return 0
