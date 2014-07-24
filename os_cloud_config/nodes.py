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
import time

from ironicclient.openstack.common.apiclient import exceptions as ironicexp
from novaclient.openstack.common.apiclient import exceptions as novaexc
from os_cloud_config.utils import _clients as clients

LOG = logging.getLogger(__name__)


def register_nova_bm_node(service_host, node, client=None):
    if not service_host:
        raise ValueError("Nova-baremetal requires a service host.")
    kwargs = {'pm_address': node["pm_addr"], 'pm_user': node["pm_user"]}
    # Nova now enforces the password to be 255 or less characters, and the
    # ssh key/password to use is set in configuration.
    if not node.get('pm_password'):
        LOG.debug('pm_password not set.')
    elif len(node["pm_password"]) <= 255:
        LOG.debug('Setting pm_password for nova-bm, it is <=255 characters.')
        kwargs["pm_password"] = node["pm_password"]
    else:
        LOG.info('Ignoring pm_password for nova-bm, it is >255 characters.')
    node_created = False
    for count in range(60):
        LOG.debug('Registering %s node with nova-baremetal, try #%d.' %
                  (node["pm_addr"], count))
        try:
            bm_node = client.baremetal.create(service_host, node["cpu"],
                                              node["memory"], node["disk"],
                                              node["mac"][0], **kwargs)
            node_created = True
            break
        except (novaexc.ConnectionRefused, novaexc.ServiceUnavailable):
            LOG.debug('Service not available, sleeping for 10 seconds.')
            time.sleep(10)
    if not node_created:
        LOG.debug('Service unavailable after 10 minutes, giving up.')
        raise novaexc.ServiceUnavailable()
    for mac in node["mac"][1:]:
        client.baremetal.add_interface(bm_node, mac)


def register_ironic_node(service_host, node, client=None):
    properties = {"cpus": node["cpu"],
                  "memory_mb": node["memory"],
                  "local_gb": node["disk"],
                  "cpu_arch": node["arch"]}
    if "ipmi" in node["pm_type"]:
        driver_info = {"ipmi_address": node["pm_addr"],
                       "ipmi_username": node["pm_user"],
                       "ipmi_password": node["pm_password"]}
    elif node["pm_type"] == "pxe_ssh":
        driver_info = {"ssh_address": node["pm_addr"],
                       "ssh_username": node["pm_user"],
                       "ssh_key_contents": node["pm_password"],
                       "ssh_virt_type": "virsh"}
    else:
        raise Exception("Unknown pm_type: %s" % node["pm_type"])

    node_created = False
    for count in range(60):
        LOG.debug('Registering %s node with ironic, try #%d.' %
                  (node["pm_addr"], count))
        try:
            ironic_node = client.node.create(driver=node["pm_type"],
                                             driver_info=driver_info,
                                             properties=properties)
            node_created = True
            break
        except (ironicexp.ConnectionRefused, ironicexp.ServiceUnavailable):
            LOG.debug('Service not available, sleeping for 10 seconds.')
            time.sleep(10)
    if not node_created:
        LOG.debug('Service unavailable after 10 minutes, giving up.')
        raise ironicexp.ServiceUnavailable()

    for mac in node["mac"]:
        client.port.create(address=mac, node_uuid=ironic_node.uuid)
    # Ironic should do this directly, see bug 1315225.
    try:
        client.node.set_power_state(ironic_node.uuid, 'off')
    except ironicexp.Conflict:
        # Conflict means the Ironic conductor got there first, so we can
        # ignore the exception.
        pass


def register_all_nodes(service_host, nodes_list, client=None):
    LOG.debug('Registering all nodes.')
    if using_ironic(keystone=None):
        if client is None:
            client = clients.get_ironic_client()
        register_func = register_ironic_node
    else:
        if client is None:
            client = clients.get_nova_bm_client()
        register_func = register_nova_bm_node
    for node in nodes_list:
        register_func(service_host, node, client=client)


def using_ironic(keystone=None):
    LOG.debug('Checking for usage of ironic.')
    if keystone is None:
        keystone = clients.get_keystone_client()
    return 'ironic' in [service.name for service in keystone.services.list()]
