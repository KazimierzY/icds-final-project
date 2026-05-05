try:
    from ollama import Client as OllamaClient
except ImportError:
    OllamaClient = None

from openai import OpenAI

from ai_client import MODEL_ID, client as teacher_qwen_client


OLLAMA_MODEL = "qwen2.5:0.5b"


class ChatBotClient:
    def __init__(
            self,
            name="AI_Bot",
            personality="friendly",
            model=OLLAMA_MODEL,
            host="http://localhost:11434",
            headers=None,
            max_history=20):
        if OllamaClient is None:
            raise ImportError("The ollama package is required to use ChatBotClient.")

        self.host = host
        self.name = name
        self.model = model
        self.client = OllamaClient(host=self.host, headers=headers or {"x-some-header": "some-value"})
        self.max_history = max_history
        self.personality = personality
        self.messages = []
        self.reset()

    def reset(self):
        self.messages = [{"role": "system", "content": self.build_system_prompt()}]

    def set_personality(self, personality):
        self.personality = personality.strip() or "friendly"
        self.reset()

    def build_system_prompt(self):
        return (
            f"You are {self.name}, a {self.personality} AI chatbot inside a student socket chat app. "
            "Answer clearly and naturally. Keep replies concise unless the user asks for detail."
        )

    def ask(self, message: str):
        return self.chat(message)

    def chat(self, message: str):
        self.messages.append({"role": "user", "content": message})

        response = self.client.chat(
            model=self.model,
            messages=self.messages
        )
        msg = response["message"]["content"]

        self.messages.append({"role": "assistant", "content": msg})
        self.trim_history()
        return msg

    def stream_chat(self, message):
        self.messages.append({
            "role": "user",
            "content": message,
        })
        response = self.client.chat(self.model, self.messages, stream=True)
        answer = ""
        for chunk in response:
            piece = chunk["message"]["content"]
            print(piece, end="")
            answer += piece
        self.messages.append({"role": "assistant", "content": answer})
        self.trim_history()
        return answer

    def trim_history(self):
        system_message = self.messages[:1]
        recent_messages = self.messages[1:][-self.max_history:]
        self.messages = system_message + recent_messages


class ChatBotClientOpenAI:
    def __init__(self, name="AI_Bot", personality="friendly", client=None, model=MODEL_ID, max_history=20):
        self.name = name
        self.model = model
        self.client = client or teacher_qwen_client
        self.max_history = max_history
        self.personality = personality
        self.messages = []
        self.reset()

    def reset(self):
        self.messages = [{"role": "system", "content": self.build_system_prompt()}]

    def set_personality(self, personality):
        self.personality = personality.strip() or "friendly"
        self.reset()

    def build_system_prompt(self):
        return (
            f"You are {self.name}, a {self.personality} AI chatbot inside a student socket chat app. "
            "Answer clearly and naturally. Keep replies concise unless the user asks for detail."
        )

    def ask(self, message: str):
        self.messages.append({"role": "user", "content": message})
        reply = self.chat(self.messages)
        self.messages.append({"role": "assistant", "content": reply})
        self.trim_history()
        return reply

    def chat(self, messages):
        response = self.client.chat.completions.create(
            messages=self.format_messages(messages),
            model=self.model,
            temperature=0.6,
        )
        return response.choices[0].message.content

    def trim_history(self):
        system_message = self.messages[:1]
        recent_messages = self.messages[1:][-self.max_history:]
        self.messages = system_message + recent_messages

    def format_messages(self, messages):
        formatted = []
        for msg in messages:
            role = msg["role"]
            content = msg["content"]
            if role == "user" and isinstance(content, str):
                content = [{"type": "text", "text": content}]
            formatted.append({"role": role, "content": content})
        return formatted


if __name__ == "__main__":
    c = ChatBotClient()
    print(c.ask("Who are you?"))
