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
import six

from os_cloud_config.cmd.utils import _clients as clients
from os_cloud_config import glance

LOG = logging.getLogger(__name__)


def register_nova_bm_node(service_host, node, client=None, blocking=True):
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
    for count in range(60):
        LOG.debug('Registering %s node with nova-baremetal, try #%d.' %
                  (node["pm_addr"], count))
        try:
            bm_node = client.baremetal.create(service_host,
                                              six.text_type(node["cpu"]),
                                              six.text_type(node["memory"]),
                                              six.text_type(node["disk"]),
                                              node["mac"][0], **kwargs)
            break
        except (novaexc.ConnectionRefused, novaexc.ServiceUnavailable):
            if blocking:
                LOG.debug('Service not available, sleeping for 10 seconds.')
                time.sleep(10)
            else:
                LOG.debug('Service not available.')
    else:
        if blocking:
            LOG.debug('Service unavailable after 10 minutes, giving up.')
        else:
            LOG.debug('Service unavailable after 60 tries, giving up.')
        raise novaexc.ServiceUnavailable()
    for mac in node["mac"][1:]:
        client.baremetal.add_interface(bm_node, mac)
    return bm_node


def _extract_driver_info(node):
    if "ipmi" in node["pm_type"]:
        driver_info = {"ipmi_address": node["pm_addr"],
                       "ipmi_username": node["pm_user"],
                       "ipmi_password": node["pm_password"]}
    elif node["pm_type"] == "pxe_drac":
        driver_info = {"drac_host": node["pm_addr"],
                       "drac_username": node["pm_user"],
                       "drac_password": node["pm_password"]}
    elif node["pm_type"] == "pxe_ssh":
        if "pm_virt_type" not in node:
            node["pm_virt_type"] = "virsh"
        driver_info = {"ssh_address": node["pm_addr"],
                       "ssh_username": node["pm_user"],
                       "ssh_key_contents": node["pm_password"],
                       "ssh_virt_type": node["pm_virt_type"]}
    elif node["pm_type"] == "pxe_ilo":
        driver_info = {"ilo_address": node["pm_addr"],
                       "ilo_username": node["pm_user"],
                       "ilo_password": node["pm_password"]}
    elif node["pm_type"] == "pxe_iboot":
        driver_info = {"iboot_address": node["pm_addr"],
                       "iboot_username": node["pm_user"],
                       "iboot_password": node["pm_password"]}
        # iboot_relay_id and iboot_port are optional
        if "pm_relay_id" in node:
            driver_info["iboot_relay_id"] = node["pm_relay_id"]
        if "pm_port" in node:
            driver_info["iboot_port"] = node["pm_port"]
    else:
        raise ValueError("Unknown pm_type: %s" % node["pm_type"])
    if "pxe" in node["pm_type"]:
        if "kernel_id" in node:
            driver_info["deploy_kernel"] = node["kernel_id"]
        if "ramdisk_id" in node:
            driver_info["deploy_ramdisk"] = node["ramdisk_id"]
    return driver_info


def register_ironic_node(service_host, node, client=None, blocking=True):
    properties = {"cpus": six.text_type(node["cpu"]),
                  "memory_mb": six.text_type(node["memory"]),
                  "local_gb": six.text_type(node["disk"]),
                  "cpu_arch": node["arch"]}
    driver_info = _extract_driver_info(node)

    for count in range(60):
        LOG.debug('Registering %s node with ironic, try #%d.' %
                  (node["pm_addr"], count))
        try:
            ironic_node = client.node.create(driver=node["pm_type"],
                                             driver_info=driver_info,
                                             properties=properties)
            break
        except (ironicexp.ConnectionRefused, ironicexp.ServiceUnavailable):
            if blocking:
                LOG.debug('Service not available, sleeping for 10 seconds.')
                time.sleep(10)
            else:
                LOG.debug('Service not available.')
    else:
        if blocking:
            LOG.debug('Service unavailable after 10 minutes, giving up.')
        else:
            LOG.debug('Service unavailable after 60 tries, giving up.')
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
    return ironic_node


def _populate_node_mapping(ironic_in_use, client):
    LOG.debug('Populating list of registered nodes.')
    node_map = {'mac': {}, 'pm_addr': {}}
    if ironic_in_use:
        nodes = [n.to_dict() for n in client.node.list()]
        for node in nodes:
            node_details = client.node.get(node['uuid'])
            if node_details.driver == 'pxe_ssh':
                for port in client.node.list_ports(node['uuid']):
                    node_map['mac'][port.address] = node['uuid']
            elif 'ipmi' in node_details.driver:
                pm_addr = node_details.driver_info['ipmi_address']
                node_map['pm_addr'][pm_addr] = node['uuid']
            elif node_details.driver == 'pxe_ilo':
                pm_addr = node_details.driver_info['ilo_address']
                node_map['pm_addr'][pm_addr] = node['uuid']
            elif node_details.driver == 'pxe_drac':
                pm_addr = node_details.driver_info['drac_host']
                node_map['pm_addr'][pm_addr] = node['uuid']
    else:
        nodes = [bmn.to_dict() for bmn in client.baremetal.list()]
        for node in nodes:
            node_map['pm_addr'][node['pm_address']] = node['id']
            for addr in node['interfaces']:
                node_map['mac'][addr['address']] = node['id']
    return node_map


def _get_node_id(node, node_map):
    if node['pm_type'] == 'pxe_ssh':
        for mac in node['mac']:
            if mac.lower() in node_map['mac']:
                return node_map['mac'][mac.lower()]
    else:
        if node['pm_addr'] in node_map['pm_addr']:
            return node_map['pm_addr'][node['pm_addr']]


def _update_or_register_bm_node(service_host, node, node_map, client=None,
                                blocking=True):
    bm_id = _get_node_id(node, node_map)
    if bm_id:
        bm_node = client.baremetal.get(bm_id)
    else:
        bm_node = None
    if bm_node is None:
        bm_node = register_nova_bm_node(service_host, node, client,
                                        blocking=blocking)
    else:
        LOG.warning('Node %d already registered, skipping.' % bm_node.id)
    return bm_node.id


def _update_or_register_ironic_node(service_host, node, node_map, client=None,
                                    blocking=True):
    node_uuid = _get_node_id(node, node_map)
    massage_map = {'cpu': '/properties/cpus',
                   'memory': '/properties/memory_mb',
                   'disk': '/properties/local_gb',
                   'arch': '/properties/cpu_arch'}
    if "ipmi" in node['pm_type']:
        massage_map.update({'pm_addr': '/driver_info/ipmi_address',
                            'pm_user': '/driver_info/ipmi_username',
                            'pm_password': '/driver_info/ipmi_password'})
    elif node['pm_type'] == 'pxe_ssh':
        massage_map.update({'pm_addr': '/driver_info/ssh_address',
                            'pm_user': '/driver_info/ssh_username',
                            'pm_password': '/driver_info/ssh_key_contents'})
    elif node['pm_type'] == 'pxe_ilo':
        massage_map.update({'pm_addr': '/driver_info/ilo_address',
                            'pm_user': '/driver_info/ilo_username',
                            'pm_password': '/driver_info/ilo_password'})
    elif node['pm_type'] == 'pxe_drac':
        massage_map.update({'pm_addr': '/driver_info/drac_host',
                            'pm_user': '/driver_info/drac_username',
                            'pm_password': '/driver_info/drac_password'})
    if node_uuid:
        ironic_node = client.node.get(node_uuid)
    else:
        ironic_node = None
    if ironic_node is None:
        ironic_node = register_ironic_node(service_host, node, client,
                                           blocking=blocking)
    else:
        LOG.debug('Node %s already registered, updating details.' % (
            ironic_node.uuid))
        node_patch = []
        for key, value in massage_map.items():
            node_patch.append({'path': value,
                               'value': six.text_type(node[key]),
                               'op': 'replace'})
        for count in range(2):
            try:
                client.node.update(ironic_node.uuid, node_patch)
                break
            except ironicexp.Conflict:
                LOG.debug('Node %s locked for updating.' %
                          ironic_node.uuid)
                time.sleep(5)
        else:
            raise ironicexp.Conflict()
    return ironic_node.uuid


def _clean_up_extra_nodes(ironic_in_use, seen, client, remove=False):
    if ironic_in_use:
        all_nodes = set([n.uuid for n in client.node.list()])
        remove_func = client.node.delete
    else:
        all_nodes = set([bmn.id for bmn in client.baremetal.list()])
        remove_func = client.baremetal.delete
    extra_nodes = all_nodes - seen
    for node in extra_nodes:
        if remove:
            LOG.debug('Removing extra registered node %s.' % node)
            remove_func(node)
        else:
            LOG.debug('Extra registered node %s found.' % node)


def _register_list_of_nodes(register_func, node_map, client, nodes_list,
                            blocking, service_host, kernel_id, ramdisk_id):
    seen = set()
    for node in nodes_list:
        if kernel_id:
            if 'kernel_id' not in node:
                node['kernel_id'] = kernel_id
        if ramdisk_id:
            if 'ramdisk_id' not in node:
                node['ramdisk_id'] = ramdisk_id
        try:
            new_node = register_func(service_host, node, node_map,
                                     client=client, blocking=blocking)
            seen.add(new_node)
        except ironicexp.Conflict:
            LOG.debug("Could not update node, moving to next host")
            seen.add(node)
    return seen


def register_all_nodes(service_host, nodes_list, client=None, remove=False,
                       blocking=True, keystone_client=None, glance_client=None,
                       kernel_name=None, ramdisk_name=None):
    LOG.debug('Registering all nodes.')
    ironic_in_use = using_ironic(keystone=keystone_client)
    if ironic_in_use:
        if client is None:
            LOG.warn('Creating ironic client inline is deprecated, please '
                     'pass the client as parameter.')
            client = clients.get_ironic_client()
        register_func = _update_or_register_ironic_node
    else:
        if client is None:
            LOG.warn('Creating nova-bm client inline is deprecated, please '
                     'pass the client as parameter.')
            client = clients.get_nova_bm_client()
        register_func = _update_or_register_bm_node
    node_map = _populate_node_mapping(ironic_in_use, client)
    glance_ids = {'kernel': None, 'ramdisk': None}
    if kernel_name and ramdisk_name:
        if glance_client is None:
            LOG.warn('Creating glance client inline is deprecated, please '
                     'pass the client as a parameter.')
            client = clients.get_glance_client()
        glance_ids = glance.create_or_find_kernel_and_ramdisk(
            glance_client, kernel_name, ramdisk_name)
    seen = _register_list_of_nodes(register_func, node_map, client,
                                   nodes_list, blocking, service_host,
                                   glance_ids['kernel'], glance_ids['ramdisk'])
    _clean_up_extra_nodes(ironic_in_use, seen, client, remove=remove)


def using_ironic(keystone=None):
    LOG.debug('Checking for usage of ironic.')
    if keystone is None:
        LOG.warn('Creating keystone client inline is deprecated, please pass '
                 'the client as parameter.')
        keystone = clients.get_keystone_client()
    return 'ironic' in [service.name for service in keystone.services.list()]
