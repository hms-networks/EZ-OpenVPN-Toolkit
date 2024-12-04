# ca_setup.py
# Copyright (C) 2024 - 2025 HMS Industrial Network Solutions
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

import os
import logging
from helpers import run_command, create_directory, get_base_dir
from config import OPENSSL_PATH
import subprocess

BASE_DIR = get_base_dir()


def generate_openssl_config(openssl_cnf_path, ca_dir, common_details):
    """Generates an OpenSSL configuration file."""
    try:
        # Replace backslashes with forward slashes for Windows compatibility
        ca_dir_forward = ca_dir.replace("\\", "/")

        with open(openssl_cnf_path, "w") as f:
            f.write(
                f"""
[ ca ]
default_ca = CA_default

[ CA_default ]
dir = {ca_dir_forward}
certs = $dir/certs
new_certs_dir = $dir/newcerts
database = $dir/index.txt
serial = $dir/serial
crlnumber = $dir/crlnumber
RANDFILE = $dir/.rand

private_key = $dir/ca.key
certificate = $dir/ca.crt

default_md = sha256
preserve = no
policy = policy_strict
default_days = 3650
default_crl_days = 30  # Added default_crl_days

[ policy_strict ]
countryName = supplied
stateOrProvinceName = supplied
organizationName = supplied
organizationalUnitName = optional
commonName = supplied
emailAddress = optional

[ req ]
default_bits = 4096
prompt = no
default_md = sha256
distinguished_name = req_distinguished_name
string_mask = utf8only

[ req_distinguished_name ]
C = {common_details['C']}
ST = {common_details['ST']}
L = {common_details['L']}
O = {common_details['O']}
OU = {common_details['OU']}
CN = {common_details.get('CN', 'OpenVPN-CA')}
emailAddress = {common_details['email_address']}

[ server_cert ]
basicConstraints = CA:FALSE
nsCertType = server
nsComment = "OpenSSL Generated Server Certificate"
subjectKeyIdentifier = hash
authorityKeyIdentifier = keyid,issuer:always
keyUsage = critical, digitalSignature, keyEncipherment
extendedKeyUsage = serverAuth

[ client_cert ]
basicConstraints = CA:FALSE
nsCertType = client
nsComment = "OpenSSL Generated Client Certificate"
subjectKeyIdentifier = hash
authorityKeyIdentifier = keyid,issuer:always
keyUsage = critical, digitalSignature, keyEncipherment
extendedKeyUsage = clientAuth

[ v3_ca ]
subjectKeyIdentifier = hash
authorityKeyIdentifier = keyid:always,issuer
basicConstraints = critical, CA:true
keyUsage = critical, cRLSign, keyCertSign
"""
            )
        logging.info(f"OpenSSL configuration file generated at {openssl_cnf_path}")
    except Exception as e:
        logging.error(f"Failed to generate OpenSSL configuration file: {e}")
        raise


def setup_ca(certificate_details):
    try:
        ca_dir = os.path.join(BASE_DIR, "ca")
        create_directory(ca_dir)
        logging.info(f"CA directory created at: {ca_dir}")

        # **Create Required Directories**
        certs_dir = os.path.join(ca_dir, "certs")
        newcerts_dir = os.path.join(ca_dir, "newcerts")
        create_directory(certs_dir)
        create_directory(newcerts_dir)
        logging.info(f"Certs directory created at: {certs_dir}")
        logging.info(f"Newcerts directory created at: {newcerts_dir}")

        # Generate OpenSSL configuration file
        openssl_cnf_path = os.path.join(ca_dir, "openssl.cnf")
        generate_openssl_config(openssl_cnf_path, ca_dir, certificate_details)

        # Generate CA key
        ca_key_path = os.path.join(ca_dir, "ca.key")
        run_command([OPENSSL_PATH, "genrsa", "-out", ca_key_path, "4096"])
        logging.info(f"CA key generated at: {ca_key_path}")

        # Generate CA certificate with v3_ca extensions
        ca_cert_path = os.path.join(ca_dir, "ca.crt")
        subject = f"/C={certificate_details['C']}/ST={certificate_details['ST']}/L={certificate_details['L']}/O={certificate_details['O']}/OU={certificate_details['OU']}/CN=ca/emailAddress={certificate_details['email_address']}"
        run_command(
            [
                OPENSSL_PATH,
                "req",
                "-new",
                "-x509",
                "-days",
                "3650",
                "-config",
                openssl_cnf_path,
                "-extensions",
                "v3_ca",  # Added this line
                "-key",
                ca_key_path,
                "-out",
                ca_cert_path,
                "-subj",
                subject,
            ]
        )
        logging.info(f"CA certificate generated at: {ca_cert_path}")

        # Initialize OpenSSL database files
        index_file = os.path.join(ca_dir, "index.txt")
        serial_file = os.path.join(ca_dir, "serial")
        crlnumber_file = os.path.join(ca_dir, "crlnumber")

        open(index_file, "w").close()
        with open(serial_file, "w") as f:
            f.write("01\n")
        with open(crlnumber_file, "w") as f:
            f.write("01\n")
        logging.info("OpenSSL database files initialized.")

        # Generate initial CRL (Certificate Revocation List)
        crl_path = os.path.join(ca_dir, "crl.pem")
        run_command(
            [
                OPENSSL_PATH,
                "ca",
                "-config",
                openssl_cnf_path,
                "-gencrl",
                "-out",
                crl_path,
            ]
        )
        logging.info(f"Initial CRL generated at: {crl_path}")

    except Exception as e:
        logging.error(f"Error during CA setup: {e}")
        raise
