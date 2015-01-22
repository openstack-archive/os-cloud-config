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

import collections

import mock

from os_cloud_config import neutron
from os_cloud_config.tests import base


class NeutronTest(base.TestCase):

    def test_get_admin_tenant_id(self):
        client = mock.MagicMock()
        neutron._get_admin_tenant_id(client)
        client.tenants.find.assert_called_once_with(name='admin')

    def test_create_net_physical(self):
        client = mock.MagicMock()
        network = {'physical': {'name': 'ctlplane'}}
        neutron._create_net(client, network, 'physical', 'admin_tenant')
        physical_call = {'network': {'tenant_id': 'admin_tenant',
                                     'provider:network_type': 'flat',
                                     'name': 'ctlplane',
                                     'provider:physical_network': 'ctlplane',
                                     'admin_state_up': True}}
        client.create_network.assert_called_once_with(physical_call)

    def test_create_net_physical_vlan_tag(self):
        client = mock.MagicMock()
        network = {'physical': {'name': 'public',
                                'segmentation_id': '123',
                                'physical_network': 'ctlplane'}}
        neutron._create_net(client, network, 'physical', 'admin_tenant')
        physical_call = {'network': {'tenant_id': 'admin_tenant',
                                     'provider:network_type': 'vlan',
                                     'name': 'public',
                                     'provider:physical_network': 'ctlplane',
                                     'provider:segmentation_id': '123',
                                     'admin_state_up': True}}
        client.create_network.assert_called_once_with(physical_call)

    def test_create_net_float(self):
        client = mock.MagicMock()
        network = {'float': {'name': 'default-net'}}
        neutron._create_net(client, network, 'float', None)
        float_call = {'network': {'shared': True,
                                  'name': 'default-net',
                                  'admin_state_up': True}}
        client.create_network.assert_called_once_with(float_call)

    def test_create_net_external(self):
        client = mock.MagicMock()
        network = {'external': {'name': 'ext-net'}}
        neutron._create_net(client, network, 'external', None)
        external_call = {'network': {'router:external': True,
                                     'name': 'ext-net',
                                     'admin_state_up': True}}
        client.create_network.assert_called_once_with(external_call)

    def test_create_subnet_physical(self):
        client = mock.MagicMock()
        net = {'network': {'id': 'abcd'}}
        network = {'physical': {'name': 'ctlplane',
                                'cidr': '10.0.0.0/24',
                                'metadata_server': '10.0.0.1'}}
        neutron._create_subnet(client, net, network, 'physical',
                               'admin_tenant')
        host_routes = [{'nexthop': '10.0.0.1',
                        'destination': '169.254.169.254/32'}]
        physical_call = {'subnet': {'ip_version': 4,
                                    'network_id': 'abcd',
                                    'cidr': '10.0.0.0/24',
                                    'host_routes': host_routes,
                                    'tenant_id': 'admin_tenant'}}
        client.create_subnet.assert_called_once_with(physical_call)

    def test_create_subnet_float(self):
        client = mock.MagicMock()
        net = {'network': {'id': 'abcd'}}
        network = {'float': {'name': 'default-net',
                             'cidr': '172.16.5.0/24'}}
        neutron._create_subnet(client, net, network, 'float', None)
        float_call = {'subnet': {'ip_version': 4,
                                 'network_id': 'abcd',
                                 'cidr': '172.16.5.0/24',
                                 'dns_nameservers': ['8.8.8.8']}}
        client.create_subnet.assert_called_once_with(float_call)

    def test_create_subnet_external(self):
        client = mock.MagicMock()
        net = {'network': {'id': 'abcd'}}
        network = {'external': {'name': 'ext-net',
                                'cidr': '1.2.3.0/24'}}
        neutron._create_subnet(client, net, network, 'external', None)
        external_call = {'subnet': {'ip_version': 4,
                                    'network_id': 'abcd',
                                    'cidr': '1.2.3.0/24',
                                    'enable_dhcp': False}}
        client.create_subnet.assert_called_once_with(external_call)

    def test_create_subnet_with_gateway(self):
        client = mock.MagicMock()
        net = {'network': {'id': 'abcd'}}
        network = {'external': {'name': 'ext-net',
                                'cidr': '1.2.3.0/24',
                                'gateway': '1.2.3.4'}}
        neutron._create_subnet(client, net, network, 'external', None)
        external_call = {'subnet': {'ip_version': 4,
                                    'network_id': 'abcd',
                                    'cidr': '1.2.3.0/24',
                                    'gateway_ip': '1.2.3.4',
                                    'enable_dhcp': False}}
        client.create_subnet.assert_called_once_with(external_call)

    def test_create_subnet_with_allocation_pool(self):
        client = mock.MagicMock()
        net = {'network': {'id': 'abcd'}}
        network = {'float': {'name': 'default-net',
                             'cidr': '172.16.5.0/24',
                             'allocation_start': '172.16.5.25',
                             'allocation_end': '172.16.5.40'}}
        neutron._create_subnet(client, net, network, 'float', None)
        float_call = {'subnet': {'ip_version': 4,
                                 'network_id': 'abcd',
                                 'cidr': '172.16.5.0/24',
                                 'dns_nameservers': ['8.8.8.8'],
                                 'allocation_pools': [{'start': '172.16.5.25',
                                                       'end': '172.16.5.40'}]}}
        client.create_subnet.assert_called_once_with(float_call)

    def test_create_physical_subnet_with_extra_routes(self):
        client = mock.MagicMock()
        net = {'network': {'id': 'abcd'}}
        routes = [{'destination': '2.3.4.0/24', 'nexthop': '172.16.6.253'}]
        network = {'physical': {'name': 'ctlplane',
                                'cidr': '10.0.0.0/24',
                                'metadata_server': '10.0.0.1',
                                'extra_routes': routes}}
        neutron._create_subnet(client, net, network, 'physical',
                               'admin_tenant')
        host_routes = [{'nexthop': '10.0.0.1',
                        'destination': '169.254.169.254/32'}] + routes
        physical_call = {'subnet': {'ip_version': 4,
                                    'network_id': 'abcd',
                                    'cidr': '10.0.0.0/24',
                                    'host_routes': host_routes,
                                    'tenant_id': 'admin_tenant'}}
        client.create_subnet.assert_called_once_with(physical_call)

    def test_create_float_subnet_with_extra_routes(self):
        client = mock.MagicMock()
        net = {'network': {'id': 'abcd'}}
        routes = [{'destination': '2.3.4.0/24', 'nexthop': '172.16.6.253'}]
        network = {'float': {'name': 'default-net',
                             'cidr': '172.16.6.0/24',
                             'extra_routes': routes}}
        neutron._create_subnet(client, net, network, 'float', None)
        float_call = {'subnet': {'ip_version': 4,
                                 'network_id': 'abcd',
                                 'cidr': '172.16.6.0/24',
                                 'dns_nameservers': ['8.8.8.8'],
                                 'host_routes': routes}}
        client.create_subnet.assert_called_once_with(float_call)

    def test_create_subnet_with_nameserver(self):
        client = mock.MagicMock()
        net = {'network': {'id': 'abcd'}}
        network = {'float': {'name': 'default-net',
                             'cidr': '172.16.5.0/24',
                             'nameserver': '172.16.5.254'}}
        neutron._create_subnet(client, net, network, 'float', None)
        float_call = {'subnet': {'ip_version': 4,
                                 'network_id': 'abcd',
                                 'cidr': '172.16.5.0/24',
                                 'dns_nameservers': ['172.16.5.254']}}
        client.create_subnet.assert_called_once_with(float_call)

    def test_create_subnet_with_no_dhcp(self):
        client = mock.MagicMock()
        net = {'network': {'id': 'abcd'}}
        network = {'physical': {'name': 'ctlplane',
                                'cidr': '10.0.0.0/24',
                                'metadata_server': '10.0.0.1',
                                'enable_dhcp': False}}
        neutron._create_subnet(client, net, network, 'physical', 'tenant')
        host_routes = [{'nexthop': '10.0.0.1',
                        'destination': '169.254.169.254/32'}]
        physical_call = {'subnet': {'ip_version': 4,
                                    'enable_dhcp': False,
                                    'network_id': 'abcd',
                                    'cidr': '10.0.0.0/24',
                                    'host_routes': host_routes,
                                    'tenant_id': 'tenant'}}
        client.create_subnet.assert_called_once_with(physical_call)

    @mock.patch('os_cloud_config.cmd.utils._clients.get_neutron_client')
    @mock.patch('os_cloud_config.cmd.utils._clients.get_keystone_client')
    def test_initialize_neutron_physical(self, keystoneclient, neutronclient):
        network_desc = {'physical': {'name': 'ctlplane',
                                     'cidr': '10.0.0.0/24',
                                     'metadata_server': '10.0.0.1'}}
        tenant = collections.namedtuple('tenant', ['id'])
        keystoneclient().tenants.find.return_value = tenant('dead-beef')
        neutron.initialize_neutron(network_desc)
        network_call = {'network': {'tenant_id': 'dead-beef',
                                    'provider:network_type': 'flat',
                                    'name': u'ctlplane',
                                    'provider:physical_network': u'ctlplane',
                                    'admin_state_up': True}}
        host_routes = [{'nexthop': '10.0.0.1',
                        'destination': '169.254.169.254/32'}]
        net_id = neutronclient().create_network.return_value['network']['id']
        subnet_call = {'subnet': {'ip_version': 4,
                                  'network_id': net_id,
                                  'cidr': u'10.0.0.0/24',
                                  'host_routes': host_routes,
                                  'tenant_id': 'dead-beef'}}
        neutronclient().create_network.assert_called_once_with(network_call)
        neutronclient().create_subnet.assert_called_once_with(subnet_call)

    @mock.patch('os_cloud_config.cmd.utils._clients.get_neutron_client')
    @mock.patch('os_cloud_config.cmd.utils._clients.get_keystone_client')
    def test_initialize_neutron_float_and_external(self, keystoneclient,
                                                   neutronclient):
        network_desc = {'float': {'name': 'default-net',
                                  'cidr': '172.16.5.0/24'},
                        'external': {'name': 'ext-net',
                                     'cidr': '1.2.3.0/24'}}
        tenant = collections.namedtuple('tenant', ['id'])
        keystoneclient().tenants.find.return_value = tenant('dead-beef')
        neutron.initialize_neutron(network_desc)
        float_network = {'network': {'shared': True,
                                     'name': 'default-net',
                                     'admin_state_up': True}}
        external_network = {'network': {'router:external': True,
                                        'name': 'ext-net',
                                        'admin_state_up': True}}
        float_subnet = {'subnet': {'ip_version': 4,
                                   'network_id': mock.ANY,
                                   'cidr': '172.16.5.0/24',
                                   'dns_nameservers': ['8.8.8.8']}}
        external_subnet = {'subnet': {'ip_version': 4,
                                      'network_id': mock.ANY,
                                      'cidr': '1.2.3.0/24',
                                      'enable_dhcp': False}}
        router_call = {'router': {'name': 'default-router'}}
        neutronclient().create_network.has_calls([float_network,
                                                  external_network])
        neutronclient().create_subnet.has_calls([float_subnet,
                                                 external_subnet])
        neutronclient().create_router.assert_called_once_with(router_call)
        network = neutronclient().create_network.return_value
        neutronclient().add_gateway_router.assert_called_once_with(
            neutronclient().create_router.return_value['router']['id'],
            {'network_id': network['network']['id']})
