#!/usr/bin/env python3
import os
import re
import sys
import json
import queue
import subprocess
import contextlib
import multiprocessing
from pathlib import Path

import sounddevice as sd
import vosk
from TTS.api import TTS  # Coqui TTS

# ──────────────────────── Configuration ────────────────────────
ROOT            = Path("/home/rod/llm_chatbot")
CONTEXT_PATH = ROOT / "contexte.txt"
VOSK_MODEL_PATH = ROOT / "vosk" / "vosk-model-small-fr-0.22"
LLAMA_CLI_PATH  = "/home/rod/llama.cpp/build/bin/llama-cli"
LLAMA_CLI_PATH  = ROOT / "llama.cpp/build/bin/llama-cli"
# LLAMA_MODEL     = ROOT / "models/Llama-3.1-8B-Instruct-q4_k_m/Llama-3.1-8B-Instruct-q4_k_m.gguf"
LLAMA_MODEL     = ROOT / "models/Meta-Llama-3.1-8B-Instruct-Q6_K/Meta-Llama-3.1-8B-Instruct-Q6_K.gguf"
N_PREDICT       = "300"
THREADS         = str(multiprocessing.cpu_count())
AUDIO_RATE      = 16_000
TTS_MODEL_NAME  = "tts_models/fr/css10/vits"

# ──────────────────────── Initialisations ────────────────────────
tts = TTS(model_name=TTS_MODEL_NAME, progress_bar=False)
if not VOSK_MODEL_PATH.exists():
    sys.exit(f"[ERREUR] Modèle VOSK introuvable à l'emplacement : {VOSK_MODEL_PATH}")
vosk_model = vosk.Model(str(VOSK_MODEL_PATH))
recognizer = vosk.KaldiRecognizer(vosk_model, AUDIO_RATE)
audio_queue = queue.Queue()

# ──────────────────────── Fonctions audio ────────────────────────
def audio_callback(indata, frames, time, status):
    audio_queue.put(bytes(indata))

def listen():
    with sd.RawInputStream(
        samplerate=AUDIO_RATE,
        blocksize=8000,
        dtype='int16',
        channels=1,
        callback=audio_callback
    ):
        while True:
            if recognizer.AcceptWaveform(audio_queue.get()):
                return json.loads(recognizer.Result())["text"]

@contextlib.contextmanager
def suppress_output():
    with open(os.devnull, 'w') as fnull:
        with contextlib.redirect_stdout(fnull), contextlib.redirect_stderr(fnull):
            yield

def speak(text, raw=False):
    cleaned_text = text if raw else clean_text(text)
    if not cleaned_text.strip():
        print("[TTS] Aucune phrase à lire.")
        return

    print(cleaned_text)
    output_path = str(ROOT / "tmp/tts.wav")
    with suppress_output():
        tts.tts_to_file(text=cleaned_text, file_path=output_path)
        subprocess.run(["aplay", output_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    os.remove(output_path)

# ──────────────────────── Traitement texte ────────────────────────
def clean_text(text):
    lines = [line for line in text.splitlines() if line.strip()]
    cleaned = lines[-1]
    return cleaned.replace("[end of text]", "\n")

# ──────────────────────── Chargement du contexte ────────────────────────
with open(CONTEXT_PATH, "r", encoding="utf-8") as f:
    PLANETE_SCIENCES_CONTEXT = f.read()


# ──────────────────────── Appel LLaMA avec contexte ────────────────────────
def llama(user_input):
    prompt = (
        "<|start_header_id|>user<|end_header_id|>\n"
        f"Tu es un assistant concis. Utilise uniquement les informations suivantes sans les répéter.\n"
        f"{PLANETE_SCIENCES_CONTEXT}\n\n"
        f"Réponds uniquement à la question suivante en 3 phrases max, sans recopier le texte ci-dessus :\n"
        f"{user_input}<|eot_id|>\n"
        "<|start_header_id|>assistant<|end_header_id|>\n"
    )

    try:
        result = subprocess.run(
            [
                str(LLAMA_CLI_PATH),
                "--model", str(LLAMA_MODEL),
                "--single-turn",
                "--n-predict", N_PREDICT,
                "--threads", THREADS,
                "-p", prompt,
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True
        )
        output = result.stdout.decode("utf-8", errors="ignore")
    except subprocess.CalledProcessError as e:
        print("Erreur LLaMA :")
        print(e.stderr.decode("utf-8", errors="ignore"))
        return "Erreur LLaMA, voir logs."

    match = re.search(
        r"<\|start_header_id\|>assistant<\|end_header_id\|>\s*(.*?)\s*<\|eot_id\|>",
        output, re.S
    )
    return match.group(1).strip() if match else output.strip()

# ──────────────────────── Démarrage ────────────────────────
if __name__ == "__main__":
    speak("Assistant vocal initialisé. Je vous écoute.", raw=True)

    try:
        while True:
            user_input = listen()
            if user_input:
                print(f"> {user_input}")
                user_input_lower = user_input.lower()

                if "stop" in user_input_lower or "armageddon" in user_input_lower:
                    speak("Fin de la conversation. Au revoir", raw=True)
                    break

                response = llama(user_input)
                speak(response)

    except KeyboardInterrupt:
        speak("Fin de la conversation. Au revoir", raw=True)
        sys.exit(0)

