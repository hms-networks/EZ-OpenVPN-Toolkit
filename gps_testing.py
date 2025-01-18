#!/usr/bin/python3

import time

# Function to parse NMEA sentences
def parse_nmea_sentence(sentence):
    parts = sentence.split(',')
    sentence_type = parts[0][1:]  # Remove the leading '$'
    
    if sentence_type == "GPRMC":
        return parse_gprmc(parts)
    elif sentence_type == "GPGGA":
        return parse_gpgga(parts)
    elif sentence_type == "GPGLL":
        return parse_gpgll(parts)
    else:
        return None

# Function to parse GPRMC sentences
def parse_gprmc(parts):
    # Recommended minimum navigation information
    status = parts[2]  # A = Active, V = Void
    speed_knots = parts[7]  # Speed over ground in knots
    
    if speed_knots:
        speed_knots = float(speed_knots)
        speed_kph = speed_knots * 1.852  # Convert knots to km/h
        speed_mph = speed_knots * 1.15078  # Convert knots to mph
        return f"Status: {'Valid' if status == 'A' else 'Invalid'}, Speed: {speed_knots:.2f} knots ({speed_kph:.2f} km/h, {speed_mph:.2f} mph)"
    else:
        return f"Status: {'Valid' if status == 'A' else 'Invalid'}, Speed: N/A"

# Function to parse GPGGA sentences
def parse_gpgga(parts):
    # Global Positioning System Fix Data
    satellites = parts[7]  # Number of satellites
    return f"Satellites: {satellites if satellites else 'N/A'}"

# Function to parse GPGLL sentences
def parse_gpgll(parts):
    # Geographic Position - Latitude/Longitude
    latitude = parts[1]
    longitude = parts[3]
    return f"Latitude: {latitude or 'N/A'}, Longitude: {longitude or 'N/A'}"

# Main script to process NMEA file
def process_nmea_file_continuously(filename):
    try:
        while True:
            with open(filename, 'r') as file:
                for line in file:
                    result = parse_nmea_sentence(line.strip())
                    if result:
                        print(result)
            time.sleep(1)  # Add a delay to prevent overwhelming the system
    except FileNotFoundError:
        print(f"Error: File '{filename}' not found.")
    except KeyboardInterrupt:
        print("\nTerminating script.")
    except Exception as e:
        print(f"An error occurred: {e}")

# Run the script
if __name__ == "__main__":
    input_file = 'gps_data.txt'  # Replace with your file name
    process_nmea_file_continuously(input_file)
