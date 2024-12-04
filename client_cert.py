# client_cert.py
import os
import logging
from helpers import run_command
from config import OPENSSL_PATH

def generate_client_key(client_key_path):
    """
    Generates a client key.
    """
    try:
        run_command([OPENSSL_PATH, "genrsa", "-out", client_key_path, "4096"])
        logging.info(f"Client key generated at: {client_key_path}")
    except Exception as e:
        logging.error(f"Failed to generate client key: {e}")
        raise

def generate_client_csr(client_key_path, client_csr_path, client_name, common_details, openssl_cnf_path):
    """
    Generates a client CSR.
    """
    try:
        # Use the actual client_name for CN
        subject = f"/C={common_details['C']}/ST={common_details['ST']}/L={common_details['L']}/O={common_details['O']}/OU={common_details['OU']}/CN={client_name}/emailAddress={common_details['email_address']}"
        run_command([
            OPENSSL_PATH,
            "req", "-new",
            "-key", client_key_path,
            "-out", client_csr_path,
            "-subj", subject,
            "-config", openssl_cnf_path
        ])
        logging.info(f"Client CSR generated at: {client_csr_path}")
    except Exception as e:
        logging.error(f"Failed to generate client CSR: {e}")
        raise

def sign_client_certificate(client_csr_path, client_crt_path, openssl_cnf_path):
    try:
        run_command([
            OPENSSL_PATH,
            "ca", "-batch",
            "-config", openssl_cnf_path,
            "-extensions", "client_cert",  # Added this line
            "-in", client_csr_path,
            "-out", client_crt_path,
            "-days", "3650",
            "-notext", "-md", "sha256"
        ])
        logging.info(f"Client certificate signed at: {client_crt_path}")
    except Exception as e:
        logging.error(f"Failed to sign client certificate: {e}")
        raise

