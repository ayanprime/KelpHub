# Kelp

Kelp is a local, offline AI assistant I built with a twist. Instead of one flat personality, Kelp is a mother figure who can either answer directly herself or call on one of her six children, each with their own specialty and personality, to respond. I named her Kelp because her knowledge should grow continuously, the way kelp spreads through the sea.

Everything runs locally through Ollama. No cloud API, no data leaving my machine.

## The family

Kelp is the mother. She handles general questions and decides who should speak. Her personality is warm, wise, and steady.

Quill handles language and writing. She is shy and soft spoken, but becomes eloquent once she gets into the writing itself.

Axiom handles math, browsing, and research. He is hot headed but fiercely protective and precise.

Cipher handles coding. He is calm, analytical, and has a dry wit.

Vault handles politics, history, and memory. He is sharp, confident, and forgets nothing.

Orion handles science and project planning. He is endlessly curious and scrappy, and breaks big goals into steps.

Vita handles health and motivation. She is energetic, warm, and the family's cheerleader.

## How it works

I send Kelp a message. Kelp decides who should respond, herself or one or more of her children, based on their specialties. Each chosen persona replies using their own system prompt, run through the same local model. Vault quietly saves anything worth remembering long term and recalls relevant facts on future turns. Replies are spoken aloud, each persona in their own distinct voice.

## What's in this project

personas.py has Kelp and her six children, each with their own personality as a system prompt.

kelp_chat.py is the main script. Kelp decides who should respond, then each chosen persona replies using any relevant memories as context. Axiom's math answers are computed for real in Python instead of being left to the model to guess.

memory.py is Vault's long term memory system. It saves facts worth remembering and recalls relevant ones for future replies.

memory_store.json is where memories are actually saved. It gets created automatically the first time something is remembered, and it is left out of git since it holds personal info.

voice.py gives each persona a distinct spoken voice using Coqui XTTS v2, which is local and offline, using built in studio voices.

requirements.txt has the packages needed for the base app. Coqui's dependencies are heavier and get installed separately, explained below.

LICENSE is the MIT license.

.gitignore keeps model files, generated audio, memory data, the coqui_env virtual environment, and other local clutter out of the repo.

## Setup

First, make sure Ollama is installed and running with a model pulled.

```
ollama pull llama3.1:8b
```

Then install the base dependency.

```
cd kelp
pip3 install -r requirements.txt
```

Then run the text only version to confirm the core app works.

```
python3 kelp_chat.py
```

## Setting up voices

Coqui needs Python 3.10 or higher and much heavier dependencies than the rest of the project, so it lives in its own virtual environment called coqui_env instead of mixing with the base setup.

First, install Python 3.11 if I don't already have it. I download the macOS installer from python.org.

Then create and activate the environment, one time only.

```
cd kelp
python3.11 -m venv coqui_env
source coqui_env/bin/activate
```

Then install everything needed, also one time only.

```
pip install --upgrade pip
pip install coqui-tts
pip install torch torchaudio
pip install "transformers>=4.57,<5"
pip install "coqui-tts[codec]"
```

From now on, I always run Kelp from inside this environment.

```
source coqui_env/bin/activate
python3 kelp_chat.py
```

The first time I actually speak with Kelp, not just launch her, the XTTS v2 model downloads automatically. That only happens once. I can type voice at any prompt to toggle speech on or off if I want text only. I can type memories at any prompt to see everything Vault has saved so far.

## Roadmap

Base chat and routing is done. Shared memory through Vault is done. Unique voices per persona through Coqui are done, after starting with Piper first. Real arithmetic for Axiom instead of model guessed math is done.

Still to build: a visual interface with Kelp centered on a cosmic background, her six children arranged around her in a color wheel, glowing and growing with the pitch of their voice when they speak.
