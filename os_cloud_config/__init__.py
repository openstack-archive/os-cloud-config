# -*- coding: utf-8 -*-

# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import logging
import sys

import pbr.version


__version__ = pbr.version.VersionInfo('os_cloud_config').version_string()


def configure_logging(args=None):
    if args and args.log_config:
        logging.config.fileConfig(args.log_config,
                                  disable_existing_loggers=False)
    else:
        format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        date_format = '%Y-%m-%d %H:%M:%S'
        log_level = logging.DEBUG if args and args.debug else logging.INFO
        logging.basicConfig(datefmt=date_format,
                            format=format,
                            level=log_level,
                            stream=sys.stdout)

configure_logging()
LOG = logging.getLogger(__name__)
LOG.warning("os-cloud-config is DEPRECATED in the Ocata release and will "
            "be removed in Pike.")
