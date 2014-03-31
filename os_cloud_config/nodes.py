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

import subprocess


def _get_id_line(lines, id_description, position=3):
    for line in lines.split('\n'):
        if id_description in line:
            return line.split()[position]


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


def register_nova_bm_node(service_host, node):
    if not service_host:
        raise ValueError("Nova-baremetal requires a service host.")
    out = _check_output(["nova", "baremetal-node-create",
                         "--pm_address=%s" % node["pm_addr"],
                         "--pm_user=%s" % node["pm_user"],
                         "--pm_password=%s" % node["pm_password"],
                         service_host, node["cpu"], node["memory"],
                         node["disk"], node["mac"][0]])
    bm_id = _get_id_line(out, " id ")
    for mac in node["mac"][1:]:
        subprocess.check_call(["nova", "baremetal-interface-add", bm_id, mac])


def register_ironic_node(service_host, node):
    out = _check_output(["ironic", "node-create", "-d", node["pm_type"]])
    node_id = _get_id_line(out, "uuid")
    node_properties = ["properties/cpus=%s" % node["cpu"],
                       "properties/memory_mb=%s" % node["memory"],
                       "properties/local_gb=%s" % node["disk"],
                       "properties/cpu_arch=%s" % node["arch"]]
    if "ipmi" in node["pm_type"]:
        pm_password = node["pm_password"]
        ipmi_properties = ["driver_info/ipmi_address=%s" % node["pm_addr"],
                           "driver_info/ipmi_username=%s" % node["pm_user"],
                           "driver_info/ipmi_password=%s" % pm_password]
        node_properties.extend(ipmi_properties)
    elif node["pm_type"] == "pxe_ssh":
        ssh = ("driver_info/ssh_key_filename=/mnt/state/var/lib/ironic/"
               "virtual-power-key")
        ssh_properties = ["driver_info/ssh_address=%s" % node["pm_addr"],
                          "driver_info/ssh_username=%s" % node["pm_user"],
                          ssh, "driver_info/ssh_virt_type=virsh"]
        node_properties.extend(ssh_properties)
    else:
        raise Exception("Unknown pm_type: %s" % node["pm_type"])

    subprocess.check_call(["ironic", "node-update", node_id, "add"]
                          + node_properties)
    # Ironic should do this directly, see bug 1315225.
    subprocess.check_call(["ironic", "node-set-power-state", node_id, "off"])
    for mac in node["mac"]:
        subprocess.check_call(["ironic", "port-create", "-a", mac, "-n",
                              node_id])


def register_all_nodes(service_host, nodes_list):
    if using_ironic():
        register_func = register_ironic_node
    else:
        register_func = register_nova_bm_node
    for node in nodes_list:
        register_func(service_host, node)


# TODO(StevenK): Perhaps this should spin over the first node until it is
# registered successfully for a minute or so, replacing this function.
def check_nova_bm_service():
    subprocess.check_call(["wait_for", "60", "10", "nova",
                          "baremetal-node-create", "devtest_canary", "1", "1",
                          "1", "11:22:33:44:55:66"])
    out = subprocess.check_output(["nova", "baremetal-node-list"])
    node_id = _get_id_line(out, "devtest_canary", position=1)
    subprocess.check_call(["nova", "baremetal-node-delete", node_id])


# TODO(StevenK): Perhaps this should spin over the first node until it is
# registered successfully for a minute or so, replacing this function.
def check_ironic_service():
    subprocess.check_call(["wait_for", "60", "10", "ironic", "chassis-create",
                          "-d", "devtest_canary"])
    out = subprocess.check_output(["ironic", "chassis-list"])
    chassis_id = _get_id_line(out, "devtest_canary", position=1)
    subprocess.check_call(["ironic", "chassis-delete", chassis_id])


def check_service():
    if using_ironic():
        check_ironic_service()
    else:
        check_nova_bm_service()


def using_ironic():
    out = subprocess.check_output(["keystone", "service-list"])
    return 'ironic' in out
