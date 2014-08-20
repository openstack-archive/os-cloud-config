===============================
os-cloud-config
===============================

Configuration for OpenStack clouds.

os-cloud-config grew out of the need to call common cloud bring-up tasks, such
as initializing Keystone, or configuring Neutron from different code bases,
hence splitting it out into a disparate module.

* Free software: Apache license
* Documentation: http://docs.openstack.org/developer/os-cloud-config

Features
--------

* Initialize Keystone on a host with a provided admin token, admin e-mail and
  admin password, optionally changing the region and the public endpoint
  registering Keystone with itself.
* Register nodes with a baremetal service, such as Nova-baremetal or Ironic.
* Generate a certificate authority and a signing key for use with Keystone
  Public Key Infrastructure token signing.
