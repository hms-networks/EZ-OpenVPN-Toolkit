import socket

# Define management interface parameters
MANAGEMENT_HOST = '10.0.1.1'  # Replace with actual IP of your OpenVPN server
MANAGEMENT_PORT = 7505         # Replace with actual port of the management interface
TIMEOUT = 5                    # Set a 5-second timeout for socket connections
BUFFER_SIZE = 4096             # Set a larger buffer size for receiving data

def get_clients_status():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(TIMEOUT)  # Set a timeout for the socket connection
    try:
        print(f"Connecting to OpenVPN management interface at {MANAGEMENT_HOST}:{MANAGEMENT_PORT}")
        s.connect((MANAGEMENT_HOST, MANAGEMENT_PORT))

        # Receive the welcome message
        welcome_msg = s.recv(BUFFER_SIZE)
        print(f"Received welcome message: {welcome_msg.decode('utf-8')}")

        # Send the 'status' command to the management interface
        print("Sending 'status' command...")
        s.sendall(b'status\n')

        # Receive and accumulate the response
        response = b""
        while True:
            data = s.recv(BUFFER_SIZE)
            if not data:
                break
            response += data

            # Debug: print the length of the received data chunk
            print(f"Received {len(data)} bytes of data...")

            # Check if the response contains the "END" marker, signaling the end of the response
            if b"END" in data:
                print("Received the full response, ending reception.")
                break

        # Decode the response into a string
        response = response.decode('utf-8')
        print("Complete response received.")

        # Initialize client and routing lists
        clients = []
        routing_info = []

        # Split the response line-by-line for easier processing
        lines = response.splitlines()
        current_section = None  # To track if we're in CLIENT_LIST or ROUTING_TABLE

        for line in lines:
            # Skip headers and focus on the data
            if line.startswith("HEADER"):
                continue

            # Detect sections (CLIENT_LIST, ROUTING_TABLE, etc.)
            if line.startswith("CLIENT_LIST"):
                current_section = "CLIENT_LIST"
                client_data = line.split(',')
                if len(client_data) >= 8:
                    client = {
                        'common_name': client_data[1],
                        'real_address': client_data[2],
                        'virtual_address': client_data[3],
                        'bytes_received': client_data[5],
                        'bytes_sent': client_data[6],
                        'connected_since': client_data[7],
                    }
                    clients.append(client)

            elif line.startswith("ROUTING_TABLE"):
                current_section = "ROUTING_TABLE"
                routing_data = line.split(',')
                if len(routing_data) >= 5:
                    route = {
                        'virtual_address': routing_data[1],
                        'common_name': routing_data[2],
                        'real_address': routing_data[3],
                        'last_ref': routing_data[4],
                    }
                    routing_info.append(route)

            elif line.startswith("GLOBAL_STATS"):
                current_section = "GLOBAL_STATS"
                continue

        # Add routing table info to the corresponding client entries
        for client in clients:
            for route in routing_info:
                if client['common_name'] == route['common_name']:
                    client['virtual_address'] = route['virtual_address']
                    client['last_ref'] = route['last_ref']

        return clients

    except socket.timeout:
        print("Error: Connection to the OpenVPN management interface timed out.")
        return []
    except Exception as e:
        print(f"Error: {e}")
        return []
    finally:
        # Always close the socket connection, even if an error occurs
        s.close()

# Example usage: Retrieve and display client connection status
def display_client_status():
    clients = get_clients_status()
    if clients:
        print(f"Total clients connected: {len(clients)}")
        for client in clients:
            print(f"Client: {client['common_name']}")
            print(f"  Real Address: {client['real_address']}")
            print(f"  Virtual Address: {client.get('virtual_address', 'N/A')}")
            print(f"  Bytes Received: {client['bytes_received']}")
            print(f"  Bytes Sent: {client['bytes_sent']}")
            print(f"  Connected Since: {client['connected_since']}")
            print(f"  Last Ref: {client.get('last_ref', 'N/A')}\n")
    else:
        print("No clients are connected.")

# Run the example
if __name__ == "__main__":
    display_client_status()
