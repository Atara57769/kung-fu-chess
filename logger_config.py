import logging
import os
import sys

def setup_logging(default_level=logging.INFO):
    """Sets up the global logging configuration."""
    log_format = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    
    # We can write to stderr by default.
    logging.basicConfig(
        level=default_level,
        format=log_format,
        handlers=[
            logging.StreamHandler(sys.stderr)
        ]
    )
