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

from os_cloud_config import keystone_pki


def parse_args():
    description = textwrap.dedent("""
    Generate 4 files inside <directory> for use with Keystone PKI
    token signing:

    ca_key.pem       - certificate authority key
    ca_cert.pem      - self-signed certificate authority certificate
    signing_key.pem  - key for signing tokens
    signing_cert.pem - certificate for verifying token validity, the
                       certificate itself is verifiable by ca_cert.pem

    ca_key.pem doesn't have to (shouldn't) be uploaded to Keystone nodes.
    """)

    parser = argparse.ArgumentParser(
        description=description,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        'directory',
        metavar='<directory>',
        help='directory where keys/certs will be generated',
    )
    return parser.parse_args()


def main():
    args = parse_args()
    keystone_pki.create_and_write_ca_and_signing_pairs(args.directory)
