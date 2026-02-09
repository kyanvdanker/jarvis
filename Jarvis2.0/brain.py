import json
import re
from word2number import w2n
from ollama_client import ask_ollama
import os
import datetime
import project_manager as pm
import agenda_manager as am
import rocket_simulation as rs
import importlib.util
from memory import Memory
import requests
import email_manager as email
import pdf_manager as pdfS
import system_manager as system


internet = False

# Instantiate Memory with the local memory.json file
mem = Memory(memory_file=os.path.join(os.path.dirname(__file__), "memory.json"))


def check_reminder_time():
    # Checks if the reminder time has been reached and triggers the reminder if so
    now = datetime.datetime.now()
    reminder_file = "reminders.txt"
    if os.path.isfile(reminder_file):
        with open(reminder_file, "r") as f:
            lines = f.readlines()
        for line in lines:
            try:
                time_str, message = line.strip().split(" ", 1)
                reminder_time = datetime.datetime.strptime(time_str, "%Y-%m-%d %H:%M")
                if now >= reminder_time:
                    speak(f"Reminder: {message}")
                    lines.remove(line)  # Remove the triggered reminder
            except ValueError:
                continue  # Skip malformed lines
        with open(reminder_file, "w") as f:
            f.writelines(lines)  # Write back remaining reminders
    

def speak(text):
    print(text)

def clean_text(text: str) -> str:
    text = re.sub(r'[^a-zA-Z0-9\s]', '', text).lower()
    words = text.split()
    for i, word in enumerate(words):
        try:
            num = w2n.word_to_num(word)
            words[i] = str(num)
        except:
            pass  # not a number word
    text = ' '.join(words)
    return text

def process_text(text):
    # keep original user text and also a cleaned version for similarity checks
    user_text = text
    cleaned = clean_text(user_text)

    # Try to obtain most similar memory (if available)
    try:
        memory_text = mem.find_relevant_memories(cleaned)
    except Exception:
        memory_text, mem_score = None, 0.0

    # Build a simple prompt; fall back to echo if model call fails
    prompt = f"User: {user_text}\nMemory that is already storred: {memory_text or ''}\nJarvis:"
    print(f"Prompt to model: {prompt}")
    try:
        response, internet = ask_ollama(prompt)
    except Exception:
        response = user_text
    print(f"Model response: {response}")

    if internet:
        search_query = response.split("internet:", 1)[1].strip()
        info = internet_search(search_query)

        # Now ask the model again, giving it the internet results
        response, internet = ask_ollama(
            f"Internet results for '{search_query}':\n{info}\n first question: {prompt} Now answer the original question."
        )


    # Parse optional command and memory instructions from the model response
    if "command:" in response:
        command = response.split("command:", 1)[1].strip()
        command = command.split("memory:", 1)[0].strip()
    else:
        command = None

    if command:
        try:
            eval(command)  # Execute the command (e.g., pm.add_memo("..."))
        except Exception as e:
            speak(f"Error executing command: {e}")

    # If model instructs to store memory, call available add/remember API
    if "memory:" in response:
        mem_text = response.split("memory:", 1)[1].strip()
        if mem_text == "None" or mem_text == "" or mem_text =="[]":
            pass  # No memory to store
        # If the model returns a Python list, parse it
        if mem_text.startswith("[") and mem_text.endswith("]"):
            try:
                items = json.loads(mem_text.replace("'", '"'))
                for item in items:
                    mem.add_memory(item)
            except Exception:
                pass
        else:
            # Single memory string
            mem.add_memory(mem_text)

        


    # Extract a 'response:' section if the model provided one, otherwise use full response
    if "response:" in response:
        response_text = response.split("response:", 1)[1].strip()
        response_text = response_text.split("command:", 1)[0].split("memory:", 1)[0].strip()
    else:
        response_text = response

    speak(response_text)

def main():
    while True:
        check_reminder_time()
        user_input = input("You: ")
        if user_input.lower() in ["exit", "quit"]:
            break
        process_text(user_input)

# function that allows to store new memories in the database without using the ollama model, for testing and demonstration purposes
def storing():
    while True:
        mem_input = input("Enter a memory to store (or 'exit' to quit): ")
        if mem_input.lower() in ["exit", "quit"]:
            break
        mem.add_memory(mem_input)
        print("Memory stored.")

def internet_search(query):
    url = "https://api.duckduckgo.com/"
    params = {"q": query, "format": "json", "no_redirect": 1}
    data = requests.get(url, params=params).json()
    return data.get("AbstractText") or "No results found."


main()