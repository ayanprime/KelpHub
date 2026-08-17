# this gives each persona their own voice using coqui xtts v2
# it runs fully offline once the model is downloaded, and uses built in
# voices so I don't need to record anything myself

# note: this needs python 3.10+, so I run it from inside coqui_env,
# not my normal python3

import os
import re
import subprocess

os.environ["COQUI_TOS_AGREED"] = "1"  # skips the license prompt

from TTS.api import TTS

OUTPUT_WAV = os.path.join(os.path.dirname(__file__), "_voice_output.wav")

# which built in speaker each persona uses
# to test other voices, I use test_coqui_children.py
VOICE_SPEAKERS = {
    "kelp": "Nova Hogarth",
    "quill": "Daisy Studious",
    "axiom": "Dionisio Schuyler",
    "cipher": "Adde Michal",
    "vault": "Royston Min",
    "orion": "Viktor Menelaos",
    "vita": "Camilla Holmström",
}

# model loads once, only when I actually need it
_tts_model = None


def _get_model() -> TTS:
    global _tts_model
    if _tts_model is None:
        print("(loading voice model, this happens once per session, please wait...)")
        _tts_model = TTS("tts_models/multilingual/multi-dataset/xtts_v2")
    return _tts_model


def _clean_for_speech(text: str) -> str:
    # I strip stuff that shouldn't be read out loud literally
    # (code blocks, markdown, asterisk actions) and fix pauses
    text = re.sub(r"```.*?```", " I've written that out below. ", text, flags=re.DOTALL)
    text = re.sub(r"[*_`#]", "", text)
    text = re.sub(r"\.{2,}", ". ", text)  # "..." doesn't pause right otherwise

    lines = text.split("\n")
    fixed_lines = []
    for line in lines:
        stripped = line.strip()
        if stripped and stripped[-1] not in ".!?,;:":
            stripped += "."  # so line breaks actually pause
        fixed_lines.append(stripped)
    text = " ".join(line for line in fixed_lines if line)

    text = re.sub(r"\s+", " ", text).strip()
    return text


def speak(persona_key: str, text: str) -> None:
    speaker = VOICE_SPEAKERS.get(persona_key)
    if not speaker:
        return

    spoken_text = _clean_for_speech(text)
    if not spoken_text:
        return

    try:
        model = _get_model()
        model.tts_to_file(
            text=spoken_text,
            speaker=speaker,
            language="en",
            file_path=OUTPUT_WAV,
        )
        subprocess.run(["afplay", OUTPUT_WAV], check=True)
    except FileNotFoundError:
        print("(afplay not found, should be built into macOS)")
    except Exception as e:
        print(f"(voice playback failed: {e})")
