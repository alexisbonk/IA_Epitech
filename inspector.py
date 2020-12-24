import json
import logging
import os
import random
import socket
from logging.handlers import RotatingFileHandler

import protocol

passages = [{1, 4}, {0, 2}, {1, 3}, {2, 7}, {0, 5, 8},
            {4, 6}, {5, 7}, {3, 6, 9}, {4, 9}, {7, 8}]
pink_passages = [{1, 4}, {0, 2, 5, 7}, {1, 3, 6}, {2, 7}, {0, 5, 8, 9},
                 {4, 6, 1, 8}, {5, 7, 2, 9}, {3, 6, 9, 1}, {4, 9, 5},
                 {7, 8, 4, 6}]
power_move = [['pink', [1, 1, 1]], 
              ['blue', [1, 1, 1]], 
              ['grey', [1, 1, 1]],
              ['red', [1, 1, 1]], 
              ['brown', [1, 1, 1]],
              ['white', [1, 1, 1]], 
              ['black', [1, 1, 1]], 
              ['purple', [1, 1, 1]]]
            #{'color' : 
            # #index_if_nothing, 
            # #index_if_someone_above, 
            # #index_if_someone_with 
            # }

host = "localhost"
port = 12000

inspector_logger = logging.getLogger()
inspector_logger.setLevel(logging.DEBUG)
formatter = logging.Formatter(
    "%(asctime)s :: %(levelname)s :: %(message)s", "%H:%M:%S")
if os.path.exists("./logs/inspector.log"):
    os.remove("./logs/inspector.log")
file_handler = RotatingFileHandler('./logs/inspector.log', 'a', 1000000, 1)
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)
inspector_logger.addHandler(file_handler)
stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.WARNING)
inspector_logger.addHandler(stream_handler)


class Player():
    def __init__(self):
        self.end = False
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    def connect(self):
        self.socket.connect((host, port))

    def reset(self):
        self.socket.close()

    def check_players_in_rooms(self, game_state, data, room_number):
        all_room = {}
        for room in passages[room_number]:
            cpt = self.check_player_in_room(game_state, room)
            all_room[str(room)] = cpt
        print(all_room)
        return random.randint(0, len(data)-1)


    def check_player_in_room(self, game_state, room_number):
        player_cpt = 0
        for character in game_state["characters"]:
            if (character["position"] == room_number):
                player_cpt = player_cpt + 1
        return (player_cpt)

    def set_power(self, game_state, data, color):
        for moves in power_move:
            if (moves[0] == color.lower()):
                print("Color: ", color.lower())
                print("Power Moves: ", moves[1])
                if (self.check_player_in_room(game_state, 0) > 1):
                    return moves[1][1]
                elif (self.check_player_in_room(game_state, 0) > 1):
                    return moves[1][2]
                else:
                    return moves[1][0]
        return 0

    def select_power(self, game_state, data, color):
        for moves in power_move:
            if (moves[0] == color.lower()):
                print("Color: ", color.lower())
                print("Power Moves: ", moves[1])
                if (self.check_player_in_room(game_state, 0) > 1):
                    return moves[1][1]
                elif (self.check_player_in_room(game_state, 0) > 1):
                    return moves[1][2]
                else:
                    return moves[1][0]
        return 0

    def select_position(self, game_state, data):
        return self.check_players_in_rooms(game_state, data, 0)

    def select_character(self, game_state, data):
        actual_pound = -1
        index = 0
        cards_priority = {
            "red": 3,
            "pink": 2,
            "black": 1,
            "brown": 1,
            "white": 0,
            "purple": 0,
            "blue": 0,
            "grey": 0,
        }
        if (len(data) <= 2):
            cards_priority["white"] += 1
            cards_priority["brown"] += 1
            cards_priority["black"] += 1
        else:
            cards_priority["purple"] += 1
            cards_priority["pink"] += 1
        for i in range(len(data)):
            if (cards_priority[data[i]["color"]] > actual_pound):
                actual_pound = cards_priority[data[i]["color"]]
                index = i
        return index

    def answer(self, question):
        data = question["data"]
        game_state = question["game state"]
        questionType = question['question type']
        print("[Question] ", questionType)
        print("[Data]: ", data)
        if(questionType == 'select character'):
            response_index = self.select_character(game_state, data)
        elif (questionType == 'select position'):
            response_index = self.select_position(game_state, data)
        elif (questionType.split(' ')[0] == 'activate'):
            response_index = self.select_power(game_state, data, questionType.split(' ')[1])
        elif (questionType.split(' ')[1] == 'character'):
            response_index = self.set_power(game_state, data, questionType.split(' ')[0])
        else:
            response_index = random.randint(0, len(data)-1)
        print("[Response]: ", data[response_index])
        print("-------------------------")
        inspector_logger.debug("|\n|")
        inspector_logger.debug("inspector answers")
        inspector_logger.debug(f"question type ----- {question['question type']}")
        inspector_logger.debug(f"data -------------- {data}")
        inspector_logger.debug(f"response index ---- {response_index}")
        inspector_logger.debug(f"response ---------- {data[response_index]}")
        return response_index

    def handle_json(self, data):
        data = json.loads(data)
        response = self.answer(data)
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
