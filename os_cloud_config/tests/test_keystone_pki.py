# -*- coding: utf-8 -*-

# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import stat

import mock
from OpenSSL import crypto

from os_cloud_config import keystone_pki
from os_cloud_config.tests import base


class KeystonePKITest(base.TestCase):

    def test_create_ca_and_signing_pairs(self):
        # use one common test to avoid generating CA pair twice
        # do not mock out pyOpenSSL, test generated keys/certs

        # create CA pair
        ca_key_pem, ca_cert_pem = keystone_pki.create_ca_pair()
        ca_key = crypto.load_privatekey(crypto.FILETYPE_PEM, ca_key_pem)
        ca_cert = crypto.load_certificate(crypto.FILETYPE_PEM, ca_cert_pem)

        # check CA key properties
        self.assertTrue(ca_key.check())
        self.assertEqual(2048, ca_key.bits())

        # check CA cert properties
        self.assertFalse(ca_cert.has_expired())
        self.assertEqual('Keystone CA', ca_cert.get_issuer().CN)
        self.assertEqual('Keystone CA', ca_cert.get_subject().CN)

        # create signing pair
        signing_key_pem, signing_cert_pem = keystone_pki.create_signing_pair(
            ca_key_pem, ca_cert_pem)
        signing_key = crypto.load_privatekey(crypto.FILETYPE_PEM,
                                             signing_key_pem)
        signing_cert = crypto.load_certificate(crypto.FILETYPE_PEM,
                                               signing_cert_pem)

        # check signing key properties
        self.assertTrue(signing_key.check())
        self.assertEqual(2048, signing_key.bits())

        # check signing cert properties
        self.assertFalse(signing_cert.has_expired())
        self.assertEqual('Keystone CA', signing_cert.get_issuer().CN)
        self.assertEqual('Keystone Signing', signing_cert.get_subject().CN)
        # pyOpenSSL currenty cannot verify a cert against a CA cert

    @mock.patch('os_cloud_config.keystone_pki.os.chmod', create=True)
    @mock.patch('os_cloud_config.keystone_pki.os.mkdir', create=True)
    @mock.patch('os_cloud_config.keystone_pki.path.isdir', create=True)
    @mock.patch('os_cloud_config.keystone_pki.create_ca_pair')
    @mock.patch('os_cloud_config.keystone_pki.create_signing_pair')
    @mock.patch('os_cloud_config.keystone_pki.open', create=True)
    def test_create_and_write_ca_and_signing_pairs(
            self, open_, create_signing, create_ca, isdir, mkdir, chmod):
        create_ca.return_value = ('mock_ca_key', 'mock_ca_cert')
        create_signing.return_value = ('mock_signing_key', 'mock_signing_cert')
        isdir.return_value = False
        keystone_pki.create_and_write_ca_and_signing_pairs('/fake_dir')

        mkdir.assert_called_with('/fake_dir')
        chmod.assert_has_calls([
            mock.call('/fake_dir/ca_key.pem',
                      stat.S_IRUSR | stat.S_IWUSR),
            mock.call('/fake_dir/ca_cert.pem',
                      stat.S_IRUSR | stat.S_IWUSR),
            mock.call('/fake_dir/signing_key.pem',
                      stat.S_IRUSR | stat.S_IWUSR),
            mock.call('/fake_dir/signing_cert.pem',
                      stat.S_IRUSR | stat.S_IWUSR),
        ])
        # need any_order param, there are open().__enter__()
        # etc. called in between
        open_.assert_has_calls([
            mock.call('/fake_dir/ca_key.pem', 'w'),
            mock.call('/fake_dir/ca_cert.pem', 'w'),
            mock.call('/fake_dir/signing_key.pem', 'w'),
            mock.call('/fake_dir/signing_cert.pem', 'w'),
        ], any_order=True)
        cert_files = open_.return_value.__enter__.return_value
        cert_files.write.assert_has_calls([
            mock.call('mock_ca_key'),
            mock.call('mock_ca_cert'),
            mock.call('mock_signing_key'),
            mock.call('mock_signing_cert'),
        ])

    @mock.patch('os_cloud_config.keystone_pki.path.isfile', create=True)
    @mock.patch('os_cloud_config.keystone_pki.create_ca_pair')
    @mock.patch('os_cloud_config.keystone_pki.create_signing_pair')
    @mock.patch('os_cloud_config.keystone_pki.open', create=True)
    @mock.patch('os_cloud_config.keystone_pki.json.dump')
    def test_generate_certs_into_json(
        self, mock_json, open_, create_signing, create_ca, isfile):
        create_ca.return_value = ('mock_ca_key', 'mock_ca_cert')
        create_signing.return_value = ('mock_signing_key', 'mock_signing_cert')
        isfile.return_value = False

        keystone_pki.generate_certs_into_json('/jsonfile', False)

        params = mock_json.call_args[0][0]['parameter_defaults']
        self.assertEqual(params['KeystoneCACertificate'], 'mock_ca_cert')
        self.assertEqual(params['KeystoneSigningKey'], 'mock_signing_key')
        self.assertEqual(params['KeystoneSigningCertificate'],
                         'mock_signing_cert')

    @mock.patch('os_cloud_config.keystone_pki.path.isfile', create=True)
    @mock.patch('os_cloud_config.keystone_pki.create_ca_pair')
    @mock.patch('os_cloud_config.keystone_pki.create_signing_pair')
    @mock.patch('os_cloud_config.keystone_pki.open', create=True)
    @mock.patch('os_cloud_config.keystone_pki.json.load')
    @mock.patch('os_cloud_config.keystone_pki.json.dump')
    def test_generate_certs_into_json_with_existing_certs(
        self, mock_json_dump, mock_json_load, open_, create_signing,
        create_ca, isfile):
        create_ca.return_value = ('mock_ca_key', 'mock_ca_cert')
        create_signing.return_value = ('mock_signing_key', 'mock_signing_cert')
        isfile.return_value = True
        mock_json_load.return_value = {
            'parameter_defaults': {
                'KeystoneCACertificate': 'mock_ca_cert',
                'KeystoneSigningKey': 'mock_signing_key',
                'KeystoneSigningCertificate': 'mock_signing_cert'
            }
        }

        keystone_pki.generate_certs_into_json('/jsonfile', False)
        mock_json_dump.assert_not_called()
