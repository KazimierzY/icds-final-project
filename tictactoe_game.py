from tkinter import *
from tkinter import messagebox


class TicTacToeGame:
    def __init__(self, parent = None, player_name = "", on_start = None,
                 on_move = None, on_leave = None):
        self.parent = parent
        self.player_name = player_name
        self.on_start = on_start
        self.on_move = on_move
        self.on_leave = on_leave
        self.window = None
        self.status_label = None
        self.info_label = None
        self.buttons = []
        self.board = [""] * 9
        self.players = {"X": "", "O": ""}
        self.turn = "X"
        self.status = "idle"
        self.winner = None
        self.my_symbol = None
        self.room = ""
        self.close_notifies_server = True

    def start(self):
        if self.window is not None and self.window.winfo_exists():
            self.window.lift()
            self.window.focus_force()
            return

        self.window = Toplevel(self.parent) if self.parent is not None else Tk()
        self.window.title("Tic-Tac-Toe")
        self.window.resizable(False, False)
        self.window.configure(bg = "#F5F5F5")
        self.window.protocol("WM_DELETE_WINDOW", self.close)

        title = Label(self.window,
                      text = "Tic-Tac-Toe",
                      bg = "#F5F5F5",
                      fg = "#111111",
                      font = ("Helvetica", 18, "bold"))
        title.pack(pady = (14, 4))

        self.info_label = Label(self.window,
                                text = "Finding opponent...",
                                bg = "#F5F5F5",
                                fg = "#333333",
                                font = ("Helvetica", 10))
        self.info_label.pack(pady = (0, 8))

        board_frame = Frame(self.window,
                            bg = "#111111",
                            bd = 2,
                            relief = SOLID)
        board_frame.pack(padx = 18,
                         pady = 8)

        self.buttons = []
        for index in range(9):
            button = Button(board_frame,
                            text = "",
                            width = 4,
                            height = 2,
                            font = ("Helvetica", 28, "bold"),
                            bg = "#FFFFFF",
                            fg = "#111111",
                            activebackground = "#EAF2FF",
                            relief = FLAT,
                            command = lambda pos = index: self.click_square(pos))
            button.grid(row = index // 3,
                        column = index % 3,
                        padx = 1,
                        pady = 1)
            self.buttons.append(button)

        self.status_label = Label(self.window,
                                  text = "Waiting for server...",
                                  bg = "#F5F5F5",
                                  fg = "#555555",
                                  font = ("Helvetica", 11),
                                  width = 38,
                                  wraplength = 300)
        self.status_label.pack(pady = (8, 10))

        action_frame = Frame(self.window,
                             bg = "#F5F5F5")
        action_frame.pack(fill = X,
                          padx = 18,
                          pady = (0, 16))

        Button(action_frame,
               text = "New Game",
               font = ("Helvetica", 10),
               bg = "#07C160",
               fg = "#FFFFFF",
               activebackground = "#06AD56",
               activeforeground = "#FFFFFF",
               relief = FLAT,
               command = self.request_new_game).pack(side = LEFT,
                                                     expand = True,
                                                     fill = X,
                                                     padx = (0, 8))

        Button(action_frame,
               text = "Close",
               font = ("Helvetica", 10),
               bg = "#F2F3F5",
               fg = "#222222",
               activebackground = "#E5E7EB",
               relief = FLAT,
               command = self.close).pack(side = LEFT,
                                          expand = True,
                                          fill = X)

        self.center_window()
        self.refresh()

        if self.parent is None:
            self.window.mainloop()

    def center_window(self):
        self.window.update_idletasks()
        window_width = self.window.winfo_width()
        window_height = self.window.winfo_height()
        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()
        x = int((screen_width / 2) - (window_width / 2))
        y = int((screen_height / 2) - (window_height / 2))
        self.window.geometry(f"{window_width}x{window_height}+{x}+{y}")

    def request_new_game(self):
        self.board = [""] * 9
        self.players = {"X": self.player_name, "O": ""}
        self.turn = "X"
        self.status = "waiting"
        self.winner = None
        self.my_symbol = "X"
        self.refresh()
        if self.on_start is not None:
            self.on_start()

    def set_room(self, room):
        self.room = str(room).strip()
        self.refresh()

    def click_square(self, position):
        if self.status != "playing":
            return
        if self.my_symbol != self.turn:
            return
        if self.board[position] != "":
            return
        if self.on_move is not None:
            self.on_move(position)

    def apply_state(self, state):
        self.board = state.get("board", [""] * 9)
        self.players = state.get("players", {"X": "", "O": ""})
        self.turn = state.get("turn", "X")
        self.status = state.get("status", "playing")
        self.winner = state.get("winner")
        self.room = state.get("room", self.room)

        self.my_symbol = None
        for symbol, name in self.players.items():
            if name == self.player_name:
                self.my_symbol = symbol
                break

        self.refresh(state.get("message", ""))

    def show_error(self, message):
        if self.status_label is not None:
            self.status_label.config(text = message)
        if self.window is not None and self.window.winfo_exists():
            messagebox.showinfo("Tic-Tac-Toe", message, parent = self.window)

    def refresh(self, message = ""):
        if self.window is None or not self.window.winfo_exists():
            return

        for index, value in enumerate(self.board):
            color = "#111111"
            if value == "X":
                color = "#1565C0"
            elif value == "O":
                color = "#C62828"
            self.buttons[index].config(text = value,
                                       fg = color,
                                       state = self.square_state(index))

        player_text = "You are waiting for a role."
        if self.my_symbol is not None:
            player_text = "You are " + self.my_symbol
            opponent_symbol = "O" if self.my_symbol == "X" else "X"
            opponent = self.players.get(opponent_symbol, "")
            if len(opponent) > 0:
                player_text += " vs " + opponent
        if len(self.room) > 0:
            player_text = "Room " + self.room + " | " + player_text
        self.info_label.config(text = player_text)

        if len(message) > 0:
            status_text = message
        elif self.status == "waiting":
            status_text = "Waiting for another player..."
        elif self.status == "playing":
            if self.my_symbol == self.turn:
                status_text = "Your turn."
            else:
                current_player = self.players.get(self.turn, "opponent")
                status_text = "Waiting for " + current_player + "."
        elif self.winner == "draw" or self.status == "draw":
            status_text = "Draw."
        elif self.winner in ("X", "O"):
            status_text = self.players.get(self.winner, self.winner) + " wins."
        else:
            status_text = "Game finished."

        self.status_label.config(text = status_text)

    def square_state(self, index):
        if self.status != "playing":
            return DISABLED
        if self.my_symbol != self.turn:
            return DISABLED
        if self.board[index] != "":
            return DISABLED
        return NORMAL

    def close(self):
        should_notify = self.status in ("waiting", "playing")
        if should_notify == True and self.close_notifies_server == True:
            if self.on_leave is not None:
                self.on_leave()
        if self.window is not None and self.window.winfo_exists():
            self.window.destroy()


if __name__ == "__main__":
    TicTacToeGame().start()
