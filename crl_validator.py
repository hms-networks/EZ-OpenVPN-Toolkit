import os
import subprocess
import re
from datetime import datetime

# Adjust paths as necessary
BASE_DIR = r"C:\Users\rambo\OneDrive\Desktop\workspace\EZ-OpenVPN-Toolkit"
OPENSSL_PATH = os.path.join(BASE_DIR, "needed_binaries", "openssl.exe")

# Ask user where crl file is located, allow them to copy/paste the path to the prompt
CRL_PATH = input("Enter the full path to the CRL file: ")

def check_crl_dates():
    """
    Checks the creation date (from the filesystem) and the expiry date (from CRL metadata)
    of the 'crl.pem' file.
    """
    # 1. Verify that crl.pem exists
    if not os.path.exists(CRL_PATH):
        print(f"CRL file not found at: {CRL_PATH}")
        return

    # 2. Get file creation time from OS metadata
    file_stats = os.stat(CRL_PATH)
    creation_date = datetime.fromtimestamp(file_stats.st_ctime)

    # 3. Use openssl to parse CRL metadata
    #    We'll capture the text output so we can search for Last Update / Next Update lines
    try:
        result = subprocess.run(
            [OPENSSL_PATH, "crl", "-in", CRL_PATH, "-text", "-noout"],
            capture_output=True,
            text=True,
            check=True
        )
    except subprocess.CalledProcessError as e:
        print("Error running openssl command:", e)
        print("stderr:", e.stderr)
        return

    output = result.stdout

    # 4. Extract Last Update and Next Update using regular expressions
    #    Example lines from openssl crl -text output:
    #        Last Update   : Aug 16 17:19:34 2023 GMT
    #        Next Update   : Sep 15 17:19:34 2024 GMT
    last_update_match = re.search(r'Last Update\s*:\s*(.*)', output)
    next_update_match = re.search(r'Next Update\s*:\s*(.*)', output)

    last_update_str = last_update_match.group(1).strip() if last_update_match else "Not found"
    next_update_str = next_update_match.group(1).strip() if next_update_match else "Not found"

    # (Optional) Convert those date strings to Python datetimes if you need to compare them:
    # E.g., dates are typically in the format "Aug 16 17:19:34 2023 GMT"
    # You can parse them with datetime.strptime + strip out the "GMT":
    #
    #   last_update_dt = datetime.strptime(last_update_str.replace(" GMT", ""), "%b %d %H:%M:%S %Y")
    #   next_update_dt = datetime.strptime(next_update_str.replace(" GMT", ""), "%b %d %H:%M:%S %Y")

    # 5. Print or return the information
    print("============== CRL INFO ==============")
    print(f"File Path          : {CRL_PATH}")
    print(f"Creation Date (OS) : {creation_date}")
    print(f"Last Update (CRL)  : {last_update_str}")
    print(f"Next Update (CRL)  : {next_update_str}")
    print("======================================")

if __name__ == "__main__":
    check_crl_dates()
