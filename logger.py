# logger.py

import logging
import os
from helpers import get_base_dir

def setup_logging():
    """
    Sets up logging configuration.
    - Logs all messages of level INFO and above to 'master.log' file.
    - Does not output logs to the console.
    """
    BASE_DIR = get_base_dir()
    log_filename = os.path.join(BASE_DIR, 'master.log')

    # Create a custom logger
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)  # Set the lowest severity level for the logger

    # Remove any existing handlers
    if logger.hasHandlers():
        logger.handlers.clear()

    # Create handlers
    # File handler to write logs to a file
    file_handler = logging.FileHandler(log_filename)
    file_handler.setLevel(logging.INFO)

    # Create formatters and add them to the handlers
    formatter = logging.Formatter('%(asctime)s %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)

    # Add handlers to the logger
    logger.addHandler(file_handler)

    # Optionally, if you want to log errors to the console, uncomment the following lines:
    # console_handler = logging.StreamHandler()
    # console_handler.setLevel(logging.ERROR)
    # console_handler.setFormatter(formatter)
    # logger.addHandler(console_handler)
