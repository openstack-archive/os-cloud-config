===============================
os-cloud-config
===============================

Configuration for OpenStack clouds.

When first installing an OpenStack cloud there are a number of common
up-front configuration tasks that need to be performed. To alleviate
the need for different sets of tooling to reinvent solutions to these
problems, this package provides a set of tools.

These tools are intended to be well-tested, and available as
importable Python modules as well as command-line tools.

* Free software: Apache license
* Documentation: http://docs.openstack.org/developer/os-cloud-config

Features
--------

* generate-keystone-pki:

  * Generate a certificate authority and a signing key for use with Keystone
    Public Key Infrastructure token signing.

* init-keystone:

  * Initialize Keystone on a host with a provided admin token, admin e-mail
    and admin password. Also allows optionally changing the region and the
    public endpoint that Keystone registers with itself.

* register-nodes:

  * Register nodes with a baremetal service, such as Nova-baremetal or Ironic.

* setup-endpoints:

  * Register services, such as Glance and Cinder with a configured Keystone.

* setup-flavors:

  * Creates flavors in Nova, either describing the distinct set of nodes the
    cloud has registered, or a custom set of flavors that has been specified.

* setup-neutron:

  * Configure Neutron at the cloud (not the host) level, setting up either a
    physical control plane network suitable for deployment clouds, or an
    external network with an internal floating network suitable for workload
    clouds.
