===============================
os-cloud-config
===============================

Configuration for OpenStack clouds.

os-cloud-config grew out of the need to call common cloud bring-up tasks, such
as initializing Keystone, or configuring Neutron from different code bases.
The original code was written in shell, and poorly tested, which led to the
need to rewriting it in Python and provided by a distinct module.

* Free software: Apache license
* Documentation: http://docs.openstack.org/developer/os-cloud-config

Features
--------

* generate-keystone-pki:
  - Generate a certificate authority and a signing key for use with Keystone
    Public Key Infrastructure token signing.
* init-keystone:
  - Initialize Keystone on a host with a provided admin token, admin e-mail
    and admin password. Also allows optionally changing the region and the
    public endpoint that Keystone registers with itself.
* register-nodes:
  - Register nodes with a baremetal service, such as Nova-baremetal or Ironic.
* setup-endpoints:
  - Register services, such as Glance and Cinder with a configured Keystone.
* setup-flavors:
  - Creates flavors in Nova, either describing the distinct set of nodes the
    cloud has registered, or a custom set of flavors that has been specified.
* setup-neutron:
  - Configure Neutron at the cloud (not the host) level, setting up either a
    physical control plane network suitable for deployment clouds, or an
    external network with an internal floating network suitable for workload
    clouds.
