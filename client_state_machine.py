"""
Created on Sun Apr  5 00:00:32 2015

@author: zhengzhang
"""
from chat_utils import *
import json

class ClientSM:
    def __init__(self, s):
        self.state = S_OFFLINE
        self.peer = ''
        self.me = ''
        self.out_msg = ''
        self.s = s

    def set_state(self, state):
        self.state = state

    def get_state(self):
        return self.state

    def set_myname(self, name):
        self.me = name

    def get_myname(self):
        return self.me

    def connect_to(self, peer):
        msg = json.dumps({"action":"connect", "target":peer})
        mysend(self.s, msg)
        response = json.loads(myrecv(self.s))
        if response["status"] == "success":
            self.peer = peer
            self.out_msg += 'You are connected with '+ self.peer + '\n'
            return (True)
        elif response["status"] == "busy":
            self.out_msg += 'User is busy. Please try again later\n'
        elif response["status"] == "self":
            self.out_msg += 'Cannot talk to yourself (sick)\n'
        else:
            self.out_msg += 'User is not online, try again later\n'
        return(False)

    def disconnect(self):
        msg = json.dumps({"action":"disconnect"})
        mysend(self.s, msg)
        self.out_msg += 'You are disconnected from ' + self.peer + '\n'
        self.peer = ''

    def submit_game_score(self, my_msg):
        score_msg = json.loads(my_msg[len(GAME_SCORE_PREFIX):])
        game = score_msg.get("game", "snake")
        score = int(score_msg.get("score", 0))
        mysend(self.s, json.dumps({
            "action": "score_submit",
            "game": game,
            "score": score
        }))
        self.out_msg += "Submitted " + game + " score: " + str(score) + "\n"

    def request_game_leaderboard(self, my_msg):
        game = my_msg[len(GAME_LEADERBOARD_PREFIX):].strip()
        if len(game) == 0:
            game = "snake"
        mysend(self.s, json.dumps({
            "action": "scoreboard_request",
            "game": game
        }))
        response = json.loads(myrecv(self.s))
        self.handle_scoreboard(response)

    def handle_scoreboard(self, msg):
        game = msg.get("game", "snake")
        scores = msg.get("scores", [])
        self.out_msg += self.format_scoreboard(game, scores)

    def start_tictactoe(self, my_msg):
        room = my_msg[len(TICTACTOE_START_PREFIX):].strip()
        if len(room) == 0:
            room = "default"
        mysend(self.s, json.dumps({
            "action": "tictactoe_start",
            "room": room
        }))
        self.out_msg += "Requested Tic-Tac-Toe room " + room + ".\n"

    def send_tictactoe_move(self, my_msg):
        move_msg = json.loads(my_msg[len(TICTACTOE_MOVE_PREFIX):])
        mysend(self.s, json.dumps({
            "action": "tictactoe_move",
            "position": move_msg.get("position")
        }))

    def leave_tictactoe(self):
        mysend(self.s, json.dumps({"action": "tictactoe_leave"}))
        self.out_msg += "Left Tic-Tac-Toe.\n"

    def handle_tictactoe_event(self, msg):
        self.out_msg += TICTACTOE_EVENT_PREFIX + json.dumps(msg)

    def format_scoreboard(self, game, scores):
        title = game.capitalize() + " Leaderboard"
        if len(scores) == 0:
            return title + "\nNo scores yet.\n"

        lines = [title]
        for index, entry in enumerate(scores, start = 1):
            lines.append(
                str(index) + ". " + entry.get("name", "unknown")
                + " - " + str(entry.get("score", 0))
                + " (" + entry.get("time", "") + ")")
        return "\n".join(lines) + "\n"

    def handle_incoming_common(self, msg):
        if msg["action"] == "scoreboard":
            self.handle_scoreboard(msg)
            return True
        if msg["action"] == "tictactoe_state" or msg["action"] == "tictactoe_error":
            self.handle_tictactoe_event(msg)
            return True
        return False

    def proc(self, my_msg, peer_msg):
        self.out_msg = ''
#==============================================================================
# Once logged in, do a few things: get peer listing, connect, search
# And, of course, if you are so bored, just go
# This is event handling instate "S_LOGGEDIN"
#==============================================================================
        if self.state == S_LOGGEDIN:
            # todo: can't deal with multiple lines yet
            if len(my_msg) > 0:

                if my_msg == 'q':
                    self.out_msg += 'See you next time!\n'
                    self.state = S_OFFLINE

                elif my_msg == 'time':
                    mysend(self.s, json.dumps({"action":"time"}))
                    time_in = json.loads(myrecv(self.s))["results"]
                    self.out_msg += "Time is: " + time_in

                elif my_msg == 'who':
                    mysend(self.s, json.dumps({"action":"list"}))
                    logged_in = json.loads(myrecv(self.s))["results"]
                    self.out_msg += 'Here are all the users in the system:\n'
                    self.out_msg += logged_in

                elif my_msg.startswith(GAME_SCORE_PREFIX):
                    self.submit_game_score(my_msg)

                elif my_msg.startswith(GAME_LEADERBOARD_PREFIX):
                    self.request_game_leaderboard(my_msg)

                elif my_msg.startswith(TICTACTOE_START_PREFIX):
                    self.start_tictactoe(my_msg)

                elif my_msg.startswith(TICTACTOE_MOVE_PREFIX):
                    self.send_tictactoe_move(my_msg)

                elif my_msg.startswith(TICTACTOE_LEAVE_PREFIX):
                    self.leave_tictactoe()

                elif my_msg[0] == 'c':
                    peer = my_msg[1:]
                    peer = peer.strip()
                    if self.connect_to(peer) == True:
                        self.state = S_CHATTING
                        self.out_msg += 'Connect to ' + peer + '. Chat away!\n\n'
                        self.out_msg += '-----------------------------------\n'
                    else:
                        self.out_msg += 'Connection unsuccessful\n'

                elif my_msg[0] == '?':
                    term = my_msg[1:].strip()
                    mysend(self.s, json.dumps({"action":"search", "target":term}))
                    search_rslt = json.loads(myrecv(self.s))["results"].strip()
                    if (len(search_rslt)) > 0:
                        self.out_msg += search_rslt + '\n\n'
                    else:
                        self.out_msg += '\'' + term + '\'' + ' not found\n\n'

                elif my_msg[0] == 'p' and my_msg[1:].strip().isdigit():
                    poem_idx = my_msg[1:].strip()
                    mysend(self.s, json.dumps({"action":"poem", "target":poem_idx}))
                    poem = json.loads(myrecv(self.s))["results"]
                    # print(poem)
                    if (len(poem) > 0):
                        self.out_msg += poem + '\n\n'
                    else:
                        self.out_msg += 'Sonnet ' + poem_idx + ' not found\n\n'

                else:
                    self.out_msg += menu

            if len(peer_msg) > 0:
                peer_msg = json.loads(peer_msg)
                if self.handle_incoming_common(peer_msg):
                    pass
                elif peer_msg["action"] == "connect":
                    self.peer = peer_msg["from"]
                    self.out_msg += 'Request from ' + self.peer + '\n'
                    self.out_msg += 'You are connected with ' + self.peer
                    self.out_msg += '. Chat away!\n\n'
                    self.out_msg += '------------------------------------\n'
                    self.state = S_CHATTING

#==============================================================================
# Start chatting, 'bye' for quit
# This is event handling instate "S_CHATTING"
#==============================================================================
        elif self.state == S_CHATTING:
            if len(my_msg) > 0:     # my stuff going out
                if my_msg == 'bye':
                    self.disconnect()
                    self.state = S_LOGGEDIN
                    self.peer = ''
                elif my_msg.startswith(FILE_CMD_PREFIX):
                    file_msg = json.loads(my_msg[len(FILE_CMD_PREFIX):])
                    mysend(self.s, json.dumps({
                        "action": "file",
                        "from": "[" + self.me + "]",
                        "filename": file_msg["filename"],
                        "size": file_msg["size"],
                        "data": file_msg["data"]
                    }))
                    self.out_msg += "Sent file: " + file_msg["filename"] + "\n"
                elif my_msg == 'time':
                    mysend(self.s, json.dumps({"action":"time"}))
                    time_in = json.loads(myrecv(self.s))["results"]
                    self.out_msg += "Time is: " + time_in
                elif my_msg == 'who':
                    mysend(self.s, json.dumps({"action":"list"}))
                    logged_in = json.loads(myrecv(self.s))["results"]
                    self.out_msg += 'Here are all the users in the system:\n'
                    self.out_msg += logged_in
                elif my_msg.startswith(GAME_SCORE_PREFIX):
                    self.submit_game_score(my_msg)
                elif my_msg.startswith(GAME_LEADERBOARD_PREFIX):
                    self.request_game_leaderboard(my_msg)
                elif my_msg.startswith(TICTACTOE_START_PREFIX):
                    self.start_tictactoe(my_msg)
                elif my_msg.startswith(TICTACTOE_MOVE_PREFIX):
                    self.send_tictactoe_move(my_msg)
                elif my_msg.startswith(TICTACTOE_LEAVE_PREFIX):
                    self.leave_tictactoe()
                elif my_msg[0] == 'c':
                    peer = my_msg[1:].strip()
                    if self.connect_to(peer) == True:
                        self.out_msg += 'Connect to ' + peer + '. Chat away!\n\n'
                        self.out_msg += '-----------------------------------\n'
                    else:
                        self.out_msg += 'Connection unsuccessful\n'
                elif my_msg[0] == '?':
                    term = my_msg[1:].strip()
                    mysend(self.s, json.dumps({"action":"search", "target":term}))
                    search_rslt = json.loads(myrecv(self.s))["results"].strip()
                    if (len(search_rslt) > 0):
                        self.out_msg += search_rslt + '\n\n'
                    else:
                        self.out_msg += '\'' + term + '\'' + ' not found\n\n'
                elif my_msg[0] == 'p' and my_msg[1:].strip().isdigit():
                    poem_idx = my_msg[1:].strip()
                    mysend(self.s, json.dumps({"action":"poem", "target":poem_idx}))
                    poem = json.loads(myrecv(self.s))["results"]
                    if (len(poem) > 0):
                        self.out_msg += poem + '\n\n'
                    else:
                        self.out_msg += 'Sonnet ' + poem_idx + ' not found\n\n'
                else:
                    mysend(self.s, json.dumps({"action":"exchange", "from":"[" + self.me + "]", "message":my_msg}))
            if len(peer_msg) > 0:    # peer's stuff, coming in
                peer_msg = json.loads(peer_msg)
                if peer_msg["action"] == "connect":
                    self.out_msg += "(" + peer_msg["from"] + " joined)\n"
                elif peer_msg["action"] == "disconnect":
                    self.state = S_LOGGEDIN
                elif peer_msg["action"] == "file":
                    self.out_msg += FILE_RECV_PREFIX + json.dumps(peer_msg)
                elif self.handle_incoming_common(peer_msg):
                    pass
                else:
                    self.out_msg += peer_msg["from"] + peer_msg["message"]


            # Display the menu again
            if self.state == S_LOGGEDIN:
                self.out_msg += menu
#==============================================================================
# invalid state
#==============================================================================
        else:
            self.out_msg += 'How did you wind up here??\n'
            print_state(self.state)

        return self.out_msg
