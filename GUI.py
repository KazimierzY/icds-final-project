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
                self.start_ui_queue()
                # while True:
                #     self.proc()
                # the thread to receive messages
                self.running = True
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
        self.Window.configure(width = 470,
                              height = 550,
                              bg = "#17202A")
        self.labelHead = Label(self.Window,
                             bg = "#17202A", 
                              fg = "#EAECEE",
                              text = self.name ,
                               font = "Helvetica 13 bold",
                               pady = 5)
          
        self.labelHead.place(relwidth = 1)
        self.line = Label(self.Window,
                          width = 450,
                          bg = "#ABB2B9")
          
        self.line.place(relwidth = 1,
                        rely = 0.07,
                        relheight = 0.012)
          
        # Window area for displaying chat and system messages.
        self.messageFrame = Frame(self.Window,
                                  bg = "#17202A")
        self.messageFrame.place(relheight = 0.745,
                                relwidth = 1,
                                rely = 0.08)

        self.textCons = Text(self.messageFrame,
                             width = 20,
                             height = 2,
                             bg = "#17202A",
                             fg = "#EAECEE",
                             font = "Helvetica 14",
                             padx = 8,
                             pady = 8,
                             wrap = WORD,
                             state = DISABLED)

        self.textCons.pack(side = LEFT,
                           fill = BOTH,
                           expand = True)

        scrollbar = Scrollbar(self.messageFrame,
                              command = self.textCons.yview)
        scrollbar.pack(side = RIGHT,
                       fill = Y)
        self.textCons.config(yscrollcommand = scrollbar.set)
        self.textCons.tag_config("system", foreground = "#F1C40F")
        self.textCons.tag_config("me", foreground = "#82E0AA")
        self.textCons.tag_config("peer", foreground = "#85C1E9")
          
        self.labelBottom = Label(self.Window,
                                 bg = "#ABB2B9",
                                 height = 80)
          
        self.labelBottom.place(relwidth = 1,
                               rely = 0.825)
          
        self.entryMsg = Entry(self.labelBottom,
                              bg = "#2C3E50",
                              fg = "#EAECEE",
                              font = "Helvetica 13")
          
        # place the given widget
        # into the gui window
        self.entryMsg.place(relwidth = 0.74,
                            relheight = 0.06,
                            rely = 0.008,
                            relx = 0.011)
          
        self.entryMsg.focus()
        self.entryMsg.bind("<Return>", lambda event: self.sendButton(self.entryMsg.get()))
          
        # create a Send Button
        self.buttonMsg = Button(self.labelBottom,
                                text = "Send",
                                font = "Helvetica 10 bold", 
                                width = 20,
                                bg = "#ABB2B9",
                                command = lambda : self.sendButton(self.entryMsg.get()))
          
        self.buttonMsg.place(relx = 0.77,
                             rely = 0.008,
                             relheight = 0.06, 
                             relwidth = 0.22)
          
        self.textCons.config(cursor = "arrow")
          
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

        if self.sm.get_state() == S_CHATTING:
            self.display_chat_message("Me", msg, "me")

        self.outgoing_msgs.put(msg)
        # print(msg)
        self.entryMsg.delete(0, END)

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
