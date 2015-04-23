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


LOG = logging.getLogger(__name__)


def cleanup_flavors(client, names=('m1.tiny', 'm1.small', 'm1.medium',
                    'm1.large', 'm1.xlarge')):
    LOG.debug('Cleaning up non-baremetal flavors.')
    for flavor in client.flavors.list():
        if flavor.name in names:
            client.flavors.delete(flavor.id)


def check_node_properties(node):
    for node_property in 'memory_mb', 'local_gb', 'cpus', 'cpu_arch':
        if not node.properties.get(node_property):
            LOG.warning('node %s does not have %s set. Not creating flavor'
                        'from node.', node.uuid, node_property)
            return False
    return True


def create_flavors_from_ironic(client, ironic_client, kernel, ramdisk,
                               root_disk):
    node_list = []
    for node in ironic_client.node.list(detail=True):
        if not check_node_properties(node):
            continue
        node_list.append({
            'memory': node.properties['memory_mb'],
            'disk': node.properties['local_gb'],
            'cpu': node.properties['cpus'],
            'arch': node.properties['cpu_arch']})
    create_flavors_from_nodes(client, node_list, kernel, ramdisk, root_disk)


def create_flavors_from_nodes(client, node_list, kernel, ramdisk, root_disk):
    LOG.debug('Populating flavors to create from node list.')
    node_details = set()
    for node in node_list:
        disk = node['disk']
        ephemeral = 0
        if root_disk:
            disk = str(root_disk)
            ephemeral = str(int(node['disk']) - int(root_disk))
        node_details.add((node['memory'], disk, node['cpu'], node['arch'],
                         ephemeral))
    flavor_list = []
    for node in node_details:
        new_flavor = {'memory': node[0], 'disk': node[1], 'cpu': node[2],
                      'arch': node[3], 'ephemeral': node[4]}
        name = 'baremetal_%(memory)s_%(disk)s_%(ephemeral)s_%(cpu)s' % (
            new_flavor)
        new_flavor['name'] = name
        flavor_list.append(new_flavor)
    create_flavors_from_list(client, flavor_list, kernel, ramdisk)


def create_flavors_from_list(client, flavor_list, kernel, ramdisk):
    LOG.debug('Creating flavors from flavors list.')
    for flavor in filter_existing_flavors(client, flavor_list):
        flavor.update({'kernel': kernel, 'ramdisk': ramdisk})
        LOG.debug('Creating %(name)s flavor with memory %(memory)s, '
                  'disk %(disk)s, cpu %(cpu)s, %(arch)s arch.' % flavor)
        _create_flavor(client, flavor)


def filter_existing_flavors(client, flavor_list):
    flavors = client.flavors.list()
    names_to_create = (set([f['name'] for f in flavor_list]) -
                       set([f.name for f in flavors]))
    flavors_to_create = [f for f in flavor_list
                         if f['name'] in names_to_create]
    return flavors_to_create


def _create_flavor(client, flavor_desc):
    flavor = client.flavors.create(flavor_desc['name'], flavor_desc['memory'],
                                   flavor_desc['cpu'], flavor_desc['disk'],
                                   None, ephemeral=flavor_desc['ephemeral'])
    bm_prefix = 'baremetal:deploy'
    flavor_metadata = {'cpu_arch': flavor_desc['arch'],
                       '%s_kernel_id' % bm_prefix: flavor_desc['kernel'],
                       '%s_ramdisk_id' % bm_prefix: flavor_desc['ramdisk']}
    if flavor_desc.get('extra_specs'):
        flavor_metadata.update(flavor_desc['extra_specs'])
    flavor.set_keys(metadata=flavor_metadata)
