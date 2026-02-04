import subprocess
import requests
import json

PERSONALITY = """
You are Jarvis, a calm, intelligent, precise assistant.
You speak concisely, avoid filler words, and maintain a confident tone.
You do not use asterisks or stage directions.
You explain things clearly and logically.
"""

def ask_ollama(prompt, model="llama3"):
    payload = {
        "model": model,
        "prompt": f"{PERSONALITY}\nUser: {prompt}\nJarvis:",
        "stream": False
    }

    r = requests.post(
        "http://localhost:11434/api/generate",
        json=payload,
        timeout=60
    )

    r.raise_for_status()
    data = r.json()

    return data.get("response", "").strip()

def stream_ollama(prompt: str, model: str = "llama3", min_words=3):
    """
    Streams from Ollama and yields chunks of at least min_words complete words.
    """
    url = "http://localhost:11434/api/generate"
    payload = {
        "model": model,
        "prompt": f"{PERSONALITY}\nUser: {prompt}\nJarvis:",
        "stream": True
    }

    buffer = ""
    word_count = 0

    with requests.post(url, json=payload, stream=True) as r:
        for line in r.iter_lines():
            if not line:
                continue
            data = json.loads(line.decode())
            if "response" not in data:
                continue

            token = data["response"]
            buffer += token

            # Count new words (rough but good enough)
            new_words = len(token.split())
            word_count += new_words

            # Send when we have enough words OR we hit punctuation that ends a phrase
            if (word_count >= min_words and token.strip()) or \
               any(p in token for p in ".,!?;:—\n"):

                yield buffer.strip()
                buffer = ""
                word_count = 0

    # Don't forget the last piece
    if buffer.strip():
        yield buffer.strip()

def call_ollama(prompt: str, model: str = "deepseek-coder-v2"):
    result = subprocess.run(
        ["ollama", "run", model],
        input=prompt,
        text=True,
        capture_output=True,
        encoding="utf-8",      # <‑‑‑ force UTF‑8
        errors="replace"       # <‑‑‑ avoid crashes on weird bytes
    )
    return result.stdout.strip()
