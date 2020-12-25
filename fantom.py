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
        self.active_card = ""
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.function_color = {
            "brown": self.function_brown,
            "black": self.function_black,
            "white": self.function_white,
            "purple": self.function_purple,
        }

        self.function_power = {
            "blue": self.power_blue,
            "white": self.power_white,
            "grey": self.power_grey,
            "purple": self.power_purple,
            "brown": self.power_brown,
        }

    def getAroundMap_color(self, game_state, position):

        def getPeopleInRoom():
            rooms = [0] * 10
            for character in game_state["characters"]:
                rooms[character["position"]] += 1
            return rooms
        peopleAround = []
        peopleInRoom = getPeopleInRoom()
        peopleAround.append(peopleInRoom[position])
        for room in passages[position]:
            peopleAround.append(peopleInRoom[room])
        return peopleAround

    def getPosition(self, color, game_state):
        for character in game_state["characters"]:
            if character["color"] == color:
                return character["position"]

    def connect(self):
        self.socket.connect((host, port))

    def reset(self):
        self.socket.close()

    def power_brown(self, game_state):
        return 0

    def power_purple(self, game_state):
        return 0

    def power_blue(self, active_str=""):
        return 0

    def power_white(self, game_state):
        position = self.getPosition('white', game_state)
        possibility = list(passages[position])
        people_around = self.getAroundMap_color(game_state, position)
        temp = 0
        for i in range(len(possibility) - temp):
            if position in game_state["blocked"] and possibility[i - temp] in game_state["blocked"]:
                possibility.pop(i - temp)
                people_around.pop(i + 1 - temp)
                temp += 1
        for character in game_state["characters"]:
            if character["color"] == "white":
                position = character["position"]
                break
        if (self.stayAloneOrNot(game_state) == True):
            if game_state["shadow"] in passages[position]:
                return passages[position].index(game_state["shadow"])
            for i in range(len(possibility)):
                if people_around[i + 1] == 0:
                    return i
            return 0
        else:

            for i in range(len(possibility)):
                if (people_around[i + 1]) == 1:
                    return i
            if (possibility[0] == game_state["shadow"] and len(possibility)):
                return 1
            return 0

    def power_grey(self, game_state):
        rooms = [0] * 10
        for character in game_state["characters"]:
            rooms[character["position"]] += 1
        if (self.stayAloneOrNot == True):
            return rooms.index(max(rooms))
        else:
            return rooms.index(min(rooms))

    def function_brown(self, game_state):
        if (self.stayAloneOrNot == True):
            return 0
        else:
            return 1
        return 1

    def function_black(self, game_state):
        if (self.stayAloneOrNot(game_state) == True):
            return 0
        else :
            return 1

    def function_white(self, game_state):
        for character in game_state["characters"]:
            if character["color"] == "white":
                position = character["position"]
                break
        people_around = self.getAroundMap_color(game_state, position)
        if (self.stayAloneOrNot(game_state) == True):
            if (position == game_state["shadow"]):
                return 0
            return 1
        else:
            for i in range (len(passages[position])):
                if (passages[position] == game_state["shadow"]):
                    people_around.pop(i + 1)
            for i in range(1, len(people_around)):
                if people_around[i] >= 1 and passages[i - 1] != game_state["shadow"]:
                    return 1
            return 0

    def function_purple(self, game_state):
        return 0

    def select_char(self, game_state, data):
        actual_pound = -1
        index = 0
        cards = {
            "red": 3,
            "grey": 2,
            "black": 1,
            "white": 1,
            "brown": 1,
            "pink": 1,
            "purple": 1,
            "blue": 0,
        }
        if (len(data) <= 2):
            cards["white"] += 1
            cards["brown"] += 1
            cards["black"] += 1
        else:
            cards["purple"] += 1
            cards["pink"] += 1
        for i in range(len(data)):
            if (cards[data[i]["color"]] > actual_pound):
                actual_pound = cards[data[i]["color"]]
                index = i
        return index

    def stayAloneOrNot(self, game_state):
        for character in game_state["characters"]:
            if (character["color"] == game_state["fantom"]):
                position_fantom = character["position"]
                break
        if (position_fantom == game_state["shadow"]):
            return True
        for character in game_state["characters"]:
            if (character["position"] == position_fantom):
                return False
        return True


    def check_best_move(self, game_state, possible_move):
        temp = self.stayAloneOrNot(game_state)
        peopleInRoom = [0] * 10
        room_number = -1
        for character in game_state["characters"]:
            peopleInRoom[character["position"]] += 1
        if (temp == True):
            for room in possible_move:
                if (peopleInRoom[room] == 0 or room == game_state["shadow"]):
                    room_number = room
                    break
        else:
            for room in possible_move:
                if (peopleInRoom[room] > 0 and room != game_state["shadow"]):
                    room_number = room
                    break
        if (room_number == -1):
            room_number = possible_move[0]
        return (possible_move.index(room_number))

    def check_players_in_rooms(self, game_state, room_number):
        all_room = {}
        for room in passages[room_number]:
            cpt = self.check_player_in_room(game_state, room)
            all_room[str(room)] = cpt
        cpt = self.check_player_in_room(game_state, room)
        all_room[str(room)] = cpt
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
            response_index = self.select_char(question["game state"], data)
            self.active_card = data[response_index]["color"]
        elif (questionType == 'select position'):
            response_index = self.check_best_move(game_state, data)
        elif (questionType == 'activate ' + self.active_card + ' power'):
            response_index = self.function_color[self.active_card](game_state)
        elif (self.active_card + ' character power' in questionType):
            if (self.active_card == "blue"):
                response_index = self.power_blue(questionType)
            else:
                response_index = self.function_power[self.active_card](game_state)
        else:
            response_index = 0
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
