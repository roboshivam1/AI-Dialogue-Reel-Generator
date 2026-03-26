# 🎬 Paheli–Boojho AI Video Generator

An AI-powered Streamlit app that generates short two-character dialogue reels — complete with TTS audio, speaker diarization, character expression overlays, AI image inserts, and auto-captions.

---

## ✨ Features

- **Script generation** via Gemini 2.5 Flash (customisable tone, humor level, topic)
- **Multi-speaker TTS** using Gemini's preview TTS model
- **Speaker diarization** via AssemblyAI (maps audio segments back to each character)
- **Expression detection** — Gemini picks the right character face per dialogue line
- **AI image overlays** — keyword-matched images generated and timed to the script
- **Auto-captioning** via PyCaps
- **ffmpeg-based video renderer** with background video support

---

## 🚀 Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/your-username/your-repo-name.git
cd your-repo-name
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

> **Note:** `pyannote.audio` requires a Hugging Face token and model access. See [pyannote docs](https://github.com/pyannote/pyannote-audio) for setup.  
> `ffmpeg` must also be installed on your system: https://ffmpeg.org/download.html

### 3. Configure API keys

Copy the example env file and fill in your keys:

```bash
cp .env.example .env
```

Then edit `.env`:

```
GEMINI_API_KEY=your_gemini_key_here
ASSEMBLY_AI_API_KEY=your_assemblyai_key_here
ZAPCAP_API_KEY=your_zapcap_key_here
ZAPCAP_TEMPLATE_ID=your_template_id_here
```

You can also enter keys directly in the **🔑 API Keys** tab inside the app — manual entries override the `.env` values.

### 4. Run the app

```bash
streamlit run main.py
```

---

## 🔑 Where to get API keys

| Service | Link |
|---|---|
| Gemini | https://aistudio.google.com/api-keys |
| AssemblyAI | https://www.assemblyai.com/dashboard/api-keys |
| Zapcap | https://platform.zapcap.ai/dashboard/api-key |
| Zapcap Templates | https://platform.zapcap.ai/dashboard/templates |

---

## 📁 Project Structure

```
├── main.py                  # Main Streamlit app
├── character_data.py        # Character image path mappings
├── assets/
│   ├── backgrounds/         # Background video files
│   ├── characters/          # Character PNG overlays
│   └── temp/                # Temp storage for uploaded backgrounds
├── pycaps_templates_own/    # PyCaps caption templates
├── .env.example             # Template for environment variables
├── requirements.txt
└── README.md
```

---

## ⚠️ Notes

- Generated audio, images, and video files are listed in `.gitignore` and will not be committed.
- Never commit your `.env` file.
- The `assets/` folder (character images, backgrounds) is not included in this repo — add your own or contact the author.