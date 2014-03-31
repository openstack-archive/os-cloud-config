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
import sys

from os_cloud_config.keystone import initialize_for_heat


def parse_args(args):
    parser = OptionParser()
    parser.add_option('-o', '--host', dest='host',
                      help="ip/hostname of node where Keystone is running",
                      metavar='HOST')
    parser.add_option('-t', '--admin_token', dest='admin_token',
                      help="admin token to use with Keystone's admin endpoint",
                      metavar='ADMIN_TOKEN')
    parser.add_option('-p', '--domain-admin-password',
                      dest='domain_admin_password',
                      help="heat domain admin's password to be set",
                      metavar='DOMAIN_ADMIN_PASSWORD')
    return parser.parse_args()


def main():
    (options, args) = parse_args(sys.argv)
    if (options.host is None or options.admin_token is None or
        options.domain_admin_password is None):
        print("All options are required.")
        return 1
    initialize_for_heat(options.host, options.admin_token,
                        options.domain_admin_password)
