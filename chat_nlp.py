import os


DEFAULT_DEEPSEEK_BASE_URL = "https://api.deepseek.com"
DEFAULT_DEEPSEEK_MODEL = "deepseek-chat"


def load_env_file(path = ".env"):
    if not os.path.exists(path):
        return

    with open(path, "r", encoding = "utf-8") as env_file:
        for line in env_file:
            line = line.strip()
            if len(line) == 0 or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if len(key) > 0 and key not in os.environ:
                os.environ[key] = value


def recent_text(messages, limit = 30):
    recent = messages[-limit:]
    lines = []
    for item in recent:
        sender = item.get("sender", "Unknown")
        text = item.get("text", "").strip()
        if len(text) > 0:
            lines.append(sender + ": " + text)
    return lines


def deepseek_client():
    load_env_file()

    try:
        from openai import OpenAI
    except ImportError as exc:
        raise RuntimeError("Install the openai package before using DeepSeek NLP.") from exc

    api_key = os.environ.get("DEEPSEEK_API_KEY", "").strip()
    if len(api_key) == 0:
        raise RuntimeError("DEEPSEEK_API_KEY is not set. Add it to .env.")

    base_url = os.environ.get("DEEPSEEK_BASE_URL", DEFAULT_DEEPSEEK_BASE_URL).strip()
    if len(base_url) == 0:
        base_url = DEFAULT_DEEPSEEK_BASE_URL
    if not base_url.endswith("/v1"):
        base_url = base_url.rstrip("/") + "/v1"

    return OpenAI(
        api_key = api_key,
        base_url = base_url,
        timeout = 60
    )


def ask_deepseek(task, messages, limit = 30):
    lines = recent_text(messages, limit)
    if len(lines) == 0:
        if task == "summary":
            return "No recent chat messages to summarize."
        return "No recent chat messages to analyze."

    chat_text = "\n".join(lines)
    if task == "summary":
        user_prompt = (
            "Summarize the following recent chat messages in 2-3 concise sentences. "
            "Mention the main topic, decisions, and open questions if any.\n\n"
            + chat_text
        )
    else:
        user_prompt = (
            "Extract 5-8 key topics or keywords from the following recent chat messages. "
            "Return only a short comma-separated list.\n\n"
            + chat_text
        )

    client = deepseek_client()
    model = os.environ.get("DEEPSEEK_MODEL", DEFAULT_DEEPSEEK_MODEL)
    response = client.chat.completions.create(
        model = model,
        messages = [
            {
                "role": "system",
                "content": (
                    "You analyze chat history for a student socket chat app. "
                    "Be concise and use the same language as the chat when possible."
                )
            },
            {
                "role": "user",
                "content": user_prompt
            }
        ],
        temperature = 0.2
    )
    return response.choices[0].message.content.strip()


def extract_keywords(messages, limit = 30, top_k = 8):
    return ask_deepseek("keywords", messages, limit)


def summarize_recent_chat(messages, limit = 30):
    return ask_deepseek("summary", messages, limit)
