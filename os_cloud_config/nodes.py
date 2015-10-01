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
import six

from os_cloud_config.cmd.utils import _clients as clients
from os_cloud_config import glance

LOG = logging.getLogger(__name__)


def _extract_driver_info(node):
    driver_info = {}
    if "ipmi" in node["pm_type"]:
        driver_info = {"ipmi_address": node["pm_addr"],
                       "ipmi_username": node["pm_user"],
                       "ipmi_password": node["pm_password"]}
        for params in ('ipmi_bridging', 'ipmi_transit_address',
                       'ipmi_transit_channel', 'ipmi_target_address',
                       'ipmi_target_channel', 'ipmi_local_address'):
            if node.get(params):
                driver_info[params] = node[params]
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
    elif node["pm_type"] == "fake_pxe":
        # The fake_pxe driver doesn't need any credentials since there's
        # no power management
        pass
    elif node["pm_type"] == "pxe_ucs":
        driver_info = {"ucs_hostname": node["pm_addr"],
                       "ucs_username": node["pm_user"],
                       "ucs_password": node["pm_password"],
                       "ucs_service_profile": node["pm_service_profile"]}
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

    if 'capabilities' in node:
        properties.update({"capabilities":
                          six.text_type(node.get('capabilities'))})

    create_map = {"driver": node["pm_type"],
                  "properties": properties,
                  "driver_info": driver_info}

    if 'name' in node:
        create_map.update({"name": six.text_type(node.get('name'))})

    for count in range(60):
        LOG.debug('Registering %s node with ironic, try #%d.' %
                  (node.get("pm_addr", ''), count))
        try:
            ironic_node = client.node.create(**create_map)
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


def _populate_node_mapping(client):
    LOG.debug('Populating list of registered nodes.')
    node_map = {'mac': {}, 'pm_addr': {}}
    nodes = [n.to_dict() for n in client.node.list()]
    for node in nodes:
        node_details = client.node.get(node['uuid'])
        if node_details.driver in ('pxe_ssh', 'fake_pxe'):
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
        elif node_details.driver == 'pxe_iboot':
            iboot_addr = node_details.driver_info['iboot_address']
            if "iboot_port" in node_details.driver_info:
                iboot_addr += (':%s' %
                               node_details.driver_info['iboot_port'])
            if "iboot_relay_id" in node_details.driver_info:
                iboot_addr += ('#%s' %
                               node_details.driver_info['iboot_relay_id'])
            node_map['pm_addr'][iboot_addr] = node['uuid']
    return node_map


def _get_node_id(node, node_map):
    if node['pm_type'] in ('pxe_ssh', 'fake_pxe'):
        for mac in node['mac']:
            if mac.lower() in node_map['mac']:
                return node_map['mac'][mac.lower()]
    elif node['pm_type'] == 'pxe_iboot':
        iboot_addr = node["pm_addr"]
        if "pm_port" in node:
            iboot_addr += ':%s' % node["pm_port"]
        if "pm_relay_id" in node:
            iboot_addr += '#%s' % node["pm_relay_id"]
        if iboot_addr in node_map['pm_addr']:
            return node_map['pm_addr'][iboot_addr]
    else:
        if node['pm_addr'] in node_map['pm_addr']:
            return node_map['pm_addr'][node['pm_addr']]


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

    if "name" in node:
        massage_map.update({'name': '/name'})

    if "capabilities" in node:
        massage_map.update({'capabilities': '/properties/capabilities'})

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


def _clean_up_extra_nodes(seen, client, remove=False):
    all_nodes = set([n.uuid for n in client.node.list()])
    remove_func = client.node.delete
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
    if client is None:
        LOG.warn('Creating ironic client inline is deprecated, please '
                 'pass the client as parameter.')
        client = clients.get_ironic_client()
    register_func = _update_or_register_ironic_node
    node_map = _populate_node_mapping(client)
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
    _clean_up_extra_nodes(seen, client, remove=remove)
