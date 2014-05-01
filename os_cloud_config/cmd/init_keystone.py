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

from os_cloud_config.keystone import initialize


def parse_args(args):
    parser = OptionParser()
    parser.add_option('-o', '--host', dest='host',
                      help="ip/hostname of node where Keystone is running")
    parser.add_option('-t', '--admin-token', dest='admin_token',
                      help="admin token to use with Keystone's admin endpoint")
    parser.add_option('-e', '--admin-email', dest='admin_email',
                      help="admin user's e-mail address to be set")
    parser.add_option('-p', '--admin-password', dest='admin_password',
                      help="admin user's password to be set")
    parser.add_option('-r', '--region', dest='region',
                      help="region to create the endpoint in",
                      default='regionOne')
    parser.add_option('-s', '--ssl', dest='ssl',
                      help="ip/hostname to use as the ssl endpoint, if "
                      "required")
    return parser.parse_args()


def main():
    (options, args) = parse_args(sys.argv)
    if not all((options.host, options.admin_token, options.admin_email,
               options.admin_password)):
        print("The --host, --admin-token, --admin-email and --admin-password "
              "options are required.")
        return 1
    initialize(options.host, options.admin_token, options.admin_email,
               options.admin_password, options.region, options.ssl)
