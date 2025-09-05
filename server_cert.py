# Copyright (C) 2024 - 2025 HMS Industrial Network Solutions
# Software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

# server_cert.py

import os
import logging
import subprocess
from helpers import run_command, run_command_with_progress
from config import OPENSSL_PATH, OPENVPN_PATH


def generate_dh_parameters(server_dir: str) -> None:
    """Generates the Diffie-Hellman parameters file (dh.pem)."""
    try:
        dh_path = os.path.join(server_dir, "dh.pem")
        run_command_with_progress(
            [OPENSSL_PATH, "dhparam", "-out", dh_path, "2048"],
            "Generating 2048-bit Diffie-Hellman parameters (this may take a minute)",
        )
        logging.info(f"Diffie-Hellman parameters generated at: {dh_path}")
    except subprocess.CalledProcessError as e:
        logging.error(f"Failed to generate Diffie-Hellman parameters: {e}")
        raise


def generate_server_certificates(ca_dir: str, server_dir: str, common_details: dict, openssl_cnf_path: str) -> None:
    """Generates the server certificates and keys."""
    try:
        # 1) Server private key (4096-bit RSA)
        server_key_path = os.path.join(server_dir, "server.key")
        run_command_with_progress(
            [OPENSSL_PATH, "genrsa", "-out", server_key_path, "4096"],
            "Generating 4096-bit server private key",
        )
        logging.info(f"Server key generated at {server_key_path}")

        # 2) Server CSR
        server_csr_path = os.path.join(server_dir, "server.csr")
        subject = (
            f"/C={common_details['C']}"
            f"/ST={common_details['ST']}"
            f"/L={common_details['L']}"
            f"/O={common_details['O']}"
            f"/OU={common_details['OU']}"
            f"/CN=server"
            f"/emailAddress={common_details['email_address']}"
        )
        run_command_with_progress(
            [
                OPENSSL_PATH, "req", "-new",
                "-key", server_key_path,
                "-out", server_csr_path,
                "-subj", subject,
                "-config", openssl_cnf_path,
            ],
            "Creating server CSR",
        )
        logging.info(f"Server CSR generated at: {server_csr_path}")

        # 3) Sign server certificate
        server_crt_path = os.path.join(server_dir, "server.crt")
        run_command_with_progress(
            [
                OPENSSL_PATH, "ca", "-batch",
                "-config", openssl_cnf_path,
                "-extensions", "server_cert",
                "-days", "3650", "-notext", "-md", "sha256",
                "-in", server_csr_path,
                "-out", server_crt_path,
            ],
            "Signing server certificate with CA",
        )
        logging.info(f"Server certificate generated at {server_crt_path}")

        # 4) DH params
        generate_dh_parameters(server_dir)

        # 5) TLS auth key (fast)
        ta_key_path = os.path.join(server_dir, "ta.key")
        run_command([OPENVPN_PATH, "--genkey", "secret", ta_key_path])
        logging.info(f"TLS authentication key generated at {ta_key_path}")

    except Exception as e:
        logging.error(f"Failed to generate server certificates: {e}")
        raise
