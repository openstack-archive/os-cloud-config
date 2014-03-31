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
import subprocess

from os_cloud_config import nodes
from os_cloud_config.tests import base


class NodesTest(base.TestCase):

    def setUp(self):
        super(NodesTest, self).setUp()
        subprocess.check_call = mock.MagicMock()
        subprocess.check_output = mock.MagicMock()

    def _get_node(self):
        return {'cpu': '1', 'memory': '2048', 'disk': '30', 'arch': 'amd64',
                'mac': ['aaa'], 'pm_addr': 'foo.bar', 'pm_user': 'test',
                'pm_password': 'random', 'pm_type': 'pxe_ssh'}

    def test_register_all_nodes_nova_bm(self):
        node_list = [self._get_node(), self._get_node()]
        nodes.using_ironic = mock.MagicMock(return_value=False)
        nodes.register_all_nodes('servicehost', node_list)
        subprocess.check_output.assert_called_with(
            ["nova", "baremetal-node-create", "--pm_address=foo.bar",
             "--pm_user=test", "--pm_password=random", "servicehost", "1",
             "2048", "30", "aaa"])

    def test_register_all_nodes_ironic(self):
        node_list = [self._get_node(), self._get_node()]
        nodes.using_ironic = mock.MagicMock(return_value=True)
        nodes.register_all_nodes('servicehost', node_list)
        subprocess.check_output.assert_called_with(
            ["ironic", "node-create", "-d", "pxe_ssh"])
