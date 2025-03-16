import argparse
from ftp import FTP
from utils.utils import get_db_connection
from auth import add_default_user
from client_manager import ClientManager
import logging
import logging.handlers
import threading


def main():
    parser = argparse.ArgumentParser(description="FTP Server with FastAPI Support")
    parser.add_argument("--ftp_ip", type=str, default="0.0.0.0", help="FTP server IP address (default: 0.0.0.0)")
    parser.add_argument("--ftp_port", type=int, default=21, help="FTP server port (default: 21)")
    parser.add_argument("--shared_dir", type=str, default="shared", help="Shared directory for FTP server (default: shared)")
    parser.add_argument("--log_file", type=str, default="ftp_server.log", help="Log file for FTP server (default: ftp_server.log)")
    args = parser.parse_args()

    # Database initialization (same as original)
    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS User (
            user_id INT PRIMARY KEY,
            username VARCHAR(255) NOT NULL,
            group_id INT,
            hash_password BLOB,
            home_dir VARCHAR(255),
            permissions VARCHAR(255),
            FOREIGN KEY (group_id) REFERENCES userGroup(group_id)
        );
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS FileOrDirectory (
            id INT PRIMARY KEY,
            path VARCHAR(255) NOT NULL,
            owner_id INT,
            group_id INT,
            owner_perms VARCHAR(255),
            group_perms VARCHAR(255),
            public_perms VARCHAR(255),
            parent_id INT,
            FOREIGN KEY (owner_id) REFERENCES User(user_id),
            FOREIGN KEY (group_id) REFERENCES userGroup(group_id),
            FOREIGN KEY (parent_id) REFERENCES FileOrDirectory(id)
        );
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS userGroup (
            group_id INT PRIMARY KEY,
            group_name VARCHAR(255) NOT NULL
        );
        """
    )

    connection.commit()
    cursor.close()
    connection.close()

    add_default_user()
    logger = logging.getLogger("FTP")
    logger.setLevel(logging.DEBUG)
    handler = logging.handlers.RotatingFileHandler(
        args.log_file, maxBytes=1024 * 1024, backupCount=5
    )
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    client_manager = ClientManager(logger=logger)
    ftp_server = FTP(
        host=args.ftp_ip,
        port=args.ftp_port,
        shared_dir=args.shared_dir,
        ClientManager=client_manager,
    )

    ftp_server.start()

if __name__ == "__main__":
    main()