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
import uuid

import mock

from ironicclient.openstack.common.apiclient import exceptions as ironicexp
from novaclient.openstack.common.apiclient import exceptions as novaexc
from os_cloud_config import nodes
from os_cloud_config.tests import base


class NodesTest(base.TestCase):

    def _get_node(self):
        return {'cpu': '1', 'memory': '2048', 'disk': '30', 'arch': 'amd64',
                'mac': ['aaa'], 'pm_addr': 'foo.bar', 'pm_user': 'test',
                'pm_password': 'random', 'pm_type': 'pxe_ssh'}

    @mock.patch('os_cloud_config.nodes.using_ironic', return_value=False)
    def test_register_all_nodes_nova_bm(self, ironic_mock):
        node_list = [self._get_node(), self._get_node()]
        node_list[0]["mac"].append("bbb")
        client = mock.MagicMock()
        nodes.register_all_nodes('servicehost', node_list, client=client)
        nova_bm_call = mock.call(
            "servicehost", "1", "2048", "30", "aaa", pm_address="foo.bar",
            pm_user="test", pm_password="random")
        client.baremetal.create.has_calls([nova_bm_call, nova_bm_call])
        client.baremetal.add_interface.assert_called_once_with(mock.ANY, "bbb")

    @mock.patch('time.sleep')
    def test_register_nova_bm_node_retry(self, sleep):
        client = mock.MagicMock()
        side_effect = (novaexc.ConnectionRefused,
                       novaexc.ServiceUnavailable, mock.DEFAULT)
        client.baremetal.create.side_effect = side_effect
        nodes.register_nova_bm_node('servicehost',
                                    self._get_node(), client=client)
        sleep.assert_has_calls([mock.call(10), mock.call(10)])
        nova_bm_call = mock.call(
            "servicehost", "1", "2048", "30", "aaa", pm_address="foo.bar",
            pm_user="test", pm_password="random")
        client.has_calls([nova_bm_call])

    @mock.patch('time.sleep')
    def test_register_nova_bm_node_failure(self, sleep):
        client = mock.MagicMock()
        client.baremetal.create.side_effect = novaexc.ConnectionRefused
        self.assertRaises(novaexc.ServiceUnavailable,
                          nodes.register_nova_bm_node, 'servicehost',
                          self._get_node(), client=client)

    def test_register_nova_bm_node_ignore_long_pm_password(self):
        client = mock.MagicMock()
        node = self._get_node()
        node["pm_password"] = 'abc' * 100
        nodes.register_nova_bm_node('servicehost', node, client=client)
        nova_bm_call = mock.call(
            "servicehost", "1", "2048", "30", "aaa", pm_address="foo.bar",
            pm_user="test")
        client.has_calls([nova_bm_call])

    def assert_nova_bm_call_with_no_pm_password(self, node):
        client = mock.MagicMock()
        nodes.register_nova_bm_node('servicehost', node, client=client)
        nova_bm_call = mock.call(
            "servicehost", "1", "2048", "30", "aaa", pm_address="foo.bar",
            pm_user="test")
        client.has_calls([nova_bm_call])

    def test_register_nova_bm_node_no_pm_password(self):
        node = self._get_node()
        del node["pm_password"]
        self.assert_nova_bm_call_with_no_pm_password(node)

    def test_register_nova_bm_node_pm_password_of_none(self):
        node = self._get_node()
        node["pm_password"] = None
        self.assert_nova_bm_call_with_no_pm_password(node)

    def test_register_nova_bm_node_pm_password_of_empty_string(self):
        node = self._get_node()
        node["pm_password"] = ""
        self.assert_nova_bm_call_with_no_pm_password(node)

    @mock.patch('os_cloud_config.nodes.using_ironic', return_value=True)
    def test_register_all_nodes_ironic(self, using_ironic):
        node_list = [self._get_node(), self._get_node()]
        node_list[1]["pm_type"] = "ipmi"
        node_properties = {"cpus": "1",
                           "memory_mb": "2048",
                           "local_gb": "30",
                           "cpu_arch": "amd64"}
        ironic = mock.MagicMock()
        nodes.register_all_nodes('servicehost', node_list, client=ironic)
        pxe_node_driver_info = {"ssh_address": "foo.bar",
                                "ssh_username": "test",
                                "ssh_key_contents": "random",
                                "ssh_virt_type": "virsh"}
        ipmi_node_driver_info = {"ipmi_address": "foo.bar",
                                 "ipmi_username": "test",
                                 "ipmi_password": "random"}
        pxe_node = mock.call(driver="pxe_ssh",
                             driver_info=pxe_node_driver_info,
                             properties=node_properties)
        port_call = mock.call(node_uuid=ironic.node.create.return_value.uuid,
                              address='aaa')
        power_off_call = mock.call(ironic.node.create.return_value.uuid, 'off')
        ipmi_node = mock.call(driver="ipmi",
                              driver_info=ipmi_node_driver_info,
                              properties=node_properties)
        ironic.node.create.assert_has_calls([pxe_node, ipmi_node])
        ironic.port.create.assert_has_calls([port_call, port_call])
        ironic.node.set_power_state.assert_has_calls(
            [power_off_call, power_off_call])

    @mock.patch('time.sleep')
    def test_register_ironic_node_retry(self, sleep):
        ironic = mock.MagicMock()
        ironic_node = collections.namedtuple('node', ['uuid'])
        side_effect = (ironicexp.ConnectionRefused,
                       ironicexp.ServiceUnavailable, ironic_node('1'))
        ironic.node.create.side_effect = side_effect
        nodes.register_ironic_node(None, self._get_node(), client=ironic)
        sleep.assert_has_calls([mock.call(10), mock.call(10)])
        node_create = mock.call(driver='pxe_ssh',
                                driver_info=mock.ANY,
                                properties=mock.ANY)
        ironic.node.create.assert_has_calls(node_create)

    @mock.patch('time.sleep')
    def test_register_ironic_node_failure(self, sleep):
        ironic = mock.MagicMock()
        ironic.node.create.side_effect = ironicexp.ConnectionRefused
        self.assertRaises(ironicexp.ServiceUnavailable,
                          nodes.register_ironic_node, None, self._get_node(),
                          client=ironic)

    def test_using_ironic(self):
        keystone = mock.MagicMock()
        service = collections.namedtuple('servicelist', ['name'])
        keystone.services.list.return_value = [service('compute')]
        self.assertFalse(nodes.using_ironic(keystone=keystone))
        self.assertEqual(1, keystone.services.list.call_count)

    def test_registered_nova_bm_nodes(self):
        interface = {u'datapath_id': None, u'id': 1, u'port_no': None,
                     u'address': u'aaa'}
        node_details = {u'instance_uuid': None, u'pm_address': u'foo.bar',
                        u'task_state': None, u'uuid': uuid.uuid1(),
                        u'local_gb': 30, u'interfaces': [interface],
                        u'cpus': 1, u'updated_at': None, u'memory_mb': 2048,
                        u'service_host': u'seed', u'pxe_config_path': None,
                        u'id': 1, u'pm_user': u'test', u'terminal_port': None}
        bm_node = mock.MagicMock()
        bm_node.to_dict.return_value = node_details
        client = mock.MagicMock()
        client.baremetal.list.return_value = [bm_node]
        registered_nodes = nodes.registered_nova_bm_nodes(client)
        existing_node = self._get_node()
        for key in ('cpu', 'memory', 'disk', 'mac', 'pm_addr', 'pm_user'):
            self.assertEqual(registered_nodes[0][key], existing_node[key])

    def _create_ironic_node_mock_and_assert(self, driver, driver_info):
        node = mock.MagicMock()
        node.to_dict.return_value = {'uuid': uuid.uuid1()}
        client = mock.MagicMock()
        client.node.list.return_value = [node]
        ironic_node = collections.namedtuple('node',
                                             ['properties', 'driver',
                                              'driver_info'])
        properties = {u'cpus': u'1', u'memory_mb': u'2048',
                      u'local_gb': u'30', u'cpu_arch': u'amd64'}
        client.node.get.return_value = ironic_node(properties, driver,
                                                   driver_info)
        port = collections.namedtuple('port', 'address')
        client.node.list_ports.return_value = [port('aaa')]
        registered_nodes = nodes.registered_ironic_nodes(client)
        existing_node = self._get_node()
        for key in ('cpu', 'memory', 'disk', 'arch', 'mac', 'pm_addr',
                    'pm_user', 'pm_password'):
            self.assertEqual(registered_nodes[0][key], existing_node[key])

    def test_registered_ironic_nodes_impi(self):
        driver_info = {u'ssh_address': u'foo.bar', u'ssh_username': u'test',
                       u'ssh_key_contents': u'random'}
        self._create_ironic_node_mock_and_assert('pxe_ssh', driver_info)

    def test_registered_ironic_nodes_ssh(self):
        driver_info = {u'ipmi_address': u'foo.bar', u'ipmi_username': u'test',
                       u'ipmi_password': 'random'}
        self._create_ironic_node_mock_and_assert('ipmi', driver_info)

    def test_node_is_not_registered(self):
        self.assertFalse(nodes.node_is_registered([], self._get_node()))

    def test_node_is_registered(self):
        node = self._get_node()
        registered_nodes = [self._get_node()]
        self.assertTrue(nodes.node_is_registered(registered_nodes, node))

    def test_node_is_not_registered_non_matching_second_mac(self):
        node = self._get_node()
        node["mac"].append("ccc")
        registered_nodes = [self._get_node()]
        registered_nodes[0]["mac"].append("bbb")
        self.assertFalse(nodes.node_is_registered(registered_nodes, node))

    def test_node_is_not_registered_matching_mac_non_matching_details(self):
        node = self._get_node()
        registered_nodes = [self._get_node()]
        registered_nodes[0]["pm_addr"] = 'barbaz'
        registered_nodes[0]["memory"] = 4
        self.assertFalse(nodes.node_is_registered(registered_nodes, node))
