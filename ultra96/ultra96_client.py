import socket
from Cryptodome.Cipher import AES
from Cryptodome import Random
import base64
import random
import time
import threading
HOST_ADDR = ('localhost', 8082)

# Class to handle the connection and sending data to the evaluation server


class Client(threading.Thread):
    def __init__(self, ip_addr, secret_key, ultra96):
        super(Client, self).__init__()
        self.ultra96 = ultra96
        self.ip_addr = ip_addr
        self.buff_size = 1024  # Fixed for eval server
        self.secret_key = secret_key

        self.logout = ultra96.logout  # should just use stop function to close

        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

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
            self.client.sendall(encrypted_message)
            # print(f"[MESSAGE SENT] Ultra96 sent: {msg}")
        except:
            print(f"[MESSAGE FAILED] Ultra96 failed to send: {msg}")

    def send_dance_move(self, d1, d2, d3, move, sync_delay):
        eval_message = f"#{d1} {d2} {d3}|{move}|{sync_delay}|"
        print(f"[SENT TO EVAL] {eval_message}")
        self.send_message(eval_message)

    def stop(self):
        self.client.close()
        print(f"[SOCKET CLOSED] Ultra96 client disconnected")

    def receive(self):
        # while not self.logout.is_set():
        while True:
            msg = str(self.client.recv(self.buff_size))
            print(f"------CHANGE------")
            self.ultra96.pos = [int(msg[2]), int(msg[4]), int(msg[6])]
            print(f"CURRENT POSITION: {self.ultra96.pos}")
            self.ultra96.reset_data()
            #print(f"[FROM SERVER] {msg}")

    def run(self):
        self.client.connect(self.ip_addr)
        print(f"[SOCKET STARTED] Ultra96 connected to eval server")
        thread = threading.Thread(target=self.receive)
        thread.start()


class Logout():
    def __init__(self):
        self.logout = "teste"


def main():
    logout = Logout()
    client = Client(HOST_ADDR, "0000000000000000", logout)
    client.run()

    moves = ["windows", "pushback", "rocket", "elbow_lock",
             "hair", "scarecrow", "zigzag", "shouldershrug"]
    sync_delays = [1.86, 2.13, 2.34]
    pos = [1, 2, 3]
    time.sleep(65)
    while True:
        random.shuffle(moves)
        random.shuffle(pos)
        random.shuffle(sync_delays)

        client.send_dance_move(
            pos[0], pos[1], pos[2], moves[0], sync_delays[0])
        time.sleep(5)


if __name__ == '__main__':
    main()
