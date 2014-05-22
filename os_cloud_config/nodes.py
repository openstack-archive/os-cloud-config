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

import os
import subprocess
import time

from ironicclient import client as ironicclient
from ironicclient.openstack.common.apiclient import exceptions as ironicexp
from novaclient.extension import Extension
from novaclient.openstack.common.apiclient import exceptions as novaexc
from novaclient.v1_1 import client as novav11client
from novaclient.v1_1.contrib import baremetal


def _check_output(command):
    # subprocess.check_output only exists in Python 2.7+.
    if hasattr(subprocess, 'check_output'):
        return subprocess.check_output(command)
    else:
        process = subprocess.Popen(command, stdout=subprocess.PIPE)
        output, err = process.communicate()
        return_code = process.poll()
        if return_code:
            raise subprocess.CalledProcessError
        return output


def register_nova_bm_node(service_host, node, client=None):
    if not service_host:
        raise ValueError("Nova-baremetal requires a service host.")
    for count in range(60):
        try:
            bm_node = client.baremetal.create(service_host, node["cpu"],
                                              node["memory"], node["disk"],
                                              node["mac"][0],
                                              pm_address=node["pm_addr"],
                                              pm_user=node["pm_user"],
                                              pm_password=node["pm_password"])
            break
        except (novaexc.ConnectionRefused, novaexc.ServiceUnavailable):
            time.sleep(10)
    for mac in node["mac"][1:]:
        client.baremetal.add_interface(bm_node, mac)


def register_ironic_node(service_host, node, client=None):
    properties = {"cpus": node["cpu"],
                  "memory_mb": node["memory"],
                  "local_gb": node["disk"],
                  "cpu_arch": node["arch"]}
    if "ipmi" in node["pm_type"]:
        driver_info = {"ipmi_address": node["pm_addr"],
                       "ipmi_username": node["pm_user"],
                       "ipmi_password": node["pm_password"]}
    elif node["pm_type"] == "pxe_ssh":
        ssh_key_filename = "/mnt/state/var/lib/ironic/virtual-power-key"
        driver_info = {"ssh_address": node["pm_addr"],
                       "ssh_username": node["pm_user"],
                       "ssh_key_filename": ssh_key_filename,
                       "ssh_virt_type": "virsh"}
    else:
        raise Exception("Unknown pm_type: %s" % node["pm_type"])

    for count in range(60):
        try:
            ironic_node = client.node.create(driver=node["pm_type"],
                                             driver_info=driver_info,
                                             properties=properties)
            break
        except (ironicexp.ConnectionRefused, ironicexp.ServiceUnavailable):
            time.sleep(10)

    for mac in node["mac"]:
        client.port.create(address=mac, node_uuid=ironic_node.uuid)
    # Ironic should do this directly, see bug 1315225.
    client.node.set_power_state(ironic_node.uuid, 'off')


def _get_nova_bm_client():
    baremetal_extension = Extension('baremetal', baremetal)
    return novav11client.Client(os.environ["OS_USERNAME"],
                                os.environ["OS_PASSWORD"],
                                os.environ["OS_TENANT_NAME"],
                                os.environ["OS_AUTH_URL"],
                                extensions=[baremetal_extension])


def _get_ironic_client():
    kwargs = {'os_username': os.environ['OS_USERNAME'],
              'os_password': os.environ['OS_PASSWORD'],
              'os_auth_url': os.environ['OS_AUTH_URL'],
              'os_tenant_name': os.environ['OS_TENANT_NAME']}
    return ironicclient.get_client(1, **kwargs)


def register_all_nodes(service_host, nodes_list, client=None):
    if using_ironic():
        if client is None:
            client = _get_ironic_client()
        register_func = register_ironic_node
    else:
        if client is None:
            client = _get_nova_bm_client()
        register_func = register_nova_bm_node
    for node in nodes_list:
        register_func(service_host, node, client=client)


def using_ironic():
    out = subprocess.check_output(["keystone", "service-list"])
    return 'ironic' in out
