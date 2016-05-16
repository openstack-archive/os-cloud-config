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

from os_cloud_config.cmd.utils import _clients as clients

LOG = logging.getLogger(__name__)


def initialize_neutron(network_desc, neutron_client=None,
                       keystone_client=None):
    if not neutron_client:
        LOG.warning(
            'Creating neutron client inline is deprecated, please pass '
            'the client as parameter.')
        neutron_client = clients.get_neutron_client()
    if not keystone_client:
        LOG.warning(
            'Creating keystone client inline is deprecated, please pass '
            'the client as parameter.')
        keystone_client = clients.get_keystone_client()

    admin_tenant = _get_admin_tenant_id(keystone_client)
    if 'physical' in network_desc:
        network_type = 'physical'
        if not admin_tenant:
            raise ValueError("No admin tenant registered in Keystone")
        if not network_desc['physical']['metadata_server']:
            raise ValueError("metadata_server is required for physical "
                             "networks")
    elif 'float' in network_desc:
        network_type = 'float'
    else:
        raise ValueError("No float or physical network defined.")
    net = _create_net(neutron_client, network_desc, network_type, admin_tenant)
    subnet = _create_subnet(neutron_client, net, network_desc, network_type,
                            admin_tenant)
    if 'external' in network_desc:
        router = _create_router(neutron_client, subnet)
        ext_net = _create_net(neutron_client, network_desc, 'external', None)
        _create_subnet(neutron_client, ext_net, network_desc, 'external', None)
        neutron_client.add_gateway_router(
            router['router']['id'], {'network_id': ext_net['network']['id']})
    LOG.debug("Neutron configured.")


def _get_admin_tenant_id(keystone):
    """Fetch the admin tenant id from Keystone.

    :param keystone: A keystone v2 client.
    """
    LOG.debug("Discovering admin tenant.")
    tenant = keystone.tenants.find(name='admin')
    if tenant:
        return tenant.id


def _create_net(neutron, network_desc, network_type, admin_tenant):
    """Create a new neutron net.

    :param neutron: A neutron v2 client.
    :param network_desc: A network description.
    :param network_type: The type of network to create.
    :param admin_tenant: The admin tenant id in Keystone.
    """
    LOG.debug("Creating %s network." % network_type)
    type_desc = network_desc[network_type]
    network = {'admin_state_up': True,
               'name': type_desc['name']}
    if network_type == 'physical':
        network.update({'tenant_id': admin_tenant,
                        'provider:network_type': 'flat',
                        'provider:physical_network': network['name']})
    elif network_type == 'float':
        network['shared'] = True
    elif network_type == 'external':
        network['router:external'] = True
    if type_desc.get('segmentation_id'):
        vlan_tag = type_desc['segmentation_id']
        physical_network = type_desc['physical_network']
        network.update({'provider:network_type': 'vlan',
                        'provider:segmentation_id': vlan_tag,
                        'provider:physical_network': physical_network})
    return neutron.create_network({'network': network})


def _create_subnet(neutron, net, network_desc, network_type, admin_tenant):
    """Create a new neutron subnet.

    :param neutron: A neutron v2 client.
    :param network_desc: A network description.
    :param network_type: The type of network to create.
    :param admin_tenant: The admin tenant id in Keystone.
    """
    type_desc = network_desc[network_type]
    cidr = type_desc['cidr']
    LOG.debug("Creating %s subnet, with CIDR %s." % (network_type, cidr))
    subnet = {'ip_version': 4, 'network_id': net['network']['id'],
              'cidr': cidr}
    if network_type == 'physical':
        metadata = network_desc['physical']['metadata_server']
        subnet.update({'tenant_id': admin_tenant,
                       'host_routes': [{'destination': '169.254.169.254/32',
                                       'nexthop': metadata}]})
    elif network_type == 'external':
        subnet['enable_dhcp'] = False
    if type_desc.get('gateway'):
        subnet['gateway_ip'] = type_desc['gateway']
    if type_desc.get('extra_routes'):
        routes = type_desc['extra_routes']
        if 'host_routes' not in subnet:
            subnet['host_routes'] = []
        subnet['host_routes'].extend(routes)
    if type_desc.get('nameserver'):
        subnet['dns_nameservers'] = [type_desc['nameserver']]
    elif network_type == 'float':
        subnet['dns_nameservers'] = ['8.8.8.8']
    if 'enable_dhcp' in type_desc:
        subnet['enable_dhcp'] = type_desc['enable_dhcp']
    if (type_desc.get('allocation_start') and
            type_desc.get('allocation_end')):
        allocation_start = type_desc['allocation_start']
        allocation_end = type_desc['allocation_end']
        subnet['allocation_pools'] = [{'start': allocation_start,
                                       'end': allocation_end}]
    return neutron.create_subnet({'subnet': subnet})


def _create_router(neutron, subnet):
    """Create a new neutron router.

    :param neutron: A neutron v2 client.
    :param subnet: The subnet id to route for.
    """
    LOG.debug("Creating router.")
    router = neutron.create_router({'router': {'name': 'default-router'}})
    neutron.add_interface_router(router['router']['id'],
                                 {'subnet_id': subnet['subnet']['id']})
    return router
