#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Apr 30 13:36:58 2021

@author: bing
"""

# import all the required  modules
import threading
import select
import base64
import os
from queue import Empty, Queue
from tkinter import *
from tkinter import font
from tkinter import filedialog
from tkinter import messagebox
from tkinter import simpledialog
from tkinter import ttk
from chat_utils import *
import json

BOT_UI_PREFIX = "__chatbot_reply__:"
BOT_ERROR_PREFIX = "__chatbot_error__:"
AIPIC_UI_PREFIX = "__aipic_image__:"
AIPIC_ERROR_PREFIX = "__aipic_error__:"
NLP_UI_PREFIX = "__chat_nlp_reply__:"
NLP_ERROR_PREFIX = "__chat_nlp_error__:"

# GUI class for the chat
class GUI:
    # constructor method
    def __init__(self, send, recv, sm, s):
        # chat window which is currently hidden
        self.Window = Tk()
        self.Window.withdraw()
        self.send = send
        self.recv = recv
        self.sm = sm
        self.socket = s
        self.my_msg = ""
        self.system_msg = ""
        self.outgoing_msgs = Queue()
        self.ui_msgs = Queue()
        self.running = False
        self.process = None
        self.polling_ui = False
        self.emoji_panel_visible = False
        self.bot = None
        self.bot_name = "AI_Bot"
        self.bot_personality = "friendly Python learning assistant"
        self.bot_chat_active = False
        self.aipic_mode_active = False
        self.botStyleButton = None
        self.chatbotButton = None
        self.aipicButton = None
        self.group_bot_invited = False
        self.snake_game = None
        self.tictactoe_game = None
        self.tictactoe_room = ""
        self.chat_images = []
        self.chat_history = []
        self.sidebar_groups = {}
        self.current_sidebar_body = None

    def login(self):
        # login window
        self.login = Toplevel()
        # set the title
        self.login.title("Login")
        self.login.resizable(width = False, 
                             height = False)
        self.login.configure(width = 400,
                             height = 300)
        # create a Label
        self.pls = Label(self.login, 
                       text = "Please login to continue",
                       justify = CENTER, 
                       font = "Helvetica 14 bold")
          
        self.pls.place(relheight = 0.15,
                       relx = 0.2, 
                       rely = 0.07)
        # create a Label
        self.labelName = Label(self.login,
                               text = "Name: ",
                               font = "Helvetica 12")
          
        self.labelName.place(relheight = 0.2,
                             relx = 0.1, 
                             rely = 0.2)
          
        # create a entry box for 
        # tyoing the message
        self.entryName = Entry(self.login, 
                             font = "Helvetica 14")
          
        self.entryName.place(relwidth = 0.4, 
                             relheight = 0.12,
                             relx = 0.35,
                             rely = 0.2)
          
        # set the focus of the curser
        self.entryName.focus()
        self.entryName.bind("<Return>", lambda event: self.goAhead(self.entryName.get()))
          
        # create a Continue Button 
        # along with action
        self.go = Button(self.login,
                         text = "CONTINUE", 
                         font = "Helvetica 14 bold", 
                         command = lambda: self.goAhead(self.entryName.get()))
          
        self.go.place(relx = 0.4,
                      rely = 0.55)
        self.Window.mainloop()
  
    def goAhead(self, name):
        name = name.strip()
        if len(name) > 0:
            msg = json.dumps({"action":"login", "name": name})
            self.send(msg)
            response = json.loads(self.recv())
            if response["status"] == 'ok':
                self.login.destroy()
                self.sm.set_state(S_LOGGEDIN)
                self.sm.set_myname(name)
                self.layout(name)
                self.display_system_message(menu)
                self.running = True
                self.start_ui_queue()
                self.entryMsg.focus_set()
                # while True:
                #     self.proc()
                # the thread to receive messages
                self.process = threading.Thread(target=self.proc)
                self.process.daemon = True
                self.process.start()
            else:
                messagebox.showerror("Login failed", "This name is already in use.")
        else:
            messagebox.showwarning("Login", "Please enter a name.")
  
    # The main layout of the chat
    def layout(self,name):
        
        self.name = name
        # to show chat window
        self.Window.deiconify()
        self.Window.title("CHATROOM")
        self.Window.resizable(width = False,
                              height = False)
        self.Window.geometry("780x560")
        self.Window.configure(bg = "#F5F5F5")

        self.headerFrame = Frame(self.Window,
                                 bg = "#07C160",
                                 height = 44)
        self.headerFrame.pack(side = TOP,
                              fill = X)
        self.headerFrame.pack_propagate(False)

        self.labelHead = Label(self.headerFrame,
                               bg = "#07C160",
                               fg = "#FFFFFF",
                               text = "Chatroom",
                               font = "Helvetica 14 bold",
                               anchor = W,
                               padx = 16)
        self.labelHead.pack(side = LEFT,
                            fill = BOTH,
                            expand = True)

        self.mainFrame = Frame(self.Window,
                               bg = "#F5F5F5")
        self.mainFrame.pack(side = TOP,
                            fill = BOTH,
                            expand = True)

        self.sidebar = Frame(self.mainFrame,
                             bg = "#FFFFFF",
                             width = 240)
        self.sidebar.pack(side = LEFT,
                          fill = Y)
        self.sidebar.pack_propagate(False)

        self.sidebarCanvas = Canvas(self.sidebar,
                                    bg = "#FFFFFF",
                                    bd = 0,
                                    highlightthickness = 0)
        self.sidebarScrollbar = Scrollbar(self.sidebar,
                                          orient = VERTICAL,
                                          command = self.sidebarCanvas.yview)
        self.sidebarContent = Frame(self.sidebarCanvas,
                                    bg = "#FFFFFF")
        self.sidebarWindow = self.sidebarCanvas.create_window(
            (0, 0),
            window = self.sidebarContent,
            anchor = NW)
        self.sidebarCanvas.config(yscrollcommand = self.sidebarScrollbar.set)
        self.sidebarCanvas.pack(side = LEFT,
                                fill = BOTH,
                                expand = True)
        self.sidebarScrollbar.pack(side = RIGHT,
                                   fill = Y)
        self.sidebarContent.bind("<Configure>", self.update_sidebar_scroll_region)
        self.sidebarCanvas.bind("<Configure>", self.resize_sidebar_content)
        self.bind_sidebar_scroll(self.sidebarCanvas)
        self.bind_sidebar_scroll(self.sidebarContent)

        self.profileTitle = Label(self.sidebarContent,
                                  text = "My Profile",
                                  bg = "#FFFFFF",
                                  fg = "#222222",
                                  font = "Helvetica 12 bold",
                                  anchor = W)
        self.profileTitle.pack(fill = X,
                               padx = 16,
                               pady = (18, 6))
        self.bind_sidebar_scroll(self.profileTitle)

        self.nameLabel = Label(self.sidebarContent,
                               text = "User: " + self.name,
                               bg = "#FFFFFF",
                               fg = "#333333",
                               font = "Helvetica 10",
                               anchor = W)
        self.nameLabel.pack(fill = X,
                            padx = 16,
                            pady = 3)
        self.bind_sidebar_scroll(self.nameLabel)

        self.stateLabel = Label(self.sidebarContent,
                                text = "Status: Online",
                                bg = "#FFFFFF",
                                fg = "#333333",
                                font = "Helvetica 10",
                                anchor = W)
        self.stateLabel.pack(fill = X,
                             padx = 16,
                             pady = 3)
        self.bind_sidebar_scroll(self.stateLabel)

        self.peerLabel = Label(self.sidebarContent,
                               text = "Chatting with: None",
                               bg = "#FFFFFF",
                               fg = "#333333",
                               font = "Helvetica 10",
                               anchor = W,
                               wraplength = 200,
                               justify = LEFT)
        self.peerLabel.pack(fill = X,
                            padx = 16,
                            pady = 3)
        self.bind_sidebar_scroll(self.peerLabel)

        self.add_sidebar_section("Chat")
        self.add_sidebar_button("Who", lambda: self.send_quick_command("who"))
        self.add_sidebar_button("Connect", self.ask_connect)

        self.add_sidebar_section("Game")
        self.add_sidebar_button("Play Snake", self.start_snake_game,
                                bg = "#07C160",
                                fg = "#FFFFFF",
                                activebackground = "#06AD56",
                                activeforeground = "#FFFFFF")
        self.add_sidebar_button("Leaderboard", self.request_snake_leaderboard)
        self.add_sidebar_button("Tic-Tac-Toe", self.start_tictactoe_game,
                                bg = "#EAF2FF",
                                activebackground = "#D8E8FF")

        self.add_sidebar_section("AI Assistant")
        self.chatbotButton = self.add_sidebar_button("Bot", self.ask_chatbot,
                                                     bg = "#FFE7A3",
                                                     activebackground = "#FFD980")
        self.aipicButton = self.add_sidebar_button("AI Picture", self.ask_aipic_mode,
                                                   bg = "#EAF2FF",
                                                   activebackground = "#D8E8FF")
        self.botStyleButton = self.add_sidebar_button("Bot Style", self.ask_bot_personality)

        self.add_sidebar_section("Tools")
        self.add_sidebar_button("Time", lambda: self.send_quick_command("time"))
        self.add_sidebar_button("Poem", self.ask_poem)
        self.add_sidebar_button("Search", self.ask_search)
        self.add_sidebar_button("Summary", self.show_chat_summary)
        self.add_sidebar_button("Keywords", self.show_chat_keywords)
        self.add_sidebar_button("Clear Chat", self.clear_chat)

        self.rightPanel = Frame(self.mainFrame,
                                bg = "#F5F5F5")
        self.rightPanel.pack(side = LEFT,
                             fill = BOTH,
                             expand = True)

        self.chatHeader = Frame(self.rightPanel,
                                bg = "#F5F5F5",
                                height = 44)
        self.chatHeader.pack(side = TOP,
                             fill = X,
                             padx = 14,
                             pady = (10, 8))
        self.chatHeader.pack_propagate(False)

        self.chatInfo = Label(self.chatHeader,
                              text = "No active chat",
                              bg = "#F5F5F5",
                              fg = "#555555",
                              font = "Helvetica 11 bold",
                              anchor = W)
        self.chatInfo.pack(side = LEFT,
                           fill = BOTH,
                           expand = True)

        # Window area for displaying chat and system messages.
        self.messageFrame = Frame(self.rightPanel,
                                  bg = "#FFFFFF",
                                  bd = 1,
                                  relief = SOLID)
        self.messageFrame.pack(side = TOP,
                               fill = BOTH,
                               expand = True,
                               padx = 14,
                               pady = (0, 10))

        self.textCons = Text(self.messageFrame,
                             width = 20,
                             height = 2,
                             bg = "#FFFFFF",
                             fg = "#111111",
                             font = "Helvetica 11",
                             padx = 14,
                             pady = 12,
                             wrap = WORD,
                             bd = 0,
                             relief = FLAT,
                             state = DISABLED)

        self.textCons.pack(side = LEFT,
                           fill = BOTH,
                           expand = True)

        scrollbar = Scrollbar(self.messageFrame,
                              command = self.textCons.yview)
        scrollbar.pack(side = RIGHT,
                       fill = Y)
        self.textCons.config(yscrollcommand = scrollbar.set)
        self.textCons.tag_config("system",
                                 foreground = "#888888",
                                 justify = CENTER,
                                 spacing1 = 4,
                                 spacing3 = 4)
        self.textCons.tag_config("me",
                                 foreground = "#111111",
                                 background = "#B7E6B7",
                                 justify = RIGHT,
                                 rmargin = 12,
                                 lmargin1 = 120,
                                 lmargin2 = 120,
                                 spacing1 = 6,
                                 spacing3 = 6)
        self.textCons.tag_config("peer",
                                 foreground = "#111111",
                                 background = "#EAF2FF",
                                 justify = LEFT,
                                 lmargin1 = 12,
                                 lmargin2 = 12,
                                 rmargin = 120,
                                 spacing1 = 6,
                                 spacing3 = 6)
        self.textCons.tag_config("bot",
                                 foreground = "#111111",
                                 background = "#FFF4D6",
                                 justify = LEFT,
                                 lmargin1 = 12,
                                 lmargin2 = 12,
                                 rmargin = 120,
                                 spacing1 = 6,
                                 spacing3 = 6)
          
        self.labelBottom = Frame(self.rightPanel,
                                 bg = "#F5F5F5",
                                 height = 64)
          
        self.labelBottom.pack(side = BOTTOM,
                              fill = X,
                              padx = 14,
                              pady = (0, 14))
        self.labelBottom.pack_propagate(False)
          
        self.emojiButton = Button(self.labelBottom,
                                  text = "\u263A",
                                  font = ("Segoe UI Symbol", 16),
                                  width = 3,
                                  bg = "#F5F5F5",
                                  fg = "#333333",
                                  activebackground = "#E5E7EB",
                                  activeforeground = "#111111",
                                  relief = FLAT,
                                  command = self.toggle_emoji_panel)
        self.emojiButton.pack(side = LEFT,
                              fill = Y,
                              padx = (0, 8),
                              pady = 10)

        self.fileButton = Button(self.labelBottom,
                                 text = "File",
                                 font = "Helvetica 10",
                                 width = 5,
                                 bg = "#F5F5F5",
                                 fg = "#333333",
                                 activebackground = "#E5E7EB",
                                 activeforeground = "#111111",
                                 relief = FLAT,
                                 command = self.send_file)
        self.fileButton.pack(side = LEFT,
                             fill = Y,
                             padx = (0, 8),
                             pady = 10)

        self.entryMsg = Entry(self.labelBottom,
                              bg = "#FFFFFF",
                              fg = "#111111",
                              insertbackground = "#111111",
                              font = "Helvetica 12",
                              relief = SOLID,
                              bd = 1)
          
        # place the given widget
        # into the gui window
        self.entryMsg.pack(side = LEFT,
                           fill = BOTH,
                           expand = True,
                           padx = (0, 10),
                           pady = 10)
          
        self.entryMsg.focus()
        self.entryMsg.bind("<Return>", lambda event: self.sendButton(self.entryMsg.get()))
        self.Window.bind("<Return>", lambda event: self.sendButton(self.entryMsg.get()))
          
        # create a Send Button
        self.buttonMsg = Button(self.labelBottom,
                                text = "Send",
                                font = "Helvetica 10 bold",
                                width = 10,
                                bg = "#07C160",
                                fg = "#FFFFFF",
                                activebackground = "#06AD56",
                                activeforeground = "#FFFFFF",
                                relief = FLAT,
                                command = lambda : self.sendButton(self.entryMsg.get()))
          
        self.buttonMsg.pack(side = RIGHT,
                            fill = Y,
                            pady = 10)
          
        self.textCons.config(cursor = "arrow")
          
        self.textCons.config(state = DISABLED)
        try:
            self.add_emoji_panel()
        except Exception:
            self.emojiPanel = None
        self.update_sidebar()

    def update_sidebar_scroll_region(self, event = None):
        self.sidebarCanvas.configure(scrollregion = self.sidebarCanvas.bbox("all"))

    def resize_sidebar_content(self, event):
        self.sidebarCanvas.itemconfig(self.sidebarWindow, width = event.width)

    def bind_sidebar_scroll(self, widget):
        widget.bind("<MouseWheel>", self.on_sidebar_mousewheel)
        widget.bind("<Button-4>", self.on_sidebar_mousewheel)
        widget.bind("<Button-5>", self.on_sidebar_mousewheel)

    def on_sidebar_mousewheel(self, event):
        if event.num == 4:
            self.sidebarCanvas.yview_scroll(-1, "units")
        elif event.num == 5:
            self.sidebarCanvas.yview_scroll(1, "units")
        else:
            self.sidebarCanvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def add_sidebar_section(self, text, collapsed = False):
        title = text.upper()
        group = Frame(self.sidebarContent,
                      bg = "#FFFFFF")
        group.pack(fill = X)
        self.bind_sidebar_scroll(group)

        header = Button(group,
                        text = "[-] " + title,
                        font = "Helvetica 9 bold",
                        bg = "#FFFFFF",
                        fg = "#666666",
                        activebackground = "#F2F3F5",
                        activeforeground = "#222222",
                        relief = FLAT,
                        anchor = W,
                        padx = 4,
                        command = lambda key = text: self.toggle_sidebar_section(key))
        header.pack(fill = X,
                    padx = 12,
                    pady = (20, 6))
        self.bind_sidebar_scroll(header)

        body = Frame(group,
                     bg = "#FFFFFF")
        body.pack(fill = X)
        self.bind_sidebar_scroll(body)

        self.sidebar_groups[text] = {
            "title": title,
            "header": header,
            "body": body,
            "collapsed": False
        }
        self.current_sidebar_body = body
        if collapsed == True:
            self.toggle_sidebar_section(text)
        return body

    def toggle_sidebar_section(self, text):
        group = self.sidebar_groups[text]
        if group["collapsed"] == True:
            group["body"].pack(fill = X)
            group["header"].config(text = "[-] " + group["title"])
            group["collapsed"] = False
        else:
            group["body"].pack_forget()
            group["header"].config(text = "[+] " + group["title"])
            group["collapsed"] = True
        self.update_sidebar_scroll_region()

    def add_sidebar_button(self, text, command,
                           bg = "#F2F3F5",
                           fg = "#222222",
                           activebackground = "#E5E7EB",
                           activeforeground = "#111111"):
        parent = self.current_sidebar_body
        if parent is None:
            parent = self.sidebarContent
        button = Button(parent,
                        text = text,
                        font = "Helvetica 10",
                        bg = bg,
                        fg = fg,
                        activebackground = activebackground,
                        activeforeground = activeforeground,
                        relief = FLAT,
                        anchor = W,
                        padx = 12,
                        command = command)
        button.pack(fill = X,
                    padx = 16,
                    pady = 4)
        self.bind_sidebar_scroll(button)
        return button

    def add_emoji_panel(self):
        self.emojiPanel = Frame(self.rightPanel,
                                bg = "#FFFFFF",
                                bd = 1,
                                relief = SOLID)
        emojis = [
            "\U0001F600",
            "\U0001F602",
            "\U0001F60A",
            "\U0001F44D",
            "\u2764",
            "\U0001F389",
            "\U0001F525",
            "\U0001F64F",
        ]
        fallbacks = [":)", ":D", "^_^", "+1", "<3", "yay", "!!", "thx"]

        for index, emoji in enumerate(emojis):
            try:
                button = self.create_emoji_button(emoji)
            except TclError:
                button = self.create_emoji_button(fallbacks[index])
            button.grid(row = index // 4,
                        column = index % 4,
                        padx = 3,
                        pady = 3)

    def create_emoji_button(self, emoji):
        return Button(self.emojiPanel,
                      text = emoji,
                      font = ("Segoe UI Emoji", 12),
                      bg = "#F2F3F5",
                      fg = "#111111",
                      activebackground = "#E5E7EB",
                      relief = FLAT,
                      width = 3,
                      command = lambda value = emoji: self.insert_emoji(value))

    def toggle_emoji_panel(self):
        if self.emojiPanel is None:
            messagebox.showinfo("Emoji", "Emoji panel is not available on this system.")
            return

        if self.emoji_panel_visible == True:
            self.emojiPanel.pack_forget()
            self.emoji_panel_visible = False
        else:
            self.emojiPanel.pack(side = BOTTOM,
                                 fill = X,
                                 padx = 14,
                                 pady = (0, 8))
            self.emoji_panel_visible = True

    def insert_emoji(self, emoji):
        self.entryMsg.insert(INSERT, emoji)
        self.entryMsg.focus()

    def send_file(self):
        if self.sm.get_state() != S_CHATTING:
            messagebox.showinfo("File Transfer", "Connect to another user before sending a file.")
            return

        file_path = filedialog.askopenfilename(parent = self.Window,
                                               title = "Choose a file to send")
        if len(file_path) == 0:
            return

        file_size = os.path.getsize(file_path)
        if file_size > 5 * 1024 * 1024:
            messagebox.showwarning("File Transfer", "Please choose a file smaller than 5 MB.")
            return

        with open(file_path, "rb") as file:
            encoded = base64.b64encode(file.read()).decode("ascii")

        filename = os.path.basename(file_path)
        payload = {
            "filename": filename,
            "size": file_size,
            "data": encoded
        }
        self.outgoing_msgs.put(FILE_CMD_PREFIX + json.dumps(payload))
        self.display_chat_message("Me", "[file] " + filename, "me")
        self.entryMsg.focus()

    def start_snake_game(self):
        if self.aipic_mode_active == True:
            self.exit_aipic_mode()
        if self.bot_chat_active == True:
            self.exit_bot_chat()

        try:
            from snake_game import SnakeGame
            self.snake_game = SnakeGame(
                parent = self.Window,
                player_name = self.name,
                on_game_over = self.submit_snake_score
            )
            self.snake_game.start()
            self.display_system_message("Snake started. Use arrow keys to play.")
        except Exception as exc:
            self.display_system_message("Could not start Snake: " + str(exc))

    def submit_snake_score(self, score):
        payload = {
            "game": "snake",
            "score": score
        }
        self.outgoing_msgs.put(GAME_SCORE_PREFIX + json.dumps(payload))
        self.display_system_message("Snake game over. Score submitted: " + str(score))

    def request_snake_leaderboard(self):
        if self.aipic_mode_active == True:
            self.exit_aipic_mode()
        if self.bot_chat_active == True:
            self.exit_bot_chat()
        self.outgoing_msgs.put(GAME_LEADERBOARD_PREFIX + "snake")
        self.display_system_message("Requesting Snake leaderboard...")
        self.entryMsg.focus()

    def start_tictactoe_game(self):
        if self.aipic_mode_active == True:
            self.exit_aipic_mode()
        if self.bot_chat_active == True:
            self.exit_bot_chat()

        room = simpledialog.askstring("Tic-Tac-Toe Room",
                                      "Enter room number:",
                                      initialvalue = self.tictactoe_room,
                                      parent = self.Window)
        if room is None:
            return
        room = room.strip()
        if len(room) == 0:
            messagebox.showwarning("Tic-Tac-Toe", "Please enter a room number.")
            return
        self.tictactoe_room = room

        try:
            from tictactoe_game import TicTacToeGame
            if self.tictactoe_game is None:
                self.tictactoe_game = TicTacToeGame(
                    parent = self.Window,
                    player_name = self.name,
                    on_start = self.request_tictactoe_start,
                    on_move = self.send_tictactoe_move,
                    on_leave = self.leave_tictactoe_game
                )
            self.tictactoe_game.set_room(self.tictactoe_room)
            self.tictactoe_game.start()
            self.request_tictactoe_start()
            self.display_system_message("Tic-Tac-Toe room " + self.tictactoe_room + " matchmaking started.")
        except Exception as exc:
            self.display_system_message("Could not start Tic-Tac-Toe: " + str(exc))

    def request_tictactoe_start(self):
        if len(self.tictactoe_room.strip()) == 0:
            room = simpledialog.askstring("Tic-Tac-Toe Room",
                                          "Enter room number:",
                                          parent = self.Window)
            if room is None or len(room.strip()) == 0:
                return
            self.tictactoe_room = room.strip()
            if self.tictactoe_game is not None:
                self.tictactoe_game.set_room(self.tictactoe_room)
        self.outgoing_msgs.put(TICTACTOE_START_PREFIX + self.tictactoe_room)

    def send_tictactoe_move(self, position):
        payload = {
            "position": position
        }
        self.outgoing_msgs.put(TICTACTOE_MOVE_PREFIX + json.dumps(payload))

    def leave_tictactoe_game(self):
        self.outgoing_msgs.put(TICTACTOE_LEAVE_PREFIX)

    def handle_tictactoe_event(self, event_json):
        try:
            event = json.loads(event_json)
        except json.JSONDecodeError:
            self.display_system_message("Invalid Tic-Tac-Toe update received.")
            return

        if event.get("action") == "tictactoe_error":
            message = event.get("message", "Tic-Tac-Toe error.")
            if self.tictactoe_game is not None:
                self.tictactoe_game.show_error(message)
            self.display_system_message(message)
            return

        if event.get("action") != "tictactoe_state":
            return

        try:
            from tictactoe_game import TicTacToeGame
            if self.tictactoe_game is None:
                self.tictactoe_game = TicTacToeGame(
                    parent = self.Window,
                    player_name = self.name,
                    on_start = self.request_tictactoe_start,
                    on_move = self.send_tictactoe_move,
                    on_leave = self.leave_tictactoe_game
                )
            room = event.get("room", "")
            if len(room) > 0:
                self.tictactoe_room = room
                self.tictactoe_game.set_room(room)
            self.tictactoe_game.start()
            self.tictactoe_game.apply_state(event)
        except Exception as exc:
            self.display_system_message("Could not update Tic-Tac-Toe: " + str(exc))

        message = event.get("message", "")
        if len(message) > 0:
            self.display_system_message(message)

    def update_sidebar(self):
        if self.aipic_mode_active == True:
            status = "AI Picture"
            chat_text = "Chatting with: AI Picture"
            info_text = "AI Picture mode"
        elif self.bot_chat_active == True:
            status = "ChatBot"
            chat_text = "Chatting with: " + self.bot_name
            info_text = "ChatBot mode: " + self.bot_name
        elif self.sm.get_state() == S_CHATTING and len(self.sm.peer) > 0:
            peer = self.sm.peer
            status = "Chatting"
            chat_text = "Chatting with: " + peer
            info_text = "Chatting with " + peer
        else:
            status = "Online"
            chat_text = "Chatting with: None"
            info_text = "No active chat"

        self.stateLabel.config(text = "Status: " + status)
        self.peerLabel.config(text = chat_text)
        self.chatInfo.config(text = info_text)

    def send_quick_command(self, command):
        if self.aipic_mode_active == True:
            self.exit_aipic_mode()
        if self.bot_chat_active == True:
            self.exit_bot_chat()
        self.sendButton(command)

    def can_use_menu_command(self):
        return True

    def ask_connect(self):
        peer = simpledialog.askstring("Connect", "Enter username:", parent = self.Window)
        if peer is not None and len(peer.strip()) > 0:
            if self.aipic_mode_active == True:
                self.exit_aipic_mode()
            if self.bot_chat_active == True:
                self.exit_bot_chat()
            self.sendButton("c " + peer.strip())

    def ask_poem(self):
        poem_idx = simpledialog.askstring("Poem", "Enter sonnet number:", parent = self.Window)
        if poem_idx is not None and len(poem_idx.strip()) > 0:
            if self.aipic_mode_active == True:
                self.exit_aipic_mode()
            if self.bot_chat_active == True:
                self.exit_bot_chat()
            self.sendButton("p " + poem_idx.strip())

    def ask_search(self):
        term = simpledialog.askstring("Search", "Enter search term:", parent = self.Window)
        if term is not None and len(term.strip()) > 0:
            if self.aipic_mode_active == True:
                self.exit_aipic_mode()
            if self.bot_chat_active == True:
                self.exit_bot_chat()
            self.sendButton("? " + term.strip())

    def show_chat_summary(self):
        if self.aipic_mode_active == True:
            self.exit_aipic_mode()
        if self.bot_chat_active == True:
            self.exit_bot_chat()
        self.sendButton("/summary")

    def show_chat_keywords(self):
        if self.aipic_mode_active == True:
            self.exit_aipic_mode()
        if self.bot_chat_active == True:
            self.exit_bot_chat()
        self.sendButton("/keywords")

    def ask_chatbot(self):
        if self.bot_chat_active == True:
            self.exit_bot_chat()
        else:
            self.enter_bot_chat()

    def ask_aipic_mode(self):
        if self.aipic_mode_active == True:
            self.exit_aipic_mode()
        else:
            self.enter_aipic_mode()

    def ask_bot_personality(self):
        personality = simpledialog.askstring(
            "Bot Personality",
            "Describe AI_Bot's personality:",
            initialvalue = self.bot_personality,
            parent = self.Window
        )
        if personality is not None and len(personality.strip()) > 0:
            self.bot_personality = personality.strip()
            if self.bot is not None:
                self.bot.set_personality(self.bot_personality)
            self.display_system_message("AI_Bot personality set to: " + self.bot_personality)

    def clear_chat(self):
        self.textCons.config(state = NORMAL)
        self.textCons.delete("1.0", END)
        self.textCons.config(state = DISABLED)
        self.chat_history = []

    def display_message(self, msg, tag = "system"):
        if len(msg) == 0:
            return

        self.textCons.config(state = NORMAL)
        self.textCons.insert(END, msg + "\n\n", tag)
        self.textCons.config(state = DISABLED)
        self.textCons.see(END)

    def display_system_message(self, msg):
        msg = msg.strip()
        if len(msg) > 0:
            self.display_message("[System] " + msg, "system")

    def display_chat_message(self, sender, msg, tag):
        msg = msg.strip()
        if len(msg) > 0:
            self.add_chat_history(sender, msg)
            self.display_message("[" + sender + "] " + msg, tag)

    def add_chat_history(self, sender, msg):
        msg = msg.strip()
        if len(msg) == 0:
            return
        self.chat_history.append({
            "sender": sender,
            "text": msg
        })
        self.chat_history = self.chat_history[-100:]

    def display_chat_image(self, sender, image_path, prompt):
        if not os.path.exists(image_path):
            self.display_system_message("Generated image file was not found: " + image_path)
            return

        self.textCons.config(state = NORMAL)
        self.textCons.insert(END, "[" + sender + "] AI Picture: " + prompt + "\n", "me")
        self.add_chat_history(sender, "AI Picture prompt: " + prompt)
        try:
            image = PhotoImage(file = image_path)
            if image.width() > 560:
                factor = int(image.width() / 560) + 1
                image = image.subsample(factor, factor)
            self.chat_images.append(image)
            self.textCons.image_create(END, image = image)
            self.textCons.insert(END, "\nSaved: " + image_path + "\n\n", "system")
        except TclError as exc:
            self.textCons.insert(END, "Saved: " + image_path + "\n")
            self.textCons.insert(END, "Could not preview image: " + str(exc) + "\n\n", "system")
        self.textCons.config(state = DISABLED)
        self.textCons.see(END)

    def display_state_output(self, msg):
        msg = msg.strip()
        if len(msg) == 0:
            return

        if msg.startswith(BOT_UI_PREFIX):
            self.display_chat_message(self.bot_name, msg[len(BOT_UI_PREFIX):], "bot")
            self.update_sidebar()
            return

        if msg.startswith(BOT_ERROR_PREFIX):
            self.display_system_message(msg[len(BOT_ERROR_PREFIX):])
            self.update_sidebar()
            return

        if msg.startswith(AIPIC_UI_PREFIX):
            payload = json.loads(msg[len(AIPIC_UI_PREFIX):])
            self.display_chat_image("Me", payload["path"], payload["prompt"])
            self.update_sidebar()
            return

        if msg.startswith(AIPIC_ERROR_PREFIX):
            self.display_system_message(msg[len(AIPIC_ERROR_PREFIX):])
            self.update_sidebar()
            return

        if msg.startswith(NLP_UI_PREFIX):
            self.display_system_message(msg[len(NLP_UI_PREFIX):])
            self.update_sidebar()
            return

        if msg.startswith(NLP_ERROR_PREFIX):
            self.display_system_message(msg[len(NLP_ERROR_PREFIX):])
            self.update_sidebar()
            return

        if msg.startswith(FILE_RECV_PREFIX):
            self.receive_file(msg[len(FILE_RECV_PREFIX):])
            self.update_sidebar()
            return

        event_index = msg.find(TICTACTOE_EVENT_PREFIX)
        if event_index > 0:
            before_event = msg[:event_index].strip()
            if len(before_event) > 0:
                self.display_system_message(before_event)
            self.handle_tictactoe_event(msg[event_index + len(TICTACTOE_EVENT_PREFIX):].strip())
            self.update_sidebar()
            return

        if msg.startswith(TICTACTOE_EVENT_PREFIX):
            self.handle_tictactoe_event(msg[len(TICTACTOE_EVENT_PREFIX):])
            self.update_sidebar()
            return

        sender, body = self.parse_peer_message(msg)
        if sender is not None:
            self.display_chat_message(sender, body, "peer")
        else:
            self.display_system_message(msg)
        self.update_sidebar()

    def parse_peer_message(self, msg):
        if msg.startswith("[") and "]" in msg:
            end = msg.find("]")
            sender = msg[1:end].strip()
            body = msg[end + 1:].strip()
            if len(sender) > 0 and len(body) > 0:
                return sender, body
        return None, None

    def receive_file(self, file_json):
        file_msg = json.loads(file_json)
        sender = file_msg["from"].strip("[]")
        filename = file_msg["filename"]
        self.display_chat_message(sender, "[file] " + filename, "peer")

        save_path = filedialog.asksaveasfilename(parent = self.Window,
                                                 title = "Save received file",
                                                 initialfile = filename)
        if len(save_path) == 0:
            self.display_system_message("File from " + sender + " was not saved.")
            return

        with open(save_path, "wb") as file:
            file.write(base64.b64decode(file_msg["data"]))
        self.display_system_message("Saved file from " + sender + ": " + save_path)

    def start_ui_queue(self):
        if self.polling_ui == False:
            self.polling_ui = True
            self.Window.after(100, self.process_ui_queue)

    def process_ui_queue(self):
        while True:
            try:
                msg = self.ui_msgs.get_nowait()
            except Empty:
                break
            self.display_state_output(msg)

        if self.running == True:
            self.Window.after(100, self.process_ui_queue)
        else:
            self.polling_ui = False
  
    # function to basically start the thread for sending messages
    def sendButton(self, msg):
        msg = msg.strip()
        if len(msg) == 0:
            return

        if self.aipic_mode_active == True:
            if msg.lower() == "/exit":
                self.exit_aipic_mode()
            elif self.is_nlp_command(msg):
                self.handle_nlp_command(msg)
            elif self.is_aipic_command(msg):
                self.submit_aipic_message(self.extract_aipic_prompt(msg))
            else:
                self.submit_aipic_message(msg)
            self.entryMsg.delete(0, END)
            return

        if self.is_nlp_command(msg):
            self.handle_nlp_command(msg)
            self.entryMsg.delete(0, END)
            return

        if self.bot_chat_active == True:
            if self.is_aipic_command(msg):
                self.submit_aipic_message(self.extract_aipic_prompt(msg))
            elif self.is_nlp_command(msg):
                self.handle_nlp_command(msg)
            elif msg.lower() == "/exit":
                self.exit_bot_chat()
            else:
                prompt = self.extract_bot_prompt(msg) if self.is_bot_command(msg) else msg
                self.submit_bot_message(prompt, show_prefix = False)
            self.entryMsg.delete(0, END)
            return

        if self.is_aipic_command(msg):
            self.submit_aipic_message(self.extract_aipic_prompt(msg))
            self.entryMsg.delete(0, END)
            return

        if self.is_bot_command(msg) and self.sm.get_state() != S_CHATTING:
            prompt = self.extract_bot_prompt(msg)
            if len(prompt) == 0:
                self.display_system_message("Type a question after @bot.")
            else:
                self.submit_bot_message(prompt, show_prefix = True)
            self.entryMsg.delete(0, END)
            return

        if self.is_bot_command(msg) and self.sm.get_state() == S_CHATTING:
            self.display_chat_message("Me", msg, "me")
            if self.group_bot_invited == False and self.sm.peer != self.bot_name:
                self.outgoing_msgs.put("c " + self.bot_name)
                self.group_bot_invited = True
            self.outgoing_msgs.put(msg)
            self.update_sidebar()
            self.entryMsg.delete(0, END)
            return

        if msg == "bye":
            self.group_bot_invited = False

        if self.should_display_as_chat_message(msg):
            self.display_chat_message("Me", msg, "me")

        self.outgoing_msgs.put(msg)
        self.update_sidebar()
        # print(msg)
        self.entryMsg.delete(0, END)

    def is_bot_command(self, msg):
        msg_lower = msg.lower()
        return msg_lower.startswith("@bot") or msg_lower.startswith("/bot")

    def is_aipic_command(self, msg):
        return msg.lower().startswith("/aipic:")

    def is_nlp_command(self, msg):
        msg_lower = msg.lower()
        return msg_lower == "/summary" or msg_lower == "/keywords"

    def handle_nlp_command(self, msg):
        command = msg.lower()
        self.display_system_message("Analyzing recent chat with DeepSeek...")
        thread = threading.Thread(target = self.call_chat_nlp, args = (command,))
        thread.daemon = True
        thread.start()

    def call_chat_nlp(self, command):
        try:
            history_snapshot = list(self.chat_history)
            if command == "/summary":
                from chat_nlp import summarize_recent_chat
                result = summarize_recent_chat(history_snapshot)
            else:
                from chat_nlp import extract_keywords
                result = extract_keywords(history_snapshot)
            self.ui_msgs.put(NLP_UI_PREFIX + result)
        except Exception as exc:
            self.ui_msgs.put(NLP_ERROR_PREFIX + "Chat analysis error: " + str(exc))

    def extract_aipic_prompt(self, msg):
        return msg[len("/aipic:"):].strip()

    def extract_bot_prompt(self, msg):
        if msg.lower().startswith("@bot"):
            return msg[4:].strip(" :")
        if msg.lower().startswith("/bot"):
            return msg[4:].strip(" :")
        return msg.strip()

    def submit_bot_message(self, prompt, show_prefix):
        shown_prompt = "@bot " + prompt if show_prefix == True else prompt
        self.display_chat_message("Me", shown_prompt, "me")
        self.display_system_message("AI_Bot is thinking...")
        thread = threading.Thread(target = self.call_bot, args = (prompt,))
        thread.daemon = True
        thread.start()

    def submit_aipic_message(self, prompt):
        if len(prompt) == 0:
            self.display_system_message("Type an image prompt first.")
            return

        self.display_system_message("Generating AI picture...")
        thread = threading.Thread(target = self.call_aipic, args = (prompt,))
        thread.daemon = True
        thread.start()

    def call_aipic(self, prompt):
        try:
            from aipic_client import generate_ai_picture
            image_path = generate_ai_picture(prompt)
            payload = {
                "prompt": prompt,
                "path": image_path
            }
            self.ui_msgs.put(AIPIC_UI_PREFIX + json.dumps(payload))
        except Exception as exc:
            self.ui_msgs.put(AIPIC_ERROR_PREFIX + "AI picture error: " + str(exc))

    def enter_aipic_mode(self):
        if self.bot_chat_active == True:
            self.exit_bot_chat()
        self.aipic_mode_active = True
        if self.aipicButton is not None:
            self.aipicButton.config(text = "Exit Picture")
        self.display_system_message("AI Picture mode started. Type a prompt and press Send.")
        self.update_sidebar()
        self.entryMsg.focus()

    def exit_aipic_mode(self):
        self.aipic_mode_active = False
        if self.aipicButton is not None:
            self.aipicButton.config(text = "AI Picture")
        self.display_system_message("AI Picture mode ended.")
        self.update_sidebar()
        self.entryMsg.focus()

    def enter_bot_chat(self):
        try:
            if self.aipic_mode_active == True:
                self.exit_aipic_mode()
            self.ensure_bot()
            self.bot_chat_active = True
            if self.chatbotButton is not None:
                self.chatbotButton.config(text = "Exit")
            self.display_system_message("ChatBot mode started.")
            self.update_sidebar()
            self.entryMsg.focus()
        except Exception as exc:
            self.display_system_message("AI_Bot error: " + str(exc))

    def exit_bot_chat(self):
        self.bot_chat_active = False
        if self.chatbotButton is not None:
            self.chatbotButton.config(text = "Bot")
        self.display_system_message("ChatBot mode ended.")
        self.update_sidebar()
        self.entryMsg.focus()

    def ensure_bot(self):
        if self.bot is None:
            from chat_bot_client import ChatBotClient
            self.bot = ChatBotClient(
                name = self.bot_name,
                personality = self.bot_personality
            )
        return self.bot

    def call_bot(self, prompt):
        try:
            bot = self.ensure_bot()
            reply = bot.ask(prompt)
            self.ui_msgs.put(BOT_UI_PREFIX + reply)
        except Exception as exc:
            self.ui_msgs.put(BOT_ERROR_PREFIX + "AI_Bot error: " + str(exc))

    def should_display_as_chat_message(self, msg):
        if self.sm.get_state() != S_CHATTING:
            return False
        if msg == "bye":
            return False
        if msg == "time":
            return False
        if msg == "who":
            return False
        if self.is_nlp_command(msg):
            return False
        if msg[0] == "c":
            return False
        if msg.startswith(FILE_CMD_PREFIX):
            return False
        if msg.startswith(GAME_SCORE_PREFIX):
            return False
        if msg.startswith(GAME_LEADERBOARD_PREFIX):
            return False
        if msg.startswith(TICTACTOE_START_PREFIX):
            return False
        if msg.startswith(TICTACTOE_MOVE_PREFIX):
            return False
        if msg.startswith(TICTACTOE_LEAVE_PREFIX):
            return False
        if msg[0] == "?":
            return False
        if msg[0] == "p" and msg[1:].strip().isdigit():
            return False
        return True

    def proc(self):
        # print(self.msg)
        while self.running == True:
            read, write, error = select.select([self.socket], [], [], 0.1)
            peer_msg = ""
            my_msg = ""
            # print(self.msg)
            if self.socket in read:
                peer_msg = self.recv()
            try:
                my_msg = self.outgoing_msgs.get_nowait()
            except Empty:
                my_msg = ""
            if len(my_msg) > 0 or len(peer_msg) > 0:
                # print(self.system_msg)
                self.system_msg = self.sm.proc(my_msg, peer_msg)
                self.ui_msgs.put(self.system_msg)

    def run(self):
        self.login()
# create a GUI class object
if __name__ == "__main__": 
    g = GUI()
