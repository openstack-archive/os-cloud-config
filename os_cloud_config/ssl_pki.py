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
import os
from os import path
import simplejson
import stat

from OpenSSL import crypto

LOG = logging.getLogger(__name__)

CA_KEY_SIZE = 2048
CA_CERT_DAYS = 10 * 365
SIGNING_KEY_SIZE = 2048
SIGNING_CERT_DAYS = 10 * 365
X509_VERSION = 2


def create_ca_pair(cert_serial=1,
                   subject_C='XX',
                   subject_ST='Unset',
                   subject_L='Unset',
                   subject_O='Unset',
                   subject_CN='os-cloud-config CA'):
    """Create CA private key and self-signed certificate.

    CA generation is mostly meant for proof-of-concept
    deployments. For real deployments it is suggested to use an
    external CA (separate from deployment tools).

    :param cert_serial: serial number of the generated certificate
    :type  cert_serial: integer
    :param subject_C: Country code
    :type subject_C: string
    :param subject_ST: State/Province code
    :type subject_ST: string
    :param subject_L: Locality name
    :type subject_L: string
    :param subject_O: Organization name
    :type subject_O: string
    :param subject_CN: Common name
    :type subject_CN: string
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
    subject.C = subject_C
    subject.ST = subject_ST
    subject.L = subject_L
    subject.O = subject_O
    subject.CN = subject_CN
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


def create_certificate_pair(ca_key_pem,
                            ca_cert_pem,
                            cert_serial=2,
                            subject_C='XX',
                            subject_ST='Unset',
                            subject_L='Unset',
                            subject_O='Unset',
                            subject_CN='os-cloud-config Signing'):
    """Create ssl key and certificate.

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
    :param subject_C: Country code
    :type subject_C: string
    :param subject_ST: State/Province code
    :type subject_ST: string
    :param subject_L: Locality name
    :type subject_L: string
    :param subject_O: Organization name
    :type subject_O: string
    :param subject_CN: Common name
    :type subject_CN: string
    :return: (key_pem, cert_pem) tuple of base64
             encoded ssl private key and certificate
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
    subject.C = subject_C
    subject.ST = subject_ST
    subject.L = subject_L
    subject.O = subject_O
    subject.CN = subject_CN
    signing_cert.gmtime_adj_notBefore(0)
    signing_cert.gmtime_adj_notAfter(60 * 60 * 24 * SIGNING_CERT_DAYS)
    signing_cert.set_issuer(ca_cert.get_subject())
    signing_cert.set_pubkey(signing_key)
    signing_cert.sign(ca_key, 'sha1')
    LOG.debug('Generated signing certificate.')

    return (crypto.dump_privatekey(crypto.FILETYPE_PEM, signing_key),
            crypto.dump_certificate(crypto.FILETYPE_PEM, signing_cert))


def create_and_write_certificate(directory, name, overwrite=False):
    """Create and write out an SSL certificate.

    Gernerate cert_<name>.pem and cert_<name>_key.pem and write them out to
    directory.

    :param directory: directory where the certificate and key will be written
    :type directory: string
    :param name: name for the certificate.
    :type name: string
    :param overwrite: overwrite certificate if it already exists
    :type overwrite: boolean
    """
    if not path.isdir(directory):
        os.mkdir(directory)

    if not overwrite:
        for dest in ('cert_%s.pem', 'cert_%s_key.pem'):
            if path.isfile(path.join(directory, dest % name)):
                return

    key_pem, cert_pem = create_certificate_pair(ca_key_pem, ca_cert_pem)

    _write_pki_file(path.join(directory, 'cert_%s_key.pem'), key_pem)
    _write_pki_file(path.join(directory, 'cert_%s.pem'), cert_pem)


def create_and_write_ca(directory, overwrite=False):
    """Create and write out CA certificat and private key.

    Generate ca_key.pem, ca_cert.pem, signing_key.pem,
    signing_cert.pem and write them out to a directory.

    :param directory: directory where keys and certs will be written
    :type  directory: string
    :param overwrite: overwrite certificate if it already exists
    :type overwrite: boolean
    """
    if not path.isdir(directory):
        os.mkdir(directory)

    if not overwrite:
        for dest in ('ca_key.pem', 'ca_cert.pem'):
            if path.isfile(path.join(directory, dest)):
                return

    ca_key_pem, ca_cert_pem = create_ca_pair()

    _write_pki_file(path.join(directory, 'ca_key.pem'), ca_key_pem)
    _write_pki_file(path.join(directory, 'ca_cert.pem'), ca_cert_pem)


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
            all_data = simplejson.load(json_fd)
    else:
        all_data = {}

    if seed:
        parent = 'keystone'
        ca_cert_name = 'ca_certificate'
        signing_key_name = 'signing_key'
        signing_cert_name = 'signing_certificate'
    else:
        parent = 'parameters'
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
            simplejson.dump(all_data, json_fd, sort_keys=True)
            LOG.debug("Wrote key/certs into '%s'.", path.abspath(jsonfile))
    else:
        LOG.info("Key/certs are already present in '%s', skipping.",
                 path.abspath(jsonfile))


def _write_pki_file(file_path, contents):
    with open(file_path, 'w') as f:
        f.write(contents)
    os.chmod(file_path, stat.S_IRUSR | stat.S_IWUSR)
    LOG.debug("Wrote '%s'.", path.abspath(file_path))
