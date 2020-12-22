import json
import logging
import os
import random
import socket
from logging.handlers import RotatingFileHandler

import protocol


passages = [{1, 4}, {0, 2}, {1, 3}, {2, 7}, {0, 5, 8},
            {4, 6}, {5, 7}, {3, 6, 9}, {4, 9}, {7, 8}]
host = "localhost"
port = 12000
# HEADERSIZE = 10

"""
set up fantom logging
"""
fantom_logger = logging.getLogger()
fantom_logger.setLevel(logging.DEBUG)
formatter = logging.Formatter(
    "%(asctime)s :: %(levelname)s :: %(message)s", "%H:%M:%S")
# file
if os.path.exists("./logs/fantom.log"):
    os.remove("./logs/fantom.log")
file_handler = RotatingFileHandler('./logs/fantom.log', 'a', 1000000, 1)
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)
fantom_logger.addHandler(file_handler)
# stream
stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.WARNING)
fantom_logger.addHandler(stream_handler)


class Player():

    def __init__(self):

        self.end = False
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    def connect(self):
        self.socket.connect((host, port))

    def reset(self):
        self.socket.close()


    def select_char(self, game_state):
        cards = {
            "Red": 3,
            "Grey": 2,
            "Black": 1,
            "White": 1,
            "Brawn": 1,
            "Pink": 1,
            "Purple": 1,
            "Blue": 0,
        }
        self.check_players_in_rooms(game_state, 0)
        #print(cards)
        #print(game_state)
        return

    def check_players_in_rooms(self, game_state, room_number):
        print(type(room_number))
        all_room = {}
        for room in passages[room_number]:
            print(type(room))
            cpt = self.check_player_in_room(game_state, room)
            all_room[str(room)] = cpt
        print(all_room)
        return all_room


    def check_player_in_room(self, game_state, room_number):
        player_cpt = 0
        for character in game_state["characters"]:
            if (character["position"] == room_number):
                player_cpt = player_cpt + 1
        return (player_cpt)

    def answer(self, question):
        # work
        data = question["data"]
        game_state = question["game state"]
        questionType = question['question type']
        if(questionType == 'select character'):
            self.select_char(question["game state"])
        response_index = random.randint(0, len(data)-1)
        # log
        fantom_logger.debug("|\n|")
        fantom_logger.debug("fantom answers")
        fantom_logger.debug(f"question type ----- {question['question type']}")
        fantom_logger.debug(f"data -------------- {data}")
        fantom_logger.debug(f"response index ---- {response_index}")
        fantom_logger.debug(f"response ---------- {data[response_index]}")
        return response_index

    def handle_json(self, data):
        data = json.loads(data)
        response = self.answer(data)
        # send back to server
        bytes_data = json.dumps(response).encode("utf-8")
        protocol.send_json(self.socket, bytes_data)

    def run(self):

        self.connect()

        while self.end is not True:
            received_message = protocol.receive_json(self.socket)
            if received_message:
                self.handle_json(received_message)
            else:
                print("no message, finished learning")
                self.end = True


p = Player()

p.run()
