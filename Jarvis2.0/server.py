"""Server that allows the wearable client to connect and send voice input, 
and receive responses from the main Jarvis brain. 
It also handles the memory management and command execution for the wearable client. 
This is meant to be a lightweight server that can run on a small device, 
and will communicate with the main Jarvis brain over the internet. 
It also has a simple command system that allows the wearable 
client to trigger commands on the main Jarvis brain, 
such as managing projects, agendas, and simulating rocket performance. 
The main purpose of this is to allow Jarvis to have a presence on the go, 
and to be able to interact with the user in a more natural way.
It also creates a simple chat website for allowing the user to interact
with jarvis trough the web
"""
from flask import Flask, render_template, request, jsonify
from brain import process_text
from memory import Memory
from ollama_client import ask_ollama

app = Flask(__name__)
mem = Memory()

@app.route("/interact", methods=["POST"])
def interact():
    data = request.json
    user_input = data.get("input", "")
    if not user_input:
        return jsonify({"error": "No input provided"}), 400

    # Process the user input and get a response
    response = process_text(user_input)
    return jsonify({"response": response})

# website route for simple chat interface
@app.route("/", methods=["GET", "POST"])
def chat():
    if request.method == "POST":
        user_input = request.form.get("user_input", "")
        if user_input:
            response = process_text(user_input)
            return render_template("index.html", response=response, user_input=user_input)
    return render_template("index.html", response=None, user_input=None)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
