import logging

def setup_logging():
    # Create a custom logger
    logger = logging.getLogger(__name__)

    # Set the default logging level
    logger.setLevel(logging.DEBUG)

    # Create handlers
    console_handler = logging.StreamHandler()  # For logging to console
    file_handler = logging.FileHandler('app.log')  # For logging to a file

    # Set logging levels for handlers
    console_handler.setLevel(logging.DEBUG)
    file_handler.setLevel(logging.INFO)

    # Create formatters and add them to the handlers
    console_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

    console_handler.setFormatter(console_formatter)
    file_handler.setFormatter(file_formatter)

    # Add the handlers to the logger
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger
