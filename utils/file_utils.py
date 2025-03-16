import os
from datetime import datetime
import stat


def get_permissions(mode):
    """
    Get file permissions in a human-readable format (e.g., 'drwxr-xr-x').
    :param mode: File mode (from os.stat().st_mode).
    :return: String representing file permissions.
    """
    permissions = [
        "d" if stat.S_ISDIR(mode) else "-",  # Directory or file
        "r" if mode & 0o400 else "-",  # Owner read
        "w" if mode & 0o200 else "-",  # Owner write
        "x" if mode & 0o100 else "-",  # Owner execute
        "r" if mode & 0o040 else "-",  # Group read
        "w" if mode & 0o020 else "-",  # Group write
        "x" if mode & 0o010 else "-",  # Group execute
        "r" if mode & 0o004 else "-",  # Others read
        "w" if mode & 0o002 else "-",  # Others write
        "x" if mode & 0o001 else "-",  # Others execute
    ]
    return "".join(permissions)


def format_time(timestamp):
    """
    Format a timestamp into a human-readable string.
    :param timestamp: Timestamp (e.g., from os.stat().st_mtime).
    :return: Formatted time string.
    """
    return datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")


def format_size(size):
    """
    Convert file size into a human-readable format (e.g., bytes, KB, MB, GB).
    """
    if size < 1024:
        return f"{size} B"
    elif size < 1024 * 1024:
        return f"{size / 1024:.2f} KB"
    elif size < 1024 * 1024 * 1024:
        return f"{size / (1024 * 1024):.2f} MB"
    else:
        return f"{size / (1024 * 1024 * 1024):.2f} GB"

def list_files(directory):
    try:
       
        if directory.startswith("/"):
            directory = directory[1:]
        if not os.path.exists(directory):
            return f"Error: Directory '{directory}' does not exist." 
        files = os.listdir(directory)
        file_list = []

        for file in files:
            file_path = os.path.join(directory, file)
            file_stat = os.stat(file_path)

            # Get file permissions (like 'drwxr-xr-x')
            permissions = get_permissions(file_stat.st_mode)

            # Get the number of hard links
            nlinks = file_stat.st_nlink

            # Get the owner and group (you can use `pwd` and `grp` modules for names)
            owner = file_stat.st_uid
            group = file_stat.st_gid

            # Get fromated file size
            size = format_size(file_stat.st_size)

            # Get the last modification time
            mtime = format_time(file_stat.st_mtime)

            # Format file information
            file_info = (
                f"{permissions}\t{nlinks}\t{owner}\t{group}\t{size}\t{mtime}\t{file}"
            )
            file_list.append(file_info)

        # Join the file list into a single string
        file_list_str = "\r\n".join(file_list) + "\r\n"
        return file_list_str
    except Exception as e:
        return e


def cwd(current_dir, dir_name, root):
    if dir_name == "..":
        new_dir = os.path.dirname(current_dir)
    elif dir_name.startswith("../"):
        new_dir = os.path.normpath(os.path.join(current_dir, dir_name))
    else:
        new_dir = os.path.normpath(os.path.join(current_dir, dir_name))

    if not new_dir.startswith(root):
        response = "550 Cannot go above root directory\r\n"
    elif not os.path.isdir(new_dir):
        response = "550 Directory not found\r\n"
    else:
        response = f"250 Directory changed to {new_dir}\r\n"

    return response, new_dir


def create_directory(new_dir, username=None):
    try:
        os.mkdir(new_dir)
        response = f"257 Directory created: {new_dir}\r\n"
        log_message = f"User {username} created directory {new_dir}"
        return response, log_message
    except FileExistsError:
        response = f"550 Directory already exists\r\n"
        log_message = (
            f"User {username} failed to create directory {new_dir} (already exists)"
        )
        return response, log_message
    except PermissionError:
        response = "550 Permission denied: Cannot create directory.\r\n"
        log_message = (
            f"User {username} failed to create directory {new_dir} (permission denied)"
        )
        return response, log_message
    except Exception as e:
        response = "550 Failed to create directory.\r\n"
        log_message = (
            f"User {username} failed to create directory {new_dir} (error: {e})"
        )
        return response, log_message


def convert_line_endings(transfer_mode, data):
    if transfer_mode == "ascii":
        text = data.decode("utf-8")
        text = text.replace("\r\n", "\n")
        if os.linesep != "\n":
            text = text.replace("\n", os.linesep)
        return text.encode("utf-8")
    else:
        return data


def delete_folder(dir_name):
    try:
        os.rmdir(dir_name)
        response = f"257 Directory deleted: {dir_name}\r\n"
        log_message = f"Directory deleted: {dir_name}"
        return response, log_message
    except OSError as e:
        if "The directory is not empty" in str(e):
            response = f"550 Directory not empty: {dir_name}\r\n"
            log_message = f"Failed to delete directory {dir_name} (directory not empty)"
        elif "Permission denied" in str(e):
            response = "550 Permission denied: Cannot delete directory.\r\n"
            log_message = f"Failed to delete directory {dir_name} (permission denied)"
        elif "The system cannot find the file specified" in str(e):
            response = f"550 Directory not found: {dir_name}\r\n"
            log_message = f"Failed to delete directory {dir_name} (directory not found)"
        else:
            response = "550 Failed to delete directory.\r\n"
            log_message = f"Failed to delete directory {dir_name} (error: {e})"
        return response, log_message
    except Exception as e:
        response = "550 Failed to delete directory.\r\n"
        log_message = f"Failed to delete directory {dir_name} (error: {e})"
        return response, log_message


def upload_file(filepath, data_socket, transfer_mode):

    try:

        with open(filepath, "wb") as file:
            while True:
                chunk = data_socket.recv(1024)
                if not chunk:
                    break
                chunk = convert_line_endings(transfer_mode, chunk)
                file.write(chunk)
        response = "226 File upload successful.\r\n"
        log_message = f"File uploaded: {filepath}"
        return response, log_message
    except Exception as e:
        response = "550 Failed to upload file.\r\n"
        log_message = f"Failed to upload file {filepath}: {e}"
        return response, log_message


def delete_recursive(path):

    try:
        if os.path.isdir(path):
            for item in os.listdir(path):
                item_path = os.path.join(path, item)
                delete_recursive(item_path)
            os.rmdir(path)
        else:
            os.remove(path)
        response = f"257 Directory deleted: {path}\r\n"
        log_message = f"Deleted: {path}"
        return response, log_message
    except Exception as e:
        response = "550 Failed to delete directory.\r\n"
        log_message = f"Failed to delete {path}: {e}"
        return response, log_message


def download_file(filepath, send_socket, transfer_mode):
    try:
        with open(filepath, "rb") as file:
            while True:
                chunk = file.read(1024)
                if not chunk:
                    break
                chunk = convert_line_endings(transfer_mode, chunk)
                send_socket(chunk)
        response = "226 File download successful.\r\n"
        log_message = f"File downloaded: {filepath}"
        return response, log_message
    except FileNotFoundError:
        response = f"550 File not found: {os.path.basename(filepath)}\r\n"
        log_message = f"File not found: {filepath}"
        return response, log_message
    except PermissionError:
        response = "550 Permission denied: Cannot access file.\r\n"
        log_message = f"Permission denied: {filepath}"
        return response, log_message
    except Exception as e:
        response = "550 Failed to download file.\r\n"
        log_message = f"Failed to download file {filepath}: {e}"
        return response, log_message
