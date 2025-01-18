# Copyright (C) 2024 - 2025 HMS Industrial Network Solutions
# Software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

# server_cert.py

import os
import logging
from helpers import run_command
from config import OPENSSL_PATH
from config import OPENVPN_PATH
import subprocess


def generate_dh_parameters(server_dir):
    """Generates the Diffie-Hellman parameters file (dh.pem)."""
    try:
        dh_path = os.path.join(server_dir, "dh.pem")
        run_command([OPENSSL_PATH, "dhparam", "-out", dh_path, "2048"])
        logging.info(f"Diffie-Hellman parameters generated at: {dh_path}")
    except subprocess.CalledProcessError as e:
        logging.error(f"Failed to generate Diffie-Hellman parameters: {e}")
        raise


def generate_server_certificates(ca_dir, server_dir, common_details, openssl_cnf_path):
    """Generates the server certificates and keys."""
    try:
        # Generate server key
        server_key_path = os.path.join(server_dir, "server.key")
        run_command([OPENSSL_PATH, "genrsa", "-out", server_key_path, "4096"])
        logging.info(f"Server key generated at {server_key_path}")

        # Generate server CSR
        server_csr_path = os.path.join(server_dir, "server.csr")
        subject = f"/C={common_details['C']}/ST={common_details['ST']}/L={common_details['L']}/O={common_details['O']}/OU={common_details['OU']}/CN=server/emailAddress={common_details['email_address']}"
        run_command(
            [
                OPENSSL_PATH,
                "req",
                "-new",
                "-key",
                server_key_path,
                "-out",
                server_csr_path,
                "-subj",
                subject,
                "-config",
                openssl_cnf_path,
            ]
        )
        logging.info(f"Server CSR generated at: {server_csr_path}")

        # Sign server certificate
        server_crt_path = os.path.join(server_dir, "server.crt")
        run_command(
            [
                OPENSSL_PATH,
                "ca",
                "-batch",
                "-config",
                openssl_cnf_path,
                "-extensions",
                "server_cert",
                "-days",
                "3650",
                "-notext",
                "-md",
                "sha256",
                "-in",
                server_csr_path,
                "-out",
                server_crt_path,
            ]
        )
        logging.info(f"Server certificate generated at {server_crt_path}")

        # Generate Diffie-Hellman parameters
        generate_dh_parameters(server_dir)

        # **Generate ta.key using OpenVPN command**
        ta_key_path = os.path.join(server_dir, "ta.key")
        run_command([OPENVPN_PATH, "--genkey", "secret", ta_key_path])
        logging.info(f"TLS authentication key generated at {ta_key_path}")

    except Exception as e:
        logging.error(f"Failed to generate server certificates: {e}")
        raise
