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

import json
import logging
import os
from os import path
import stat

from OpenSSL import crypto

LOG = logging.getLogger(__name__)

CA_KEY_SIZE = 2048
CA_CERT_DAYS = 10 * 365
SIGNING_KEY_SIZE = 2048
SIGNING_CERT_DAYS = 10 * 365
X509_VERSION = 2


def create_ca_pair(cert_serial=1):
    """Create CA private key and self-signed certificate.

    CA generation is mostly meant for proof-of-concept
    deployments. For real deployments it is suggested to use an
    external CA (separate from deployment tools).

    :param cert_serial: serial number of the generated certificate
    :type  cert_serial: integer
    :return: (ca_key_pem, ca_cert_pem) tuple of base64 encoded CA
             private key and CA certificate (PEM format)
    :rtype:  (string, string)
    """
    ca_key = crypto.PKey()
    ca_key.generate_key(crypto.TYPE_RSA, CA_KEY_SIZE)
    LOG.debug('Generated CA key.')

    ca_cert = crypto.X509()
    ca_cert.set_version(X509_VERSION)
    ca_cert.set_serial_number(cert_serial)
    subject = ca_cert.get_subject()
    subject.C = 'XX'
    subject.ST = 'Unset'
    subject.L = 'Unset'
    subject.O = 'Unset'
    subject.CN = 'Keystone CA'
    ca_cert.gmtime_adj_notBefore(0)
    ca_cert.gmtime_adj_notAfter(60 * 60 * 24 * CA_CERT_DAYS)
    ca_cert.set_issuer(subject)
    ca_cert.set_pubkey(ca_key)
    ca_cert.add_extensions([
        crypto.X509Extension(b"basicConstraints", True, b"CA:TRUE, pathlen:0"),
    ])
    ca_cert.sign(ca_key, 'sha1')
    LOG.debug('Generated CA certificate.')

    return (crypto.dump_privatekey(crypto.FILETYPE_PEM, ca_key),
            crypto.dump_certificate(crypto.FILETYPE_PEM, ca_cert))


def create_signing_pair(ca_key_pem, ca_cert_pem, cert_serial=2):
    """Create signing private key and certificate.

    Os-cloud-config key generation and certificate signing is mostly
    meant for proof-of-concept deployments. For real deployments it is
    suggested to use certificates signed by an external CA.

    :param ca_key_pem: CA private key to sign the signing certificate,
                       base64 encoded (PEM format)
    :type  ca_key_pem: string
    :param ca_cert_pem: CA certificate, base64 encoded (PEM format)
    :type  ca_cert_pem: string
    :param cert_serial: serial number of the generated certificate
    :type  cert_serial: integer
    :return: (signing_key_pem, signing_cert_pem) tuple of base64
             encoded signing private key and signing certificate
             (PEM format)
    :rtype:  (string, string)
    """
    ca_key = crypto.load_privatekey(crypto.FILETYPE_PEM, ca_key_pem)
    ca_cert = crypto.load_certificate(crypto.FILETYPE_PEM, ca_cert_pem)

    signing_key = crypto.PKey()
    signing_key.generate_key(crypto.TYPE_RSA, CA_KEY_SIZE)
    LOG.debug('Generated signing key.')

    signing_cert = crypto.X509()
    signing_cert.set_version(X509_VERSION)
    signing_cert.set_serial_number(cert_serial)
    subject = signing_cert.get_subject()
    subject.C = 'XX'
    subject.ST = 'Unset'
    subject.L = 'Unset'
    subject.O = 'Unset'
    subject.CN = 'Keystone Signing'
    signing_cert.gmtime_adj_notBefore(0)
    signing_cert.gmtime_adj_notAfter(60 * 60 * 24 * SIGNING_CERT_DAYS)
    signing_cert.set_issuer(ca_cert.get_subject())
    signing_cert.set_pubkey(signing_key)
    signing_cert.sign(ca_key, 'sha1')
    LOG.debug('Generated signing certificate.')

    return (crypto.dump_privatekey(crypto.FILETYPE_PEM, signing_key),
            crypto.dump_certificate(crypto.FILETYPE_PEM, signing_cert))


def create_and_write_ca_and_signing_pairs(directory):
    """Create and write out CA and signing keys and certificates.

    Generate ca_key.pem, ca_cert.pem, signing_key.pem,
    signing_cert.pem and write them out to a directory.

    :param directory: directory where keys and certs will be written
    :type  directory: string
    """
    if not path.isdir(directory):
        os.mkdir(directory)

    ca_key_pem, ca_cert_pem = create_ca_pair()
    signing_key_pem, signing_cert_pem = create_signing_pair(ca_key_pem,
                                                            ca_cert_pem)

    _write_pki_file(path.join(directory, 'ca_key.pem'), ca_key_pem)
    _write_pki_file(path.join(directory, 'ca_cert.pem'), ca_cert_pem)
    _write_pki_file(path.join(directory, 'signing_key.pem'), signing_key_pem)
    _write_pki_file(path.join(directory, 'signing_cert.pem'), signing_cert_pem)


def generate_certs_into_json(jsonfile, seed):
    """Create and write out CA certificate and signing certificate/key.

    Generate CA certificate, signing certificate and signing key and
    add them into a JSON file. If key/certs already exist in JSON file, no
    change is done.

    :param jsonfile: JSON file where certs and key will be written
    :type  jsonfile: string
    :param seed: JSON file for seed machine has different structure. Different
                 key/certs names and different parent node are used
    :type  seed: boolean
    """
    if os.path.isfile(jsonfile):
        with open(jsonfile) as json_fd:
            all_data = json.load(json_fd)
    else:
        all_data = {}

    if seed:
        parent = 'keystone'
        ca_cert_name = 'ca_certificate'
        signing_key_name = 'signing_key'
        signing_cert_name = 'signing_certificate'
    else:
        parent = 'parameter_defaults'
        ca_cert_name = 'KeystoneCACertificate'
        signing_key_name = 'KeystoneSigningKey'
        signing_cert_name = 'KeystoneSigningCertificate'

    if parent not in all_data:
        all_data[parent] = {}
    parent_node = all_data[parent]

    if not (ca_cert_name in parent_node and
            signing_key_name in parent_node and
            signing_cert_name in parent_node):
        ca_key_pem, ca_cert_pem = create_ca_pair()
        signing_key_pem, signing_cert_pem = create_signing_pair(ca_key_pem,
                                                                ca_cert_pem)
        parent_node.update({ca_cert_name: ca_cert_pem,
                            signing_key_name: signing_key_pem,
                            signing_cert_name: signing_cert_pem})
        with open(jsonfile, 'w') as json_fd:
            json.dump(all_data, json_fd, sort_keys=True)
            LOG.debug("Wrote key/certs into '%s'.", path.abspath(jsonfile))
    else:
        LOG.info("Key/certs are already present in '%s', skipping.",
                 path.abspath(jsonfile))


def _write_pki_file(file_path, contents):
    with open(file_path, 'w') as f:
        f.write(contents)
    os.chmod(file_path, stat.S_IRUSR | stat.S_IWUSR)
    LOG.debug("Wrote '%s'.", path.abspath(file_path))
