========
Usage
========

To use os-cloud-config in a project::

	import os_cloud_config

-----------------------------------
Initializing Keystone for a host
-----------------------------------

The init-keystone command line utility initializes Keystone for use with
normal authentication by creating the admin and service tenants, the admin
and Member roles, the admin user, configure certificates and finally
registers the initial identity endpoint.

 .. note::

    init-keystone will wait up to 10 minutes for a Keystone service to be
    running on the specified host.

For example::

    init-keystone -o 192.0.2.1 -t unset -e admin@example.com -p unset -u root

That acts on the 192.0.2.1 host, sets the admin token and the admin password
to the string "unset", the admin e-mail address to "admin@example.com", and
uses the root user to connect to the host via ssh to configure certificates.

--------------------------------------------
Registering nodes with a baremetal service
--------------------------------------------

The register-nodes command line utility supports registering nodes with
either Ironic or Nova-baremetal. Ironic will be used if the Ironic service
is registered with Keystone.

 .. note::

    register-nodes will ask Ironic to power off every machine as they are
    registered.

 .. note::

    register-nodes will wait up to 10 minutes for the baremetal service to
    register a node.

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
