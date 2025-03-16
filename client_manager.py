
import threading


class ClientManager:
    def __init__(self,logger):
        self.client_sessions = []  
        self.logger=logger
        self.lock = threading.Lock()  

    def add_client(self, client_session):
        print(client_session)
        with self.lock:
            self.client_sessions.append(client_session)
        self.logger.info(f"user {client_session["ip"]}:{client_session["port"]} connected")

    def remove_client(self, client_session):
        with self.lock:
            if client_session in self.client_sessions:
                self.client_sessions.remove(client_session)
        self.logger.info(f"user {client_session["ip"]}:{client_session["port"]} disconnected")
    def broadcast_message(self, message):
        with self.lock:
            for session in self.client_sessions:
                try:
                    session.send_data(message)
                except Exception as e:
                    print(f"Error broadcasting to {session.address}: {e}")

    def count_clients(self):
        with self.lock:
            return len(self.client_sessions)