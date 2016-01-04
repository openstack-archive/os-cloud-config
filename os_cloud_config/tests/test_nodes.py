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

from ironicclient import exc as ironicexp
import mock
from testtools import matchers

from os_cloud_config import nodes
from os_cloud_config.tests import base


class NodesTest(base.TestCase):

    def _get_node(self):
        return {'cpu': '1', 'memory': '2048', 'disk': '30', 'arch': 'amd64',
                'mac': ['aaa'], 'pm_addr': 'foo.bar', 'pm_user': 'test',
                'pm_password': 'random', 'pm_type': 'pxe_ssh', 'name': 'node1',
                'capabilities': 'num_nics:6'}

    def test_register_list_of_nodes(self):
        nodes_list = ['aaa', 'bbb']
        return_node = nodes_list[0]
        register_func = mock.MagicMock()
        register_func.side_effect = [return_node, ironicexp.Conflict]
        seen = nodes._register_list_of_nodes(register_func, {}, None,
                                             nodes_list, False, 'servicehost',
                                             None, None)
        self.assertEqual(seen, set(nodes_list))

    def test_extract_driver_info_ipmi(self):
        node = self._get_node()
        node["pm_type"] = "ipmi"
        expected = {"ipmi_address": "foo.bar",
                    "ipmi_username": "test",
                    "ipmi_password": "random"}
        self.assertEqual(expected, nodes._extract_driver_info(node))

    def test_extract_driver_info_ipmi_extended(self):
        node = self._get_node()
        node["pm_type"] = "ipmi"
        node["ipmi_bridging"] = "dual"
        node["ipmi_transit_address"] = "0x42"
        node["ipmi_transit_channel"] = "0"
        node["ipmi_target_address"] = "0x41"
        node["ipmi_target_channel"] = "1"
        node["ipmi_local_address"] = "0"
        expected = {"ipmi_address": "foo.bar",
                    "ipmi_username": "test",
                    "ipmi_password": "random",
                    "ipmi_bridging": "dual",
                    "ipmi_transit_address": "0x42",
                    "ipmi_transit_channel": "0",
                    "ipmi_target_address": "0x41",
                    "ipmi_target_channel": "1",
                    "ipmi_local_address": "0",
                    }
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

    def test_extract_driver_info_pxe_ucs(self):
        node = self._get_node()
        node["pm_type"] = "pxe_ucs"
        node["pm_service_profile"] = "foo_profile"
        expected = {"ucs_hostname": "foo.bar",
                    "ucs_username": "test",
                    "ucs_password": "random",
                    "ucs_service_profile": "foo_profile"}
        self.assertEqual(expected, nodes._extract_driver_info(node))

    def test_extract_driver_info_pxe_irmc(self):
        node = self._get_node()
        node["pm_type"] = "pxe_irmc"
        expected = {"irmc_address": "foo.bar",
                    "irmc_username": "test",
                    "irmc_password": "random"}
        self.assertEqual(expected, nodes._extract_driver_info(node))

    def test_extract_driver_info_pxe_irmc_with_irmc_port(self):
        node = self._get_node()
        node["pm_type"] = "pxe_irmc"
        node["pm_port"] = "443"
        expected = {"irmc_address": "foo.bar",
                    "irmc_username": "test",
                    "irmc_password": "random",
                    "irmc_port": "443"}
        self.assertEqual(expected, nodes._extract_driver_info(node))

    def test_extract_driver_info_pxe_irmc_with_irmc_auth_method(self):
        node = self._get_node()
        node["pm_type"] = "pxe_irmc"
        node["pm_auth_method"] = "baz_auth_method"
        expected = {"irmc_address": "foo.bar",
                    "irmc_username": "test",
                    "irmc_password": "random",
                    "irmc_auth_method": "baz_auth_method"}
        self.assertEqual(expected, nodes._extract_driver_info(node))

    def test_extract_driver_info_pxe_irmc_with_irmc_client_timeout(self):
        node = self._get_node()
        node["pm_type"] = "pxe_irmc"
        node["pm_client_timeout"] = "60"
        expected = {"irmc_address": "foo.bar",
                    "irmc_username": "test",
                    "irmc_password": "random",
                    "irmc_client_timeout": "60"}
        self.assertEqual(expected, nodes._extract_driver_info(node))

    def test_extract_driver_info_pxe_irmc_with_irmc_sensor_method(self):
        node = self._get_node()
        node["pm_type"] = "pxe_irmc"
        node["pm_sensor_method"] = "ipmitool"
        expected = {"irmc_address": "foo.bar",
                    "irmc_username": "test",
                    "irmc_password": "random",
                    "irmc_sensor_method": "ipmitool"}
        self.assertEqual(expected, nodes._extract_driver_info(node))

    def test_extract_driver_info_iscsi_irmc(self):
        node = self._get_node()
        node["pm_type"] = "iscsi_irmc"
        node["pm_deploy_iso"] = "deploy.iso"
        expected = {"irmc_address": "foo.bar",
                    "irmc_username": "test",
                    "irmc_password": "random",
                    "irmc_deploy_iso": "deploy.iso"}
        self.assertEqual(expected, nodes._extract_driver_info(node))

    def test_extract_driver_info_agent_irmc(self):
        node = self._get_node()
        node["pm_type"] = "agent_irmc"
        node["pm_deploy_iso"] = "deploy.iso"
        expected = {"irmc_address": "foo.bar",
                    "irmc_username": "test",
                    "irmc_password": "random",
                    "irmc_deploy_iso": "deploy.iso"}
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

    def test_extract_driver_info_pxe_wol(self):
        node = self._get_node()
        node["pm_type"] = "pxe_wol"
        expected = {"wol_host": "foo.bar"}
        self.assertEqual(expected, nodes._extract_driver_info(node))

    def test_extract_driver_info_unknown_type(self):
        node = self._get_node()
        node["pm_type"] = "unknown_type"
        self.assertRaises(ValueError, nodes._extract_driver_info, node)

    def test_register_all_nodes_ironic_no_hw_stats(self):
        node_list = [self._get_node()]

        # Remove the hardware stats from the node dictionary
        node_list[0].pop("cpu")
        node_list[0].pop("memory")
        node_list[0].pop("disk")
        node_list[0].pop("arch")

        # Node properties should be created with empty string values for the
        # hardware statistics
        node_properties = {"capabilities": "num_nics:6"}

        ironic = mock.MagicMock()
        nodes.register_all_nodes('servicehost', node_list, client=ironic)
        pxe_node_driver_info = {"ssh_address": "foo.bar",
                                "ssh_username": "test",
                                "ssh_key_contents": "random",
                                "ssh_virt_type": "virsh"}
        pxe_node = mock.call(driver="pxe_ssh",
                             name='node1',
                             driver_info=pxe_node_driver_info,
                             properties=node_properties)
        port_call = mock.call(node_uuid=ironic.node.create.return_value.uuid,
                              address='aaa')
        power_off_call = mock.call(ironic.node.create.return_value.uuid, 'off')
        ironic.node.create.assert_has_calls([pxe_node, mock.ANY])
        ironic.port.create.assert_has_calls([port_call])
        ironic.node.set_power_state.assert_has_calls([power_off_call])

    def test_register_all_nodes_ironic(self):
        node_list = [self._get_node()]
        node_properties = {"cpus": "1",
                           "memory_mb": "2048",
                           "local_gb": "30",
                           "cpu_arch": "amd64",
                           "capabilities": "num_nics:6"}
        ironic = mock.MagicMock()
        nodes.register_all_nodes('servicehost', node_list, client=ironic)
        pxe_node_driver_info = {"ssh_address": "foo.bar",
                                "ssh_username": "test",
                                "ssh_key_contents": "random",
                                "ssh_virt_type": "virsh"}
        pxe_node = mock.call(driver="pxe_ssh",
                             name='node1',
                             driver_info=pxe_node_driver_info,
                             properties=node_properties)
        port_call = mock.call(node_uuid=ironic.node.create.return_value.uuid,
                              address='aaa')
        power_off_call = mock.call(ironic.node.create.return_value.uuid, 'off')
        ironic.node.create.assert_has_calls([pxe_node, mock.ANY])
        ironic.port.create.assert_has_calls([port_call])
        ironic.node.set_power_state.assert_has_calls([power_off_call])

    def test_register_all_nodes_ironic_kernel_ramdisk(self):
        node_list = [self._get_node()]
        node_properties = {"cpus": "1",
                           "memory_mb": "2048",
                           "local_gb": "30",
                           "cpu_arch": "amd64",
                           "capabilities": "num_nics:6"}
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
                             name='node1',
                             driver_info=pxe_node_driver_info,
                             properties=node_properties)
        port_call = mock.call(node_uuid=ironic.node.create.return_value.uuid,
                              address='aaa')
        power_off_call = mock.call(ironic.node.create.return_value.uuid, 'off')
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
                                name='node1',
                                driver_info=mock.ANY,
                                properties=mock.ANY)
        ironic.node.create.assert_has_calls([node_create, node_create,
                                             node_create])

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
                {'path': '/name', 'value': 'node1'},
                {'path': '/driver_info/ssh_key_contents', 'value': 'random'},
                {'path': '/driver_info/ssh_address', 'value': 'foo.bar'},
                {'path': '/properties/memory_mb', 'value': '2048'},
                {'path': '/properties/local_gb', 'value': '30'},
                {'path': '/properties/cpu_arch', 'value': 'amd64'},
                {'path': '/properties/cpus', 'value': '1'},
                {'path': '/properties/capabilities', 'value': 'num_nics:6'},
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

    def test_update_node_ironic_pxe_drac(self):
        self._update_by_type('pxe_drac')

    def test_update_node_ironic_pxe_ilo(self):
        self._update_by_type('pxe_ilo')

    def test_update_node_ironic_pxe_irmc(self):
        self._update_by_type('pxe_irmc')

    def test_register_ironic_node_update_uppercase_mac(self):
        node = self._get_node()
        node['mac'][0] = node['mac'][0].upper()
        ironic = mock.MagicMock()
        node_map = {'mac': {'aaa': 1}}

        def side_effect(*args, **kwargs):
            update_patch = [
                {'path': '/name', 'value': 'node1'},
                {'path': '/driver_info/ssh_key_contents', 'value': 'random'},
                {'path': '/driver_info/ssh_address', 'value': 'foo.bar'},
                {'path': '/properties/memory_mb', 'value': '2048'},
                {'path': '/properties/local_gb', 'value': '30'},
                {'path': '/properties/cpu_arch', 'value': 'amd64'},
                {'path': '/properties/cpus', 'value': '1'},
                {'path': '/properties/capabilities', 'value': 'num_nics:6'},
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
                           "cpu_arch": "amd64",
                           "capabilities": "num_nics:6"}
        node = self._get_node()
        node['cpu'] = 1
        node['memory'] = 2048
        node['disk'] = 30
        client = mock.MagicMock()
        nodes.register_ironic_node('service_host', node, client=client)
        client.node.create.assert_called_once_with(driver=mock.ANY,
                                                   name='node1',
                                                   properties=node_properties,
                                                   driver_info=mock.ANY)

    def test_register_ironic_node_fake_pxe(self):
        node_properties = {"cpus": "1",
                           "memory_mb": "2048",
                           "local_gb": "30",
                           "cpu_arch": "amd64",
                           "capabilities": "num_nics:6"}
        node = self._get_node()
        for v in ('pm_addr', 'pm_user', 'pm_password'):
            del node[v]
        node['pm_type'] = 'fake_pxe'
        client = mock.MagicMock()
        nodes.register_ironic_node('service_host', node, client=client)
        client.node.create.assert_called_once_with(driver='fake_pxe',
                                                   name='node1',
                                                   properties=node_properties,
                                                   driver_info={})

    def test_register_ironic_node_update_int_values(self):
        node = self._get_node()
        ironic = mock.MagicMock()
        node['cpu'] = 1
        node['memory'] = 2048
        node['disk'] = 30
        node_map = {'mac': {'aaa': 1}}

        def side_effect(*args, **kwargs):
            update_patch = [
                {'path': '/name', 'value': 'node1'},
                {'path': '/driver_info/ssh_key_contents', 'value': 'random'},
                {'path': '/driver_info/ssh_address', 'value': 'foo.bar'},
                {'path': '/properties/memory_mb', 'value': '2048'},
                {'path': '/properties/local_gb', 'value': '30'},
                {'path': '/properties/cpu_arch', 'value': 'amd64'},
                {'path': '/properties/cpus', 'value': '1'},
                {'path': '/properties/capabilities', 'value': 'num_nics:6'},
                {'path': '/driver_info/ssh_username', 'value': 'test'}]
            for key in update_patch:
                key['op'] = 'replace'
            self.assertThat(update_patch,
                            matchers.MatchesSetwise(*(map(matchers.Equals,
                                                      args[1]))))
        ironic.node.update.side_effect = side_effect
        nodes._update_or_register_ironic_node(None, node, node_map,
                                              client=ironic)

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
        self.assertEqual(expected, nodes._populate_node_mapping(client))

    def test_populate_node_mapping_ironic_fake_pxe(self):
        client = mock.MagicMock()
        node = mock.MagicMock()
        node.to_dict.return_value = {'uuid': 'abcdef'}
        ironic_node = collections.namedtuple('node', ['uuid', 'driver',
                                             'driver_info'])
        ironic_port = collections.namedtuple('port', ['address'])
        node_detail = ironic_node('abcdef', 'fake_pxe', None)
        client.node.get.return_value = node_detail
        client.node.list_ports.return_value = [ironic_port('aaa')]
        client.node.list.return_value = [node]
        expected = {'mac': {'aaa': 'abcdef'}, 'pm_addr': {}}
        self.assertEqual(expected, nodes._populate_node_mapping(client))

    def test_clean_up_extra_nodes_ironic(self):
        node = collections.namedtuple('node', ['uuid'])
        client = mock.MagicMock()
        client.node.list.return_value = [node('foobar')]
        nodes._clean_up_extra_nodes(set(('abcd',)), client, remove=True)
        client.node.delete.assert_called_once_with('foobar')

    def test__get_node_id_fake_pxe(self):
        node = self._get_node()
        node['pm_type'] = 'fake_pxe'
        node_map = {'mac': {'aaa': 'abcdef'}, 'pm_addr': {}}
        self.assertEqual('abcdef', nodes._get_node_id(node, node_map))
