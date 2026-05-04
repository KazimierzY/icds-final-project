#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Apr 30 13:36:58 2021

@author: bing
"""

# import all the required  modules
import threading
import select
from queue import Empty, Queue
from tkinter import *
from tkinter import font
from tkinter import messagebox
from tkinter import simpledialog
from tkinter import ttk
from chat_utils import *
import json

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
                             width = 220)
        self.sidebar.pack(side = LEFT,
                          fill = Y)
        self.sidebar.pack_propagate(False)

        self.profileTitle = Label(self.sidebar,
                                  text = "My Profile",
                                  bg = "#FFFFFF",
                                  fg = "#222222",
                                  font = "Helvetica 12 bold",
                                  anchor = W)
        self.profileTitle.pack(fill = X,
                               padx = 16,
                               pady = (18, 6))

        self.nameLabel = Label(self.sidebar,
                               text = "User: " + self.name,
                               bg = "#FFFFFF",
                               fg = "#333333",
                               font = "Helvetica 10",
                               anchor = W)
        self.nameLabel.pack(fill = X,
                            padx = 16,
                            pady = 3)

        self.stateLabel = Label(self.sidebar,
                                text = "Status: Online",
                                bg = "#FFFFFF",
                                fg = "#333333",
                                font = "Helvetica 10",
                                anchor = W)
        self.stateLabel.pack(fill = X,
                             padx = 16,
                             pady = 3)

        self.peerLabel = Label(self.sidebar,
                               text = "Chatting with: None",
                               bg = "#FFFFFF",
                               fg = "#333333",
                               font = "Helvetica 10",
                               anchor = W,
                               wraplength = 180,
                               justify = LEFT)
        self.peerLabel.pack(fill = X,
                            padx = 16,
                            pady = 3)

        self.actionTitle = Label(self.sidebar,
                                 text = "Actions",
                                 bg = "#FFFFFF",
                                 fg = "#222222",
                                 font = "Helvetica 12 bold",
                                 anchor = W)
        self.actionTitle.pack(fill = X,
                              padx = 16,
                              pady = (24, 8))

        self.add_sidebar_button("Time", lambda: self.send_quick_command("time"))
        self.add_sidebar_button("Who", lambda: self.send_quick_command("who"))
        self.add_sidebar_button("Connect", self.ask_connect)
        self.add_sidebar_button("Poem", self.ask_poem)
        self.add_sidebar_button("Search", self.ask_search)
        self.add_sidebar_button("Clear Chat", self.clear_chat)

        self.rightPanel = Frame(self.mainFrame,
                                bg = "#F5F5F5")
        self.rightPanel.pack(side = LEFT,
                             fill = BOTH,
                             expand = True)

        self.chatInfo = Label(self.rightPanel,
                              text = "No active chat",
                              bg = "#F5F5F5",
                              fg = "#555555",
                              font = "Helvetica 11 bold",
                              anchor = W,
                              padx = 16)
        self.chatInfo.pack(side = TOP,
                           fill = X,
                           pady = (12, 8))

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

    def add_sidebar_button(self, text, command):
        button = Button(self.sidebar,
                        text = text,
                        font = "Helvetica 10",
                        bg = "#F2F3F5",
                        fg = "#222222",
                        activebackground = "#E5E7EB",
                        activeforeground = "#111111",
                        relief = FLAT,
                        anchor = W,
                        padx = 12,
                        command = command)
        button.pack(fill = X,
                    padx = 16,
                    pady = 4)

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

    def update_sidebar(self):
        if self.sm.get_state() == S_CHATTING and len(self.sm.peer) > 0:
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
        self.sendButton(command)

    def can_use_menu_command(self):
        return True

    def ask_connect(self):
        peer = simpledialog.askstring("Connect", "Enter username:", parent = self.Window)
        if peer is not None and len(peer.strip()) > 0:
            self.sendButton("c " + peer.strip())

    def ask_poem(self):
        poem_idx = simpledialog.askstring("Poem", "Enter sonnet number:", parent = self.Window)
        if poem_idx is not None and len(poem_idx.strip()) > 0:
            self.sendButton("p " + poem_idx.strip())

    def ask_search(self):
        term = simpledialog.askstring("Search", "Enter search term:", parent = self.Window)
        if term is not None and len(term.strip()) > 0:
            self.sendButton("? " + term.strip())

    def clear_chat(self):
        self.textCons.config(state = NORMAL)
        self.textCons.delete("1.0", END)
        self.textCons.config(state = DISABLED)

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
            self.display_message("[" + sender + "] " + msg, tag)

    def display_state_output(self, msg):
        msg = msg.strip()
        if len(msg) == 0:
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

        if self.should_display_as_chat_message(msg):
            self.display_chat_message("Me", msg, "me")

        self.outgoing_msgs.put(msg)
        self.update_sidebar()
        # print(msg)
        self.entryMsg.delete(0, END)

    def should_display_as_chat_message(self, msg):
        if self.sm.get_state() != S_CHATTING:
            return False
        if msg == "bye":
            return False
        if msg == "time":
            return False
        if msg == "who":
            return False
        if msg[0] == "c":
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
