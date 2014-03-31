========
Usage
========

To use os-cloud-config in a project::

	import os_cloud_config

Registering nodes with a baremetal service::

The register-nodes command line utility supports registering nodes with
either Ironic or Nova-baremetal. Ironic will be used if the Ironic service
is registered with Keystone.

 .. note::

    register-nodes will ask Ironic to power off every machine as they are
    registered.

The nodes argument to register-nodes is a JSON file describing the nodes to
be registered in a list of objects.

For example::

    register-nodes -s seed -n /tmp/one-node

Where /tmp/one-node contains::

[
  {
    "memory": "2048",
    "disk": "30",
    "arch": "i386",
    "pm_user": "steven",
    "pm_addr": "192.168.122.1",
    "pm_password": "password",
    "pm_type": "pxe_ssh",
    "mac": [
      "00:76:31:1f:f2:a0"
    ],
    "cpu": "1"
  }
]
