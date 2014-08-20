===============================
os-cloud-config
===============================

Configuration for OpenStack clouds.

os-cloud-config grew out of the need to call common cloud bring-up tasks, such
as initializing Keystone, or configuring Neutron from different code bases,
without calling shell scripts, hence rewriting the functionality to be in
Python, and provided by a distinct module.

* Free software: Apache license
* Documentation: http://docs.openstack.org/developer/os-cloud-config

Features
--------

* generate-keystone-pki:
  - Generate a certificate authority and a signing key for use with Keystone
    Public Key Infrastructure token signing.
* init-keystone:
  - Initialize Keystone on a host with a provided admin token, admin e-mail
    and admin password, optionally changing the region and the public endpoint
    registering Keystone with itself.
* register-nodes:
  - Register nodes with a baremetal service, such as Nova-baremetal or Ironic.
* setup-neutron:
  - Configure Neutron at the cloud (not the host) level, setting up either a
    physical control plane network suitable for deployment clouds, or an
    external network with an internal floating network suitable for workload
    clouds.
