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
import textwrap

from os_cloud_config import ssl_pki


def parse_args():
    description = textwrap.dedent("""
    Generate and sign certificate with CA

    This script generates a certificate and signes certificate using the CA
    in the heat environment. If no CA is in the heat environment then a new
    CA will be generated. The resulting certificate and CA (if one is made)
    are added to the heat environment.
    """)

    parser = argparse.ArgumentParser(
        description=description,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        'heat_env',
        metavar='<heat_env>',
        help='path to JSON heat environment file'
    )
    parser.add_argument(
        'name',
        metavar='<name>',
        help='name for key/certificate pair',
    )
    return parser.parse_args()


def main():
    args = parse_args()
    ssl_pki.create_and_write_certificate(args.directory, args.name,
                                         args.overwrite)
