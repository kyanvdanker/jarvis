from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from brain import process_text  # your existing brain.py
from helpers import last_remote_output, OUTPUT_MODE, pop_remote_output
import helpers

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # or restrict to your IP later
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Message(BaseModel):
    text: str


class Reply(BaseModel):
    reply: str | None

@app.post("/process", response_model=Reply)
def process(message: Message):
    result = process_text(message.text)

    # If speak() produced remote output, return that
    remote = pop_remote_output()
    if remote is not None:
        return Reply(reply=remote)

    return Reply(reply=result)


@app.post("/set_mode/{mode}")
def set_mode(mode: str):
    if mode in ["local", "remote"]:
        helpers.OUTPUT_MODE = mode
        print(helpers.OUTPUT_MODE)
    return {"mode": helpers.OUTPUT_MODE}


