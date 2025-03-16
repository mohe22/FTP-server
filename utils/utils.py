import sqlite3
from datetime import datetime

DATABASE_FILE = "my_database.db"


def get_db_connection():
    """Create a new database connection."""
    connection = sqlite3.connect(DATABASE_FILE)
    connection.row_factory = sqlite3.Row  # Enable dictionary-like access to rows
    return connection

def format_time(timestamp):
        """
        Format a timestamp into a human-readable string.
        :param timestamp: The timestamp from os.stat.
        :return: A formatted time string.
        """

        return datetime.fromtimestamp(timestamp).strftime("%b %d %H:%M")
