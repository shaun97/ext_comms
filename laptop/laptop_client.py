import random
import socket
import sshtunnel
from Cryptodome.Cipher import AES
from Cryptodome import Random
import base64
import sys
import time
import threading
from config import *
import os
import errno
import subprocess

# Class for the laptop client, calls the c code and creates an SSH tunnel and handles the connection to the Ultra96
class Client():
    def __init__(self, ip_addr, en_format, dancer_id, secret_key, dancer_name, buff_size=1024):
        self.ip_addr = ip_addr
        self.en_format = en_format

        self.dancer_id = dancer_id
        self.dancer_name = dancer_name
        self.buff_size = buff_size
        self.secret_key = secret_key

        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.one_way_trip_delay = 0
        self.server_offset = 0
        self.handle_command_thread = threading.Thread(
            target=self.handle_commands)

        self.is_start = threading.Event()
        self.read_from_c_thread = threading.Thread(target=self.read_from_c)

    # starts the tunnel into sunfire -> ultra96
    def start_tunnel(self, user, password):
        tunnel1 = sshtunnel.open_tunnel(
            ('sunfire.comp.nus.edu.sg', 22),  # host address for ssh, 22
            # xilinx address to bind to localhost port
            remote_bind_address=('137.132.86.243', 22),
            ssh_username=user,
            ssh_password=password,
            # local_bind_address=('127.0.0.1', 8081),
            block_on_close=False
        )
        tunnel1.start()
        print('[Tunnel Opened] Tunnel into Sunfire opened ' +
              str(tunnel1.local_bind_port))
        tunnel2 = sshtunnel.open_tunnel(
            ssh_address_or_host=(
                'localhost', tunnel1.local_bind_port),  # ssh into xilinx
            remote_bind_address=('127.0.0.1', 8081),  # binds xilinx host
            ssh_username='xilinx',
            ssh_password='xilinx',
            local_bind_address=('127.0.0.1', 8081),  # localhost to bind it to
            block_on_close=False
        )
        tunnel2.start()
        print('[Tunnel Opened] Tunnel into Xilinx opened')

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

    def decrypt_message(self, cipher_text):
        decoded_message = base64.b64decode(cipher_text)
        iv = decoded_message[:16]
        secret_key = bytes(str(self.secret_key), encoding="utf8")
        cipher = AES.new(secret_key, AES.MODE_CBC, iv)
        decrypted_message = cipher.decrypt(decoded_message[16:]).strip()
        return decrypted_message.decode('utf8')

    # Starts the startup procedure for each laptop
    def procedure(self):
        try:
            self.client.settimeout(2)
            # Send dancer info
            start_msg = f"!S|{self.dancer_id}|{self.dancer_name}|"
            self.send_message(start_msg)
            print(f"[READY] Dancer {self.dancer_id}, startup procedure completed")

            # # Wait for start
            self.wait_for_start()

            self.clock_sync()
            self.is_start.set()
            print(f"[STARTED] Dancer {self.dancer_id}, program started.")
            while self.is_start.is_set():
                time.sleep(1)
        except Exception as e:
            print(e)

    def run(self):
        # Start c program form here on a separate process
        self.read_from_c_thread.setDaemon(True)
        self.read_from_c_thread.start()

        self.start_tunnel(SUNFIRE_USER, SUNFIRE_PASS)

        # Continuously connect to the Ultra96
        while True:
            try:
                self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.client.settimeout(1)
                self.client.connect(self.ip_addr)
                print(f"[ULTRA96 CONNECTED] Dancer {self.dancer_id} is connected to Ultra96")
                self.procedure()
                time.sleep(1)
            except ConnectionRefusedError:
                self.is_start.clear()
                time.sleep(1)
                print("[TRYING] Why u no let me connect?? (┛ಠ_ಠ)┛彡┻━┻")
            except Exception as e:
                pass

    def send_message(self, msg):
        encrypted_message = self.encrypt_message(msg)
        try:
            self.client.sendall(encrypted_message)
            print(f"[MESSAGE SENT] Dancer {self.dancer_id} sent: {msg}")
        except ConnectionResetError:
            raise ConnectionResetError
        except BrokenPipeError:
            raise ConnectionResetError
        except OSError as e:
            raise OSError
        except Exception as e:
            print(
                f"[MESSAGE FAILED] Dancer {self.dancer_id} failed to send: {msg}")

    # Runs on a separate thread and handles commands from the Ultra96
    def handle_commands(self):
        while True:
            try:
                data = self.client.recv(self.buff_size)
                curr_time = time.time()
                if data:
                    msg = self.decrypt_message(data)
                    print(msg)
                    if "!T" in msg:
                        self.clock_sync()
                    elif "!C" in msg:
                        self.stop()
            except socket.timeout:
                pass

    def clock_sync(self):
        # Start the clock sync procedure by sending a message with curr time
        t1 = time.time()
        clock_msg = f"!T|{t1}|"
        self.send_message(clock_msg)

        data = self.client.recv(self.buff_size)
        t4 = time.time()
        msg = self.decrypt_message(data)
        split_message = msg.split("|")
        t1 = float(split_message[1])
        t2 = float(split_message[2])
        t3 = float(split_message[3])
        self.one_way_trip_delay = ((t4 - t1) - (t3 - t2)) / 2

        # Send the RTT to the server, O for network offset
        self.send_message(f"!O|{self.one_way_trip_delay}|")

        # Difference in time between server and laptop, server - laptop in seconds
        self.server_offset = t4 - t3 - self.one_way_trip_delay
        print(f"[CLOCK SYNC] Completed, offset: {self.server_offset}")

    # Loops and wait for a start command from the Ultra96
    def wait_for_start(self):
        # Wait for the start packet from server
        isStart = False
        while not isStart:
            try:
                encrypted_msg = self.client.recv(self.buff_size)
                msg = self.decrypt_message(encrypted_msg)
                if "!S" in msg:
                    isStart = True
            except socket.timeout:
                print("I am waiting for someone to start me :'(")
            except KeyboardInterrupt:
                self.stop()

    def stop(self):
        close_msg = "!C$"
        self.send_message(close_msg)
        self.client.close()
        print(f"[SOCKET CLOSED] Dancer {self.dancer_id} disconnected")

    # Thread to handle data from the bluno
    def handle_bluno_data(self, data):
        # Don't do anything until start flag is received
        if not self.is_start.is_set():
            print("[SKIPPING BLUNO DATA] Evaluation not started")
            return

        # When S, skip, dont send anything
        try:
            if "S" in data:
                print("reset")
                pass
            # If movement packet sent, reset on ultra96 side
            elif "R" in data or "L" in data or "N" in data:
                print(data)
                data = data.split("|")[0]
                data = data.strip()
                self.send_message(f"!M|{data}")
            else:
                data = data.split("|")[0]
                data = data.split(" ")
                data[12] = str(float(data[12]) / 1000 + self.server_offset)

                formatted_msg = "|".join(data)
                formatted_msg = f"!D|{self.dancer_id}|{formatted_msg}|"
                print(formatted_msg)
                self.send_message(formatted_msg)
        except ConnectionResetError:
            raise ConnectionResetError

    # Calls the c program and creates the named pipe
    def read_from_c(self):
        proc = subprocess.Popen("../../Bluetooth/laptop/mthread.out")
        time.sleep(1)
        try:
            os.mkfifo(FIFO)
        except OSError as oe:
            if oe.errno != errno.EEXIST:
                raise
        while True:

            with open(FIFO) as fifo:
                print("FIFO opened")
                while True:
                    data = fifo.read(C_BUFF_SIZE)
                    if len(data) == 0:
                        print("Writer closed")
                        break
                    try:
                        self.handle_bluno_data(data)
                    except ConnectionResetError:
                        self.is_start.clear()
                        print("[CONNECTION DROPPED] Connection to ultra96 dropped, trying to reconnect")
                        break

# Some testing scripts
def test_script():
    time.sleep(2)
    bluno_data = [[random.randint(-32000, 32000)
                   for j in range(12)] for i in range(1000)]
    dancer_client = Client(HOST_ADDR, EN_FORMAT, DANCER_NO,
                           SECRET_KEY, DANCER_NAME, BUFF_SIZE)
    dancer_client.run()
    msg_no = 0
    for index, data in enumerate(bluno_data):
        msg_no += 1
        message = "!D|" + str(random.randrange(0, 3)) + "|"
        for i in data:
            message += (str(i) + "|")
        message += f"{time.time()}|"
        dancer_client.send_message(message)
        if (index + 1) % 100 == 0:
            time.sleep(10)
            dancer_client.send_message("!R")
        time.sleep(0.07)
    dancer_client.stop()

def test_script_sync(dancer_no):
    bluno_data = [[random.randint(-32000, 32000)
                   for j in range(12)] for i in range(200)]
    dancer_client = Client(HOST_ADDR, EN_FORMAT, dancer_no,
                           SECRET_KEY, DANCER_NAME, BUFF_SIZE)
    dancer_client.run()
    time.sleep(dancer_no * 1)
    for index, data in enumerate(bluno_data):
        message = "!D|" + 1 + "|"
        for i in data:
            message += (str(i) + "|")
        message += f"{time.time()}|"
        dancer_client.send_message(message)
        if (index + 1) % 40 == 0:
            time.sleep(10)
            dancer_client.send_message("!R")
        time.sleep(0.07)
    dancer_client.stop()

if __name__ == '__main__':
    dancer_client = Client(HOST_ADDR, EN_FORMAT, DANCER_NO,
                           SECRET_KEY, DANCER_NAME, BUFF_SIZE)
    dancer_client.run()