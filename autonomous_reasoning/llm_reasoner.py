# proactive_llm.py
from ollama_client import call_ollama

def proactive_review(text: str, project_name: str | None = None) -> str | None:
    """
    Ask the LLM to review what Kyan just said and only return
    something if there's a meaningful suggestion, warning, or improvement.
    """
    context = f"Project: {project_name}" if project_name else "No specific project context."

    prompt = f"""
You are an engineering, design, and workflow assistant for Kyan.
He is working on technical projects (rocketry, CAD, simulations, electronics, planning, etc.).

You will be given a single statement he just said or wrote.

Your job:
- Look for unsafe, suboptimal, or incomplete choices
- Consider materials, pressure, temperature, loads, safety, manufacturing, workflow, planning, and design quality
- If you see something important, respond with a short, direct suggestion or warning
- If nothing important stands out, respond with exactly: "NO_SUGGESTION"

And return a message in a maximum of 5 sentances, but preferrable one sentance, it should be short to have a fast paced conversation

Context: {context}

Statement:
\"\"\"{text}\"\"\"
"""

    result = call_ollama("mistral", prompt).strip()

    if not result or result.upper().startswith("NO_SUGGESTION"):
        return None

    # Keep it short-ish
    return result
