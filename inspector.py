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
        self.active_card = ""
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    def connect(self):
        self.socket.connect((host, port))

    def reset(self):
        self.socket.close()

    def getPeopleInRoom(self, game_state):
        rooms = [0] * 10
        for character in game_state["characters"]:
            rooms[character["position"]] += 1
        return rooms

    def getAroundMap_color(self, game_state, position):
        peopleInRoom = self.getPeopleInRoom(game_state)
        peopleAround = []
        peopleAround.append(peopleInRoom[position])
        for room in passages[position]:
            peopleAround.append(peopleInRoom[room])
        return peopleAround

    def getPosition(self, color, game_state):
        for character in game_state["characters"]:
            if character["color"] == color:
                return character["position"]

    def check_player_in_room(self, game_state, room_number):
        player_cpt = 0
        for character in game_state["characters"]:
            if (character["position"] == room_number):
                player_cpt = player_cpt + 1
        return (player_cpt)

    def set_power(self, game_state, data, color):
        peopleInRoom = self.getPeopleInRoom(game_state)
        position = self.getPosition(color, game_state)
        if (color.lower() == 'purple'):  #swap with any suspect
            for character in game_state["characters"]:
                for color_with in data:
                    if (character["color"] == color_with and character["suspect"]):
                        return data.index(color_with)
        elif (color.lower() == 'grey'):  #turn off the light in empty room
            return peopleInRoom.index(0)
        elif (color.lower() == 'brown'): #check if suspect with him
            for character in game_state["characters"]:
                for color_with in data:
                    if (character["color"] == color_with and character["suspect"]):
                        return data.index(color_with)
        return random.randint(0, len(data)-1)

    def select_power(self, game_state, data, color):
        position = self.getPosition(color, game_state)
        people_around = self.getAroundMap_color(game_state, position)
        power_move = [
            ['pink', [1, 1, 1]],
            ['red', [1, 1, 1]],
            ['blue', [0, 0, 0]],
            ['grey', [1, 1, 1]],
            ['brown', [0, 0, 1]],
            ['white', [1, 0, 1]],
            ['black', [0, 1, 0]],
            ['purple', [1, 1, 1]]
        ]
        for moves in power_move:
            if (moves[0] == color.lower()):
                if (people_around[0] > 1):
                    return moves[1][1]
                elif (people_around[1] > 1 or people_around[2] > 1):
                    return moves[1][2]
                else:
                    return moves[1][0]
        return random.randint(0, len(data)-1)

    def select_position(self, game_state, data, index):
        suspectInRoom = [0] * 10
        room_number = -1
        for character in game_state["characters"]:
            if (character["suspect"]):
                suspectInRoom[character["position"]] += 1
        for room in data:
            if (suspectInRoom[room] > 0 or room != game_state["shadow"]):
                room_number = room
                break
        if (room_number == -1):
            room_number = data[0]
        return (data.index(room_number))

    def select_character(self, game_state, data, index):
        actual_pound = -1
        cards_priority = {
            "red": 4,
            "pink": 3,
            "black": 2,
            "brown": 2,
            "white": 1,
            "purple": 1,
            "blue": 0,
            "grey": 0,
        }
        for i in range(len(data)):
            if (cards_priority[data[i]["color"]] > actual_pound):
                actual_pound = cards_priority[data[i]["color"]]
                index = i
        self.active_card = data[index]["color"]
        return (index)

    def get_answer(self, game_state, data, questionType):
        if(questionType == 'select character'):
            response_index = self.select_character(game_state, data, 0)
        elif (questionType == 'select position'):
            response_index = self.select_position(game_state, data, 0)
        elif (questionType.split(' ')[0] == 'activate'):
            response_index = self.select_power(game_state, data, questionType.split(' ')[1])
        elif (questionType.split(' ')[1] == 'character'): #Blue, white, grey, brown
            response_index = self.set_power(game_state, data, questionType.split(' ')[0])
        else:
            response_index = random.randint(0, len(data)-1)
        return (response_index)

    def answer(self, question):
        data = question["data"]
        game_state = question["game state"]
        questionType = question['question type']
        response_index = self.get_answer(game_state, data, questionType)
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
