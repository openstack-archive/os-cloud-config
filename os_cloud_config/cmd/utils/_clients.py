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

from os_cloud_config.utils import clients

LOG = logging.getLogger(__name__)


def _get_client_args():
    return (os.environ["OS_USERNAME"],
            os.environ["OS_PASSWORD"],
            os.environ["OS_TENANT_NAME"],
            os.environ["OS_AUTH_URL"],
            os.environ.get("OS_CACERT"))


def get_nova_bm_client():
    return clients.get_nova_bm_client(*_get_client_args())


def get_ironic_client():
    return clients.get_ironic_client(*_get_client_args())


def get_keystone_client():
    return clients.get_keystone_client(*_get_client_args())


def get_keystone_v3_client():
    return clients.get_keystone_v3_client(*_get_client_args())


def get_neutron_client():
    return clients.get_neutron_client(*_get_client_args())


def get_glance_client():
    return clients.get_glance_client(*_get_client_args())
