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

import logging
from os import path

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
        crypto.X509Extension("basicConstraints", True, "CA:TRUE, pathlen:0"),
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
    ca_key_pem, ca_cert_pem = create_ca_pair()
    signing_key_pem, signing_cert_pem = create_signing_pair(ca_key_pem,
                                                            ca_cert_pem)

    ca_key_path = path.join(directory, 'ca_key.pem')
    with open(ca_key_path, 'w') as f:
        f.write(ca_key_pem)
    LOG.debug("Wrote '%s'.", path.abspath(ca_key_path))

    ca_cert_path = path.join(directory, 'ca_cert.pem')
    with open(ca_cert_path, 'w') as f:
        f.write(ca_cert_pem)
    LOG.debug("Wrote '%s'.", path.abspath(ca_cert_path))

    signing_key_path = path.join(directory, 'signing_key.pem')
    with open(signing_key_path, 'w') as f:
        f.write(signing_key_pem)
    LOG.debug("Wrote '%s'.", path.abspath(signing_key_path))

    signing_cert_path = path.join(directory, 'signing_cert.pem')
    with open(signing_cert_path, 'w') as f:
        f.write(signing_cert_pem)
    LOG.debug("Wrote '%s'.", path.abspath(signing_cert_path))
