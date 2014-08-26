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

import logging
import logging.config
import os
import sys

from os_cloud_config import exception


def _ensure():
    environ = ("OS_USERNAME", "OS_PASSWORD", "OS_AUTH_URL", "OS_TENANT_NAME")
    missing = set(environ).difference(os.environ)
    plural = "s are"
    if missing:
        if len(missing) == 1:
            plural = " is"
        message = ("%s environment variable%s required to be set." % (
                   ", ".join(sorted(missing)), plural))
        raise exception.MissingEnvironment(message)


def _add_logging_arguments(parser):
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--debug', action='store_true',
                       help='set logging level to DEBUG (default is INFO)')
    group.add_argument('--log-config',
                       help='external logging configuration file')


def _configure_logging(args):
    if args.log_config:
        logging.config.fileConfig(args.log_config,
                                  disable_existing_loggers=False)
    else:
        format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        date_format = '%Y-%m-%d %H:%M:%S'
        log_level = logging.DEBUG if args.debug else logging.INFO
        logging.basicConfig(datefmt=date_format,
                            format=format,
                            level=log_level,
                            stream=sys.stdout)
