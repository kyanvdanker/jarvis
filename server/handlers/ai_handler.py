import json
from ollama_client import ask_ollama  # or your AI function

async def handle_ai_request(ws, data):
    request = data["request"]
    payload = data["data"]

    # Ask your AI model
    result = ask_ollama(f"Analyze this event: {json.dumps(payload)}")

    # Send result back to Pi
    await ws.send_text(json.dumps({
        "type": "ai_response",
        "request": request,
        "result": result
    }))
