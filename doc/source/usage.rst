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

    init-keystone will wait for a user-specified amount of time for a Keystone 
    service to be running on the specified host.  The default is a 10 minute
    wait time with 10 seconds between poll attempts.

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

----------------------------------------------------------
Generating keys and certificates for use with Keystone PKI
----------------------------------------------------------

The generate-keystone-pki line utility generates keys and certificates
which Keystone uses for signing authentication tokens.

- Keys and certificates can be generated into separate files::

    generate-keystone-pki /tmp/certificates

  That creates four files with signing and CA keys and certificates in
  /tmp/certificates directory.

- Key and certificates can be generated into heat environment file::

    generate-keystone-pki -j overcloud-env.json

  That adds following values into overcloud-env.json file::

    {
      "parameters": {
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
