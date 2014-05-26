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

    def test_check_output(self):
        self.assertEqual("/dev/null\n",
                         nodes._check_output(["ls", "/dev/null"]))

    @mock.patch('os_cloud_config.nodes._check_output')
    @mock.patch('os_cloud_config.nodes.using_ironic', return_value=False)
    def test_register_all_nodes_nova_bm(self, ironic_mock, check_mock):
        node_list = [self._get_node(), self._get_node()]
        nodes.register_all_nodes('servicehost', node_list)
        nova_bm_call = mock.call(
            ["nova", "baremetal-node-create", "--pm_address=foo.bar",
             "--pm_user=test", "--pm_password=random", "servicehost", "1",
             "2048", "30", "aaa"])
        check_mock.has_calls([nova_bm_call, nova_bm_call])

    @mock.patch('os.environ')
    @mock.patch('ironicclient.client.get_client')
    def test_get_ironic_client(self, client_mock, environ):
        nodes._get_ironic_client()
        client_mock.assert_called_once_with(
            1, os_username=environ["OS_USERNAME"],
            os_password=environ["OS_PASSWORD"],
            os_auth_url=environ["OS_AUTH_URL"],
            os_tenant_name=environ["OS_TENANT_NAME"])

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
        ssh_key = "/mnt/state/var/lib/ironic/virtual-power-key"
        pxe_node_driver_info = {"ssh_address": "foo.bar",
                                "ssh_username": "test",
                                "ssh_key_filename": ssh_key,
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
