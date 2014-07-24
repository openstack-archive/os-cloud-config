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
import os

from ironicclient import client as ironicclient
from keystoneclient.v2_0 import client as ksclient
from novaclient.extension import Extension
from novaclient.v1_1 import client as novav11client
from novaclient.v1_1.contrib import baremetal

LOG = logging.getLogger(__name__)


def get_nova_bm_client():
    LOG.debug('Creating nova client.')
    baremetal_extension = Extension('baremetal', baremetal)
    return novav11client.Client(os.environ["OS_USERNAME"],
                                os.environ["OS_PASSWORD"],
                                os.environ["OS_TENANT_NAME"],
                                os.environ["OS_AUTH_URL"],
                                extensions=[baremetal_extension])


def get_ironic_client():
    LOG.debug('Creating ironic client.')
    kwargs = {'os_username': os.environ['OS_USERNAME'],
              'os_password': os.environ['OS_PASSWORD'],
              'os_auth_url': os.environ['OS_AUTH_URL'],
              'os_tenant_name': os.environ['OS_TENANT_NAME']}
    return ironicclient.get_client(1, **kwargs)


def get_keystone_client():
    LOG.debug('Creating keystone client.')
    kwargs = {'username': os.environ["OS_USERNAME"],
              'password': os.environ["OS_PASSWORD"],
              'tenant_name': os.environ["OS_TENANT_NAME"],
              'auth_url': os.environ["OS_AUTH_URL"]}
    return ksclient.Client(**kwargs)
