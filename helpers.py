# Copyright (C) 2024 - 2025 HMS Industrial Network Solutions
# Software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

# helpers.py

import subprocess
import os
import logging
import sys
from config import get_base_dir

BASE_DIR = get_base_dir()


def run_command(command_list):
    """
    Runs a command using subprocess and logs the output.
    """
    try:
        result = subprocess.run(
            command_list,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
        )
        logging.info(f"Command executed successfully: {' '.join(command_list)}")
        logging.debug(result.stdout)
    except subprocess.CalledProcessError as e:
        logging.error(f"Command failed: {' '.join(command_list)}")
        logging.error(f"Exit code: {e.returncode}")
        logging.error(f"Output: {e.stderr}")
        raise e


def create_directory(path):
    """
    Creates a directory if it doesn't exist.
    """
    if not os.path.exists(path):
        os.makedirs(path)
        logging.info(f"Directory created: {path}")
    else:
        logging.debug(f"Directory already exists: {path}")
