"""
Created on Tue Jul 22 00:47:05 2014

@author: alina, zzhang
"""

import time
import socket
import select
import sys
import string
import indexer
import json
import pickle as pkl
from chat_utils import *
import chat_group as grp

class Server:
    def __init__(self):
        self.new_clients = [] #list of new sockets of which the user id is not known
        self.logged_name2sock = {} #dictionary mapping username to socket
        self.logged_sock2name = {} # dict mapping socket to user name
        self.all_sockets = []
        self.group = grp.Group()
        self.scoreboards = {}
        self.tictactoe_waiting = None
        self.tictactoe_sessions = {}
        #start server
        self.server=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind(SERVER)
        self.server.listen(5)
        self.all_sockets.append(self.server)
        #initialize past chat indices
        self.indices={}
        # sonnet
        # self.sonnet_f = open('AllSonnets.txt.idx', 'rb')
        # self.sonnet = pkl.load(self.sonnet_f)
        # self.sonnet_f.close()
        self.sonnet = indexer.PIndex("AllSonnets.txt")

    def record_game_score(self, name, game, score):
        try:
            score = int(score)
        except (TypeError, ValueError):
            score = 0
        if score < 0:
            score = 0

        entry = {
            "name": name,
            "score": score,
            "time": time.strftime('%d.%m.%y,%H:%M', time.localtime())
        }
        if game not in self.scoreboards:
            self.scoreboards[game] = []

        replaced = False
        for index, old_entry in enumerate(self.scoreboards[game]):
            if old_entry["name"] == name:
                if score > old_entry["score"]:
                    self.scoreboards[game][index] = entry
                replaced = True
                break

        if replaced == False:
            self.scoreboards[game].append(entry)

        self.scoreboards[game].sort(key = lambda item: item["score"], reverse = True)
        self.scoreboards[game] = self.scoreboards[game][:10]

    def scoreboard_msg(self, game):
        return json.dumps({
            "action": "scoreboard",
            "game": game,
            "scores": self.scoreboards.get(game, [])
        })

    def send_scoreboard(self, sock, game):
        mysend(sock, self.scoreboard_msg(game))

    def broadcast_scoreboard(self, game):
        msg = self.scoreboard_msg(game)
        for sock in list(self.logged_name2sock.values()):
            mysend(sock, msg)

    def tictactoe_state_msg(self, session, status = "playing", message = ""):
        return json.dumps({
            "action": "tictactoe_state",
            "status": status,
            "board": session["board"],
            "turn": session["turn"],
            "players": session["players"],
            "winner": session["winner"],
            "message": message
        })

    def send_tictactoe_state(self, name, status = "playing", message = ""):
        if name not in self.tictactoe_sessions:
            return
        sock = self.logged_name2sock.get(name)
        if sock is not None:
            mysend(sock, self.tictactoe_state_msg(
                self.tictactoe_sessions[name], status, message))

    def broadcast_tictactoe_state(self, session, status = "playing", message = ""):
        msg = self.tictactoe_state_msg(session, status, message)
        for player_name in session["players"].values():
            sock = self.logged_name2sock.get(player_name)
            if sock is not None:
                mysend(sock, msg)

    def send_tictactoe_error(self, sock, message):
        mysend(sock, json.dumps({
            "action": "tictactoe_error",
            "message": message
        }))

    def find_tictactoe_winner(self, board):
        winning_lines = [
            (0, 1, 2), (3, 4, 5), (6, 7, 8),
            (0, 3, 6), (1, 4, 7), (2, 5, 8),
            (0, 4, 8), (2, 4, 6)
        ]
        for a, b, c in winning_lines:
            if board[a] != "" and board[a] == board[b] and board[b] == board[c]:
                return board[a]
        if "" not in board:
            return "draw"
        return None

    def start_tictactoe(self, sock):
        name = self.logged_sock2name[sock]
        if name in self.tictactoe_sessions:
            self.send_tictactoe_state(name, "playing", "You are already in a Tic-Tac-Toe game.")
            return

        if self.tictactoe_waiting == name:
            self.send_tictactoe_error(sock, "Waiting for another player to join Tic-Tac-Toe.")
            return

        if self.tictactoe_waiting is None:
            self.tictactoe_waiting = name
            mysend(sock, json.dumps({
                "action": "tictactoe_state",
                "status": "waiting",
                "board": [""] * 9,
                "turn": "X",
                "players": {"X": name, "O": ""},
                "winner": None,
                "message": "Waiting for another player..."
            }))
            return

        first_player = self.tictactoe_waiting
        self.tictactoe_waiting = None
        session = {
            "board": [""] * 9,
            "turn": "X",
            "players": {
                "X": first_player,
                "O": name
            },
            "winner": None
        }
        self.tictactoe_sessions[first_player] = session
        self.tictactoe_sessions[name] = session
        self.broadcast_tictactoe_state(session, "playing", "Tic-Tac-Toe game started.")

    def make_tictactoe_move(self, sock, position):
        name = self.logged_sock2name[sock]
        if name not in self.tictactoe_sessions:
            self.send_tictactoe_error(sock, "You are not in a Tic-Tac-Toe game.")
            return

        session = self.tictactoe_sessions[name]
        if session["winner"] is not None:
            self.send_tictactoe_error(sock, "This Tic-Tac-Toe game is already over.")
            return

        symbol = None
        for mark, player_name in session["players"].items():
            if player_name == name:
                symbol = mark
                break

        if symbol != session["turn"]:
            self.send_tictactoe_error(sock, "It is not your turn.")
            return

        try:
            position = int(position)
        except (TypeError, ValueError):
            self.send_tictactoe_error(sock, "Invalid Tic-Tac-Toe move.")
            return

        if position < 0 or position > 8:
            self.send_tictactoe_error(sock, "Move must be inside the board.")
            return
        if session["board"][position] != "":
            self.send_tictactoe_error(sock, "That square is already taken.")
            return

        session["board"][position] = symbol
        session["winner"] = self.find_tictactoe_winner(session["board"])
        if session["winner"] is None:
            session["turn"] = "O" if session["turn"] == "X" else "X"
            self.broadcast_tictactoe_state(session, "playing", name + " moved.")
        else:
            status = "draw" if session["winner"] == "draw" else "finished"
            if session["winner"] == "draw":
                message = "Tic-Tac-Toe ended in a draw."
            else:
                message = session["players"][session["winner"]] + " wins Tic-Tac-Toe!"
            players = list(session["players"].values())
            self.broadcast_tictactoe_state(session, status, message)
            for player_name in players:
                if player_name in self.tictactoe_sessions:
                    del self.tictactoe_sessions[player_name]

    def leave_tictactoe(self, sock):
        name = self.logged_sock2name.get(sock)
        if name is None:
            return
        if self.tictactoe_waiting == name:
            self.tictactoe_waiting = None
            return
        if name not in self.tictactoe_sessions:
            return

        session = self.tictactoe_sessions[name]
        opponent = None
        for player_name in session["players"].values():
            if player_name != name:
                opponent = player_name
                break

        for player_name in list(session["players"].values()):
            if player_name in self.tictactoe_sessions:
                del self.tictactoe_sessions[player_name]

        if opponent in self.logged_name2sock:
            ended_session = {
                "board": session["board"],
                "turn": session["turn"],
                "players": session["players"],
                "winner": None
            }
            mysend(self.logged_name2sock[opponent], self.tictactoe_state_msg(
                ended_session, "finished", name + " left Tic-Tac-Toe."))

    def new_client(self, sock):
        #add to all sockets and to new clients
        print('new client...')
        sock.setblocking(0)
        self.new_clients.append(sock)
        self.all_sockets.append(sock)

    def login(self, sock):
        #read the msg that should have login code plus username
        try:
            msg = json.loads(myrecv(sock))
            print("login:", msg)
            if len(msg) > 0:

                if msg["action"] == "login":
                    name = msg["name"]
                    
                    if self.group.is_member(name) != True:
                        #move socket from new clients list to logged clients
                        self.new_clients.remove(sock)
                        #add into the name to sock mapping
                        self.logged_name2sock[name] = sock
                        self.logged_sock2name[sock] = name
                        #load chat history of that user
                        if name not in self.indices.keys():
                            try:
                                self.indices[name]=pkl.load(open(name+'.idx','rb'))
                            except IOError: #chat index does not exist, then create one
                                self.indices[name] = indexer.Index(name)
                        print(name + ' logged in')
                        self.group.join(name)
                        mysend(sock, json.dumps({"action":"login", "status":"ok"}))
                    else: #a client under this name has already logged in
                        mysend(sock, json.dumps({"action":"login", "status":"duplicate"}))
                        print(name + ' duplicate login attempt')
                else:
                    print ('wrong code received')
            else: #client died unexpectedly
                self.logout(sock)
        except:
            self.all_sockets.remove(sock)

    def logout(self, sock):
        #remove sock from all lists
        name = self.logged_sock2name[sock]
        self.leave_tictactoe(sock)
        pkl.dump(self.indices[name], open(name + '.idx','wb'))
        del self.indices[name]
        del self.logged_name2sock[name]
        del self.logged_sock2name[sock]
        self.all_sockets.remove(sock)
        self.group.leave(name)
        sock.close()

#==============================================================================
# main command switchboard
#==============================================================================
    def handle_msg(self, from_sock):
        #read msg code
        msg = myrecv(from_sock)
        if len(msg) > 0:
#==============================================================================
# handle connect request
#==============================================================================
            msg = json.loads(msg)
            if msg["action"] == "connect":
                to_name = msg["target"]
                from_name = self.logged_sock2name[from_sock]
                if to_name == from_name:
                    msg = json.dumps({"action":"connect", "status":"self"})
                # connect to the peer
                elif self.group.is_member(to_name):
                    to_sock = self.logged_name2sock[to_name]
                    from_was_in_group, _ = self.group.find_group(from_name)
                    peer_was_in_group, _ = self.group.find_group(to_name)
                    self.group.connect(from_name, to_name)
                    the_guys = self.group.list_me(from_name)
                    msg = json.dumps({"action":"connect", "status":"success"})
                    for g in the_guys[1:]:
                        to_sock = self.logged_name2sock[g]
                        if from_was_in_group == True and peer_was_in_group == False and g != to_name:
                            joined_name = to_name
                        else:
                            joined_name = from_name
                        mysend(to_sock, json.dumps({"action":"connect", "status":"request", "from":joined_name}))
                else:
                    msg = json.dumps({"action":"connect", "status":"no-user"})
                mysend(from_sock, msg)
#==============================================================================
# handle messeage exchange: one peer for now. will need multicast later
#==============================================================================
            elif msg["action"] == "exchange":
                from_name = self.logged_sock2name[from_sock]
                the_guys = self.group.list_me(from_name)
                #said = msg["from"]+msg["message"]
                said2 = text_proc(msg["message"], from_name)
                self.indices[from_name].add_msg_and_index(said2)
                for g in the_guys[1:]:
                    to_sock = self.logged_name2sock[g]
                    self.indices[g].add_msg_and_index(said2)
                    mysend(to_sock, json.dumps({"action":"exchange", "from":msg["from"], "message":msg["message"]}))
#==============================================================================
# handle file transfer
#==============================================================================
            elif msg["action"] == "file":
                from_name = self.logged_sock2name[from_sock]
                the_guys = self.group.list_me(from_name)
                filename = msg["filename"]
                file_note = text_proc("[file] " + filename, from_name)
                self.indices[from_name].add_msg_and_index(file_note)
                for g in the_guys[1:]:
                    to_sock = self.logged_name2sock[g]
                    self.indices[g].add_msg_and_index(file_note)
                    mysend(to_sock, json.dumps({
                        "action": "file",
                        "from": msg["from"],
                        "filename": filename,
                        "size": msg["size"],
                        "data": msg["data"]
                    }))
#==============================================================================
# handle single-player game scores
#==============================================================================
            elif msg["action"] == "score_submit":
                from_name = self.logged_sock2name[from_sock]
                game = msg.get("game", "snake")
                score = msg.get("score", 0)
                self.record_game_score(from_name, game, score)
                self.broadcast_scoreboard(game)

            elif msg["action"] == "scoreboard_request":
                game = msg.get("game", "snake")
                self.send_scoreboard(from_sock, game)
#==============================================================================
# handle interactive Tic-Tac-Toe multiplayer game
#==============================================================================
            elif msg["action"] == "tictactoe_start":
                self.start_tictactoe(from_sock)

            elif msg["action"] == "tictactoe_move":
                self.make_tictactoe_move(from_sock, msg.get("position"))

            elif msg["action"] == "tictactoe_leave":
                self.leave_tictactoe(from_sock)
#==============================================================================
#                 listing available peers
#==============================================================================
            elif msg["action"] == "list":
                from_name = self.logged_sock2name[from_sock]
                msg = self.group.list_all()
                mysend(from_sock, json.dumps({"action":"list", "results":msg}))
#==============================================================================
#             retrieve a sonnet
#==============================================================================
            elif msg["action"] == "poem":
                poem_indx = int(msg["target"])
                from_name = self.logged_sock2name[from_sock]
                print(from_name + ' asks for ', poem_indx)
                poem = self.sonnet.get_poem(poem_indx)
                poem = '\n'.join(poem).strip()
                print('here:\n', poem)
                mysend(from_sock, json.dumps({"action":"poem", "results":poem}))
#==============================================================================
#                 time
#==============================================================================
            elif msg["action"] == "time":
                ctime = time.strftime('%d.%m.%y,%H:%M', time.localtime())
                mysend(from_sock, json.dumps({"action":"time", "results":ctime}))
#==============================================================================
#                 search
#==============================================================================
            elif msg["action"] == "search":
                term = msg["target"]
                from_name = self.logged_sock2name[from_sock]
                print('search for ' + from_name + ' for ' + term)
                # search_rslt = (self.indices[from_name].search(term))
                search_rslt = '\n'.join([x[-1] for x in self.indices[from_name].search(term)])
                print('server side search: ' + search_rslt)
                mysend(from_sock, json.dumps({"action":"search", "results":search_rslt}))
#==============================================================================
# the "from" guy has had enough (talking to "to")!
#==============================================================================
            elif msg["action"] == "disconnect":
                from_name = self.logged_sock2name[from_sock]
                the_guys = self.group.list_me(from_name)
                self.group.disconnect(from_name)
                the_guys.remove(from_name)
                if len(the_guys) == 1:  # only one left
                    g = the_guys.pop()
                    to_sock = self.logged_name2sock[g]
                    mysend(to_sock, json.dumps({"action":"disconnect"}))
#==============================================================================
#                 the "from" guy really, really has had enough
#==============================================================================

        else:
            #client died unexpectedly
            self.logout(from_sock)

#==============================================================================
# main loop, loops *forever*
#==============================================================================
    def run(self):
        print ('starting server...')
        while(1):
           read,write,error=select.select(self.all_sockets,[],[])
           print('checking logged clients..')
           for logc in list(self.logged_name2sock.values()):
               if logc in read:
                   self.handle_msg(logc)
           print('checking new clients..')
           for newc in self.new_clients[:]:
               if newc in read:
                   self.login(newc)
           print('checking for new connections..')
           if self.server in read :
               #new client request
               sock, address=self.server.accept()
               self.new_client(sock)

def main():
    server=Server()
    server.run()

if __name__ == "__main__":
    main()
