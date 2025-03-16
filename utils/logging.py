import logging
import logging.handlers

def setup_logger(log_file="ftp_server.log"):
    """Setup and return a logger instance."""
    logger = logging.getLogger("FTP")
    logger.setLevel(logging.DEBUG)

    # Prevent duplicate handlers
    if not logger.handlers:
        handler = logging.handlers.RotatingFileHandler(
            log_file, maxBytes=1024 * 1024, backupCount=5
        )
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger

# Global logger instance (can be imported directly)
logger = setup_logger()
