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

from ironicclient.openstack.common.apiclient import exceptions as ironicexp
import mock
from novaclient.openstack.common.apiclient import exceptions as novaexc
from testtools import matchers

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

    def test_register_list_of_nodes(self):
        nodes_list = ['aaa', 'bbb']
        return_node = nodes_list[0]
        register_func = mock.MagicMock()
        register_func.side_effect = [return_node, ironicexp.Conflict]
        seen = nodes._register_list_of_nodes(register_func, {}, None,
                                             nodes_list, False, 'servicehost',
                                             None, None)
        self.assertEqual(seen, set(nodes_list))

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

    @mock.patch('os_cloud_config.nodes.using_ironic', return_value=False)
    @mock.patch('os_cloud_config.nodes.register_nova_bm_node')
    def test_register_nova_bm_node_no_update(self, ironic_mock, register_mock):
        client = mock.MagicMock()
        node_map = {'mac': {'aaa': 1}}
        nodes._update_or_register_bm_node('servicehost', self._get_node(),
                                          node_map, client=client)
        client.baremetal.get.assert_called_once_with(1)
        register_mock.assert_not_called()

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

    def test_register_nova_bm_node_int_values(self):
        node = self._get_node()
        node['cpu'] = 1
        node['memory'] = 2048
        node['disk'] = 30
        client = mock.MagicMock()
        nodes.register_nova_bm_node('service_host', node, client=client)
        client.baremetal.create.assert_called_once_with('service_host', '1',
                                                        '2048', '30',
                                                        node["mac"][0],
                                                        pm_password='random',
                                                        pm_address='foo.bar',
                                                        pm_user='test')

    def test_extract_driver_info_ipmi(self):
        node = self._get_node()
        node["pm_type"] = "ipmi"
        expected = {"ipmi_address": "foo.bar",
                    "ipmi_username": "test",
                    "ipmi_password": "random"}
        self.assertEqual(expected, nodes._extract_driver_info(node))

    def test_extract_driver_info_pxe_ssh(self):
        node = self._get_node()
        node["pm_type"] = "pxe_ssh"
        expected = {"ssh_address": "foo.bar",
                    "ssh_username": "test",
                    "ssh_key_contents": "random",
                    "ssh_virt_type": "virsh"}
        self.assertEqual(expected, nodes._extract_driver_info(node))

    def test_extract_driver_info_pxe_drac(self):
        node = self._get_node()
        node["pm_type"] = "pxe_drac"
        expected = {"drac_host": "foo.bar",
                    "drac_username": "test",
                    "drac_password": "random"}
        self.assertEqual(expected, nodes._extract_driver_info(node))

    def test_extract_driver_info_pxe_ssh_with_pm_virt_type(self):
        node = self._get_node()
        node["pm_type"] = "pxe_ssh"
        node["pm_virt_type"] = "vbox"
        expected = {"ssh_address": "foo.bar",
                    "ssh_username": "test",
                    "ssh_key_contents": "random",
                    "ssh_virt_type": "vbox"}
        self.assertEqual(expected, nodes._extract_driver_info(node))

    def test_extract_driver_info_pxe_iboot(self):
        node = self._get_node()
        node["pm_type"] = "pxe_iboot"
        expected = {"iboot_address": "foo.bar",
                    "iboot_username": "test",
                    "iboot_password": "random"}
        self.assertEqual(expected, nodes._extract_driver_info(node))

    def test_extract_driver_info_pxe_iboot_with_pm_relay_id(self):
        node = self._get_node()
        node["pm_type"] = "pxe_iboot"
        node["pm_relay_id"] = "pxe_iboot_id"
        expected = {"iboot_address": "foo.bar",
                    "iboot_username": "test",
                    "iboot_password": "random",
                    "iboot_relay_id": "pxe_iboot_id"}
        self.assertEqual(expected, nodes._extract_driver_info(node))

    def test_extract_driver_info_pxe_iboot_with_pm_port(self):
        node = self._get_node()
        node["pm_type"] = "pxe_iboot"
        node["pm_port"] = "8080"
        expected = {"iboot_address": "foo.bar",
                    "iboot_username": "test",
                    "iboot_password": "random",
                    "iboot_port": "8080"}
        self.assertEqual(expected, nodes._extract_driver_info(node))

    def test_extract_driver_info_pxe_ipmi_with_kernel_ramdisk(self):
        node = self._get_node()
        node["pm_type"] = "pxe_ipmi"
        node["kernel_id"] = "kernel-abc"
        node["ramdisk_id"] = "ramdisk-foo"
        expected = {"ipmi_address": "foo.bar",
                    "ipmi_username": "test",
                    "ipmi_password": "random",
                    "deploy_kernel": "kernel-abc",
                    "deploy_ramdisk": "ramdisk-foo"}
        self.assertEqual(expected, nodes._extract_driver_info(node))

    def test_extract_driver_info_unknown_type(self):
        node = self._get_node()
        node["pm_type"] = "unknown_type"
        self.assertRaises(ValueError, nodes._extract_driver_info, node)

    @mock.patch('os_cloud_config.nodes.using_ironic', return_value=True)
    def test_register_all_nodes_ironic(self, using_ironic):
        node_list = [self._get_node()]
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
        pxe_node = mock.call(driver="pxe_ssh",
                             driver_info=pxe_node_driver_info,
                             properties=node_properties)
        port_call = mock.call(node_uuid=ironic.node.create.return_value.uuid,
                              address='aaa')
        power_off_call = mock.call(ironic.node.create.return_value.uuid, 'off')
        using_ironic.assert_called_once_with(keystone=None)
        ironic.node.create.assert_has_calls([pxe_node, mock.ANY])
        ironic.port.create.assert_has_calls([port_call])
        ironic.node.set_power_state.assert_has_calls([power_off_call])

    @mock.patch('os_cloud_config.nodes.using_ironic', return_value=True)
    def test_register_all_nodes_ironic_kernel_ramdisk(self, using_ironic):
        node_list = [self._get_node()]
        node_properties = {"cpus": "1",
                           "memory_mb": "2048",
                           "local_gb": "30",
                           "cpu_arch": "amd64"}
        ironic = mock.MagicMock()
        glance = mock.MagicMock()
        image = collections.namedtuple('image', ['id'])
        glance.images.find.side_effect = (image('kernel-123'),
                                          image('ramdisk-999'))
        nodes.register_all_nodes('servicehost', node_list, client=ironic,
                                 glance_client=glance, kernel_name='bm-kernel',
                                 ramdisk_name='bm-ramdisk')
        pxe_node_driver_info = {"ssh_address": "foo.bar",
                                "ssh_username": "test",
                                "ssh_key_contents": "random",
                                "ssh_virt_type": "virsh",
                                "deploy_kernel": "kernel-123",
                                "deploy_ramdisk": "ramdisk-999"}
        pxe_node = mock.call(driver="pxe_ssh",
                             driver_info=pxe_node_driver_info,
                             properties=node_properties)
        port_call = mock.call(node_uuid=ironic.node.create.return_value.uuid,
                              address='aaa')
        power_off_call = mock.call(ironic.node.create.return_value.uuid, 'off')
        using_ironic.assert_called_once_with(keystone=None)
        ironic.node.create.assert_has_calls([pxe_node, mock.ANY])
        ironic.port.create.assert_has_calls([port_call])
        ironic.node.set_power_state.assert_has_calls([power_off_call])

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

    def test_register_ironic_node_update(self):
        node = self._get_node()
        ironic = mock.MagicMock()
        node_map = {'mac': {'aaa': 1}}

        def side_effect(*args, **kwargs):
            update_patch = [
                {'path': '/driver_info/ssh_key_contents', 'value': 'random'},
                {'path': '/driver_info/ssh_address', 'value': 'foo.bar'},
                {'path': '/properties/memory_mb', 'value': '2048'},
                {'path': '/properties/local_gb', 'value': '30'},
                {'path': '/properties/cpu_arch', 'value': 'amd64'},
                {'path': '/properties/cpus', 'value': '1'},
                {'path': '/driver_info/ssh_username', 'value': 'test'}]
            for key in update_patch:
                key['op'] = 'replace'
            self.assertThat(update_patch,
                            matchers.MatchesSetwise(*(map(matchers.Equals,
                                                          args[1]))))
        ironic.node.update.side_effect = side_effect
        nodes._update_or_register_ironic_node(None, node, node_map,
                                              client=ironic)
        ironic.node.update.assert_called_once_with(
            ironic.node.get.return_value.uuid, mock.ANY)

    def _update_by_type(self, pm_type):
        ironic = mock.MagicMock()
        node_map = {'mac': {}, 'pm_addr': {}}
        node = self._get_node()
        node['pm_type'] = pm_type
        node_map['pm_addr']['foo.bar'] = ironic.node.get.return_value.uuid
        nodes._update_or_register_ironic_node('servicehost', node,
                                              node_map, client=ironic)
        ironic.node.update.assert_called_once_with(
            ironic.node.get.return_value.uuid, mock.ANY)

    def test_update_node_ironic_pxe_ipmitool(self):
        self._update_by_type('pxe_ipmitool')

    def test_ipdate_node_ironic_pxe_drac(self):
        self._update_by_type('pxe_drac')

    def test_update_node_ironic_pxe_ilo(self):
        self._update_by_type('pxe_ilo')

    def test_register_ironic_node_update_uppercase_mac(self):
        node = self._get_node()
        node['mac'][0] = node['mac'][0].upper()
        ironic = mock.MagicMock()
        node_map = {'mac': {'aaa': 1}}

        def side_effect(*args, **kwargs):
            update_patch = [
                {'path': '/driver_info/ssh_key_contents', 'value': 'random'},
                {'path': '/driver_info/ssh_address', 'value': 'foo.bar'},
                {'path': '/properties/memory_mb', 'value': '2048'},
                {'path': '/properties/local_gb', 'value': '30'},
                {'path': '/properties/cpu_arch', 'value': 'amd64'},
                {'path': '/properties/cpus', 'value': '1'},
                {'path': '/driver_info/ssh_username', 'value': 'test'}]
            for key in update_patch:
                key['op'] = 'replace'
            self.assertThat(update_patch,
                            matchers.MatchesSetwise(*(map(matchers.Equals,
                                                          args[1]))))

        ironic.node.update.side_effect = side_effect
        nodes._update_or_register_ironic_node(None, node, node_map,
                                              client=ironic)
        ironic.node.update.assert_called_once_with(
            ironic.node.get.return_value.uuid, mock.ANY)

    @mock.patch('time.sleep')
    def test_register_ironic_node_update_locked_node(self, sleep):
        node = self._get_node()
        ironic = mock.MagicMock()
        ironic.node.update.side_effect = ironicexp.Conflict
        node_map = {'mac': {'aaa': 1}}
        self.assertRaises(ironicexp.Conflict,
                          nodes._update_or_register_ironic_node, None, node,
                          node_map, client=ironic)

    def test_register_ironic_node_int_values(self):
        node_properties = {"cpus": "1",
                           "memory_mb": "2048",
                           "local_gb": "30",
                           "cpu_arch": "amd64"}
        node = self._get_node()
        node['cpu'] = 1
        node['memory'] = 2048
        node['disk'] = 30
        client = mock.MagicMock()
        nodes.register_ironic_node('service_host', node, client=client)
        client.node.create.assert_called_once_with(driver=mock.ANY,
                                                   properties=node_properties,
                                                   driver_info=mock.ANY)

    def test_register_ironic_node_update_int_values(self):
        node = self._get_node()
        ironic = mock.MagicMock()
        node['cpu'] = 1
        node['memory'] = 2048
        node['disk'] = 30
        node_map = {'mac': {'aaa': 1}}

        def side_effect(*args, **kwargs):
            update_patch = [
                {'path': '/driver_info/ssh_key_contents', 'value': 'random'},
                {'path': '/driver_info/ssh_address', 'value': 'foo.bar'},
                {'path': '/properties/memory_mb', 'value': '2048'},
                {'path': '/properties/local_gb', 'value': '30'},
                {'path': '/properties/cpu_arch', 'value': 'amd64'},
                {'path': '/properties/cpus', 'value': '1'},
                {'path': '/driver_info/ssh_username', 'value': 'test'}]
            for key in update_patch:
                key['op'] = 'replace'
            self.assertThat(update_patch,
                            matchers.MatchesSetwise(*(map(matchers.Equals,
                                                      args[1]))))
        ironic.node.update.side_effect = side_effect
        nodes._update_or_register_ironic_node(None, node, node_map,
                                              client=ironic)

    def test_populate_node_mapping_nova_bm(self):
        client = mock.MagicMock()
        node1 = mock.MagicMock()
        node1.to_dict.return_value = {'id': '1',
                                      'interfaces': [{'address': 'aaa'}],
                                      'pm_address': '10.0.1.5'}
        node4 = mock.MagicMock()
        node4.to_dict.return_value = {'id': '4', 'interfaces': [],
                                      'pm_address': '10.0.1.2'}
        client.baremetal.list.return_value = [node1, node4]
        expected = {'mac': {'aaa': '1'},
                    'pm_addr': {'10.0.1.2': '4', '10.0.1.5': '1'}}
        self.assertEqual(expected, nodes._populate_node_mapping(False, client))

    def test_populate_node_mapping_ironic(self):
        client = mock.MagicMock()
        node1 = mock.MagicMock()
        node1.to_dict.return_value = {'uuid': 'abcdef'}
        node2 = mock.MagicMock()
        node2.to_dict.return_value = {'uuid': 'fedcba'}
        ironic_node = collections.namedtuple('node', ['uuid', 'driver',
                                             'driver_info'])
        ironic_port = collections.namedtuple('port', ['address'])
        node1_detail = ironic_node('abcdef', 'pxe_ssh', None)
        node2_detail = ironic_node('fedcba', 'ipmi',
                                   {'ipmi_address': '10.0.1.2'})
        client.node.get.side_effect = (node1_detail, node2_detail)
        client.node.list_ports.return_value = [ironic_port('aaa')]
        client.node.list.return_value = [node1, node2]
        expected = {'mac': {'aaa': 'abcdef'},
                    'pm_addr': {'10.0.1.2': 'fedcba'}}
        self.assertEqual(expected, nodes._populate_node_mapping(True, client))

    def test_clean_up_extra_nodes_nova_bm(self):
        node = collections.namedtuple('node', ['id'])
        client = mock.MagicMock()
        client.baremetal.list.return_value = [node('4')]
        nodes._clean_up_extra_nodes(False, set((1,)), client, remove=True)
        client.baremetal.delete.assert_called_once_with('4')

    def test_clean_up_extra_nodes_ironic(self):
        node = collections.namedtuple('node', ['uuid'])
        client = mock.MagicMock()
        client.node.list.return_value = [node('foobar')]
        nodes._clean_up_extra_nodes(True, set(('abcd',)), client, remove=True)
        client.node.delete.assert_called_once_with('foobar')

    def test_using_ironic(self):
        keystone = mock.MagicMock()
        service = collections.namedtuple('servicelist', ['name'])
        keystone.services.list.return_value = [service('compute')]
        self.assertFalse(nodes.using_ironic(keystone=keystone))
        self.assertEqual(1, keystone.services.list.call_count)
