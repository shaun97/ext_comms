import socket
from Cryptodome.Cipher import AES
from Cryptodome import Random
import base64
import random

# Class to handle the communication with the dashboard server
class Dashboard_Server():
    def __init__(self, ip_addr, secret_key, dashboard_ready, buff_size=256):

        self.ip_addr = ip_addr
        self.buff_size = buff_size
        self.secret_key = secret_key

        self.dashboard_ready = dashboard_ready
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.conn = None
        self.addr = None

    def encrypt_message(self, plain_text):
        plain_text += ' ' * (16 - len(plain_text) %
                             16)  # Pad it to multiples of 16
        key = bytes(str(self.secret_key), encoding="utf8")
        iv = Random.new().read(16)
        cipher = AES.new(key, AES.MODE_CBC, iv)
        encrypted_text = cipher.encrypt(
            plain_text.encode("utf8"))  # Default is utf8
        # return base64.b64encode(iv + encrypted_text)
        encrypted_text = base64.b64encode(iv + encrypted_text)
        # Pad to full just in case
        return encrypted_text + b' ' * (self.buff_size - len(encrypted_text))

    def send_message(self, msg):
        encrypted_message = self.encrypt_message(msg)
        try:
            self.conn.sendall(encrypted_message)
            #print(f"[MESSAGE SENT] Ultra96 sent to dashboard: {msg}")
        except:
            pass
            #print(f"[MESSAGE FAILED] Ultra96 failed to send to dashboard: {msg}")

    # Starts the socket connection for the dashboard server to connect to
    def start(self):
        self.server.bind(self.ip_addr)
        self.server.listen()
        self.server.settimeout(1)
        print("[WAITING FOR DASHBOARD] Waiting for dashboard to connect")
        while True:
            try:
                self.conn, self.addr = self.server.accept()
                break
            except socket.timeout:
                pass
        self.dashboard_ready.set()
        print(f"[DASHBOARD CONNECTED] Ultra96 to Dashboard connected")

    def stop(self):
        self.server.close()
        print(f"[DASHBOARD DISCLOSED] Socket from ultra96 to dashboard disconnected")
