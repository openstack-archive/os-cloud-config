========
Usage
========

To use os-cloud-config in a project::

    import os_cloud_config

-----------------------------------
Initializing Keystone for a host
-----------------------------------

The ``init-keystone`` command line utility initializes Keystone for use with normal
authentication by creating the admin and service tenants, the admin role, the
admin user, configure certificates and finally registers the initial identity
endpoint.

 .. note::

    init-keystone will wait for a user-specified amount of time for a Keystone
    service to be running on the specified host.  The default is a 10 minute
    wait time with 10 seconds between poll attempts.

For example::

    init-keystone -o 192.0.2.1 -t unset -e admin@example.com -p unset -u root

That acts on the host ``192.0.2.1``, sets the admin token and the admin password
to the string ``unset``, the admin e-mail address to ``admin@example.com``, and
uses the root user to connect to the host via ssh to configure certificates.

--------------------------------------------
Registering nodes with a baremetal service
--------------------------------------------

The ``register-nodes`` command line utility supports registering nodes with
either Ironic or Nova-baremetal. Ironic will be used if the Ironic service
is registered with Keystone.

 .. note::

    register-nodes will ask Ironic to power off every machine as they are
    registered.

 .. note::

    register-nodes will wait up to 10 minutes for the baremetal service to
    register a node.

The nodes argument to register-nodes is a JSON file describing the nodes to
be registered in a list of objects. If the node is determined to be currently
registered, the details from the JSON file will be used to update the node
registration.

 .. note::

    Nova-baremetal does not support updating registered nodes, any previously
    registered nodes will be skipped.

For example::

    register-nodes -s seed -n /tmp/one-node

Where ``/tmp/one-node`` contains::

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

 .. note::

    The memory, disk, arch, and cpu fields are optional and can be omitted.

----------------------------------------------------------
Generating keys and certificates for use with Keystone PKI
----------------------------------------------------------

The ``generate-keystone-pki`` command line utility generates keys and certificates
which Keystone uses for signing authentication tokens.

- Keys and certificates can be generated into separate files::

    generate-keystone-pki /tmp/certificates

  That creates four files with signing and CA keys and certificates in
  ``/tmp/certificates`` directory.

- Key and certificates can be generated into heat environment file::

    generate-keystone-pki -j overcloud-env.json

  That adds following values into ``overcloud-env.json`` file::

    {
      "parameter_defaults": {
        "KeystoneSigningKey": "some_key",
        "KeystoneSigningCertificate": "some_cert",
        "KeystoneCACertificate": "some_cert"
      }
    }

  CA key is not added because this file is not needed by Keystone PKI.

- Key and certificates can be generated into os-apply-config metadata file::

    generate-keystone-pki -s -j local.json

  This adds following values into local.json file::

    {
      "keystone": {
        "signing_certificate": "some_cert",
        "signing_key": "some_key",
        "ca_certificate": "some_cert"
      }
    }

  CA key is not added because this file is not needed by Keystone PKI.

---------------------
Setting up networking
---------------------

The ``setup-neutron`` command line utility allows setting up of a physical control
plane network suitable for deployment clouds, or an external network with an
internal floating network suitable for workload clouds.

The network JSON argument allows specifying the network(s) to be created::

    setup-neutron -n /tmp/ctlplane

Where ``/tmp/ctlplane`` contains::

    {
      "physical": {
        "gateway": "192.0.2.1",
        "metadata_server": "192.0.2.1",
        "cidr": "192.0.2.0/24",
        "allocation_end": "192.0.2.20",
        "allocation_start": "192.0.2.2",
        "name": "ctlplane"
      }
    }

This will create a Neutron flat net with a name of ``ctlplane``, and a subnet
with a CIDR of ``192.0.2.0/24``, a metadata server and gateway of ``192.0.2.1``,
and will allocate DHCP leases in the range of ``192.0.2.2`` to ``192.0.2.20``, as
well as adding a route for ``169.254.169.254/32``.

setup-neutron also supports datacentre networks that require 802.1Q VLAN tags::

    setup-neutron -n /tmp/ctlplane-dc

Where ``/tmp/ctlplane-dc`` contains::

    {
      "physical": {
        "gateway": "192.0.2.1",
        "metadata_server": "192.0.2.1",
        "cidr": "192.0.2.0/24",
        "allocation_end": "192.0.2.20",
        "allocation_start": "192.0.2.2",
        "name": "public",
        "physical_network": "ctlplane",
        "segmentation_id": 25
      }
    }

This creates a Neutron 'net' called ``public`` using VLAN tag ``25``, that uses
an existing 'net' called ``ctlplane`` as a physical transport.


 .. note::

    The key ``physical_network`` is required when creating a network that
    specifies a ``segmentation_id``, and it must reference an existing net.

setup-neutron can also create two networks suitable for workload clouds::

    setup-neutron -n /tmp/float

Where ``/tmp/float`` contains::

    {
      "float": {
          "cidr": "10.0.0.0/8",
          "name": "default-net",
      },
      "external": {
          "name": "ext-net",
          "cidr": "192.0.2.0/24",
          "allocation_start": "192.0.2.45",
          "allocation_end": "192.0.2.64",
          "gateway": "192.0.2.1"
      }
    }

This creates two Neutron nets, the first with a name of ``default-net`` and
set as shared, and second with a name ``ext-net`` with the ``router:external``
property set to true. The ``default-net`` subnet has a CIDR of ``10.0.0.0/8`` and a
default nameserver of ``8.8.8.8``, and the ``ext-net`` subnet has a CIDR of
``192.0.2.0/24``, a gateway of ``192.0.2.1`` and allocates DHCP from
``192.0.2.45`` until ``192.0.2.64``. setup-neutron will also create a router
for the float network, setting the external network as the gateway.

----------------
Creating flavors
----------------

The ``setup-flavors`` command line utility creates flavors in Nova -- either using
the nodes that have been registered to provide a distinct set of hardware that
is provisioned, or by specifying the set of flavors that should be created.

 .. note::

    setup-flavors will delete the existing default flavors, such as m1.small
    and m1.xlarge. For this use case, the cloud that is having flavors created
    is a cloud only using baremetal hardware, so only needs to describe the
    hardware available.

Utilising the ``/tmp/one-node`` file specified in the ``register-nodes`` example
above, create a flavor::

    setup-flavors -n /tmp/one-node

Which results in a flavor called ``baremetal_2048_30_None_1``.

If the ``ROOT_DISK`` environment variable is set in the environment, that will be
used as the disk size, leaving the remainder set as ephemeral storage, giving
a flavor name of ``baremetal_2048_10_20_1``.

Conversely, you can specify a JSON file describing the flavors to create::

    setup-flavors -f /tmp/one-flavor

Where ``/tmp/one-flavor`` contains::

    [
      {
        "name": "controller",
        "memory": "2048",
        "disk": "30",
        "arch": "i386",
        "cpu": "1"
      }
    ]

The JSON file can also contain an ``extra_specs`` parameter, which is a JSON
object describing the key-value pairs to add into the flavor metadata::

    [
      {
        "name": "controller",
        "memory": "2048",
        "disk": "30",
        "arch": "i386",
        "cpu": "1",
        "extra_specs": {
          "key": "value"
        }
      }
    ]
