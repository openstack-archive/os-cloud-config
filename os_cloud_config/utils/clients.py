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

import logging

import glanceclient
from ironicclient import client as ironicclient
from keystoneclient.auth.identity import v2
from keystoneclient import session
from keystoneclient.v2_0 import client as ksclient
from keystoneclient.v3 import client as ks3client
from neutronclient.neutron import client as neutronclient
from novaclient.extension import Extension
from novaclient.v1_1 import client as novav11client
from novaclient.v1_1.contrib import baremetal

LOG = logging.getLogger(__name__)


def get_nova_bm_client(username, password, tenant_name, auth_url):
    LOG.debug('Creating nova client.')
    baremetal_extension = Extension('baremetal', baremetal)
    return novav11client.Client(username,
                                password,
                                tenant_name,
                                auth_url,
                                extensions=[baremetal_extension])


def get_ironic_client(username, password, tenant_name, auth_url):
    LOG.debug('Creating ironic client.')
    kwargs = {'os_username': username,
              'os_password': password,
              'os_auth_url': auth_url,
              'os_tenant_name': tenant_name}
    return ironicclient.get_client(1, **kwargs)


def get_keystone_client(username, password, tenant_name, auth_url):
    LOG.debug('Creating keystone client.')
    kwargs = {'username': username,
              'password': password,
              'tenant_name': tenant_name,
              'auth_url': auth_url}
    return ksclient.Client(**kwargs)


def get_keystone_v3_client(username, password, tenant_name, auth_url):
    LOG.debug('Creating keystone v3 client.')
    kwargs = {'username': username,
              'password': password,
              'tenant_name': tenant_name,
              'auth_url': auth_url.replace('v2.0', 'v3')}
    return ks3client.Client(**kwargs)


def get_neutron_client(username, password, tenant_name, auth_url):
    LOG.debug('Creating neutron client.')
    kwargs = {'username': username,
              'password': password,
              'tenant_name': tenant_name,
              'auth_url': auth_url}
    neutron = neutronclient.Client('2.0', **kwargs)
    neutron.format = 'json'
    return neutron


def get_glance_client(username, password, tenant_name, auth_url,
                      region_name='regionOne'):
    LOG.debug('Creating Keystone session to fetch Glance endpoint.')
    auth = v2.Password(auth_url=auth_url, username=username, password=password,
                       tenant_name=tenant_name)
    ks_session = session.Session(auth=auth)
    endpoint = ks_session.get_endpoint(service_type='image',
                                       interface='public',
                                       region_name=region_name)
    token = ks_session.get_token()
    LOG.debug('Creating glance client.')
    return glanceclient.Client('1', endpoint=endpoint, token=token)
