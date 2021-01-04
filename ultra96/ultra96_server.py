import socket
import threading
import time
import base64
from Cryptodome.Cipher import AES
import sys
from Cryptodome import Random
import time

# Class to handle the connection to the laptop (acts as the server and opens the socket)


class Server(threading.Thread):
    def __init__(self, ip_addr, secret_key, ultra96, sync_threshold, buff_size=256, num_of_dancers=3):
        super(Server, self).__init__()

        self.ip_addr = ip_addr
        self.buff_size = buff_size
        self.num_of_dancers = num_of_dancers
        self.secret_key = secret_key
        self.logout = ultra96.logout
        self.ultra96 = ultra96
        self.dancers_ready = ultra96.dancers_ready
        self.sync_threshold = sync_threshold

        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket_conn = []

    def stop(self):
        for conn in self.socket_conn:
            conn.close()
        self.server.close()
        print("[ULTRA96 SERVER CLOSED]")

    def recvall(self, conn):
        # Buffer to ensure that only reading the full 256 bytes
        received_chunks = []
        remaining = self.buff_size
        while remaining > 0:
            received = conn.recv(remaining)
            if not received:
                return None
            received_chunks.append(received)
            remaining -= len(received)
        return b''.join(received_chunks)

    # Function to handle the messages from each socket, runs on a separate thread
    def handle_client(self, conn, addr):
        self.num_of_dancers -= 1
        dancer_id = -1
        dancer_name = ""
        network_delay = 0
        while not self.logout.is_set():
            data = self.recvall(conn)
            recv_time = time.time()
            if data:
                try:
                    msg = self.decrypt_message(data)
                    msg = msg.strip()
                    if "!T" in msg:
                        # Clock sync message
                        self.clock_sync(conn, msg, dancer_id, recv_time)
                    elif "!S" in msg:
                        # Start message
                        split_message = msg.split("|")
                        dancer_id = int(split_message[1])
                        dancer_name = str(split_message[2])
                        time.sleep(0.02 * int(dancer_id))
                        self.ultra96.dashboard_server.send_message(msg)
                        self.ultra96.create_dancer(dancer_id, dancer_name)
                        print(
                            f"[DANCER {dancer_id}] Dancer {dancer_id} {dancer_name} connected.")
                    elif "!D" in msg:
                        # Data message
                        dashboard_message = msg + f"{dancer_name}|"
                        self.ultra96.dashboard_server.send_message(
                            dashboard_message)
                        msg = msg.split("|")
                        self.ultra96.add_data(dancer_id, msg[2:])
                    elif "!O" in msg:
                        # Contains the offset calculated
                        network_delay = float(msg.split("|")[1])
                    elif "!R" in msg:
                        pass
                    elif "!M" in msg:
                        # Movement data, sets the program into EVALUATE state
                        msg = msg.split("|")
                        print(
                            f"RESET + MOVEMENT {dancer_id} {dancer_name} {msg[1]}")
                        self.ultra96.reset_evaluation_flag(dancer_id)
                        self.ultra96.update_positions(dancer_id, msg[1])
                except Exception as e:
                    print(e)
            else:
                print("No data received")
                break
        self.ultra96.stop()
        print(
            f"[{dancer_id} DISCONNECTED] Dancer {dancer_id} {dancer_name} has disconnected")

    def start_clock_sync_all(self):
        for conn in self.socket_conn:
            self.send_message(conn, "!T|")

    # Replies the clock synchronisation protocol
    def clock_sync(self, conn, msg, dancer_id, recv_time):
        msg += f"{recv_time}|"
        send_time = time.time()
        msg += f"{send_time}|"
        self.send_message(conn, msg, dancer_id=dancer_id)

    # Main driver of the program, spawns a thread for each socket connection. Once x number of
    # dancers connected, sets a flag to signal all dancers ready
    def run(self):
        self.server.bind(self.ip_addr)
        self.server.listen()
        self.server.settimeout(5)
        print(
            f"[WAITING FOR DANCERS] Waiting for {self.num_of_dancers} dancers to connect")
        while self.num_of_dancers > 0 and not self.logout.is_set():
            try:
                conn, addr = self.server.accept()
                thread = threading.Thread(
                    target=self.handle_client, args=(conn, addr))
                self.socket_conn.append(conn)
                thread.start()
            except socket.timeout:
                pass
            except OSError:
                pass
        if self.logout.is_set():
            self.stop()
            print("[LAPTOP SERVER CLOSED] Bye bye")
        else:
            print(f"[READY] {len(self.socket_conn)} dancers connected.")
            self.dancers_ready.set()

    # Sends a start message to all dancers
    def start_evaluation(self):
        # Start command
        for conn in self.socket_conn:
            self.send_message(conn, "!S")

    def send_message(self, conn, msg, dancer_id="ALL"):
        encrypted_message = self.encrypt_message(msg)
        try:
            conn.sendall(encrypted_message)
        except:
            pass

    def decrypt_message(self, cipher_text):
        decoded_message = base64.b64decode(cipher_text)
        iv = decoded_message[:16]
        secret_key = bytes(str(self.secret_key), encoding="utf8")
        cipher = AES.new(secret_key, AES.MODE_CBC, iv)
        decrypted_message = cipher.decrypt(decoded_message[16:]).strip()
        return decrypted_message.decode('utf8')

    def encrypt_message(self, plain_text):
        plain_text += ' ' * (16 - len(plain_text) %
                             16)  # Pad it to multiples of 16
        key = bytes(str(self.secret_key), encoding="utf8")
        iv = Random.new().read(16)
        cipher = AES.new(key, AES.MODE_CBC, iv)
        encrypted_text = cipher.encrypt(plain_text.encode("utf8"))
        # print("size of plaintext encode: " + str(sys.getsizeof(plain_text.encode())))
        encrypted_text = base64.b64encode(iv + encrypted_text)
        # Pad to full just in case
        return encrypted_text + b' ' * (self.buff_size - len(encrypted_text))


def main():
    pass


if __name__ == '__main__':
    main()
