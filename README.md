# EZOpenVPNToolkit

**EZOpenVPNToolkit** is a comprehensive tool designed to simplify the process of setting up a self-provisioned OpenVPN Certificate Authority (CA), server, and multiple client configurations. It supports various platforms including FlexEdge devices, Ewon Cosy/Flexy, Anybus Defender, Windows, and Linux systems.

## Table of Contents

- [EZOpenVPNToolkit](#ezopenvpntoolkit)
  - [Table of Contents](#table-of-contents)
  - [Features](#features)
  - [Supported Products](#supported-products)
  - [Requirements](#requirements)
  - [Quick Setup Overview](#quick-setup-overview)
  - [Installation](#installation)
  - [Usage Guide](#usage-guide)
    - [1. Run EZOpenVPNToolkit](#1-run-ezopenvpntoolkit)
    - [2. Initialize the OpenVPN Server](#2-initialize-the-openvpn-server)
    - [3. Generate Additional Client Certificates and Configurations](#3-generate-additional-client-certificates-and-configurations)
    - [4. Revoke Existing Clients](#4-revoke-existing-clients)
    - [5. Package the Server for Deployment](#5-package-the-server-for-deployment)
    - [6. Deploying Server on Windows or Linux](#6-deploying-server-on-windows-or-linux)
      - [For Windows](#for-windows)
      - [For Linux](#for-linux)
      - [For FlexEdge](#for-flexedge)
      - [For Anybus Defender](#for-anybus-defender)
    - [Deploying Client Configurations](#deploying-client-configurations)
      - [For Windows PC](#for-windows-pc)
      - [For FlexEdge](#for-flexedge-1)
      - [For Ewon Cosy/Flexy](#for-ewon-cosyflexy)
  - [Additional Notes](#additional-notes)
  - [License](#license)

## Features

- Simplifies OpenVPN server and client setup across multiple platforms.
- Automates the generation of CA, server, and client certificates.
- Supports deployment on Windows, Linux, FlexEdge devices, and more.
- Provides easy client revocation and configuration management.
- Packages server and client configurations for easy deployment.

## Supported Products

This toolkit works with the following products:

- FlexEdge Server/Client (DA50A and DA70A)
- Ewon Cosy/Flexy
- Anybus Defender
- Windows 10/11 Server/Client
- Debian or RHEL-based Linux OS Server/Client (Debian/Ubuntu/RHEL/Fedora/etc.)

## Requirements

- **EZOpenVPNToolkit.exe** (Runs on Windows 10/11)
- For FlexEdge Devices: **Crimson 3.2** (Tested on version 3.2.1028.0)
- **FTP Client software** (e.g., WinSCP)

## Quick Setup Overview

1. **Run** `EZOpenVPNToolkit.exe`.
2. **Initialize** the OpenVPN Server.
3. **Generate** Additional Client Configurations as needed.
4. **Revoke** Clients if necessary.
5. **Package** Server for Deployment on Windows/Linux/FlexEdge.
6. **Deploy** OpenVPN on the desired server and client devices.

---

## Installation

1. **Download** the `EZOpenVPNToolkit.exe` file from the repository.
2. **Ensure** you are running Windows 10/11.
3. **Install** any required software for your specific devices (e.g., Crimson 3.2 for FlexEdge).

---

## Usage Guide

### 1. Run EZOpenVPNToolkit

- Double-click on the `EZOpenVPNToolkit.exe` file to start the program.

### 2. Initialize the OpenVPN Server

1. **Select Option 1** to initialize the OpenVPN server.
2. **Enter Certificate Authority Details** when prompted:
     - **Country Code (2-letter code, e.g., `US` for United States, `IN` for India)**
         **Note:** The **Country Code must be exactly 2 letters**. If you enter a code longer or shorter than 2 letters, you will encounter an error during the setup process. Refer to the [ISO 3166-1 alpha-2 standard](https://en.wikipedia.org/wiki/List_of_ISO_3166_country_codes) for valid country codes.
     - **State or Province Name** (e.g., `MO`)
     - **Locality Name** (e.g., `Mineral Point`)
     - **Organization Name** (e.g., `GregNet`)
     - **Organizational Unit Name** (e.g., `IT`)
     - **Email Address** (e.g., `gregory.allen.whitlock@gmail.com`)
3. **Review Entered Details:**
     **Confirm** that all details are correct before proceeding.
4. **Generate Certificate Authority Files and OpenVPN Configuration:**
     - **OpenVPN Tunnel Subnet** (e.g., `10.0.0.0/24`)
     - **Server LAN Subnet** (e.g., `10.0.1.0/24`)
     **Note:** Generating the Diffie-Hellman parameters (`dh.pem` file) can take several minutes. Please be patient during this process.
5. **Specify Client Details:**
     - Enter the **number of clients**.
     - Provide a **unique name** for each client.
     - If any client has a unique **subnet to push over the VPN tunnel**, specify it here.
     Subnet entries are validated to prevent overlaps.

### 3. Generate Additional Client Certificates and Configurations

1. **Select Option 2** from the main menu.
2. **Enter Client Details:**
     - Specify the **number of additional clients**.
     - Provide unique **names** for each client.
     - **Specify subnets** if clients need specific subnets pushed.
     **Note:** This will update the Certificate Revocation List (CRL) and the server configuration. You will need to redeploy the updated server configuration to your OpenVPN server.

### 4. Revoke Existing Clients

1. **Select Option 3** from the menu.
2. **Choose the Client** you wish to revoke.
3. **Confirm** the revocation.
     - The client’s configuration, certificates, and routes will be removed from the setup.
     - The CRL and server configuration will be updated. Redeploy the server configuration to your OpenVPN server.

### 5. Package the Server for Deployment

- **Select Option 4** for Windows, **Option 5** for Linux, or **Option 6** for FlexEdge.
- A zip file (`OpenVPN_Server_Windows.zip`, `OpenVPN_Server_Linux.zip`, or `OpenVPN_Server_FlexEdge.zip`) will be generated.
- **Follow the deployment instructions** provided by the program to set up the server on your desired platform.

### 6. Deploying Server on Windows or Linux

#### For Windows

1. **Transfer** `OpenVPN_Server_Windows.zip` to the Windows server.
2. **Extract** the zip file to a directory of your choice.
3. **Open PowerShell** in the extracted directory.
4. **Run**:

        
        powershell -ExecutionPolicy Bypass -File deploy_ovpn_server_on_win10-11.ps1

        Process Includes:
        - Starting the OpenVPN service.
        - Enabling IP routing.
        - Configuring Routing and Remote Access.
        - Setting up a scheduled task for startup.

#### For Linux

1. Transfer `OpenVPN_Server_Linux.zip` to the Linux server (tested on Fedora 40 and Debian 12).
2. Extract the zip file.
3. Run the following commands:

        chmod +x deploy_ovpn_server_linux.sh
        sudo ./deploy_ovpn_server_linux.sh

        Process Includes:
        - Installing OpenVPN.
        - Configuring firewall settings.
        - Starting the OpenVPN service.

#### For FlexEdge

1. Extract `OpenVPN_Server_FlexEdge.zip` to a folder of your choice.
2. Locate the `server.conf` file in the server folder.
3. Use Crimson or the Web GUI:
     - Navigate to Device Configuration > Tunnels > OpenVPN Tunnels.
     - Add the server configuration file.
4. Configure VPN Settings:
     - Go to Device > Configuration > Software Configuration > VPN1.
     - Set Tunnel Mode to Config File and choose the appropriate server configuration.
5. Prepare MicroSD Card:
     - Format a MicroSD card (e.g., 32GB) as FAT32.
     - Copy all files and folders from the `files_for_sdcard` folder to the root of the MicroSD card.
     - Insert the MicroSD card into the FlexEdge device and power it on.

#### For Anybus Defender

1. Access the device's web interface.
2. Upload Certificates:
     - Navigate to System > Cert Manager.
     - Add the `ca.crt` and `ca.key` files from your ca folder.
     - Under Certificates, copy and paste your `server.crt` and `server.key` files from your server folder.
     - Under Certificate Revocation, copy your `crl.pem` file from your server folder.
3. Configure VPN:
     - Go to VPN > OpenVPN and add a new server.
     - Set the following settings to match your initial configuration:
         - **Server Mode:** Remote Access (SSL/TLS)
         - **Protocol:** (As chosen during setup)
         - **Device Mode:** tun – Layer 3 Tunnel Mode
         - **Interface:** WAN
         - **Local Port:** (As chosen during setup)
         - **TLS Configuration:** Use a TLS Key
         - **TLS Key:** Copy and paste the contents of the generated `ta.key`
         - **TLS Key Usage Mode:** TLS Authentication
         - **TLS keydir direction:** Direction 0
         - **Peer Certificate Authority:** Select your CA file
         - **Peer Cert Revocation List:** Select your CRL file
         - **Server Certificate:** Select your server certificate
         - **DH Parameter Length:** 2048 bit
         - **Data Encryption Negotiation:** Enabled
         - **Data Encryption Algorithms:** Include the data-ciphers selected during server initialization
         - **Fallback Data Encryption Algorithm:** Select the weakest cipher from your choices
         - **Auth Digest Algorithm:** SHA1 (default)
         - **IPv4 Tunnel Network:** OpenVPN Tunnel Subnet
         - **IPv4 Local Network:** Server LAN Subnet
         - **Inter-client communication:** Enabled
         - **Topology:** subnet
     - Save the configuration.

### Deploying Client Configurations

#### For Windows PC

1. Copy the client configuration file (`.ovpn`) to `C:\Program Files\OpenVPN\config`.
2. Open OpenVPN-GUI as administrator.
3. Right-click on the icon in the system tray.
4. Select the new configuration and click Connect.

#### For FlexEdge

1. Use Crimson or the Web GUI:
     - Navigate to Device Configuration > Tunnels > OpenVPN Tunnels.
     - Add the client configuration file.
2. Configure VPN Settings:
     - Go to Device > Configuration > Software Configuration > VPN1.
     - Set Tunnel Mode to Config File and choose the appropriate client configuration.

#### For Ewon Cosy/Flexy

1. Select Option 7 in the EZOpenVPNToolkit executable to package the client for Ewon devices.
2. Locate the generated zip file in the client's folder.
3. Using an FTP client, connect to your Ewon device.
4. Upload the `.ovpn` file and `ta.key` to the `/usr` directory.
5. Configure the Device:
     - Access the web GUI of the Ewon device.
     - Navigate to Setup > System > Storage > Tabular Edition.
     - Edit `COM cfg`:
         - Set `VPNCfgFile` to point to your OpenVPN file (e.g., `/usr/gregewoncosy.ovpn`).
         - Change `VPNCnxType` value to `2` to start OpenVPN connections.
     - Save the configuration.

## Additional Notes

- **Server Config Updates:** After each client generation or revocation, the server configuration is updated. Redeploy the server configuration if you're running it on a separate device.
- **Firewall Configuration:** Ensure that the necessary ports and protocols are open in your firewall settings.
- **Logs:** If you encounter any errors, check the `master.log` file located in the same directory as the `EZOpenVPNToolkit.exe` for detailed information.
- **Patience:** Some processes, like generating the Diffie-Hellman parameters, can take several minutes.

## License

This project is licensed under the MIT License.
