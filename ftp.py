import socket
import os
import threading
from utils.file_utils import list_files,cwd,create_directory,upload_file,download_file,delete_recursive,delete_folder
from auth import authenticate
#TODO: parallel upload/download , port forwarding, enable logging
class ClientSession:
    def __init__(self, client_socket , manager, root_dir="shared"):
        self.client_socket = client_socket
        self.client_manager = manager
        self.user_info = None
        self.username = None
        self.data_socket = None
        self.root = os.path.join(os.getcwd(), root_dir)
        self.transfer_mode = "binary"
        

    def send_data(self, data):
        try:
            if isinstance(data, str):
                self.client_socket.sendall(data.encode("utf-8"))
            elif isinstance(data, bytes):
                self.client_socket.sendall(data)
            else:
                raise TypeError("Data must be a string or bytes")
        except Exception as e:
            print(f"Error sending data: {e}")
    def handle_create_folder(self, data):
        dir_name = data.split(" ")[1]
        new_dir = os.path.join(self.user_info["current_dir"], dir_name)

        response, log_message = create_directory(
            new_dir=new_dir,
            username=self.username
        )

        self.send_data(response)

        # if response.startswith("257"):
        #     self..info(log_message)
        # else:
        #     self..error(log_message)
    def handle_delete_folder(self, data):
        dir_name = data.split(" ")[1]
        dir_path = os.path.join(self.user_info["current_dir"], dir_name)

        # Call the utility function
        response, log_message = delete_folder(dir_path)

        # Send the response to the client
        self.send_data(response)

        # Log the result
        # if response.startswith("257"):
        #     self..info(f"User {self.username} {log_message}")
        # else:
        #     self..error(f"User {self.username} {log_message}")

    def recursive_delete(self, path):
  
        response, log_message = delete_recursive(path)
        self.send_data(response)
        # if response.startswith("257"):
        #     self..info(f"User {self.username} {log_message}")
        # else:
        #     self..error(f"User {self.username} {log_message}")
    
    def handle_download(self, data):
        if not self.data_socket:
            self.send_data("425 No data connection established.\r\n")
            return

        filename = data.split(" ")[1]
        filepath = os.path.join(self.user_info["current_dir"], filename)

        if not os.path.isfile(filepath):
            self.send_data(f"550 not found: {filename}\r\n")
            return

        self.send_data(f"150 Opening data connection for file download. \nFile size: {os.path.getsize(filepath)} bytes.\r\n")
        response, log_message = download_file(
            filepath=filepath,
            send_socket=self.data_socket.sendall,
            transfer_mode=self.transfer_mode
        )

        self.send_data(response)
        # if response.startswith("226"):
        #     self..info(f"User {self.username} {log_message}")
        # else:
        #     self..error(f"User {self.username} {log_message}")
        self.data_socket.close()
        self.data_socket = None

 
    def handle_upload(self, data):
        if not self.data_socket:
            self.send_data("425 No data connection established.\r\n")
            return

        filename = data.split(" ")[1]
        filepath = os.path.join(self.user_info["current_dir"], filename)
        self.send_data(f"150 Opening data connection for file upload.\r\n")
        response, log_message = upload_file(
            filepath=filepath,
            data_socket=self.data_socket,
            transfer_mode=self.transfer_mode
        )
        self.send_data(response)
        # if response.startswith("226"):
        #     self..info(f"User {self.username} {log_message}")
        # else:
        #     self..error(f"User {self.username} {log_message}")

        self.data_socket.close()
        self.data_socket = None

    def handle_pwd(self):
        if self.user_info and "current_dir" in self.user_info:
            self.send_data(
                f'257 "{self.user_info["current_dir"].replace("\\", "/")}" is the current directory.\r\n'
            )
        else:
            self.send_data("550 Failed to get current directory.\r\n")


    def handle_cwd(self, data):
        dir_name = data.split(" ")[1]
        current_dir = self.user_info["current_dir"]

        # Call the utility function
        response, new_dir = cwd(
            current_dir=current_dir,
            dir_name=dir_name,
            root=self.root,
        )

        # Update the current directory if the change was successful
        if response.startswith("250"):
            self.user_info["current_dir"] = new_dir

        # Send the response to the client
        self.send_data(response)


    
    def handle_list_files(self):
        if not self.data_socket:
            self.send_data("425 No data connection established.\r\n")
            return
        try:
            
            file_list_str = list_files(self.user_info["current_dir"])
            self.send_data("150 Here comes the directory listing.\r\n")            
            self.data_socket.sendall(file_list_str.encode("utf-8"))
            self.data_socket.close()
            self.send_data("226 Transfer complete.\r\n")
            # self..info(f"User {self.username} listed files in {self.user_info['current_dir']}")

        except Exception as e:
            self.send_data("550 Failed to list directory.\r\n")
            # self..error(f"User {self.username} failed to list files in {self.user_info['current_dir']}: {e}")
    
    
    def handle_port(self, data):
        if self.data_socket:
            self.data_socket.close()
        parts = data.split(" ")[1].split(",")
        data_host = ".".join(parts[:4])
        data_port = (int(parts[4]) << 8) + int(parts[5])
        self.data_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.data_socket.connect((data_host, data_port))
            self.send_data("200 PORT command successful.\r\n")
        except Exception as e:
            print(f"Error connecting to data socket: {e}")
            self.send_data("425 Cannot open data connection.\r\n")
    def handle_command(self, data):
        if data.startswith("USER"):
            self.username = data.split(" ")[1]
            self.send_data("331 Please specify the password.\r\n")
        elif data.startswith("PASS"):
            if self.username:
                password = data.split(" ")[1]
                user =authenticate(self.username, password,self.root)
                if user:
                    self.user_info = user
                    self.send_data("230 User logged in successfully.\r\n")
                else:
                    self.send_data("530 Login failed\r\n")
        elif data.startswith("OPTS UTF8 ON"):
            self.send_data("200 UTF8 mode is on.\r\n")
        elif data.startswith("LIST") or data.startswith("NLST"):
            self.handle_list_files()
        elif data.startswith("XPWD"):
            self.handle_pwd()
        # upload
        elif data.startswith("STOR"):
            self.handle_upload(data)
        # download
        elif data.startswith("RETR"):
            self.handle_download(data)
        elif data.startswith("XMKD"):
            self.handle_create_folder(data)
        elif data.startswith("XRMD"):
            self.handle_delete_folder(data)
        elif data.startswith("DELE"):
            path = os.path.join(self.user_info["current_dir"], data.split(" ")[1])
            self.recursive_delete(path)
        elif data.startswith("CWD"):
            self.handle_cwd(data)
        elif data.startswith("PORT"):
            self.handle_port(data)
        elif data.startswith("TYPE A"):
            self.transfer_mode = "ascii"
            self.send_data("200 Switching to ASCII mode.\r\n")
        elif data.startswith("TYPE I"):
            self.transfer_mode = "binary"
            self.send_data("200 Switching to Binary mode.\r\n")
        elif data.startswith("QUIT"):
            self.send_data("221 Goodbye\r\n")
            return False
        else:
            self.send_data("500 Unknown command\r\n")
        return True

    def run(self):
        client_ip, client_port = self.client_socket.getsockname()
        self.client_manager.add_client({"ip": client_ip, "port": client_port})
        self.send_data("220 Welcome to the FTP Server\r\n")
        while True:
            try:
                data = self.client_socket.recv(1024).decode("utf-8").strip()
                print("received data:", data)

                if not data:
                    break
                if not self.handle_command(data):
                    break

            except Exception as e:
                print(f"Error: {e}")
                break
        self.client_socket.close()
        self.client_manager.remove_client({"ip": client_ip, "port": client_port})


class FTP:
    def __init__(
        self, 
        host="0.0.0.0", 
        port=21,
        max_clients=5, 
        shared_dir="shared",
        ClientManager=None,
    ):
        self.host = host
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(max_clients)        
        self.client_manager = ClientManager
        self.shared_dir=shared_dir
     

    def start(self):
        while True:
            try:
                client_socket, address = self.server_socket.accept()
                session = ClientSession(
                    client_socket,
                    self.client_manager,
                    self.shared_dir,
                )
                client_thread = threading.Thread(target=session.run)
                client_thread.start()
            except OSError as e:
                print(f"Error: {e}")

    def stop(self):
        self.server_socket.close()

    def update_config(self, host, port):
        self.stop()  
        self.host = host
        self.port = port
        self.start() 





