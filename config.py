# config.py

import sys
import os

def get_base_dir():
    """Determines the base directory of the application."""
    if getattr(sys, 'frozen', False):
        # Running as a bundled executable
        BASE_DIR = os.path.dirname(os.path.abspath(sys.executable))
    else:
        # Running in a normal Python environment
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    return BASE_DIR

BASE_DIR = get_base_dir()

# Paths to external binaries
if getattr(sys, 'frozen', False):
    # Adjust paths when running as a bundled executable
    OPENSSL_PATH = os.path.join(sys._MEIPASS, "needed_binaries", "openssl.exe")
    OPENVPN_PATH = os.path.join(sys._MEIPASS, "needed_binaries", "openvpn.exe")
else:
    OPENSSL_PATH = os.path.join(BASE_DIR, "needed_binaries", "openssl.exe")
    OPENVPN_PATH = os.path.join(BASE_DIR, "needed_binaries", "openvpn.exe")

# Common certificate details (defaults)
COMMON_DETAILS = {
    "C": "US",
    "ST": "MO",
    "L": "Mineral Point",
    "O": "GregNet",
    "OU": "IT",
    "email_address": "gregory.allen.whitlock@gmail.com",
}

def get_user_input(prompt, default):
    """Helper function to get input from user, with a default option."""
    user_input = input(f"{prompt} [{default}]: ")
    return user_input if user_input else default

def get_certificate_details():
    """Prompt user for certificate details or use defaults."""
    while True:
        c_code = get_user_input("Country Name (2 letter code)", COMMON_DETAILS["C"])
        if len(c_code) == 2 and c_code.isalpha():
            break
        else:
            print("Error: Country code must be exactly 2 letters. Please try again.")
    user_details = {
        "C": c_code,
        "ST": get_user_input("State or Province Name (full name)", COMMON_DETAILS["ST"]),
        "L": get_user_input("Locality Name (eg, city)", COMMON_DETAILS["L"]),
        "O": get_user_input("Organization Name (eg, company)", COMMON_DETAILS["O"]),
        "OU": get_user_input("Organizational Unit Name (eg, section)", COMMON_DETAILS["OU"]),
        "email_address": get_user_input("Email Address", COMMON_DETAILS["email_address"]),
    }
    return user_details
