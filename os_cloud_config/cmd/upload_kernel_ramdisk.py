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

from os_cloud_config.cmd.utils import _clients as clients
from os_cloud_config.cmd.utils import environment
from os_cloud_config import glance


def parse_args():
    description = textwrap.dedent("""
    Uploads the provided kernel and ramdisk to a Glance store.
    """)

    parser = argparse.ArgumentParser(
        description=description,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument('-k', '--kernel', dest='kernel',
                        help='Name of the kernel image', required=True)
    parser.add_argument('-l' '--kernel-file', dest='kernel_file',
                        help='Kernel to upload', required=True)
    parser.add_argument('-r', '--ramdisk', dest='ramdisk',
                        help='Name of the ramdisk image', required=True)
    parser.add_argument('-s', '--ramdisk-file', dest='ramdisk_file',
                        help='Ramdisk to upload', required=True)
    environment._add_logging_arguments(parser)
    return parser.parse_args()


def main():
    args = parse_args()
    environment._configure_logging(args)
    try:
        environment._ensure()
        client = clients.get_glance_client()
        glance.create_or_find_kernel_and_ramdisk(
            client, args.kernel, args.ramdisk, kernel_path=args.kernel_file,
            ramdisk_path=args.ramdisk_file)
    except Exception:
        logging.exception("Unexpected error during command execution")
        return 1
    return 0
