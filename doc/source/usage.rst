========
Usage
========

To use os-cloud-config in a project::

	import os_cloud_config

Initializing Keystone for a host::

The init-keystone command line utility initializes Keystone for use with
normal authentication by creating the admin and service tenants, the admin
and Member roles, the admin user, and finally registers the initial identity
endpoint.

For example::

    init-keystone -o 192.0.2.1 -t unset -e admin@example.com -p unset

That acts on the 192.0.2.1 host, sets the admin token and the admin password
to the string "unset", and the admin e-mail address to "admin@example.com".
