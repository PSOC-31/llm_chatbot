# llm Planète Sciences

Un assistant vocal local en français qui utilise la reconnaissance vocale, la synthèse vocale et un modèle LLaMA pour répondre à des questions sur l'association **Planète Sciences Occitanie**.


## Fonctionnalités

- **Reconnaissance vocale** : via [VOSK](https://alphacephei.com/vosk/)
- **Génération de réponses** : via [llama.cpp](https://github.com/ggerganov/llama.cpp)
- **Synthèse vocale** : via [Coqui TTS](https://github.com/coqui-ai/TTS)
- **Connaissances intégrées** : le modèle est guidé par un contexte prédéfini sur l’association Planète Sciences (fichier **contexte.txt**)
- 100% local (aucune API externe)


## Structure du projet

stage_nano_llm/
│
├── main.py # Script principal
├── contexte_planete.txt # Contexte injecté dans LLaMA
├── tmp/ # Dossier temporaire pour fichiers audio
├── vosk/ # Contient le modèle VOSK
│ └── vosk-model-small-fr-0.22/
├── models/ # Modèles GGUF pour llama.cpp
│ └── Meta-Llama-3.1-8B-Instruct-Q6_K/
└── llama.cpp/ # Dossier contenant llama.cpp compilé


## Utilisation
Assurez-vous que les dépendances sont installées (voir ci-dessous), puis exécutez la commande bash


## Prérequis

- Python 3.8+
- Modèle VOSK français (`vosk-model-small-fr-0.22`)
- `llama.cpp` compilé avec `llama-cli`
- Modèle GGUF LLaMA compatible (`Meta-Llama-3.1-8B-Instruct-Q6_K`)
- Dépendances Python : pip install sounddevice vosk TTS

```bash
python3 main.py
# llm_chatbot
