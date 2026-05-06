import base64
import os
import time
import urllib.request


DEFAULT_IMAGE_MODEL = "gpt-image-1"
DEFAULT_IMAGE_SIZE = "1024x1024"
DEFAULT_IMAGE_QUALITY = "low"
DEFAULT_ARK_IMAGE_MODEL = "doubao-seedream-4-0-250828"
DEFAULT_ARK_BASE_URL = "https://ark.cn-beijing.volces.com/api/v3"


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


def safe_filename(text):
    safe = []
    for char in text.lower():
        if char.isalnum():
            safe.append(char)
        elif char in (" ", "-", "_"):
            safe.append("_")
    name = "".join(safe).strip("_")
    if len(name) == 0:
        name = "image"
    return name[:40]


def generate_ai_picture(prompt, output_dir = "generated_images"):
    load_env_file()

    try:
        from openai import OpenAI
    except ImportError as exc:
        raise RuntimeError("Install the openai package before using /aipic.") from exc

    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if len(api_key) == 0:
        api_key = os.environ.get("ARK_API_KEY", "").strip()
    if len(api_key) == 0:
        raise RuntimeError("OPENAI_API_KEY or ARK_API_KEY is not set. Add one to .env.")

    is_ark = len(os.environ.get("ARK_API_KEY", "").strip()) > 0 and len(os.environ.get("OPENAI_API_KEY", "").strip()) == 0
    default_model = DEFAULT_ARK_IMAGE_MODEL if is_ark == True else DEFAULT_IMAGE_MODEL
    default_size = "2K" if is_ark == True else DEFAULT_IMAGE_SIZE
    model = os.environ.get("AIPIC_MODEL", default_model)
    size = os.environ.get("AIPIC_SIZE", default_size)
    base_url = os.environ.get("OPENAI_BASE_URL", "").strip()
    if len(base_url) == 0:
        base_url = os.environ.get("ARK_BASE_URL", "").strip()
    if is_ark == True and len(base_url) == 0:
        base_url = DEFAULT_ARK_BASE_URL

    client_args = {
        "api_key": api_key,
        "timeout": 120
    }
    if len(base_url) > 0:
        client_args["base_url"] = base_url
    client = OpenAI(**client_args)

    request_args = {
        "model": model,
        "prompt": prompt,
        "size": size,
        "n": 1
    }
    if is_ark == True:
        response_format = os.environ.get("AIPIC_RESPONSE_FORMAT", "url")
        request_args["response_format"] = response_format
        request_args["extra_body"] = {
            "watermark": False
        }
    else:
        request_args["quality"] = os.environ.get("AIPIC_QUALITY", DEFAULT_IMAGE_QUALITY)

    response = client.images.generate(**request_args)

    os.makedirs(output_dir, exist_ok = True)
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    filename = timestamp + "_" + safe_filename(prompt) + ".png"
    output_path = os.path.abspath(os.path.join(output_dir, filename))

    image = response.data[0]
    if getattr(image, "b64_json", None):
        image_bytes = base64.b64decode(image.b64_json)
        with open(output_path, "wb") as image_file:
            image_file.write(image_bytes)
    elif getattr(image, "url", None):
        urllib.request.urlretrieve(image.url, output_path)
    else:
        raise RuntimeError("The image API returned no image data.")

    return output_path
