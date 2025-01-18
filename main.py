# Copyright (C) 2024 - 2025 HMS Industrial Network Solutions
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

# main.py

import os
import json
import logging
import shutil
import sys
import zipfile
from client_revoke import revoke_client
from config import get_certificate_details, get_base_dir
from ca_setup import setup_ca
from client_manager import list_current_clients, manage_client_creation
from server_cert import generate_server_certificates
from openvpn_config import generate_server_conf
from subnet_management import (
    validate_subnet,
    save_subnet_to_csv,
    load_existing_subnets,
    get_subnet_by_name,
)
from helpers import create_directory
from logger import setup_logging

BASE_DIR = get_base_dir()
setup_logging()

CONFIG_FILE = os.path.join(BASE_DIR, "server_config.json")
CLIENTS_DIR = os.path.join(BASE_DIR, "clients")


def resource_path(relative_path):
    """Get the absolute path to a resource, works for PyInstaller and normal execution."""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except AttributeError:
        # If not running as a PyInstaller executable, use the current directory
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


def load_server_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    return None


def save_server_config(config):
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f)


def initialize_server():
    try:
        logging.info("Starting OpenVPN server initialization...")

        # Prompt for certificate details using config.py function
        certificate_details = get_certificate_details()
        certificate_details["server_initialized"] = True
        save_server_config(certificate_details)
        print("\nFinal certificate details:")
        for key, value in certificate_details.items():
            if key != "server_initialized":
                print(f"{key}: {value}")

        # Step 1: Set up the Certificate Authority
        setup_ca(certificate_details)  # Pass certificate_details here

        # Assign server_dir and ca_dir here
        server_dir = os.path.join(BASE_DIR, "server")
        ca_dir = os.path.join(BASE_DIR, "ca")
        openssl_cnf_path = os.path.join(ca_dir, "openssl.cnf")

        # Create server and ccd directories if they don't exist
        create_directory(server_dir)
        ccd_dir_full = os.path.join(server_dir, "ccd")  # Absolute path
        create_directory(ccd_dir_full)

        # Prompt for OpenVPN Tunnel Subnet
        existing_subnets = load_existing_subnets(os.path.join(BASE_DIR, "subnets.csv"))
        while True:
            openvpn_tunnel_subnet_input = input(
                "Enter the OpenVPN tunnel subnet (e.g., 10.8.0.0/24): "
            )
            try:
                openvpn_tunnel_subnet = validate_subnet(
                    openvpn_tunnel_subnet_input, existing_subnets
                )
                break
            except ValueError as e:
                print(f"Error: {e}")
        # Save to CSV
        save_subnet_to_csv(
            os.path.join(BASE_DIR, "subnets.csv"),
            "openvpn_tunnel_subnet",
            openvpn_tunnel_subnet,
        )
        existing_subnets.append(str(openvpn_tunnel_subnet))

        # Prompt for Server LAN Subnet
        while True:
            server_lan_subnet_input = input(
                "Enter the Server LAN subnet (e.g., 192.168.1.0/24): "
            )
            try:
                server_lan_subnet = validate_subnet(
                    server_lan_subnet_input, existing_subnets
                )
                break
            except ValueError as e:
                print(f"Error: {e}")
        # Save to CSV
        save_subnet_to_csv(
            os.path.join(BASE_DIR, "subnets.csv"),
            "server_local_private_subnet",
            server_lan_subnet,
        )
        existing_subnets.append(str(server_lan_subnet))

        # Step 2: Generate Server Certificates
        common_details = certificate_details.copy()
        generate_server_certificates(
            ca_dir, server_dir, common_details, openssl_cnf_path
        )

        # Step 3: Set up clients and get server details
        client_names, server_address, port, proto, cipher, data_ciphers = (
            prompt_for_clients()
        )

        # Save server details to a JSON file
        server_details = {
            "server_address": server_address,
            "port": port,
            "proto": proto,
            "cipher": cipher,
            "data_ciphers": data_ciphers,
        }
        with open(os.path.join(BASE_DIR, "server_details.json"), "w") as f:
            json.dump(server_details, f)
        logging.info("Server details saved to server_details.json")

        # Step 4: Generate Server Configuration
        generate_server_conf(
            os.path.join(server_dir, "server.conf"),
            openvpn_tunnel_subnet,
            os.path.join(ca_dir, "ca.crt"),
            os.path.join(server_dir, "server.crt"),
            os.path.join(server_dir, "server.key"),
            os.path.join(server_dir, "dh.pem"),
            os.path.join(server_dir, "ta.key"),
            os.path.join(ca_dir, "crl.pem"),
            port=port,
            proto=proto,
            cipher=cipher,
            data_ciphers=data_ciphers,
            server_lan_subnet=server_lan_subnet,
            ccd_dir="ccd",  # Pass the relative path as a string
        )

        # Step 5: Set up clients
        for client_name in client_names:
            manage_client_creation(
                client_name,
                ca_dir,
                certificate_details,  # Pass custom certificate details
                openssl_cnf_path,
                os.path.join(server_dir, "server.conf"),
                ccd_dir_full,
                openvpn_tunnel_subnet,
                server_address,
                port,
                proto,
                cipher,
                data_ciphers,
            )

        # Mark server as initialized after successful setup
        save_server_config(certificate_details)
        logging.info("OpenVPN server initialization completed.")

    except Exception as e:
        logging.error(f"Error during OpenVPN server initialization: {e}")
        print(
            "Failed to initialize the OpenVPN server. Check the logs for more details."
        )
        print(f"Error: {e}")  # Print the error message


def generate_client_certificates():
    try:
        logging.info("Starting Client Certificate and Configuration generation...")

        # Load server details from JSON file
        server_details_json = os.path.join(BASE_DIR, "server_details.json")
        if not os.path.exists(server_details_json):
            print("Server details not found. Please re-initialize the server.")
            return
        with open(server_details_json, "r") as f:
            server_details = json.load(f)
            server_address = server_details["server_address"]
            port = server_details["port"]
            proto = server_details["proto"]
            cipher = server_details["cipher"]
            data_ciphers = server_details["data_ciphers"]

        # Load custom certificate details from server_config.json
        certificate_details = load_server_config()
        if not certificate_details:
            print("Certificate details not found. Please re-initialize the server.")
            return
        # Remove 'server_initialized' key if present
        certificate_details.pop("server_initialized", None)

        # Prompt for client names
        client_names = prompt_for_clients_existing_server()

        # Load openvpn_tunnel_subnet from subnets.csv
        openvpn_tunnel_subnet = get_subnet_by_name(
            os.path.join(BASE_DIR, "subnets.csv"), "openvpn_tunnel_subnet"
        )
        if not openvpn_tunnel_subnet:
            print("OpenVPN tunnel subnet not found. Please re-initialize the server.")
            return

        for client_name in client_names:
            manage_client_creation(
                client_name,
                os.path.join(BASE_DIR, "ca"),
                certificate_details,  # Pass custom certificate details
                os.path.join(BASE_DIR, "ca", "openssl.cnf"),
                os.path.join(BASE_DIR, "server", "server.conf"),
                os.path.join(BASE_DIR, "server", "ccd"),
                openvpn_tunnel_subnet,
                server_address,
                port,
                proto,
                cipher,
                data_ciphers,
            )
        logging.info("Client Certificates and Configurations generated.")
    except Exception as e:
        logging.error(
            f"Error during Client Certificate and Configuration generation: {e}"
        )
        print(
            "Failed to generate client certificates and configurations. Check the logs for more details."
        )


def prompt_for_clients():
    """
    Prompts the user to enter client information for client creation.
    Ensures the weakest cipher is selected for fallback and sets data-ciphers.

    Returns:
        new_client_names (list): List of newly added client names.
        server_address (str): The OpenVPN server address.
        port (str): The OpenVPN server port.
        proto (str): The OpenVPN protocol (tcp/udp).
        weakest_cipher (str): The weakest selected cipher (lowest in valid_ciphers list).
        selected_ciphers (list): List of selected ciphers for data-ciphers.
    """
    # Default values for server configuration
    default_values = {
        "server_address": "example.com",
        "port": "1194",
        "proto": "udp"
    }

    # Load existing client names from JSON if file exists
    client_names_json = os.path.join(BASE_DIR, "client_names.json")
    if os.path.exists(client_names_json):
        with open(client_names_json, "r") as f:
            client_names = json.load(f)
    else:
        client_names = []

    # Prompt for number of clients, ensuring it's a valid positive integer
    while True:
        try:
            num_clients = int(input("Enter the number of clients to create: "))
            if num_clients <= 0:
                print("Please enter a positive integer.")
                continue
            break
        except ValueError:
            print("Please enter a valid integer.")

    # Ask for client name for each client, ensure it does not already exist
    new_client_names = []
    for i in range(num_clients):
        while True:
            client_name = input(f"Enter the name for client {i + 1}: ").strip()
            if not client_name:
                print("Client name cannot be empty.")
                continue
            if client_name in client_names:
                print("Client name already exists. Please enter a different name.")
                continue
            # Add to both the in-memory list of all client names and the list of newly created names
            client_names.append(client_name)
            new_client_names.append(client_name)
            break

    # Save updated client names to client_names.json
    with open(client_names_json, "w") as f:
        json.dump(client_names, f)

    # Prompt for server details with default values
    server_address = input(f"Enter the OpenVPN server address [{default_values['server_address']}]: ").strip()
    if not server_address:
        server_address = default_values["server_address"]

    port = input(f"Enter the OpenVPN server port [{default_values['port']}]: ").strip()
    if not port:
        port = default_values["port"]

    # Force user to enter either 'tcp' or 'udp'
    while True:
        proto = input(f"Enter the protocol (tcp/udp) [{default_values['proto']}]: ").strip().lower()
        if not proto:
            proto = default_values["proto"]
        if proto in ["tcp", "udp"]:
            break
        else:
            print("Invalid protocol. Please enter either 'tcp' or 'udp'.")

    # List of valid ciphers in ascending order of strength (weakest to strongest)
    valid_ciphers = [
        "DES-EDE3-CBC",       # 1.) Very weak (not recommended)
        "BF-CBC",             # 2.) Weak (not recommended)
        "SEED-CBC",           # 3.)
        "CAMELLIA-128-CBC",   # 4.)
        "AES-128-CBC",        # 5.)
        "CAMELLIA-192-CBC",   # 6.)
        "AES-192-CBC",        # 7.)
        "CAMELLIA-256-CBC",   # 8.)
        "AES-256-CBC",        # 9.)
        "AES-128-GCM",        # 10.)
        "AES-192-GCM",        # 11.)
        "AES-256-GCM",        # 12.)
        "CHACHA20-POLY1305",  # 13.)
    ]

    selected_ciphers = []
    print(
        "\nSelect ciphers for data-ciphers one at a time (at least one is required)."
        " Enter the number corresponding to the cipher."
    )
    print("When you are done selecting ciphers, enter 0 or 'done'.")

    while True:
        # If there are no valid ciphers left to choose from, break
        if not valid_ciphers:
            print("\nNo more ciphers available to select.")
            break

        print("\nAvailable Ciphers:")
        for idx, cipher_name in enumerate(valid_ciphers, start=1):
            print(f"{idx}.) {cipher_name}")

        # Show user which ciphers have been selected so far
        if selected_ciphers:
            print(f"\nCiphers currently selected: {', '.join(selected_ciphers)}")

        selection = input("Select a cipher (0 to finish): ").strip().lower()
        if selection in ("0", "done"):
            # Ensure the user has selected at least one cipher
            if selected_ciphers:
                break
            else:
                print("You must select at least one cipher.")
                continue

        try:
            selection_int = int(selection)
            if 1 <= selection_int <= len(valid_ciphers):
                cipher_selected = valid_ciphers[selection_int - 1]
                selected_ciphers.append(cipher_selected)
                # Remove selected cipher from the list so it can't be chosen again
                valid_ciphers.remove(cipher_selected)
                print(f"Selected cipher: {cipher_selected}")
            else:
                print(f"Please enter a number between 1 and {len(valid_ciphers)}.")
        except ValueError:
            print("Invalid input. Please enter a number.")

    # Determine the weakest cipher by its position in the original ordering
    full_ordering = [
        "DES-EDE3-CBC",
        "BF-CBC",
        "SEED-CBC",
        "CAMELLIA-128-CBC",
        "AES-128-CBC",
        "CAMELLIA-192-CBC",
        "AES-192-CBC",
        "CAMELLIA-256-CBC",
        "AES-256-CBC",
        "AES-128-GCM",
        "AES-192-GCM",
        "AES-256-GCM",
        "CHACHA20-POLY1305",
    ]
    if selected_ciphers:
        weakest_cipher = min(selected_ciphers, key=lambda c: full_ordering.index(c))
    else:
        weakest_cipher = None

    # Return the new client names along with the chosen server/cipher information
    return new_client_names, server_address, port, proto, weakest_cipher, selected_ciphers

def prompt_for_clients_existing_server():
    """
    Prompts for client names for an existing server setup.
    """
    # Load existing client names from client_names.json if it exists
    client_names_json = os.path.join(BASE_DIR, "client_names.json")
    if os.path.exists(client_names_json):
        with open(client_names_json, "r") as f:
            existing_client_names = json.load(f)
    else:
        existing_client_names = []

    new_client_names = []

    # Get number of clients, ensuring it's a valid integer
    while True:
        try:
            num_clients = int(input("Enter the number of clients to create: "))
            break
        except ValueError:
            print("Please enter a valid number.")

    # Ask for client name for each client, make sure it does not already exist
    for i in range(num_clients):
        client_name = input(f"Enter the name for client {i + 1}: ")
        while client_name in existing_client_names or client_name in new_client_names:
            print("Client name already exists. Please enter a different name.")
            client_name = input(f"Enter the name for client {i + 1}: ")
        new_client_names.append(client_name)

    # Combine existing and new client names
    all_client_names = existing_client_names + new_client_names

    # Save all client names to client_names.json
    with open(client_names_json, "w") as f:
        json.dump(all_client_names, f)

    return new_client_names  # Return only new client names


def revoke_clients():
    try:
        while True:
            client_names = list_current_clients()
            if not client_names:
                print("No clients found to revoke.")
                break

            print("Current Clients:")
            for idx, client_name in enumerate(client_names, start=1):
                print(f"{idx}.) {client_name}")
            print(f"{len(client_names) + 1}.) Exit")

            selection = input("Please select which client you would like to revoke: ")
            try:
                selection_int = int(selection)
                if 1 <= selection_int <= len(client_names):
                    client_name_to_revoke = client_names[selection_int - 1]
                    confirm = input(
                        f"Are you sure you want to revoke client '{client_name_to_revoke}'? (y/n): "
                    ).lower()
                    if confirm == "y":
                        revoke_client(
                            client_name_to_revoke,
                            os.path.join(BASE_DIR, "ca"),
                            os.path.join(BASE_DIR, "ca", "openssl.cnf"),
                            os.path.join(BASE_DIR, "subnets.csv"),
                        )
                        logging.info(f"Client {client_name_to_revoke} revoked.")
                        print(f"Client '{client_name_to_revoke}' has been revoked.")
                    else:
                        print("Client revocation cancelled.")
                elif selection_int == len(client_names) + 1:
                    print("Exiting client revocation menu.")
                    break
                else:
                    print(
                        f"Please enter a number between 1 and {len(client_names) + 1}."
                    )
            except ValueError:
                print("Invalid input. Please enter a number.")
    except Exception as e:
        logging.error(f"Error during client revocation: {e}")
        print(f"Failed to revoke the client. Check the logs for more details.")


def package_server_windows():
    try:
        print("Packaging OpenVPN server for deployment on Windows PC...")

        server_dir = os.path.join(BASE_DIR, "server")
        if not os.path.exists(server_dir):
            print("Server directory not found. Please initialize the server first.")
            return

        # Paths to the deployment scripts using resource_path
        powershell_script = resource_path("deploy_ovpn_server_on_win10-11.ps1")

        if not os.path.exists(powershell_script):
            print("PowerShell deployment script not found.")
            return

        # Create a temporary directory to hold the files for zipping
        temp_dir = os.path.join(BASE_DIR, "temp_windows_deploy")
        os.makedirs(temp_dir, exist_ok=True)

        # Copy the 'server' directory to the temp directory
        shutil.copytree(server_dir, os.path.join(temp_dir, "server"))

        # Copy the deployment scripts to the temp directory
        shutil.copy(powershell_script, temp_dir)

        # Create the zip file
        zip_filename = os.path.join(BASE_DIR, "OpenVPN_Server_Windows.zip")
        with zipfile.ZipFile(zip_filename, "w", zipfile.ZIP_DEFLATED) as zipf:
            # Walk through the temp directory and add files to the zip
            for root, dirs, files in os.walk(temp_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, start=temp_dir)
                    zipf.write(file_path, arcname)
        print(
            f"Packaged server files into '{zip_filename}'. You can transfer this zip file to the Windows server and extract it there."
        )
        logging.info(f"Packaged server for Windows deployment: {zip_filename}")

        # Print instructions for deployment
        print(f"Instructions for Deployment")
        print(
            f"1.) Copy OpenVPN_Server_Windows.zip to the Windows PC you plan to use as the OpenVPN Server."
        )
        print(f"2.) Unzip/Extract Zip file to a directory of your choice.")
        print(
            f"3.) Open Powershell in the directory where you unzipped/extracted the zip file"
        )
        print(
            f"4.) At the Powershell prompt, run this command powershell -ExecutionPolicy Bypass -File deploy_ovpn_server_on_win10-11.ps1"
        )
        print(
            f"Once the process is complete, the server directory will be copied to C:\\Program Files\\OpenVPN\\config\\server"
        )
        print(f"It will Start and configure OpenVPN service")
        print(
            f"It will Enable IP routing in Windows, Enable and start Routing and Remote Access service"
        )
        print(
            f"Create a scheduled task to run the batch file, which starts OpenVPN Server, at startup"
        )

        # Clean up the temporary directory
        shutil.rmtree(temp_dir)

    except Exception as e:
        print(
            f"An error occurred while packaging the server for Windows deployment: {e}"
        )
        logging.error(f"Error packaging server for Windows: {e}")


def package_server_linux():
    try:
        print("Packaging OpenVPN server for deployment on Linux PC...")

        server_dir = os.path.join(BASE_DIR, "server")
        if not os.path.exists(server_dir):
            print("Server directory not found. Please initialize the server first.")
            return

        # Path to the deployment script using resource_path
        bash_script = resource_path("deploy_ovpn_server_linux.sh")

        if not os.path.exists(bash_script):
            print("Bash deployment script not found.")
            return

        # Create a temporary directory to hold the files for zipping
        temp_dir = os.path.join(BASE_DIR, "temp_linux_deploy")
        os.makedirs(temp_dir, exist_ok=True)

        # Copy the 'server' directory to the temp directory
        shutil.copytree(server_dir, os.path.join(temp_dir, "server"))

        # Copy the deployment script to the temp directory
        shutil.copy(bash_script, temp_dir)

        # Create the zip file
        zip_filename = os.path.join(BASE_DIR, "OpenVPN_Server_Linux.zip")
        with zipfile.ZipFile(zip_filename, "w", zipfile.ZIP_DEFLATED) as zipf:
            # Walk through the temp directory and add files to the zip
            for root, dirs, files in os.walk(temp_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, start=temp_dir)
                    zipf.write(file_path, arcname)
        print(
            f"Packaged server files into '{zip_filename}'. You can transfer this zip file to the Linux server and extract it there."
        )
        logging.info(f"Packaged server for Linux deployment: {zip_filename}")

        # Clean up the temporary directory
        shutil.rmtree(temp_dir)

        # Print the deployment instructions
        print(f"Instructions for Deployment")
        print(
            f"1.) Copy OpenVPN_Server_Linux.zip to the RHEL/Debian based Linux PC you plan to use as the OpenVPN Server"
        )
        print(f"2.) Unzip/Extract Zip file to a directory of your choice.")
        print(
            f"3.) Open terminal/shell in the directory where you unzipped/extracted the zip file"
        )
        print(
            f"4.) At the terminal shell run this command chmod +x deploy_ovpn_server_linux.sh"
        )
        print(f"5.) Then run this command ./deploy_ovpn_server_linux.sh")
        print(
            f"Once the process is complete, the server directory will be copied to /etc/openvpn/server"
        )
        print(f"It will Start and configure OpenVPN service")
        print(f"It will make the necessary changes to the Firewall")

    except Exception as e:
        print(f"An error occurred while packaging the server for Linux deployment: {e}")
        logging.error(f"Error packaging server for Linux: {e}")


def package_server_flexedge():
    try:
        print("Packaging OpenVPN server for deployment on FlexEdge...")

        server_dir = os.path.join(BASE_DIR, "server")
        if not os.path.exists(server_dir):
            print("Server directory not found. Please initialize the server first.")
            return

        # Create a temporary directory to hold the files for zipping
        temp_dir = os.path.join(BASE_DIR, "temp_flexedge_deploy")
        os.makedirs(temp_dir, exist_ok=True)

        # Copy the 'server' directory to the temp directory
        temp_server_dir = os.path.join(temp_dir, "server")
        shutil.copytree(server_dir, temp_server_dir)

        # Modify server.conf in temp_server_dir
        server_conf_path = os.path.join(temp_server_dir, "server.conf")
        modify_server_conf_for_flexedge(server_conf_path)

        # create a server.ovpn file by copying server.conf in the temp_server_dir
        shutil.copy(server_conf_path, os.path.join(temp_server_dir, "server.ovpn"))

        # In the temp directory create a folder named files_for_sdcard
        files_for_sdcard_dir = os.path.join(temp_dir, "files_for_sdcard")
        os.makedirs(files_for_sdcard_dir, exist_ok=True)

        # Copy these files and folder from the temp server directory to files_for_sdcard
        files_to_copy = ["ipp.txt", "openvpn-status.log", "openvpn.log"]
        folder_to_copy = "ccd"
        for file in files_to_copy:
            shutil.copy(os.path.join(temp_server_dir, file), files_for_sdcard_dir)
        shutil.copytree(
            os.path.join(temp_server_dir, folder_to_copy),
            os.path.join(files_for_sdcard_dir, folder_to_copy),
        )

        # Create the zip file
        zip_filename = os.path.join(BASE_DIR, "OpenVPN_Server_FlexEdge.zip")
        with zipfile.ZipFile(zip_filename, "w", zipfile.ZIP_DEFLATED) as zipf:
            # Walk through the temp directory and add files and directories to the zip
            for root, dirs, files in os.walk(temp_dir):
                # Add empty directories
                for dir in dirs:
                    dir_path = os.path.join(root, dir)
                    arcname = os.path.relpath(dir_path, start=temp_dir)
                    zip_info = zipfile.ZipInfo(arcname + "/")
                    zipf.writestr(zip_info, "")

                # Add files
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, start=temp_dir)
                    zipf.write(file_path, arcname)

        print(
            f"Packaged server files into '{zip_filename}'. You can transfer this zip file to the FlexEdge device and extract it there."
        )
        logging.info(f"Packaged server for FlexEdge deployment: {zip_filename}")

        # Clean up the temporary directory
        shutil.rmtree(temp_dir)

        # Print the deployment instructions
        print(f"Instructions for Deployment")
        print(
            f"1.) Open the OpenVPN_Server_FlexEdge.zip file and extract it to a directory of your choice."
        )
        print(
            f"2.) In the Server directory, you will find the server configuration file server.conf. Upload this configuration file to the FlexEdge device. Instructions in How-to guide."
        )
        print(f"3a.) Format a MicroSD card with FAT32 file system")
        print(
            f"3b.) Now you can either copy the files in the files_for_sdcard directory or Use FTP client to move the files to the E-Drive of the FlexEdge device. (Make sure formatted MicroSD card is inserted in the FlexEdge device before boot)"
        )

    except Exception as e:
        print(
            f"An error occurred while packaging the server for FlexEdge deployment: {e}"
        )
        logging.error(f"Error packaging server for FlexEdge: {e}")


def modify_server_conf_for_flexedge(server_conf_path):
    """
    Modifies the server.conf file to adjust paths for FlexEdge deployment.
    """
    try:
        # Read the existing server.conf
        with open(server_conf_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        # Define the new paths
        new_status_log = "/media/sdcard/openvpn-status.log"
        new_log_append = "/media/sdcard/openvpn.log"
        new_ccd_dir = "/media/sdcard/ccd"
        new_ipp_file = "/media/sdcard/ipp.txt"

        # Update the lines
        updated_lines = []
        for line in lines:
            if line.startswith("status "):
                updated_lines.append(f"status {new_status_log}\n")
            elif line.startswith("log-append "):
                updated_lines.append(f"log-append {new_log_append}\n")
            elif line.startswith("client-config-dir "):
                updated_lines.append(f"client-config-dir {new_ccd_dir}\n")
            elif line.startswith("ifconfig-pool-persist "):
                updated_lines.append(f"ifconfig-pool-persist {new_ipp_file}\n")
            else:
                updated_lines.append(line)

        # Write back the updated configuration
        with open(server_conf_path, "w", encoding="utf-8") as f:
            f.writelines(updated_lines)

        # Ensure ccd directory exists
        ccd_dir = os.path.join(os.path.dirname(server_conf_path), "ccd")
        if not os.path.exists(ccd_dir):
            os.makedirs(ccd_dir, exist_ok=True)

        # Create empty log files if they don't exist
        openvpn_status_log = os.path.join(
            os.path.dirname(server_conf_path), "openvpn-status.log"
        )
        openvpn_log = os.path.join(os.path.dirname(server_conf_path), "openvpn.log")
        ipp_file = os.path.join(os.path.dirname(server_conf_path), "ipp.txt")
        for filepath in [openvpn_status_log, openvpn_log, ipp_file]:
            if not os.path.exists(filepath):
                open(filepath, "w").close()

        logging.info(
            f"Modified server.conf for FlexEdge deployment at {server_conf_path}"
        )
    except Exception as e:
        logging.error(f"Failed to modify server.conf for FlexEdge: {e}")
        raise


def package_client_ewon():
    try:
        print("Packaging client for deployment on Ewon Cosy/Flexy...")

        # Ensure OpenVPN server is initialized
        server_dir = os.path.join(BASE_DIR, "server")
        if not os.path.exists(server_dir):
            print(
                "Server directory not found. Please initialize the OpenVPN server first."
            )
            return

        # Get list of existing clients
        client_names = list_current_clients()
        if not client_names:
            print("No clients found. Please generate client certificates first.")
            return

        # Display list of clients for user to select
        print("\nAvailable Clients:")
        for idx, client_name in enumerate(client_names, start=1):
            print(f"{idx}. {client_name}")
        print(f"{len(client_names) + 1}. Exit")

        # Get user selection
        while True:
            try:
                choice = int(input("Select a client to package for Ewon Cosy/Flexy: "))
                if 1 <= choice <= len(client_names):
                    client_name = client_names[choice - 1]
                    break
                elif choice == len(client_names) + 1:
                    print("Exiting client packaging menu.")
                    return
                else:
                    print("Invalid choice, please select a valid client.")
            except ValueError:
                print("Please enter a valid number.")

        # Navigate to the selected client's folder
        client_dir = os.path.join(CLIENTS_DIR, client_name)
        client_ovpn_path = os.path.join(client_dir, f"{client_name}.ovpn")
        ta_key_source_path = os.path.join(server_dir, "ta.key")

        # Ensure required files exist
        if not os.path.exists(client_ovpn_path):
            print(f"Client OVPN file not found for {client_name}.")
            return
        if not os.path.exists(ta_key_source_path):
            print("TLS authentication key (ta.key) not found in server directory.")
            return

        # Modify the client's OVPN file
        with open(client_ovpn_path, "r", encoding="utf-8") as ovpn_file:
            lines = ovpn_file.readlines()

        with open(client_ovpn_path, "w", encoding="utf-8") as ovpn_file:
            inside_tls_auth = False
            for line in lines:
                if line.strip() == "<tls-auth>":
                    inside_tls_auth = True
                elif line.strip() == "</tls-auth>":
                    inside_tls_auth = False
                    continue  # Skip writing the closing tag
                if not inside_tls_auth:
                    ovpn_file.write(line)
            # Append the new TLS-auth directive
            ovpn_file.write("tls-auth /usr/ta.key\n")

        print(
            f"Updated OVPN file for {client_name} to use Ewon Cosy/Flexy-compatible configuration."
        )

        # Copy the ta.key file to the client's directory
        ta_key_dest_path = os.path.join(client_dir, "ta.key")
        shutil.copy(ta_key_source_path, ta_key_dest_path)
        print(f"Copied ta.key file to {client_dir}.")

        # Create a zip file for deployment
        zip_filename = os.path.join(
            client_dir, f"ewon_flexy-cosy_deploy__{client_name}.zip"
        )
        with zipfile.ZipFile(zip_filename, "w", zipfile.ZIP_DEFLATED) as zipf:
            zipf.write(client_ovpn_path, arcname=f"{client_name}.ovpn")
            zipf.write(ta_key_dest_path, arcname="ta.key")

        print(
            f"Packaged client files into '{zip_filename}' for Ewon Cosy/Flexy deployment."
        )
        logging.info(
            f"Packaged client {client_name} for Ewon Cosy/Flexy: {zip_filename}"
        )

    except Exception as e:
        logging.error(f"Error packaging client for Ewon Cosy/Flexy: {e}")
        print(f"An error occurred while packaging the client: {e}")


def main():
    server_initialized = False

    while True:
        server_config = load_server_config()
        server_initialized = server_config is not None and server_config.get(
            "server_initialized", False
        )

        print("\nOpenVPN Setup Menu:")
        if not server_initialized:
            print("1. Initialize OpenVPN server")
        else:
            print("1. Initialize OpenVPN server (Already Initialized) - Disabled")
        print("2. Generate Additional Client Certificates and Configurations")
        print("3. Revoke existing clients")
        print("4. Package Server for Deployment on Windows PC")
        print("5. Package Server for Deployment on Linux PC")
        print("6. Package Server for Deployment on FlexEdge")
        print("7. Package Client for Deployment on Ewon Cosy/Flexy")
        print("8. Exit")

        choice = input("Enter your choice: ")

        if choice == "1" and not server_initialized:
            initialize_server()
            server_initialized = True  # Set to True after successful initialization
        elif choice == "1" and server_initialized:
            print("OpenVPN server is already initialized.")
        elif choice == "2":
            if not server_initialized:
                print("Please initialize OpenVPN server first.")
            else:
                generate_client_certificates()
        elif choice == "3":
            if not server_initialized:
                print("Please initialize OpenVPN server first.")
            else:
                revoke_clients()
        elif choice == "4":
            if not server_initialized:
                print("Please initialize OpenVPN server first.")
            else:
                package_server_windows()
        elif choice == "5":
            if not server_initialized:
                print("Please initialize OpenVPN server first.")
            else:
                package_server_linux()
        elif choice == "6":
            if not server_initialized:
                print("Please initialize OpenVPN server first.")
            else:
                package_server_flexedge()
        elif choice == "7":
            if not server_initialized:
                print("Please initialize OpenVPN server first.")
            else:
                package_client_ewon()
        elif choice == "8":
            print("Exiting...")
            break
        else:
            print("Invalid choice, please try again.")


if __name__ == "__main__":
    main()
