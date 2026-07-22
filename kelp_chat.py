"""
Kelp - main chat script (v1, text only, no voices yet).

How this works:
1. You type a message.
2. We ask Kelp (using a special "routing" instruction) who should respond:
   herself, or one or more of her children.
3. We call the model again for each chosen persona, using their unique
   system prompt, and print their reply.

Requires: Ollama running locally with the model pulled, e.g.:
    ollama pull llama3.1:8b
"""

import json
import requests

from personas import PERSONAS

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "llama3.1:8b"  # change this if you're using a different model

CHILD_NAMES = ["quill", "axiom", "cipher", "vault", "orion", "vita"]


def call_ollama(system_prompt: str, user_message: str, temperature: float = 0.8) -> str:
    """Send one message to the model with a given system prompt, return the reply text.

    temperature controls randomness: lower = more consistent/predictable,
    higher = more varied/creative. We use a low temperature for routing
    decisions (we want consistency) and a higher one for persona replies
    (we want personality and variety).
    """
    response = requests.post(
        OLLAMA_URL,
        json={
            "model": MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            "stream": False,
            "options": {"temperature": temperature},
        },
    )
    response.raise_for_status()
    data = response.json()
    return data["message"]["content"]


def decide_who_speaks(user_message: str) -> list[str]:
    """
    Ask Kelp who should respond. She can pick herself and/or any of her
    children. Returns a list of persona keys, e.g. ["kelp"] or ["cipher", "orion"].
    """
    routing_prompt = (
        "You are Kelp, deciding who in your AI family should respond to the "
        "user's message. Your children and their specialties are:\n"
        "- quill: language and writing (poems, essays, emails, stories, editing)\n"
        "- axiom: math, browsing, and research (calculations, looking things up, data)\n"
        "- cipher: coding (writing/debugging/explaining code)\n"
        "- vault: politics, history, and memory (past events, remembering facts)\n"
        "- orion: science and project planning (how things work, breaking down plans)\n"
        "- vita: health and motivation (fitness, wellbeing, encouragement)\n\n"
        "STRICT RULE: pick exactly ONE persona for almost every message, even if "
        "the topic could loosely connect to more than one specialty. A topic "
        "belongs to whichever specialty is the MOST direct match, not every "
        "specialty that could theoretically relate. Only pick two personas if "
        "the user's message contains two clearly separate requests joined by "
        "'and' (e.g. 'write me a poem AND also fix this code').\n"
        "Pick 'kelp' alone for greetings, general chat, opinions, or anything "
        "that doesn't clearly match one child's specialty.\n"
        "Reply with ONLY the lowercase key(s), comma-separated if more than "
        "one, and nothing else - no explanation, no punctuation.\n\n"
        "Examples:\n"
        "'Can you help me write a poem?' -> quill\n"
        "'What's 15% of 340?' -> axiom\n"
        "'How do I fix an IndexError in Python?' -> cipher (NOT vault - this is "
        "about a coding error, not memory or history)\n"
        "'What caused World War I?' -> vault (NOT orion - this is history, not "
        "science, even though it involves complex systems)\n"
        "'I'm feeling unmotivated today' -> vita\n"
        "'hey, how's it going?' -> kelp"
    )
    raw = call_ollama(routing_prompt, user_message, temperature=0.0)
    # Parse out valid persona keys from the reply
    raw_names = [name.strip().lower() for name in raw.replace("\n", ",").split(",")]
    chosen = [name for name in raw_names if name in PERSONAS]
    if not chosen:
        chosen = ["kelp"]  # fallback if parsing fails
    return chosen[:2]  # safety net: never let routing runaway past 2 speakers


def get_persona_reply(persona_key: str, user_message: str) -> str:
    persona = PERSONAS[persona_key]
    return call_ollama(persona["system_prompt"], user_message, temperature=0.6)


def main():
    print("Kelp is listening. Type 'quit' to exit.\n")
    while True:
        user_message = input("You: ").strip()
        if user_message.lower() in ("quit", "exit"):
            break
        if not user_message:
            continue

        speakers = decide_who_speaks(user_message)

        for persona_key in speakers:
            display_name = PERSONAS[persona_key]["display_name"]
            print(f"\n{display_name} is thinking...")
            reply = get_persona_reply(persona_key, user_message)
            print(f"{display_name}: {reply}")
        print()


if __name__ == "__main__":
    main()