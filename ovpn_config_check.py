#!/usr/bin/env python3

# Copyright (C) 2024 - 2025 HMS Industrial Network Solutions
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

import os
import subprocess
import tempfile
import re
import sys

# Paths to your configuration files
SERVER_CONF = "server.conf"
CLIENT_OVPN = "YU23MAR2300047.ovpn"

# Define the path to the OpenSSL executable
OPENSSL_PATH = r"C:\Users\rambo\OneDrive\Desktop\workspace\OpenVPN_Setup_w_GUI\needed_binaries\openssl.exe"  # Replace with your OpenSSL path


def openssl_command(*args):
    """
    Constructs the OpenSSL command using the specified OPENSSL_PATH.
    """
    return [OPENSSL_PATH] + list(args)


def extract_inline_section(filename, tag):
    """
    Extracts the content between <tag> and </tag> from the given file.
    """
    with open(filename, "r") as f:
        lines = f.readlines()

    start_tag = f"<{tag}>"
    end_tag = f"</{tag}>"
    in_section = False
    section_lines = []

    for line in lines:
        line_strip = line.strip()
        if line_strip == start_tag:
            in_section = True
            continue
        elif line_strip == end_tag:
            in_section = False
            continue
        if in_section:
            section_lines.append(line)

    return "".join(section_lines)


def save_to_file(content, filename):
    """
    Saves the given content to a file.
    """
    with open(filename, "w") as f:
        f.write(content)


def check_openssl():
    """
    Checks if OpenSSL is available at the specified path.
    """
    try:
        subprocess.run(
            openssl_command("version"), capture_output=True, text=True, check=True
        )
        return True
    except FileNotFoundError:
        return False
    except subprocess.CalledProcessError:
        return False


def validate_ca_certificate(ca_cert_path):
    """
    Validates the CA certificate to ensure it includes CA:TRUE in Basic Constraints.
    """
    print("Validating CA Certificate...")
    try:
        result = subprocess.run(
            openssl_command("x509", "-in", ca_cert_path, "-noout", "-text"),
            capture_output=True,
            text=True,
            check=True,
        )
    except subprocess.CalledProcessError as e:
        print("Failed to parse CA certificate.")
        print(e.stderr)
        return False

    output = result.stdout
    # Check for CA:TRUE in Basic Constraints
    match = re.search(r"X509v3 Basic Constraints:.*\n.*CA:TRUE", output)
    if match:
        print("CA certificate is valid and includes CA:TRUE in Basic Constraints.\n")
        return True
    else:
        print("CA certificate does NOT include CA:TRUE in Basic Constraints.\n")
        return False


def validate_certificate(cert_path, ca_cert_path, purpose):
    """
    Validates a certificate by verifying its chain and checking validity dates.
    """
    print(f"Validating {purpose} Certificate...")
    try:
        # Verify certificate chain
        verify_result = subprocess.run(
            openssl_command("verify", "-CAfile", ca_cert_path, cert_path),
            capture_output=True,
            text=True,
            check=True,
        )
        if "OK" in verify_result.stdout:
            print(f"{purpose} certificate is signed by the CA.")
        else:
            print(f"{purpose} certificate verification failed.")
            print(verify_result.stderr)
            return False
    except subprocess.CalledProcessError as e:
        print(f"{purpose} certificate verification failed.")
        print(e.stderr)
        return False

    try:
        # Check validity dates
        result = subprocess.run(
            openssl_command("x509", "-in", cert_path, "-noout", "-dates"),
            capture_output=True,
            text=True,
            check=True,
        )
        print(f"{purpose} certificate validity dates:")
        print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Failed to parse {purpose} certificate.")
        print(e.stderr)
        return False


def validate_crl(crl_path, ca_cert_path):
    """
    Validates the CRL to ensure it's correctly signed by the CA.
    """
    print("Validating CRL...")
    try:
        # Verify CRL signature
        verify_result = subprocess.run(
            openssl_command("crl", "-in", crl_path, "-noout", "-CAfile", ca_cert_path),
            capture_output=True,
            text=True,
            check=True,
        )
        print("CRL is valid and signed by the CA.\n")
        return True
    except subprocess.CalledProcessError as e:
        print("CRL verification failed.")
        print(e.stderr)
        return False


def main():
    # Check if OpenSSL is available
    if not check_openssl():
        print("OpenSSL is not installed or not available at the specified path.")
        print("Please install OpenSSL and ensure the OPENSSL_PATH is correct.")
        sys.exit(1)

    # Check if configuration files exist
    if not os.path.isfile(SERVER_CONF):
        print(f"Server configuration file '{SERVER_CONF}' not found.")
        sys.exit(1)
    if not os.path.isfile(CLIENT_OVPN):
        print(f"Client configuration file '{CLIENT_OVPN}' not found.")
        sys.exit(1)

    with tempfile.TemporaryDirectory() as tmpdir:
        # Extract and save certificates and keys from server.conf
        server_ca = extract_inline_section(SERVER_CONF, "ca")
        server_cert = extract_inline_section(SERVER_CONF, "cert")
        server_key = extract_inline_section(SERVER_CONF, "key")
        crl_verify = extract_inline_section(SERVER_CONF, "crl-verify")

        if not server_ca or not server_cert or not server_key:
            print("Failed to extract certificates or keys from server.conf.")
            sys.exit(1)

        save_to_file(server_ca, os.path.join(tmpdir, "server_ca.crt"))
        save_to_file(server_cert, os.path.join(tmpdir, "server.crt"))
        save_to_file(server_key, os.path.join(tmpdir, "server.key"))

        if crl_verify:
            save_to_file(crl_verify, os.path.join(tmpdir, "crl.pem"))
        else:
            print("No CRL found in server.conf.")

        # Extract and save certificates and keys from client.ovpn
        client_ca = extract_inline_section(CLIENT_OVPN, "ca")
        client_cert = extract_inline_section(CLIENT_OVPN, "cert")
        client_key = extract_inline_section(CLIENT_OVPN, "key")

        if not client_ca or not client_cert or not client_key:
            print("Failed to extract certificates or keys from client.ovpn.")
            sys.exit(1)

        save_to_file(client_ca, os.path.join(tmpdir, "client_ca.crt"))
        save_to_file(client_cert, os.path.join(tmpdir, "client.crt"))
        save_to_file(client_key, os.path.join(tmpdir, "client.key"))

        # Paths to the extracted files
        ca_cert_path = os.path.join(tmpdir, "server_ca.crt")
        server_cert_path = os.path.join(tmpdir, "server.crt")
        client_cert_path = os.path.join(tmpdir, "client.crt")
        crl_path = os.path.join(tmpdir, "crl.pem")

        # Validate CA certificate
        ca_valid = validate_ca_certificate(ca_cert_path)

        # Validate server certificate
        server_valid = validate_certificate(server_cert_path, ca_cert_path, "Server")

        # Validate client certificate
        client_valid = validate_certificate(client_cert_path, ca_cert_path, "Client")

        # Validate CRL if present
        if os.path.isfile(crl_path):
            crl_valid = validate_crl(crl_path, ca_cert_path)
        else:
            print("CRL file not found. Skipping CRL validation.\n")
            crl_valid = True  # Consider valid if not used

        # Summary
        print("\nValidation Summary:")
        print(f"CA Certificate Valid: {'Yes' if ca_valid else 'No'}")
        print(f"Server Certificate Valid: {'Yes' if server_valid else 'No'}")
        print(f"Client Certificate Valid: {'Yes' if client_valid else 'No'}")
        if os.path.isfile(crl_path):
            print(f"CRL Valid: {'Yes' if crl_valid else 'No'}")
        else:
            print("CRL Valid: Not Applicable")

        # Exit code based on validation results
        if all([ca_valid, server_valid, client_valid, crl_valid]):
            print("\nAll validations passed successfully.")
            sys.exit(0)
        else:
            print("\nOne or more validations failed.")
            sys.exit(1)


if __name__ == "__main__":
    main()
