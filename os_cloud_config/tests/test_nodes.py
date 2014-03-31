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

import mock

from os_cloud_config import nodes
from os_cloud_config.tests import base


class NodesTest(base.TestCase):

    def _get_node(self):
        return {'cpu': '1', 'memory': '2048', 'disk': '30', 'arch': 'amd64',
                'mac': ['aaa'], 'pm_addr': 'foo.bar', 'pm_user': 'test',
                'pm_password': 'random', 'pm_type': 'pxe_ssh'}

    @mock.patch('subprocess.check_output')
    def test_register_all_nodes_nova_bm(self, check_output):
        node_list = [self._get_node(), self._get_node()]
        nodes.using_ironic = mock.MagicMock(return_value=False)
        nodes.register_all_nodes('servicehost', node_list)
        nova_bm_call = mock.call(
            ["nova", "baremetal-node-create", "--pm_address=foo.bar",
             "--pm_user=test", "--pm_password=random", "servicehost", "1",
             "2048", "30", "aaa"])
        check_output.has_calls([nova_bm_call, nova_bm_call])

    @mock.patch('subprocess.check_call')
    @mock.patch('subprocess.check_output')
    def test_register_all_nodes_ironic(self, check_output, check_call):
        node_list = [self._get_node(), self._get_node()]
        node_list[1]["pm_type"] = "impi"
        nodes.using_ironic = mock.MagicMock(return_value=True)
        nodes._get_id_line = mock.MagicMock(return_value="1")
        nodes.register_all_nodes('servicehost', node_list)
        pxe_node_create = mock.call(
            ["ironic", "node-create", "-d", "pxe_ssh"])
        impi_node_create = mock.call(
            ["ironic", "node-create", "-d", "impi"])
        check_output.has_calls([pxe_node_create, impi_node_create])
        ssh_key = "/mnt/state/var/lib/ironic/virtual-power-key"
        common_update_args = [
            "ironic", "node-update", "1", "add", "properties/cpus=1",
            "properties/memory_mb=2048", "properties/local_gb=30",
            "properties/cpu_arch=amd64"]
        pxe_node_update_call = mock.call(
            common_update_args + ["driver_info/ssh_address=foo.bar",
                                  "driver_info/ssh_username=test",
                                  "driver_info/ssh_key_filename=%s" % ssh_key,
                                  "driver_info/ssh_virt_type=virsh"])
        impi_node_update_call = mock.call(
            common_update_args + ["driver_info/ipmi_address=foo.bar",
                                  "driver_info/ipmi_username=test",
                                  "driver_info/impi_password=random"])
        power_off_call = mock.call(
            ["ironic", "node-set-power-state", "1", "off"])
        port_update_call = mock.call(
            ["ironic", "port-create", "-a", "aaa", "-n", "1"])
        check_call.assert_has_calls(
            [pxe_node_update_call, power_off_call, port_update_call,
             impi_node_update_call, power_off_call, port_update_call])
