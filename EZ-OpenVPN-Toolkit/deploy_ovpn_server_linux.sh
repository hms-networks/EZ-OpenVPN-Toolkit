#deploy_ovpn_server_linux.sh

#!/bin/bash

# Ensure system is using systemd
if [ ! -d /etc/systemd/system ]; then
    echo "This script is only for systemd systems" 1>&2
    exit 2
fi

# Ensure script is run as root
if [ "$(id -u)" != "0" ]; then
    echo "This script must be run as root" 1>&2
    exit 1
fi

# Ensure required commands are available
for cmd in unzip systemctl awk grep date firewall-cmd; do
    if ! command -v $cmd > /dev/null; then
        echo "Error: $cmd is not installed or not in the PATH" 1>&2
        exit 1
    fi
done

# Detect the distribution and package manager
if grep -Ei 'debian|ubuntu' /etc/os-release > /dev/null; then
    pkg_mgr="apt"
elif grep -Ei 'fedora|rhel|centos|rocky' /etc/os-release > /dev/null; then
    if command -v dnf >/dev/null; then
        pkg_mgr="dnf"
    elif command -v yum >/dev/null; then
        pkg_mgr="yum"
    fi

    # Set SELinux to permissive mode if RHEL-based system is detected
    echo "Detected RHEL-based system. Setting SELinux to permissive..."
    sed -i 's/^SELINUX=.*/SELINUX=permissive/' /etc/selinux/config
    setenforce 0
    echo "SELinux is now in permissive mode. Reboot is recommended for the change to take full effect."
else
    echo "This script is only for Debian/Ubuntu or RHEL-based systems like Fedora, CentOS, and Rocky" 1>&2
    exit 1
fi

# Check if firewalld is installed and active, install if necessary
if ! command -v firewall-cmd >/dev/null; then
    echo "firewalld is not installed. Installing firewalld..."
    if [ "$pkg_mgr" = "apt" ]; then
        apt update && apt install -y firewalld
    else
        $pkg_mgr install -y firewalld
    fi
fi

# Enable and start firewalld if it's not already running
if ! systemctl is-active --quiet firewalld; then
    echo "Starting firewalld..."
    systemctl enable firewalld
    systemctl start firewalld
fi

# Check if firewalld is running successfully
if systemctl is-active --quiet firewalld; then
    echo "firewalld is running"
else
    echo "Error: firewalld is not active or failed to start." 1>&2
    exit 1
fi

# Ensure OpenVPN is installed
if ! command -v openvpn >/dev/null; then
    echo "Error: OpenVPN is not installed. Attempting to install OpenVPN..." 1>&2
    if [ "$pkg_mgr" = "apt" ]; then
        apt update && apt install -y openvpn
    else
        $pkg_mgr install -y openvpn
    fi
fi

# Check if new server.conf exists in the current directory's server subdirectory
if [ ! -f server/server.conf ]; then
    echo "Error: No server.conf found in the server subdirectory." 1>&2
    exit 1
fi

# Extract timestamp from the new server.conf
new_timestamp=$(grep -m 1 "^# [0-9]\{4\}-[0-9]\{2\}-[0-9]\{2\} [0-9]\{2\}:[0-9]\{2\}:[0-9]\{2\} #" server/server.conf | awk '{print $2, $3}')

# Check if the timestamp was found
if [ -z "$new_timestamp" ]; then
    echo "Error: No timestamp found in the new server.conf" 1>&2
    exit 1
fi

# Convert new_timestamp to epoch
new_epoch=$(date -d "$new_timestamp" +"%s")

# Check if there is an existing server.conf to compare with
if [ -f /etc/openvpn/server/server.conf ]; then
    # Extract timestamp from the old server.conf
    old_timestamp=$(grep -m 1 "^# [0-9]\{4\}-[0-9]\{2\}-[0-9]\{2\} [0-9]\{2\}:[0-9]\{2\}:[0-9]\{2\} #" /etc/openvpn/server/server.conf | awk '{print $2, $3}')

    # Check if the old timestamp exists
    if [ -n "$old_timestamp" ]; then
        # Convert old_timestamp to epoch
        old_epoch=$(date -d "$old_timestamp" +"%s")

        # Compare the timestamps
        if [ "$new_epoch" -le "$old_epoch" ]; then
            echo "The existing server.conf in /etc/openvpn/server is newer or the same. No update required." 1>&2
            exit 0
        fi
    else
        echo "Warning: No timestamp found in the existing server.conf. Proceeding with update." 1>&2
    fi
else
    echo "No existing server.conf found in /etc/openvpn/server. Proceeding with update." 1>&2
fi

# Stop and disable any running OpenVPN services
if systemctl is-active --quiet openvpn-server@server.service; then
    echo "Stopping and disabling existing OpenVPN service..."
    systemctl stop openvpn-server@server.service
    systemctl disable openvpn-server@server.service
fi

# Backup old configuration and logs
backup_dir="/etc/openvpn/server/backup_$(date +%F_%T)"
mkdir -p "$backup_dir"
for i in ccd ipp.txt server.conf openvpn.log openvpn-status.log; do
    if [ -e /etc/openvpn/server/$i ]; then
        mv /etc/openvpn/server/$i "$backup_dir"
    fi
done

# Move the new server.conf and other files
mv server/ccd server/server.conf /etc/openvpn/server
touch /etc/openvpn/server/ipp.txt /etc/openvpn/server/openvpn.log /etc/openvpn/server/openvpn-status.log

# Extract port and protocol from server.conf
port=$(grep "^port" /etc/openvpn/server/server.conf | awk '{print $2}')
proto=$(grep "^proto" /etc/openvpn/server/server.conf | awk '{print $2}')

# Add firewalld rules if they don't already exist
if ! firewall-cmd --list-ports | grep -q "$port/$proto"; then
    echo "Adding firewalld rule for port $port/$proto"
    firewall-cmd --zone=public --add-port=$port/udp --permanent  # Forces UDP based on server.conf
    firewall-cmd --reload
fi

# Enable and start the OpenVPN service
systemctl enable openvpn-server@server.service

if systemctl is-active --quiet openvpn-server@server.service; then
    echo "Restarting OpenVPN server..."
    systemctl restart openvpn-server@server.service
else
    systemctl start openvpn-server@server.service
fi

# Check if the OpenVPN service started successfully
if systemctl is-active --quiet openvpn-server@server.service; then
    echo "OpenVPN server started successfully"
else
    echo "Failed to start OpenVPN server" 1>&2
    exit 1
fi
