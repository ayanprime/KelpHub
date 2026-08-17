# this is the main chat loop for kelp
# kelp decides who answers (herself or one or more of her kids), then I
# call ollama with that persona's prompt and get a reply
#
# needs ollama running locally with a model pulled, for example:
#   ollama pull llama3.1:8b

from __future__ import annotations

import json
import re
import requests

import memory
import voice
from personas import PERSONAS

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "llama3.1:8b"  # change this if I'm using a different model
VOICE_ENABLED = True  # set False for text only mode

MAX_HISTORY_MESSAGES = 12  # keeps the last few exchanges, enough context without slowing things down

ARITHMETIC_PATTERN = re.compile(r"^[0-9+\-*/(). ]+$")


def call_ollama(
    system_prompt: str,
    user_message: str,
    temperature: float = 0.8,
    history: list[dict] | None = None,
) -> str:
    # temperature low means consistent (good for routing), high means more
    # personality (good for replies). history is past messages so the model
    # has context, not just this one line
    messages = [{"role": "system", "content": system_prompt}]
    if history:
        messages.extend(history)
    messages.append({"role": "user", "content": user_message})

    response = requests.post(
        OLLAMA_URL,
        json={
            "model": MODEL,
            "messages": messages,
            "stream": False,
            "options": {"temperature": temperature},
        },
    )
    response.raise_for_status()
    data = response.json()
    return data["message"]["content"]


def decide_who_speaks(user_message: str, history: list[dict] | None = None) -> list[str]:
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
        "A factual question ABOUT a topic (e.g. 'tell me about X', 'how does "
        "X work', 'what caused X', 'explain X') should go to whichever "
        "specialist covers that topic, NOT to kelp. Kelp is only for "
        "greetings, general chat, opinions, and messages that don't fit any "
        "specialty at all. Do not hedge toward kelp just because the "
        "question is phrased simply.\n"
        "Reply with ONLY the lowercase key(s), comma separated if more than "
        "one, and nothing else, no explanation, no punctuation.\n\n"
        "Examples:\n"
        "'Can you help me write a poem?' -> quill\n"
        "'What's 15% of 340?' -> axiom\n"
        "'How do I fix an IndexError in Python?' -> cipher (NOT vault, this is "
        "about a coding error, not memory or history)\n"
        "'What caused World War I?' -> vault (NOT orion, this is history, not "
        "science, even though it involves complex systems)\n"
        "'Tell me about the Berlin Wall' -> vault (a historical topic, answer "
        "the question, do not default to kelp just because it's simply phrased)\n"
        "'How do black holes form?' -> orion (a science topic, answer the "
        "question, do not default to kelp)\n"
        "'I'm feeling unmotivated today' -> vita\n"
        "'hey, how's it going?' -> kelp\n"
        "'What do you think about being an AI family?' -> kelp (opinion "
        "question about kelp herself, not a specialist topic)"
    )
    raw = call_ollama(routing_prompt, user_message, temperature=0.0, history=history)

    raw_names = [name.strip().lower() for name in raw.replace("\n", ",").split(",")]
    chosen = [name for name in raw_names if name in PERSONAS]
    if not chosen:
        chosen = ["kelp"]  # fallback if parsing fails
    return chosen[:2]  # I never let more than 2 speak at once


def try_calculate(user_message: str) -> str | None:
    # small local models are bad at doing math in their head, so instead
    # I ask the model to turn the question into a plain math expression,
    # then let python do the actual calculating
    extraction_prompt = (
        "If the user's message is a math question that can be answered with "
        "a single arithmetic expression, reply with ONLY that expression "
        "using plain numbers and + - * / ( ), no words, no units, no '%' "
        "symbol, no explanation.\n"
        "For percentage questions phrased as 'N% of M', the formula is "
        "ALWAYS: M*N/100, both numbers must appear in your expression. "
        "Examples:\n"
        "'15% of 340' -> 340*15/100\n"
        "'12% of 250' -> 250*12/100\n"
        "'what's 15 times 23' -> 15*23\n"
        "'340 divided by 8' -> 340/8\n"
        "If the message is NOT a math question, reply with exactly: NONE"
    )
    raw = call_ollama(extraction_prompt, user_message, temperature=0.0).strip()

    if raw.upper() == "NONE" or not raw:
        return None
    if not ARITHMETIC_PATTERN.match(raw):
        return None  # not a plain expression, don't risk eval on it

    # I double check every number in the question shows up in the expression
    # this catches the model dropping a number, like turning "12% of 250" into "250/100"
    question_numbers = re.findall(r"\d+(?:\.\d+)?", user_message)
    expression_numbers = re.findall(r"\d+(?:\.\d+)?", raw)
    for num in question_numbers:
        if num not in expression_numbers:
            return None

    try:
        result = eval(raw, {"__builtins__": {}}, {})
    except Exception:
        return None

    if isinstance(result, float):
        result = round(result, 4)
        if result == int(result):
            result = int(result)
    return str(result)


def get_persona_reply(persona_key: str, user_message: str, history: list[dict] | None = None) -> str:
    persona = PERSONAS[persona_key]
    system_prompt = persona["system_prompt"]

    # I pull in relevant stuff vault remembers and add it as extra context
    remembered = memory.recall(user_message)
    if remembered:
        context = "\n\nThings you remember about the user that might be relevant:\n" + \
            "\n".join(f"- {fact}" for fact in remembered)
        system_prompt = system_prompt + context

    # I give axiom the real calculated answer instead of letting him guess
    if persona_key == "axiom":
        computed = try_calculate(user_message)
        if computed is not None:
            system_prompt = system_prompt + (
                f"\n\nThe exact correct answer to this calculation has "
                f"already been computed for you: {computed}. State this "
                f"exact number in your response, do not attempt to "
                f"recalculate it yourself, as you might get it wrong."
            )

    return call_ollama(system_prompt, user_message, temperature=0.6, history=history)


def extract_memorable_fact(user_message: str) -> str | None:
    # this checks if the message has something worth saving long term
    extraction_prompt = (
        "You are Vault, deciding whether the user's message contains a fact "
        "worth remembering long-term (e.g. a preference, a personal detail, "
        "a project detail, a plan, a name). Small talk, questions with no "
        "personal info, and one-off requests are NOT worth remembering.\n"
        "If there IS something worth remembering, reply with ONLY that fact "
        "as one short sentence, written plainly (e.g. 'User's favorite color "
        "is green').\n"
        "If there is NOT anything worth remembering, reply with exactly: NONE"
    )
    raw = call_ollama(extraction_prompt, user_message, temperature=0.0).strip()
    if raw.upper() == "NONE" or not raw:
        return None
    return raw


def main():
    print("Kelp is listening. Type 'quit' to exit, or 'voice' to toggle speech.\n")
    history: list[dict] = []
    voice_on = VOICE_ENABLED

    while True:
        user_message = input("You: ").strip()
        if user_message.lower() in ("quit", "exit"):
            break
        if user_message.lower() == "memories":
            facts = memory.all_facts()
            if not facts:
                print("(nothing remembered yet)\n")
            else:
                print("\n".join(f"- {fact}" for fact in facts) + "\n")
            continue
        if user_message.lower() == "voice":
            voice_on = not voice_on
            print(f"(voice {'on' if voice_on else 'off'})\n")
            continue
        if not user_message:
            continue

        speakers = decide_who_speaks(user_message, history=history)

        replies_for_printing = []
        replies_for_history = []
        for persona_key in speakers:
            display_name = PERSONAS[persona_key]["display_name"]
            print(f"\n{display_name} is thinking...")
            reply = get_persona_reply(persona_key, user_message, history=history)
            print(f"{display_name}: {reply}")
            replies_for_printing.append(f"{display_name}: {reply}")
            replies_for_history.append(reply)  # no name prefix, this avoids the model copying that format
            if voice_on:
                voice.speak(persona_key, reply)
        print()

        # I save this turn to history, then trim it to the cap
        history.append({"role": "user", "content": user_message})
        history.append({"role": "assistant", "content": "\n".join(replies_for_history)})
        history = history[-MAX_HISTORY_MESSAGES:]

        # I quietly check if anything here is worth remembering long term
        fact = extract_memorable_fact(user_message)
        if fact:
            memory.remember(fact)


if __name__ == "__main__":
    main()
