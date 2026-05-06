# Program in Python to create a Snake Game
# Adapted for the chat client so it can report the final score.

from tkinter import *
import random


WIDTH = 500
HEIGHT = 500
SPEED = 200
SPACE_SIZE = 20
BODY_SIZE = 2
SNAKE = "#00FF00"
FOOD = "#FFFFFF"
BACKGROUND = "#000000"


class Snake:
    def __init__(self, canvas):
        self.coordinates = []
        self.squares = []

        for i in range(0, BODY_SIZE):
            self.coordinates.append([0, 0])

        for x, y in self.coordinates:
            square = canvas.create_rectangle(
                x, y, x + SPACE_SIZE, y + SPACE_SIZE,
                fill = SNAKE, tag = "snake")
            self.squares.append(square)


class Food:
    def __init__(self, canvas, snake):
        self.canvas = canvas
        self.coordinates = self.pick_location(snake)

        x, y = self.coordinates
        canvas.create_oval(x, y, x + SPACE_SIZE, y + SPACE_SIZE,
                           fill = FOOD, tag = "food")

    def pick_location(self, snake):
        max_x = WIDTH // SPACE_SIZE - 1
        max_y = HEIGHT // SPACE_SIZE - 1

        while True:
            x = random.randint(0, max_x) * SPACE_SIZE
            y = random.randint(0, max_y) * SPACE_SIZE
            if [x, y] not in snake.coordinates and (x, y) not in snake.coordinates:
                return [x, y]


class SnakeGame:
    def __init__(self, parent = None, player_name = "", on_game_over = None):
        self.parent = parent
        self.player_name = player_name
        self.on_game_over = on_game_over
        self.window = None
        self.canvas = None
        self.label = None
        self.snake = None
        self.food = None
        self.score = 0
        self.direction = "down"
        self.running = False
        self.score_submitted = False

    def start(self):
        if self.window is not None and self.window.winfo_exists():
            self.window.lift()
            self.window.focus_force()
            return

        self.window = Toplevel(self.parent) if self.parent is not None else Tk()
        self.window.title("Snake")
        self.window.resizable(False, False)
        self.window.protocol("WM_DELETE_WINDOW", self.close)

        title = "Snake"
        if len(self.player_name) > 0:
            title += " - " + self.player_name
        self.window.title(title)

        self.score = 0
        self.direction = "down"
        self.running = True
        self.score_submitted = False

        self.label = Label(self.window, text = "Points:0",
                           font = ("consolas", 20))
        self.label.pack()

        self.canvas = Canvas(self.window, bg = BACKGROUND,
                             height = HEIGHT, width = WIDTH)
        self.canvas.pack()

        self.window.update_idletasks()
        self.center_window()
        self.bind_keys()

        self.snake = Snake(self.canvas)
        self.food = Food(self.canvas, self.snake)
        self.next_turn()

        if self.parent is None:
            self.window.mainloop()

    def center_window(self):
        window_width = self.window.winfo_width()
        window_height = self.window.winfo_height()
        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()

        x = int((screen_width / 2) - (window_width / 2))
        y = int((screen_height / 2) - (window_height / 2))
        self.window.geometry(f"{window_width}x{window_height}+{x}+{y}")

    def bind_keys(self):
        self.window.bind("<Left>", lambda event: self.change_direction("left"))
        self.window.bind("<Right>", lambda event: self.change_direction("right"))
        self.window.bind("<Up>", lambda event: self.change_direction("up"))
        self.window.bind("<Down>", lambda event: self.change_direction("down"))
        self.window.focus_force()

    def next_turn(self):
        if self.running == False:
            return

        x, y = self.snake.coordinates[0]

        if self.direction == "up":
            y -= SPACE_SIZE
        elif self.direction == "down":
            y += SPACE_SIZE
        elif self.direction == "left":
            x -= SPACE_SIZE
        elif self.direction == "right":
            x += SPACE_SIZE

        self.snake.coordinates.insert(0, [x, y])
        square = self.canvas.create_rectangle(
            x, y, x + SPACE_SIZE, y + SPACE_SIZE, fill = SNAKE)
        self.snake.squares.insert(0, square)

        if [x, y] == self.food.coordinates:
            self.score += 1
            self.label.config(text = "Points:" + str(self.score))
            self.canvas.delete("food")
            self.food = Food(self.canvas, self.snake)
        else:
            del self.snake.coordinates[-1]
            self.canvas.delete(self.snake.squares[-1])
            del self.snake.squares[-1]

        if self.check_collisions():
            self.game_over()
        else:
            self.window.after(SPEED, self.next_turn)

    def change_direction(self, new_direction):
        if new_direction == "left" and self.direction != "right":
            self.direction = new_direction
        elif new_direction == "right" and self.direction != "left":
            self.direction = new_direction
        elif new_direction == "up" and self.direction != "down":
            self.direction = new_direction
        elif new_direction == "down" and self.direction != "up":
            self.direction = new_direction

    def check_collisions(self):
        x, y = self.snake.coordinates[0]

        if x < 0 or x >= WIDTH:
            return True
        if y < 0 or y >= HEIGHT:
            return True

        for body_part in self.snake.coordinates[1:]:
            if x == body_part[0] and y == body_part[1]:
                return True

        return False

    def game_over(self):
        self.running = False
        self.canvas.delete(ALL)
        self.canvas.create_text(
            WIDTH / 2, HEIGHT / 2 - 40,
            font = ("consolas", 54),
            text = "GAME OVER", fill = "red", tag = "gameover")
        self.canvas.create_text(
            WIDTH / 2, HEIGHT / 2 + 35,
            font = ("consolas", 24),
            text = "Score: " + str(self.score), fill = "white")

        Button(self.window, text = "Close", command = self.close).pack(pady = 8)
        self.submit_score()

    def submit_score(self):
        if self.score_submitted == True:
            return
        self.score_submitted = True
        if self.on_game_over is not None:
            self.on_game_over(self.score)

    def close(self):
        self.running = False
        if self.window is not None and self.window.winfo_exists():
            self.window.destroy()


if __name__ == "__main__":
    SnakeGame().start()
