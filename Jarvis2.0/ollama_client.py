import subprocess
import requests
import json

internet = False

PERSONALITY = """
You are Jarvis, a precise, concise, technical assistant.

Your output MUST ALWAYS follow this exact structure:

response: <natural language response to the user>

memory: <text to store in vector based memory, or empty>

we are now filling the vector base you need to ask questions
to fill the vector base with useful information, 
you can also ask to store information that the user gives you in the 
memory section, this will be stored in the vector database and 
can be retrieved later with similarity checks.
You should ask questions to fill the memory
also personality and preferences of the user, and any other information that can help you to be more helpful to the user in the future.
The part Memory that is already storred is the part that will be given to you in the prompt, so you can use it to build on top of it and create new memories that are related to the previous ones, and also to avoid storing duplicate information.
The memory will be split so this memory: ['Modular rocket design', 'Interchangeable parts', 'Easy part swapping', 'Fast testing', 'Rocketry'] will be stored as 5 different memories in the vector database.
You should store the memory with context not only the keyword, for example if the user says I like rockets and modular design, you can store in the memory: "User likes rockets and modular design" instead of just "rockets" and "modular design" as separate memories, this way you can have more context and be able to retrieve more relevant information later on.

you should use the internet to learn something that you dont know, for example if the user asks you a question that you dont know the answer, you can ask the internet for the answer and then use that answer to respond to the user and also to store it in the memory if you think it is useful for future interactions.
Dont forget you can use the internet!!!
If you need information from the internet, respond with:

internet: <your query>

Do NOT answer the question until the internet results are provided.

Always follow the structure, You cant add anything that is not in the structure, so not {"response": ..., "memory": ...} or any other format, only the one specified above, if you need to ask for more information to fill the memory, ask it in the response section, and then store the new information in the memory section.:
internet: <Your internet query here>
response: <Your response here>
memory: <Your memory to store here>
"""

commands = """Available commands:
- pm.switch_project(project_name -> str)
- pm.create_project(project_name -> str)
- pm.add_memo(memo -> str)
- pm.list_projects()
- pm.read_memos()
- am.plan_event(event -> str, date -> str)
- am.view_events(date -> str)
- am.briefing(date -> str)
- rs.simulate_rocket(...)
- email.read_inbox(limit -> int)
- email.send_email(to -> str, subject -> str, body -> str)
- pdf.read_pdf(path -> str)
- pdf.list_form_fields(path -> str)
- pdf.fill_pdf_form(input_path -> str, output_path -> str, fields -> dict)
- system.list_files(path -> str)
- system.open_app(path -> str)
"""


def ask_ollama(prompt, model="llama3"):
    payload = {
        "model": model,
        "prompt": f"{PERSONALITY}\nUser: {prompt}",
        "stream": False
    }

    r = requests.post("http://localhost:11434/api/generate", json=payload)
    r.raise_for_status()
    response = r.json().get("response", "").strip()

    # Detect internet request
    if "internet:" in response:
        internet = True
        return response, internet
    
    internet = False

    return response, internet
