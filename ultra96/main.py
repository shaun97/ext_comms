from ultra96_client import Client
from ultra96_server import Server
from dashboard_server import Dashboard_Server
import sys
import time
import threading
from statistics import mean
from config import *
from multiprocessing import Process
from ml import *
from move_eval import *
from driver_hardware_ml import *

# Main class for the Ultra96 server. Contains the server, dashboard server and server classes
class ultra96():
    def __init__(self):
        # Stores the data from the dancers
        self.dancer_data = {}
        self.frame_no = 0
        self.dancer_names = ["Nil", "Nil", "Nil"]

        # Syncrhonisation variables
        self.dancer_data_lock = threading.Lock()
        self.logout = threading.Event()
        self.dancers_ready = threading.Event()
        self.dashboard_ready = threading.Event()

        # Various classes intialised
        self.server = Server(ULTRA_SERVER_ADDR, SECRET_KEY, ultra96=self,
                             sync_threshold=SYNC_THRESHOLD, buff_size=BUFF_SIZE, num_of_dancers=NUM_OF_DANCERS)
        self.eval_client = Client(EVAL_SERVER_ADDR, SECRET_KEY, ultra96=self)
        self.dashboard_server = Dashboard_Server(
            DASHBOARD_SERVER_ADDR, SECRET_KEY, dashboard_ready=self.dashboard_ready, buff_size=BUFF_SIZE)

        # Variables to handle the data
        self.has_evaluated = True
        self.sync_delay = 0
        self.first_x_timestamp = {}
        self.sync_evaluated = False
        self.eval_counter = 0
        # pos[0] holds the dancer no of the dancer in the 1st position
        self.pos = [1, 2, 3]
        # moves holds the movement for this iteration of dancer 0, 1, 2 respectively
        self.movements = ['', '', '']

    # Starts the program and creates relevant threads
    def start(self):
        dashboard_conn_thread = threading.Thread(
            target=self.dashboard_server.start, args=())
        dashboard_conn_thread.setDaemon(True)
        dashboard_conn_thread.start()
        self.server.setDaemon(True)
        self.server.start()

        # Keeps polling until all required connections are setup
        while True:
            self.dashboard_ready.wait(1)
            self.dancers_ready.wait(1)

            # Needed to ensure that ctrl c works
            if self.dancers_ready.is_set() and self.dashboard_ready.is_set():
                time.sleep(0.5)
                start_command = input(
                    "Do you wish to connect to eval server? [Y/N]")
                if start_command.lower() == "y":
                    break
        self.eval_client.start()

        # Wait for user input to start
        while True:
            time.sleep(0.5)
            start_command = input("Do you wish to start? [Y/N]")
            if start_command.lower() == "y":
                break

        self.server.start_evaluation()

    # Resets all the data
    def reset_data(self):
        with self.dancer_data_lock:
            self.has_evaluated = True
            self.eval_counter = 0
            # Reset sync delay for next dance move, based on flag of the start then reset
            self.sync_delay = 0
            self.sync_evaluated = False

            for dancer in self.first_x_timestamp.keys():
                self.first_x_timestamp[dancer] = []

            # reset all movements
            self.movements = ['', '', '']

    def create_dancer(self, dancer_id, dancer_name):
        self.dancer_data[dancer_id - 1] = []
        self.dancer_names[dancer_id - 1] = dancer_name
        self.first_x_timestamp[dancer_id - 1] = []

    # Checks if all incoming data are from the same frame
    def is_ready_to_update_frame(self):
        for d in self.dancer_data.values():
            if len(d) <= self.frame_no:
                return False
        return True

    # Calculates the sync delay, average of the first 5 time stamps
    def get_sync_delay(self):
        self.sync_evaluated = True
        start_of_each_dancer = [mean(timestamps)
                                for timestamps in self.first_x_timestamp.values()]
        earliest_dancer = min(start_of_each_dancer)
        latest_dancer = max(start_of_each_dancer)
        self.sync_delay = int((latest_dancer - earliest_dancer) * 1000)

    def stop(self):
        self.dashboard_server.stop()
        self.server.stop()
        self.eval_client.stop()
        self.logout.set()

    def reset_evaluation_flag(self, dancer_id):
        with self.dancer_data_lock:
            self.has_evaluated = False
            # Added this
            self.dancer_data[dancer_id - 1] = []
            self.frame_no = 0

    # Updates the position based on the 3 movements from the dancers
    def update_positions(self, dancer_id, movement):
        self.movements[dancer_id - 1] = movement

        for i in self.movements:
            if i == '':
                return

        # handle movement
        self.pos = evaluate_movement(self.movements, self.pos)

    # Function to parse the data into the ML and subsequently handle the consensus and resetting of data
    def handle_ml(self):
        predicted_moves = []
        for dancer in self.dancer_data.keys():
            data = [[] for i in range(12)]
            for i in range(NO_OF_FRAME_FOR_ML):
                # for software model (FOR TESTING!!!)
                # data[0].append(float(self.dancer_data[dancer][i][0]))
                # data[1].append(float(self.dancer_data[dancer][i][1]))
                # data[2].append(float(self.dancer_data[dancer][i][2]))
                # data[3].append(float(self.dancer_data[dancer][i][3]))
                # data[4].append(float(self.dancer_data[dancer][i][4]))
                # data[5].append(float(self.dancer_data[dancer][i][5]))
                # data[6].append(float(self.dancer_data[dancer][i][6]))
                # data[7].append(float(self.dancer_data[dancer][i][7]))
                # data[8].append(float(self.dancer_data[dancer][i][8]))
                # data[9].append(float(self.dancer_data[dancer][i][9]))
                # data[10].append(float(self.dancer_data[dancer][i][10]))
                # data[11].append(float(self.dancer_data[dancer][i][11]))
                # for hardware model (FINAL IMPLEMENTATION)
                data[0].append(int(self.dancer_data[dancer][i][0]))
                data[1].append(int(self.dancer_data[dancer][i][1]))
                data[2].append(int(self.dancer_data[dancer][i][2]))
                data[3].append(int(self.dancer_data[dancer][i][3]))
                data[4].append(int(self.dancer_data[dancer][i][4]))
                data[5].append(int(self.dancer_data[dancer][i][5]))
                data[6].append(int(self.dancer_data[dancer][i][6]))
                data[7].append(int(self.dancer_data[dancer][i][7]))
                data[8].append(int(self.dancer_data[dancer][i][8]))
                data[9].append(int(self.dancer_data[dancer][i][9]))
                data[10].append(int(self.dancer_data[dancer][i][10]))
                data[11].append(int(self.dancer_data[dancer][i][11]))
            predicted_moves.append(infer_data_hardware(data))
            # predicted_moves.append(infer_data(data))

        # Clear data after eval
        for dancer in self.dancer_data.keys():
            self.dancer_data[dancer] = []
            # self.dancer_data[dancer] = self.dancer_data[dancer][:7]
        self.frame_no = 0

        d1move = predicted_moves[0][0]
        d2move = predicted_moves[1][0] if len(predicted_moves) >= 2 else "Nil"
        d3move = predicted_moves[2][0] if len(predicted_moves) >= 3 else "Nil"

        d1score = predicted_moves[0][1]
        d2score = predicted_moves[1][1] if len(predicted_moves) >= 2 else "Nil"
        d3score = predicted_moves[2][1] if len(predicted_moves) >= 3 else "Nil"

        self.dashboard_server.send_message(
            f'#{self.pos[0]} {self.pos[1]} {self.pos[2]}|{d1move} {d2move} {d3move}|{d1score} {d2score} {d3score}|{self.sync_delay}|{self.dancer_names[self.pos[0] - 1]} {self.dancer_names[self.pos[1] - 1]} {self.dancer_names[self.pos[2] - 1]}')

        # Checks if there is a nomatch (0.85)
        temp_dance_move = predicted_moves[0][0]
        if temp_dance_move == "NoMatch":
            print(f"{self.eval_counter} No match")
            return

        # Checks for consensus among all 3 evaluations
        for move in predicted_moves:
            if temp_dance_move != move[0]:
                print(f"{self.eval_counter} No consensus")
                return
            temp_dance_move = move[0]

        # If consensus -> send to the server and set this
        print(f"PREDICTED MOVE {temp_dance_move}")

        self.eval_client.send_dance_move(
            self.pos[0], self.pos[1], self.pos[2], temp_dance_move, self.sync_delay)
        self.has_evaluated = True
        self.eval_counter = 0

        # Reset sync delay for next dance move, based on flag of the start then reset
        self.sync_delay = 0
        self.sync_evaluated = False

        for dancer in self.first_x_timestamp.keys():
            self.first_x_timestamp[dancer] = []

        # reset all movements
        self.movements = ['', '', '']

        # start clock sync for all
        self.server.start_clock_sync_all()

    # When there is a new dance move
    def add_data(self, dancer_id, data):
        with self.dancer_data_lock:
            if self.has_evaluated:
                return

        # Stores the time stamp if first 5 data comes in
        if len(self.first_x_timestamp[dancer_id - 1]) < NO_OF_TIMESTAMP:
            self.first_x_timestamp[dancer_id - 1].append(float(data[12]))

        with self.dancer_data_lock:
            self.dancer_data[dancer_id - 1].append(data[:12])

            if self.is_ready_to_update_frame():
                self.frame_no += 1

                # If 5 timestamps received, calculates sync delay and deletes all the data
                if not self.sync_evaluated and self.frame_no == NO_OF_TIMESTAMP:
                    self.get_sync_delay()
                    self.frame_no = 0
                    for dancer in self.dancer_data.keys():
                        self.dancer_data[dancer] = []
                    return

                # Every 14th data point, ML model gets called
                if self.frame_no % NO_OF_FRAME_FOR_ML == 0:
                    self.eval_counter += 1
                    if self.eval_counter == 20:
                        pass
                    self.handle_ml()


if __name__ == '__main__':
    ultra96 = ultra96()
    ultra96.start()

    # To prevent it from exiting this thread
    while not ultra96.logout.is_set():
        try:
            time.sleep(5)
        except KeyboardInterrupt:
            ultra96.logout.set()
            ultra96.server.stop()
            ultra96.dashboard_server.stop()
            ultra96.eval_client.stop()
