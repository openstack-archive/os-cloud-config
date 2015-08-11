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

from os_cloud_config import flavors
from os_cloud_config.tests import base


class FlavorsTest(base.TestCase):

    def test_cleanup_flavors(self):
        client = mock.MagicMock()
        to_del = ('m1.tiny', 'm1.small', 'm1.medium', 'm1.large', 'm1.xlarge')
        delete_calls = [mock.call(flavor) for flavor in to_del]
        flavors.cleanup_flavors(client=client)
        client.flavors.delete.has_calls(delete_calls)

    def test_filter_existing_flavors_none(self):
        client = mock.MagicMock()
        client.flavors.list.return_value = []
        flavor_list = [{'name': 'baremetal'}]
        self.assertEqual(flavor_list,
                         flavors.filter_existing_flavors(client, flavor_list))

    def test_filter_existing_flavors_one_existing(self):
        client = mock.MagicMock()
        flavor = collections.namedtuple('flavor', ['name'])
        client.flavors.list.return_value = [flavor('baremetal_1')]
        flavor_list = [{'name': 'baremetal_0'}, {'name': 'baremetal_1'}]
        self.assertEqual([flavor_list[0]],
                         flavors.filter_existing_flavors(client, flavor_list))

    def test_filter_existing_flavors_all_existing(self):
        client = mock.MagicMock()
        flavor = collections.namedtuple('flavor', ['name'])
        client.flavors.list.return_value = [flavor('baremetal_0'),
                                            flavor('baremetal_1')]
        flavor_list = [{'name': 'baremetal_0'}, {'name': 'baremetal_1'}]
        self.assertEqual([],
                         flavors.filter_existing_flavors(client, flavor_list))

    @mock.patch('os_cloud_config.flavors._create_flavor')
    def test_create_flavors_from_nodes(self, create_flavor):
        node = {'cpu': '1', 'memory': '2048', 'disk': '30', 'arch': 'i386'}
        node_list = [node, node]
        client = mock.MagicMock()
        flavors.create_flavors_from_nodes(client, node_list, 'aaa', 'bbb',
                                          '10')
        expected_flavor = node
        expected_flavor.update({'disk': '10', 'ephemeral': '20',
                                'kernel': 'aaa', 'ramdisk': 'bbb',
                                'name': 'baremetal_2048_10_20_1'})
        create_flavor.assert_called_once_with(client, expected_flavor)

    @mock.patch('os_cloud_config.flavors._create_flavor')
    def test_create_flavors_from_list(self, create_flavor):
        flavor_list = [{'name': 'controller', 'cpu': '1', 'memory': '2048',
                        'disk': '30', 'arch': 'amd64'}]
        client = mock.MagicMock()
        flavors.create_flavors_from_list(client, flavor_list, 'aaa', 'bbb')
        create_flavor.assert_called_once_with(
            client, {'disk': '30', 'cpu': '1', 'arch': 'amd64',
                     'kernel': 'aaa', 'ramdisk': 'bbb', 'memory': '2048',
                     'name': 'controller'})

    def test_create_flavor(self):
        flavor = {'cpu': '1', 'memory': '2048', 'disk': '30', 'arch': 'i386',
                  'kernel': 'aaa', 'ramdisk': 'bbb', 'name': 'baremetal',
                  'ephemeral': None}
        client = mock.MagicMock()
        flavors._create_flavor(client, flavor)
        client.flavors.create.assert_called_once_with(
            'baremetal', '2048', '1', '30', None, ephemeral=None)
        metadata = {'cpu_arch': 'i386', 'baremetal:deploy_kernel_id': 'aaa',
                    'baremetal:deploy_ramdisk_id': 'bbb'}
        client.flavors.create.return_value.set_keys.assert_called_once_with(
            metadata=metadata)

    def test_create_flavor_with_extra_spec(self):
        flavor = {'cpu': '1', 'memory': '2048', 'disk': '30', 'arch': 'i386',
                  'kernel': 'aaa', 'ramdisk': 'bbb', 'name': 'baremetal',
                  'ephemeral': None, 'extra_specs': {'key': 'value'}}
        client = mock.MagicMock()
        flavors._create_flavor(client, flavor)
        client.flavors.create.assert_called_once_with(
            'baremetal', '2048', '1', '30', None, ephemeral=None)
        metadata = {'cpu_arch': 'i386', 'baremetal:deploy_kernel_id': 'aaa',
                    'baremetal:deploy_ramdisk_id': 'bbb', 'key': 'value'}
        client.flavors.create.return_value.set_keys.assert_called_once_with(
            metadata=metadata)

    @mock.patch('os_cloud_config.flavors._create_flavor')
    def test_create_flavor_from_ironic(self, create_flavor):
        node = mock.MagicMock()
        node.uuid = 'uuid'
        node.properties = {'cpus': '1', 'memory_mb': '2048', 'local_gb': '30',
                           'cpu_arch': 'i386'}
        client = mock.MagicMock()
        ironic_client = mock.MagicMock()
        ironic_client.node.list.return_value = [node]
        flavors.create_flavors_from_ironic(client, ironic_client, 'aaa', 'bbb',
                                           '10')
        self.assertTrue(ironic_client.node.list.called)

        expected_flavor = {'disk': '10', 'ephemeral': '20',
                           'kernel': 'aaa', 'ramdisk': 'bbb',
                           'name': 'baremetal_2048_10_20_1',
                           'memory': '2048', 'arch': 'i386',
                           'cpu': '1'}
        create_flavor.assert_called_once_with(client, expected_flavor)

    def test_check_node_properties(self):
        node = mock.MagicMock()
        properties = {'memory_mb': '1024',
                      'local_gb': '10',
                      'cpus': '1',
                      'cpu_arch': 'i386'}
        node.properties = properties

        self.assertTrue(flavors.check_node_properties(node))

        properties['memory_mb'] = None
        self.assertFalse(flavors.check_node_properties(node))

        del properties['memory_mb']
        self.assertFalse(flavors.check_node_properties(node))
