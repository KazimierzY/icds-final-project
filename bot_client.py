import argparse
import json
import select
import socket
import time

from chat_bot_client import ChatBotClient
from chat_utils import CHAT_PORT, SERVER, myrecv, mysend


class GroupChatBotClient:
    def __init__(self, server=None, name="AI_Bot", personality="friendly Python learning assistant"):
        self.server = server or SERVER
        self.name = name
        self.personality = personality
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.bot = ChatBotClient(name=self.name, personality=self.personality)
        self.group_history = []
        self.running = False

    def login(self):
        self.socket.connect(self.server)
        mysend(self.socket, json.dumps({"action": "login", "name": self.name}))
        response = json.loads(myrecv(self.socket))
        if response.get("status") != "ok":
            raise RuntimeError("Bot login failed: " + response.get("status", "unknown"))
        print(self.name + " logged in. Invite it with: c " + self.name)

    def run(self):
        self.login()
        self.running = True
        while self.running:
            readable, _, _ = select.select([self.socket], [], [], 0.2)
            if self.socket in readable:
                raw_msg = myrecv(self.socket)
                if len(raw_msg) == 0:
                    self.running = False
                    break
                self.handle_server_message(raw_msg)

    def handle_server_message(self, raw_msg):
        msg = json.loads(raw_msg)
        action = msg.get("action")

        if action == "connect":
            print("Joined chat after request from " + msg.get("from", "unknown"))
            return

        if action == "disconnect":
            print("Disconnected from current group.")
            return

        if action != "exchange":
            return

        sender = msg.get("from", "").strip("[]")
        text = msg.get("message", "")
        if sender == self.name or len(text.strip()) == 0:
            return

        self.remember_group_message(sender, text)
        prompt = self.extract_mentioned_prompt(text)
        if prompt is None:
            return

        reply = self.ask_with_group_context(sender, prompt)
        self.send_group_reply(reply)

    def remember_group_message(self, sender, text):
        timestamp = time.strftime("%H:%M", time.localtime())
        self.group_history.append(f"{timestamp} {sender}: {text}")
        self.group_history = self.group_history[-20:]

    def extract_mentioned_prompt(self, text):
        lower_text = text.lower()
        triggers = ["@bot", "@ai_bot", "@" + self.name.lower()]
        matched = None
        for trigger in triggers:
            if trigger in lower_text:
                matched = trigger
                break

        if matched is None:
            return None

        start = lower_text.find(matched)
        prompt = text[:start] + text[start + len(matched):]
        prompt = prompt.strip(" :,-")
        if len(prompt) == 0:
            prompt = "Please respond naturally to the recent group chat."
        return prompt

    def ask_with_group_context(self, sender, prompt):
        context = "\n".join(self.group_history[-10:])
        full_prompt = (
            "Recent group chat:\n"
            + context
            + "\n\n"
            + sender
            + " mentioned you and asked:\n"
            + prompt
        )
        return self.bot.ask(full_prompt)

    def send_group_reply(self, reply):
        mysend(self.socket, json.dumps({
            "action": "exchange",
            "from": "[" + self.name + "]",
            "message": reply
        }))
        self.remember_group_message(self.name, reply)
        print(self.name + ": " + reply)

    def close(self):
        self.running = False
        try:
            self.socket.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass
        self.socket.close()


def main():
    parser = argparse.ArgumentParser(description="AI chatbot client for group chat")
    parser.add_argument("-d", type=str, default=None, help="server IP addr")
    parser.add_argument("-n", type=str, default="AI_Bot", help="bot username")
    parser.add_argument(
        "-p",
        type=str,
        default="friendly Python learning assistant",
        help="bot personality"
    )
    args = parser.parse_args()

    server = SERVER if args.d is None else (args.d, CHAT_PORT)
    bot_client = GroupChatBotClient(server=server, name=args.n, personality=args.p)
    try:
        bot_client.run()
    except KeyboardInterrupt:
        pass
    finally:
        bot_client.close()


if __name__ == "__main__":
    main()
