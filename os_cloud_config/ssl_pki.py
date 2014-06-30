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
    subject.CN = 'os-cloud-config CA'
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
    subject.CN = 'os-cloud-config Signing'
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


def generate_cert_into_json(jsonfile, name, auto_gen_ca=True,
                            overwrite=False):
    """Create and write out an SSL certificate.

    Create an ssl certificate, sign it with a CA, and output the certificate
    to <jsonfile> which is a heat JSON environment. If the parameters
    property exists in destination, then the following properties are added:
    {
        "parameters": {
            "<name>SSLCertificate": PEM_DATA,
            "<name>SSLCertificateKey": PEM_DATA
        }
    }

    The CA certificate and key lives in the parameters "CaSSLCertificate" and
    "CaSSLCertificateKey". If these parameters are not defined then a new CA
    is created and these properties are added.

    If no "parameters" property exists then the following properties are
    added:

    {
        "<name>": {
            "ssl" : {
                "certificate": PEM DATA,
                "certificate_key: PEM_DATA
            }
        }
    }

    The CA certificate and key in this case are:

    {
        "ssl": {
            "ca_certificate": PEM_DATA,
            "ca_certificate_key": PEM_DATA
        }
    }

    :param jsonfile: Destination to write certificate and possible CA to.
    :type jsonfile: string
    :param cert_serial: Serial for the certificate. If None then this is
                        automatically determined.
    :type cert_serial: integer
    :param name: name for the certificate.
    :type name: string
    :param overwrite: overwrite certificate if it already exists
    :type overwrite: boolean
    """
    if os.path.isfile(jsonfile):
        with open(jsonfile) as json_fd:
            all_data = json.load(json_fd)
    else:
        all_data = {}

    parent = all_data.get("parameters")
    ca_parent = None
    if parent is not None:
        cert_dest = "%sSSLCertificate" % name
        cert_key_dest = "%sSSLCertificateKey" % name
        ca_dest = "CaSSLCertificate"
        ca_key_dest = "CaSSLCertificateKey"
        cert_count_dest = "SSLCertificatCount"
        ca_parent = parent
    else:
        cert_dest = "certificate"
        cert_key_dest = "certificate_key"
        ca_dest = "ca_certificate"
        ca_key_dest = "ca_certificate_key"
        cert_count_dest = "certificate_count"

        # Make parent be a node in all_data
        svc = all_data.get(name, {})
        parent = all_data.get("ssl", {})
        svc["ssl"] = parent
        ca_parent = all_data.get("ssl", {})

        all_data[name] = svc
        all_data["ssl"] = ca_parent

    # If we only have one of cert or key this is an error if not overwriting
    if (cert_dest not in parent and cert_key_dest in parent or
            cert_dest in parent and cert_key_dest not in parent) and \
            not overwrite:
        raise ValueError("Only one of certificate or key defined.")

    if cert_dest not in parent or overwrite:
        # Check that we have both a CA cert and key or neither
        if (ca_dest not in parent and ca_key_dest in parent) or \
                (ca_dest in parent and ca_key_dest not in parent):
            raise ValueError("Only one of CA certificate or key defined.")

        # Gen CA
        if ca_dest not in parent:
            ca_key_pem, ca_cert_pem = create_ca_pair()
            ca_parent[ca_key_dest] = ca_key_pem
            ca_parent[ca_dest] = ca_cert_pem

        # Gen cert
        cert_serial = ca_parent.get(cert_count_dest, 0)
        cert_serial += 1
        signing_key_pem, signing_cert_pem = create_signing_pair(ca_key_pem,
                                                                ca_cert_pem,
                                                                cert_serial)
        ca_parent[cert_count_dest] = cert_serial
        parent[cert_key_dest] = signing_key_pem
        parent[cert_dest] = signing_cert_pem

        # Write out env
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
