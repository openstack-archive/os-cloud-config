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
import re

from ironicclient import exc as ironicexp
import six

from os_cloud_config.cmd.utils import _clients as clients
from os_cloud_config import exception
from os_cloud_config import glance

LOG = logging.getLogger(__name__)


class DriverInfo(object):
    """Class encapsulating field conversion logic."""
    DEFAULTS = {}

    def __init__(self, prefix, mapping, deprecated_mapping=None):
        self._prefix = prefix
        self._mapping = mapping
        self._deprecated_mapping = deprecated_mapping or {}

    def convert_key(self, key):
        if key in self._mapping:
            return self._mapping[key]
        elif key in self._deprecated_mapping:
            real = self._deprecated_mapping[key]
            LOG.warning('Key %s is deprecated, please use %s',
                        key, real)
            return real
        elif key.startswith(self._prefix):
            return key
        elif key != 'pm_type' and key.startswith('pm_'):
            LOG.warning('Key %s is not supported and will not be passed',
                        key)
        else:
            LOG.debug('Skipping key %s not starting with prefix %s',
                      key, self._prefix)

    def convert(self, fields):
        """Convert fields from instackenv.json format to ironic names."""
        result = self.DEFAULTS.copy()
        for key, value in fields.items():
            new_key = self.convert_key(key)
            if new_key is not None:
                result[new_key] = value
        return result

    def unique_id_from_fields(self, fields):
        """Return a string uniquely identifying a node in instackenv."""

    def unique_id_from_node(self, node):
        """Return a string uniquely identifying a node in ironic db."""


class PrefixedDriverInfo(DriverInfo):
    def __init__(self, prefix, deprecated_mapping=None,
                 has_port=False, address_field='address'):
        mapping = {
            'pm_addr': '%s_%s' % (prefix, address_field),
            'pm_user': '%s_username' % prefix,
            'pm_password': '%s_password' % prefix,
        }
        if has_port:
            mapping['pm_port'] = '%s_port' % prefix
        self._has_port = has_port

        super(PrefixedDriverInfo, self).__init__(
            prefix, mapping,
            deprecated_mapping=deprecated_mapping
        )

    def unique_id_from_fields(self, fields):
        result = fields['pm_addr']
        if self._has_port and 'pm_port' in fields:
            result = '%s:%s' % (result, fields['pm_port'])
        return result

    def unique_id_from_node(self, node):
        new_key = self.convert_key('pm_addr')
        assert new_key is not None
        try:
            result = node.driver_info[new_key]
        except KeyError:
            # Node cannot be identified
            return

        if self._has_port:
            new_port = self.convert_key('pm_port')
            assert new_port
            try:
                return '%s:%s' % (result, node.driver_info[new_port])
            except KeyError:
                pass

        return result


class SshDriverInfo(DriverInfo):
    DEFAULTS = {'ssh_virt_type': 'virsh'}

    def __init__(self):
        super(SshDriverInfo, self).__init__(
            'ssh',
            {
                'pm_addr': 'ssh_address',
                'pm_user': 'ssh_username',
                # TODO(dtantsur): support ssh_key_filename as well
                'pm_password': 'ssh_key_contents',
            },
            deprecated_mapping={
                'pm_virt_type': 'ssh_virt_type',
            }
        )


class iBootDriverInfo(PrefixedDriverInfo):
    def __init__(self):
        super(iBootDriverInfo, self).__init__(
            'iboot', has_port=True,
            deprecated_mapping={
                'pm_relay_id': 'iboot_relay_id',
            }
        )

    def unique_id_from_fields(self, fields):
        result = super(iBootDriverInfo, self).unique_id_from_fields(fields)
        if 'iboot_relay_id' in fields:
            result = '%s#%s' % (result, fields['iboot_relay_id'])
        return result

    def unique_id_from_node(self, node):
        try:
            result = super(iBootDriverInfo, self).unique_id_from_node(node)
        except IndexError:
            return

        if node.driver_info.get('iboot_relay_id'):
            result = '%s#%s' % (result, node.driver_info['iboot_relay_id'])

        return result


DRIVER_INFO = {
    # production drivers
    '.*_ipmi(tool|native)': PrefixedDriverInfo('ipmi'),
    '.*_drac': PrefixedDriverInfo('drac', address_field='host'),
    '.*_ilo': PrefixedDriverInfo('ilo'),
    '.*_ucs': PrefixedDriverInfo(
        'ucs',
        address_field='hostname',
        deprecated_mapping={
            'pm_service_profile': 'ucs_service_profile'
        }),
    '.*_irmc': PrefixedDriverInfo(
        'irmc', has_port=True,
        deprecated_mapping={
            'pm_auth_method': 'irmc_auth_method',
            'pm_client_timeout': 'irmc_client_timeout',
            'pm_sensor_method': 'irmc_sensor_method',
            'pm_deploy_iso': 'irmc_deploy_iso',
        }),
    # test drivers
    '.*_ssh': SshDriverInfo(),
    '.*_iboot': iBootDriverInfo(),
    '.*_wol': DriverInfo(
        'wol',
        mapping={
            'pm_addr': 'wol_host',
            'pm_port': 'wol_port',
        }),
    '.*_amt': DriverInfo(
        'amt',
        mapping={
            'pm_addr': 'amt_hostname',
            'pm_user': 'amt_username',
            'pm_password': 'amt_password',
        }),
    'fake(|_pxe|_agent)': DriverInfo('fake', mapping={}),
}


def _find_driver_handler(driver):
    for driver_tpl, handler in DRIVER_INFO.items():
        if re.match(driver_tpl, driver) is not None:
            return handler

    # FIXME(dtantsur): handle all drivers without hardcoding them
    raise exception.InvalidNode('unknown pm_type (ironic driver to use): '
                                '%s' % driver)


def _find_node_handler(fields):
    try:
        driver = fields['pm_type']
    except KeyError:
        raise exception.InvalidNode('pm_type (ironic driver to use) is '
                                    'required', node=fields)
    return _find_driver_handler(driver)


def register_ironic_node(service_host, node, client=None, blocking=None):
    if blocking is not None:
        LOG.warning('blocking argument to register_ironic_node is deprecated '
                    'and does nothing')

    driver_info = {}
    handler = _find_node_handler(node)

    if "kernel_id" in node:
        driver_info["deploy_kernel"] = node["kernel_id"]
    if "ramdisk_id" in node:
        driver_info["deploy_ramdisk"] = node["ramdisk_id"]

    driver_info.update(handler.convert(node))

    mapping = {'cpus': 'cpu',
               'memory_mb': 'memory',
               'local_gb': 'disk',
               'cpu_arch': 'arch'}
    properties = {k: six.text_type(node.get(v))
                  for k, v in mapping.items()
                  if node.get(v) is not None}

    if 'capabilities' in node:
        properties.update({"capabilities":
                          six.text_type(node.get('capabilities'))})

    create_map = {"driver": node["pm_type"],
                  "properties": properties,
                  "driver_info": driver_info}

    if 'name' in node:
        create_map.update({"name": six.text_type(node.get('name'))})

    node_id = handler.unique_id_from_fields(node)
    LOG.debug('Registering node %s with ironic.', node_id)
    ironic_node = client.node.create(**create_map)

    for mac in node.get("mac", []):
        client.port.create(address=mac, node_uuid=ironic_node.uuid)

    validation = client.node.validate(ironic_node.uuid)
    if not validation.power['result']:
        LOG.warning('Node %s did not pass power credentials validation: %s',
                    ironic_node.uuid, validation.power['reason'])

    try:
        client.node.set_power_state(ironic_node.uuid, 'off')
    except ironicexp.Conflict:
        # Conflict means the Ironic conductor does something with a node,
        # ignore the exception.
        pass

    return ironic_node


def _populate_node_mapping(client):
    LOG.debug('Populating list of registered nodes.')
    node_map = {'mac': {}, 'pm_addr': {}}
    nodes = client.node.list(detail=True)
    for node in nodes:
        for port in client.node.list_ports(node.uuid):
            node_map['mac'][port.address] = node.uuid

        handler = _find_driver_handler(node.driver)
        unique_id = handler.unique_id_from_node(node)
        if unique_id:
            node_map['pm_addr'][unique_id] = node.uuid

    return node_map


def _get_node_id(node, handler, node_map):
    candidates = []
    for mac in node.get('mac', []):
        try:
            candidates.append(node_map['mac'][mac.lower()])
        except KeyError:
            pass

    unique_id = handler.unique_id_from_fields(node)
    if unique_id:
        try:
            candidates.append(node_map['pm_addr'][unique_id])
        except KeyError:
            pass

    if len(candidates) > 1:
        raise exception.InvalidNode('Several candidates found for the same '
                                    'node data: %s' % candidates,
                                    node=node)
    elif candidates:
        return candidates[0]


def _update_or_register_ironic_node(service_host, node, node_map, client=None):
    handler = _find_node_handler(node)
    node_uuid = _get_node_id(node, handler, node_map)

    if node_uuid:
        LOG.info('Node %s already registered, updating details.',
                 node_uuid)

        patched = {}
        for field, path in [('cpu', '/properties/cpus'),
                            ('memory', '/properties/memory_mb'),
                            ('disk', '/properties/local_gb'),
                            ('arch', '/properties/cpu_arch'),
                            ('name', '/name'),
                            ('capabilities', '/properties/capabilities')]:
            if field in node:
                patched[path] = node.pop(field)

        driver_info = handler.convert(node)
        for key, value in driver_info.items():
            patched['/driver_info/%s' % key] = value

        node_patch = []
        for key, value in patched.items():
            node_patch.append({'path': key,
                               'value': six.text_type(value),
                               'op': 'add'})
        ironic_node = client.node.update(node_uuid, node_patch)
    else:
        ironic_node = register_ironic_node(service_host, node, client)

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


def register_all_nodes(service_host, nodes_list, client=None, remove=False,
                       blocking=True, keystone_client=None, glance_client=None,
                       kernel_name=None, ramdisk_name=None):
    LOG.debug('Registering all nodes.')
    if client is None:
        LOG.warn('Creating ironic client inline is deprecated, please '
                 'pass the client as parameter.')
        client = clients.get_ironic_client()
    node_map = _populate_node_mapping(client)

    glance_ids = {'kernel': None, 'ramdisk': None}
    if kernel_name and ramdisk_name:
        if glance_client is None:
            LOG.warn('Creating glance client inline is deprecated, please '
                     'pass the client as a parameter.')
            client = clients.get_glance_client()
        glance_ids = glance.create_or_find_kernel_and_ramdisk(
            glance_client, kernel_name, ramdisk_name)

    seen = set()
    for node in nodes_list:
        if glance_ids['kernel'] and 'kernel_id' not in node:
            node['kernel_id'] = glance_ids['kernel']
        if glance_ids['ramdisk'] and 'ramdisk_id' not in node:
            node['ramdisk_id'] = glance_ids['ramdisk']

        uuid = _update_or_register_ironic_node(service_host,
                                               node, node_map,
                                               client=client)
        seen.add(uuid)

    _clean_up_extra_nodes(seen, client, remove=remove)
