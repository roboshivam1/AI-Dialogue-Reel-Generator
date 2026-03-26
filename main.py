import asyncio
import sys
from dotenv import load_dotenv

load_dotenv()

import streamlit as st
from google import genai
from google.genai import types
import re
import base64
import mimetypes
import os
import struct
import json
import assemblyai as aai
import srt
from pyannote.audio import Pipeline
from typing import List, Tuple
import time
import requests
#from moviepy.editor import VideoFileClip, ImageClip, CompositeVideoClip, AudioFileClip
from character_data import character_pairs

st.set_page_config(page_title="Paheli–Boojho Video Generator", layout="wide")

UPLOADABLE_PATH = "final_rendered_video.mp4"
OUTPUT_VIDEO = "intermediate_render.mp4"

# =====================
#       PAGE TITLE
# =====================
st.title("🎬 Paheli–Boojho AI Video Generator")


# =====================
#       TABS
# =====================
tab1, tab2, tab3, tab4 = st.tabs(["🔑 API Keys", "🎛 Video Settings", "📝 Script Editor", "Render Video"])


# ============================================================
#                     TAB 1: API KEY INPUT
# ============================================================

with tab1:
    st.header("🔑 Enter Your API Keys")
    st.info(
        "Keys are loaded automatically from your `.env` file if present. "
        "You can also enter them manually here — manual entries take priority."
    )

    # 1. Gemini API Key
    col1, col2 = st.columns([0.7, 0.3])
    with col1:
        gemini_input = st.text_input(
            "Gemini 2.0 Flash API Key",
            type="password",
            key="gemini_key_input",
            placeholder="Loaded from .env  •  or enter manually"
        )
    with col2:
        st.write("")
        st.link_button("Get Key", "https://aistudio.google.com/api-keys")

    # 2. AssemblyAI Key
    col3, col4 = st.columns([0.7, 0.3])
    with col3:
        assembly_input = st.text_input(
            "AssemblyAI API Key",
            type="password",
            key="assembly_key_input",
            placeholder="Loaded from .env  •  or enter manually"
        )
    with col4:
        st.write("")
        st.link_button("Get Key", "https://www.assemblyai.com/dashboard/api-keys")

    # 3. Zapcap API Key
    col5, col6 = st.columns([0.7, 0.3])
    with col5:
        zapcap_input = st.text_input(
            "Zapcap API Key",
            type="password",
            key="zapcap_key_input",
            placeholder="Loaded from .env  •  or enter manually"
        )
    with col6:
        st.write("")
        st.link_button("Get Key", "https://platform.zapcap.ai/dashboard/api-key")

    # 4. Template ID
    col7, col8 = st.columns([0.7, 0.3])
    with col7:
        template_input = st.text_input(
            "Zapcap Template ID",
            type="password",
            key="zapcap_template_input",
            placeholder="Loaded from .env  •  or enter manually"
        )
    with col8:
        st.write("")
        st.link_button("View Templates", "https://platform.zapcap.ai/dashboard/templates")

# ---- Resolve keys: manual UI input overrides .env ----
GEMINI_API_KEY      = gemini_input.strip()   or os.getenv("GEMINI_API_KEY",      "")
ASSEMBLY_AI_API_KEY = assembly_input.strip() or os.getenv("ASSEMBLY_AI_API_KEY", "")
ZAPCAP_API_KEY      = zapcap_input.strip()   or os.getenv("ZAPCAP_API_KEY",      "")
TEMPLATE_ID         = template_input.strip() or os.getenv("ZAPCAP_TEMPLATE_ID",  "")


# ============================================================
#                     TAB 2: VIDEO SETTINGS
# ============================================================
with tab2:
    st.header("🎛 Customize Your Video")

    # ---------------- VOICE SELECTION ----------------
    st.subheader("🎤 Voice Selection")

    voice_options = {
        "Zephyr": "Bright, Higher pitch",
        "Puck": "Upbeat, Middle pitch",
        "Charon": "Informative, Lower pitch",
        "Kore": "Firm, Middle pitch",
        "Fenrir": "Excitable, Lower mid",
        "Achernar": "Clean, Light tone",
        "Iapetus": "Deep, Serious tone",
        "Vega": "Balanced, Natural voice",
        "Soteria": "Soft, Calm voice",
        "Artemis": "Storytelling, Warm",
    }

    SELECTED_VOICE_1 = st.selectbox(
        "Select Voice 1",
        options=list(voice_options.keys()), index=5,
        format_func=lambda v: f"{v} — {voice_options[v]}"
    )

    SELECTED_VOICE_2 = st.selectbox(
        "Select Voice 2",
        options=list(voice_options.keys()), index=6,
        format_func=lambda v: f"{v} — {voice_options[v]}"
    )

    st.markdown("---")

    # ---------------- BACKGROUND VIDEO SELECTION ----------------
    st.subheader("🎞 Background Video")

    background_options = {
        "Subway Surfers": "assets/backgrounds/subway_surfers_background.mp4",
        "Courtroom":"assets/backgrounds/courtroom_background.mp4"
        
    }

    mode = st.radio("Choose Background Type:", ["Preset Videos", "Upload Your Own"])

    if mode == "Preset Videos":
        selected_bg = st.selectbox("Choose Background Video:", list(background_options.keys()))
        final_bg_video_path = background_options[selected_bg]
        

    else:
        uploaded_bg = st.file_uploader("Upload your own background video", type=["mp4"])
        if uploaded_bg:
            final_bg_video_path = "assets/temp/custom_bg.mp4"
            with open(final_bg_video_path, "wb") as f:
                f.write(uploaded_bg.read())
    st.markdown("---")
    #----------------- CHARACTER PAIR SELECTION ------------------

    st.subheader("🧑‍🤝‍🧑 Character Pair")

    selected_pair = st.selectbox(
        "Choose Characters",
        options=list(character_pairs.keys())
    )
    imgcol1, imgcol2, imgcol3 = st.columns([0.2,0.2,0.6])
    with imgcol1:
        st.image(character_pairs[selected_pair]["speaker1"]["thumb"])
    with imgcol2:
        st.image(character_pairs[selected_pair]["speaker2"]["thumb"])
    
    st.markdown("---")

    image_overlay_radio = st.radio("Do you want image overlays in your video?", options=['Yes', 'No'])

    st.markdown("---")
    
# ============================================================
#                     TAB 3: SCRIPT EDITOR
# ============================================================
with tab3:
    st.header("📝 Script Generator Settings")

    SCRIPT_TONES = [
    "Gen-Z",
    "Sarcastic",
    "Informative (No Jokes)",
    "Friendly Conversational",
    "Hyperactive YouTuber",
    "Calm & Minimalist",
    "Storytelling & Cinematic",
    "Motivational",
    "Teacher Explainer",
    "Nerdy Developer",
    "Stand-up Comedian",
    "ELI5 (Explain Like I'm 5)",
    "Detective Noir",
    "Deadpan Dry Humor",
    "Bollywood Dramatic",
    "Fast-paced Reels Style",
    "Meme-ish + Comedy",
    ]


    topic = st.text_input(
        "📌 What should the video be about?",
        "Explain Python decorators in a fun way"
    )
    st.markdown("---")
    script_tone = st.selectbox(
        "🎭 Select Script Tone",
        options=SCRIPT_TONES
    )
    st.markdown("---")
    humor_level = st.slider(
        "😂 Humor Level",
        min_value=1,
        max_value=10,
        value=6
    )
    st.markdown("---")
    st.markdown("### ➕ Additional Prompt Instructions")

    with st.expander("Add extra instructions to the prompt (Optional)"):
        extra_prompt = st.text_area(
            "Extra prompt additions",
            placeholder="Add any specific instructions, buzzwords, constraints, etc."
        )

# Extract character names from selected pair
char1 = character_pairs[selected_pair]["speaker1"]["name"]
char2 = character_pairs[selected_pair]["speaker2"]["name"]

SCRIPT_PROMPT = f"""
You are writing a short, engaging Instagram Reel script featuring two characters:
Speaker 1 = {char1}
Speaker 2 = {char2}

### TOPIC
The script should be about: **{topic}**

### TONE & STYLE
- Overall tone: **{script_tone}**
- Humor level (0–10): **{humor_level}**
- Make the delivery appropriate for the chosen tone.
- Adapt both characters' personalities to match the tone.
- The script must have an engaging hook in the FIRST 3 seconds.
- Keep it fast-paced, entertaining, and highly watchable.

### FORMAT RULES
- ONLY output spoken dialogue in this exact format:
  Speaker 1: ...
  Speaker 2: ...
- Absolutely NO stage directions, no markdown, no descriptions, no scene notes.
- DO NOT output narration or camera instructions.
- The script should be around 40–50 seconds long.
- Make the conversation smooth, natural, and punchy.
- Balance the dialogue (unless the tone naturally favors one speaker).

### CHARACTERS
- {char1}: Curious, expressive, and reactive.
- {char2}: Knowledgeable, witty, but clear in explanation.

### ADDITIONAL CUSTOM INSTRUCTIONS
{extra_prompt if extra_prompt.strip() != "" else "No extra instructions provided."}

### OUTPUT REQUIREMENTS
Return ONLY the spoken lines, nothing else:
Speaker 1: …
Speaker 2: …

Give the output as seperate lines for each dialogue not as a single paragraph.
Write each line as a new line like:
Speaker 1: …
Speaker 2: …
NOT:
Speaker 1: … .Speaker 2: …
"""

# === GEMINI CLIENT ===
genai_client = genai.Client(api_key=GEMINI_API_KEY)

# === Generate Script ===
def generate_script():
    prompt = (SCRIPT_PROMPT)
    response = genai_client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
    st.write(response.text.strip())
    return response.text.strip()


def generate_title(script):
    title_prompt = f"Write a catchy title for an Instagram reel with the following script, Also include 8-12 suitable hashtags to get the maximum reach. Dont use emojis. Write one single title that can be directly copied and dont write any extra instructions, just the title with hashtags. Script: \n {script}"
    response = genai_client.models.generate_content(model="gemini-2.5-flash", contents=title_prompt)
    video_title = response.text.strip()
    with open('python_video_title.txt', 'w') as file:
        file.write(video_title)

# ===  Extract Image Prompts ===

def extract_image_prompts(script):

    prompt = (f"""
You are an assistant that reads narration scripts and extracts keywords and visual prompts.

SCRIPT:
\"\"\"{script}\"\"\"

INSTRUCTIONS:
- For each fact in the script, identify one **unique keyword** (e.g., "bananas", "Eiffel", "gravity").
- For each keyword, provide a **short visual prompt** that can be used to generate an image.
- The keyword can be multiple words (1-3 words). Try to write keywords as "Eiffel tower", not "EiffelTower" so that it can be exactly found in the script text.
- Format the output as a valid **JSON object** with double quotes. Like this:

{{
  "bananas": "A bunch of ripe bananas on a kitchen counter",
  "Eiffel": "Eiffel Tower expanding under summer heat",
  "gravity": "Newton under an apple tree, apple mid-fall"
}}

Only return the JSON. Do not include explanations, markdown, or bullet points. Think of atleast one image, just DO NOT return 'None'.
""")
    
    response = genai_client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
    raw = response.text.strip()

    # Strip markdown backticks if present (like ```json ... ```)
    if raw.startswith("```"):
        raw = re.sub(r"^```(?:json)?\n?", "", raw)
        raw = re.sub(r"\n?```$", "", raw)

    return raw

#=== GENERATE TTS AUDIO ======

def save_binary_file(file_name, data):
    f = open(file_name, "wb")
    f.write(data)
    f.close()
    print(f"File saved to to: {file_name}")


def generate(script):
    client = genai.Client(
        api_key=GEMINI_API_KEY,
    )

    model = "gemini-2.5-flash-preview-tts"
    contents = [
        types.Content(
            role="user",
            parts=[
                types.Part.from_text(text=f"Both speakers speak really fast.{script}"),
            ],
        ),
    ]
    generate_content_config = types.GenerateContentConfig(
        temperature=1,
        response_modalities=[
            "audio",
        ],
        speech_config=types.SpeechConfig(
            multi_speaker_voice_config=types.MultiSpeakerVoiceConfig(
                speaker_voice_configs=[
                    types.SpeakerVoiceConfig(
                        speaker="Speaker 1",
                        voice_config=types.VoiceConfig(
                            prebuilt_voice_config=types.PrebuiltVoiceConfig(
                                voice_name=SELECTED_VOICE_1
                            )
                        ),
                    ),
                    types.SpeakerVoiceConfig(
                        speaker="Speaker 2",
                        voice_config=types.VoiceConfig(
                            prebuilt_voice_config=types.PrebuiltVoiceConfig(
                                voice_name=SELECTED_VOICE_2
                            )
                        ),
                    ),
                ]
            ),
        ),
    )

    file_index = 0
    for chunk in client.models.generate_content_stream(
        model=model,
        contents=contents,
        config=generate_content_config,
    ):
        if (
            chunk.candidates is None
            or chunk.candidates[0].content is None
            or chunk.candidates[0].content.parts is None
        ):
            continue
        if chunk.candidates[0].content.parts[0].inline_data and chunk.candidates[0].content.parts[0].inline_data.data:
            file_name = f"generated_audio{file_index}"
            file_index += 1
            inline_data = chunk.candidates[0].content.parts[0].inline_data
            data_buffer = inline_data.data
            file_extension = mimetypes.guess_extension(inline_data.mime_type)
            if file_extension is None:
                file_extension = ".wav"
                data_buffer = convert_to_wav(inline_data.data, inline_data.mime_type)
            save_binary_file(f"{file_name}{file_extension}", data_buffer)
        else:
            print(chunk.text)

def convert_to_wav(audio_data: bytes, mime_type: str) -> bytes:
    """Generates a WAV file header for the given audio data and parameters.

    Args:
        audio_data: The raw audio data as a bytes object.
        mime_type: Mime type of the audio data.

    Returns:
        A bytes object representing the WAV file header.
    """
    parameters = parse_audio_mime_type(mime_type)
    bits_per_sample = parameters["bits_per_sample"]
    sample_rate = parameters["rate"]
    num_channels = 1
    data_size = len(audio_data)
    bytes_per_sample = bits_per_sample // 8
    block_align = num_channels * bytes_per_sample
    byte_rate = sample_rate * block_align
    chunk_size = 36 + data_size  # 36 bytes for header fields before data chunk size

    # http://soundfile.sapp.org/doc/WaveFormat/

    header = struct.pack(
        "<4sI4s4sIHHIIHH4sI",
        b"RIFF",          # ChunkID
        chunk_size,       # ChunkSize (total file size - 8 bytes)
        b"WAVE",          # Format
        b"fmt ",          # Subchunk1ID
        16,               # Subchunk1Size (16 for PCM)
        1,                # AudioFormat (1 for PCM)
        num_channels,     # NumChannels
        sample_rate,      # SampleRate
        byte_rate,        # ByteRate
        block_align,      # BlockAlign
        bits_per_sample,  # BitsPerSample
        b"data",          # Subchunk2ID
        data_size         # Subchunk2Size (size of audio data)
    )
    return header + audio_data

def parse_audio_mime_type(mime_type: str) -> dict[str, int | None]:
    """Parses bits per sample and rate from an audio MIME type string.

    Assumes bits per sample is encoded like "L16" and rate as "rate=xxxxx".

    Args:
        mime_type: The audio MIME type string (e.g., "audio/L16;rate=24000").

    Returns:
        A dictionary with "bits_per_sample" and "rate" keys. Values will be
        integers if found, otherwise None.
    """
    bits_per_sample = 16
    rate = 24000

    # Extract rate from parameters
    parts = mime_type.split(";")
    for param in parts: # Skip the main type part
        param = param.strip()
        if param.lower().startswith("rate="):
            try:
                rate_str = param.split("=", 1)[1]
                rate = int(rate_str)
            except (ValueError, IndexError):
                pass # Keep rate as default
        elif param.startswith("audio/L"):
            try:
                bits_per_sample = int(param.split("L", 1)[1])
            except (ValueError, IndexError):
                pass # Keep bits_per_sample as default if conversion fails

    return {"bits_per_sample": bits_per_sample, "rate": rate}

def generate_images(prompts, out_dir="generated_images"):
    os.makedirs(out_dir, exist_ok=True)
    model = "gemini-2.5-flash-image"
    image_paths = []

    for i, prompt in enumerate(prompts):
        contents = [types.Content(role="user", parts=[types.Part(text=prompt)])]
        config = types.GenerateContentConfig(response_modalities=["TEXT", "IMAGE"])

        for chunk in genai_client.models.generate_content_stream(
            model=model, contents=contents, config=config
        ):
            if not chunk.candidates:
                continue
            if not chunk.candidates[0].content:
                continue
            if not chunk.candidates[0].content.parts:
                continue

            part = chunk.candidates[0].content.parts[0]
            if part.inline_data:
                ext = mimetypes.guess_extension(part.inline_data.mime_type) or ".png"
                path = os.path.join(out_dir, f"img_{i}{ext}")
                with open(path, "wb") as f:
                    f.write(part.inline_data.data)
                image_paths.append(path)
                break  # stop after the first valid image

    return image_paths

#=== STEP 5: TRANSCRIPT FROM AUDIO FILE AND EXTRACT IMAGE TIMINGS
def transcript_assembly():
    aai.settings.api_key = ASSEMBLY_AI_API_KEY

    audio_file = "generated_audio0.wav"
   
    config = aai.TranscriptionConfig(speech_model=aai.SpeechModel.best)

    transcript = aai.Transcriber(config=config).transcribe(audio_file)

    if transcript.status == "error":
        raise RuntimeError(f"Transcription failed: {transcript.error}")

    subtitles = transcript.export_subtitles_srt()

    return(subtitles)

def get_segments_for_keywords(srt_text, keywords):
    """
    srt_text: subtitle string in SRT format
    keywords: list of strings like ["CLAT_Counselling", "Digital_Dance", "NLU_Options"]
    
    Returns:
        List of (start_time_in_seconds, end_time_in_seconds, keyword)
    """
    results = []
    subtitles = list(srt.parse(srt_text))

    for keyword in keywords:
        keyword_with_spaces = keyword.replace('_', ' ')
        keyword_lower = keyword_with_spaces.lower()
        
        for sub in subtitles:
            if keyword_lower in sub.content.lower():
                start = sub.start.total_seconds()
                end = sub.end.total_seconds()
                results.append((start, end, keyword))
                break
            words = keyword_with_spaces.split()
            if len(words) > 1:
                for word in words:
                    if len(word) > 3 and word.lower() in sub.content.lower():
                        start = sub.start.total_seconds()
                        end = sub.end.total_seconds()
                        results.append((start, end, keyword))
                        break
                if results and results[-1][2] == keyword:
                    break

    return results

#=== DIARIZE AUDIO FOR SPEAKER TIMING EXTRACTION ======
def diarize_audio():
    aai.settings.api_key = ASSEMBLY_AI_API_KEY

    audio_file = (
        "generated_audio0.wav"
    )
    diarization_timings = []
    diarization_text_only = []

    config = aai.TranscriptionConfig(
    speaker_labels=True,
    )

    transcript = aai.Transcriber().transcribe(audio_file, config)


    for utterance in transcript.utterances:
        diarization_timing_element = f"Speaker {utterance.speaker}: , start: {utterance.start}, end: {utterance.end}"
        diarization_text_element = utterance.text
        diarization_timings.append(diarization_timing_element)
        diarization_text_only.append(diarization_text_element)
    diarization_timings_parsed = []
    #PARSING THE DIARIZATION TIMINGS LIST TO MAKE IT USABLE
    for entry in diarization_timings:
        parts = entry.split(',')
        speaker = parts[0].split()[1] #'A' OR 'B'
        start_ms = int(parts[1].split(':')[1]) #START TIMING MILLISECONDS
        end_ms = int(parts[2].split(':')[1]) #ENDIND TIMING MILLISECONDS
        start_sec = start_ms/1000.0
        end_sec = end_ms/1000.0
        diarization_timings_parsed.append((speaker, start_sec, end_sec))
    print(diarization_timings_parsed)
    return diarization_timings_parsed, diarization_text_only


def detect_expressions(dialogue_lines: List[str]) -> List[str]:
    """
    Given a list of dialogue strings, returns a list of expression labels
    (e.g. "neutral", "questioning", "explaining", "laughing", etc.).
    The output list will have the same length and order as dialogue_lines.
    """
    allowed = ["neutral", "questioning", "explaining", "laughing", "surprised", "confused", "smirk"]
    
    prompt = f"""You are given {len(dialogue_lines)} lines of dialogue.  
    From this list of possible expressions:
    {allowed}
    Return a JSON array of exactly {len(dialogue_lines)} items, 
    where each item is the single best expression for the corresponding line.
    Do not include any extra text—only output the JSON list.
    Here are the lines:
    """
    for i, line in enumerate(dialogue_lines, 1):
        prompt += f"{i}. \"{line.strip()}\"\n"
    
    response = genai_client.models.generate_content(model="gemini-2.5-flash", contents=prompt).text
    
    if response.startswith("```"):
        response = re.sub(r"^```(?:json)?\s*", "", response)
        response = re.sub(r"\s*```$", "", response)
    
    try:
        expr_list = json.loads(response)
    except json.JSONDecodeError:
        expr_list = ["neutral"] * len(dialogue_lines)
    
    validated = []
    for expr in expr_list:
        e = expr.lower()
        validated.append(e if e in allowed else "neutral")
    
    if len(validated) < len(dialogue_lines):
        validated += ["neutral"] * (len(dialogue_lines) - len(validated))
    elif len(validated) > len(dialogue_lines):
        validated = validated[: len(dialogue_lines)]
    
    return validated

def map_expression_to_overlay(expression_list):
    count = 0
    overlay_path_list = []
    for expression in expression_list:
        if count%2 != 0: 
            overlay_path = character_pairs[selected_pair]["speaker2"][expression]
        else: 
            overlay_path = character_pairs[selected_pair]["speaker1"][expression]
        overlay_path_list.append(overlay_path)
        count = count+1
    return overlay_path_list

import subprocess
import re

def create_video_with_images_ffmpeg(
    script,
    audio_path,
    image_paths,
    video_path,
    output_path,
    segments,
    keyword_to_imagepath,
    diarization_timings_parsed,
    overlay_path_list
):

    # 1. Get audio duration
    probe_cmd = (
        f"ffprobe -i \"{audio_path}\" -show_entries format=duration "
        f"-v quiet -of csv=p=0"
    )
    duration = float(subprocess.check_output(probe_cmd, shell=True).decode().strip())

    # 2. Collect matched images with timings
    matched_images = []
    for (start_time, end_time, text) in segments:
        for keyword, image_path in keyword_to_imagepath.items():
            if re.search(rf"\b{re.escape(keyword)}\b", text, re.IGNORECASE):
                matched_images.append((image_path, start_time, end_time))
                break

    # 3. FFmpeg inputs
    ffmpeg_inputs = [
        f"-i \"{video_path}\"",
        f"-i \"{audio_path}\""
    ]

    for img_path, _, _ in matched_images:
        ffmpeg_inputs.append(f"-framerate 1 -i \"{img_path}\"")

    for img_path in overlay_path_list:
        ffmpeg_inputs.append(f"-framerate 1 -i \"{img_path}\"")

    # 4. Build filter_complex
    filter_parts = []
    current_base = "[0:v]"

    # ---------------- KEYWORD IMAGES (TOP) ----------------
    for idx, (_, start_time, end_time) in enumerate(matched_images):
        img_in = idx + 2
        scaled = f"[kw{idx}]"

        filter_parts.append(
            f"[{img_in}:v]format=rgba,scale=720:-1{scaled}"
        )

        filter_parts.append(
            f"{current_base}{scaled}overlay="
            f"x=(W-w)/2:y=20:"
            f"enable='between(t,{start_time},{end_time})'"
            f"[v_kw{idx}]"
        )

        current_base = f"[v_kw{idx}]"

    # ---------------- CHARACTER OVERLAYS (BOTTOM) ----------------
    overlay_base_index = 2 + len(matched_images)

    for idx, (speaker, start_time, end_time) in enumerate(diarization_timings_parsed):
        img_in = overlay_base_index + idx
        scaled = f"[char{idx}]"

        filter_parts.append(
            f"[{img_in}:v]format=rgba,scale=720:-1{scaled}"
        )

        filter_parts.append(
            f"{current_base}{scaled}overlay="
            f"x=(W-w)/2:y=(H-h)-20:"
            f"enable='between(t,{start_time},{end_time})'"
            f"[v_char{idx}]"
        )

        current_base = f"[v_char{idx}]"

    filter_complex = "; ".join(filter_parts)

    # 5. Final FFmpeg command
    final_cmd = (
        f"ffmpeg -y "
        f"{' '.join(ffmpeg_inputs)} "
        f"-filter_complex \"{filter_complex}\" "
        f"-map \"{current_base}\" -map 1:a "
        f"-shortest "
        f"-c:v libx264 -preset fast -crf 23 "
        f"-c:a aac "
        f"-fps_mode vfr "
        f"\"{output_path}\""
    )

    print("\nRUNNING FFMPEG COMMAND:\n", final_cmd, "\n")
    subprocess.run(final_cmd, shell=True, check=True)
    print("Render complete →", output_path)

    return output_path



def create_video_without_images_ffmpeg(
    script,
    audio_path,
    video_path,
    output_path,
    diarization_timings_parsed,
    overlay_path_list
):

    # 1. Read audio duration (ffprobe)
    probe_cmd = (
        f"ffprobe -i {audio_path} -show_entries format=duration "
        f"-v quiet -of csv=p=0"
    )
    duration = float(subprocess.check_output(probe_cmd, shell=True).decode().strip())

    # 2. Prepare FFmpeg input list
    ffmpeg_inputs = [
        f"-i {video_path}",
        f"-i {audio_path}"
    ]

    for img_path in overlay_path_list:
        ffmpeg_inputs.append(f"-loop 1 -i {img_path}")

    # 3. Build filter_complex
    filter_parts = []

    current_base = "[0:v]"

    for idx, (speaker, start, end) in enumerate(diarization_timings_parsed):
        img_in = idx + 2
        scaled = f"[scaled{idx}]"

        scale_filter = f"[{img_in}:v]scale=iw:ih {scaled}"

        overlay_filter = (
            f"{current_base}{scaled}overlay="
            f"x=(W-w)/2:y=(H-h)-20:"
            f"enable='between(t,{start},{end})'[v{idx}]"
        )

        filter_parts.append(scale_filter)
        filter_parts.append(overlay_filter)

        current_base = f"[v{idx}]"

    filter_complex = "; ".join(filter_parts)

    # 4. Final ffmpeg command
    final_cmd = (
        f"ffmpeg -y "
        f"{' '.join(ffmpeg_inputs)} "
        f"-filter_complex \"{filter_complex}\" "
        f"-map \"{current_base}\" -map 1:a "
        f"-t {duration} "
        f"-c:v libx264 -preset fast -c:a aac "
        f"{output_path}"
    )

    print("\nRUNNING FFMPEG COMMAND:\n", final_cmd, "\n")
    subprocess.run(final_cmd, shell=True)
    print("Render complete →", output_path)
    return output_path



def add_captions(video_path):
    from pycaps import TemplateLoader
    builder = TemplateLoader("pycaps_templates_own/hype_own").with_input_video(video_path).load(False)

    pipeline = builder.build()
    pipeline.run()



with tab4:

    st.header("🚀 Render Final Video")

    # --- PROGRESS + STATUS UI ---
    progress_bar = st.progress(0)
    status_text = st.empty()

    # We'll render logs inside this placeholder
    log_placeholder = st.empty()
    logs = []

    def log(message: str):
        """Append a line to the render log and update the UI."""
        logs.append(message)
        log_placeholder.text("\n".join(logs))

    # --- RENDER BUTTON ---
    if st.button("Start Rendering", type="primary", use_container_width=True):

        # Guard: check all required keys are present
        missing_keys = []
        if not GEMINI_API_KEY:
            missing_keys.append("Gemini API Key")
        if not ASSEMBLY_AI_API_KEY:
            missing_keys.append("AssemblyAI API Key")
        if not ZAPCAP_API_KEY:
            missing_keys.append("Zapcap API Key")
        if not TEMPLATE_ID:
            missing_keys.append("Zapcap Template ID")

        if missing_keys:
            st.error(
                f"⚠️ Missing API keys: **{', '.join(missing_keys)}**. "
                "Please add them in the **🔑 API Keys** tab or in your `.env` file."
            )
            st.stop()

        # ======================================================
        # 1. GENERATE SCRIPT
        # ======================================================
        status_text.text("📝 Generating Script...")
        progress_bar.progress(5)
        log("Generating script...")
        try:
            script = generate_script()
            log("Script generated.")
        except Exception as e:
            st.error(f"Failed at script generation: {e}")
            st.stop()

        st.session_state["script"] = script

        # ======================================================
        # 2. GENERATE TITLE
        # ======================================================
        status_text.text("🏷 Generating Title...")
        progress_bar.progress(10)
        log("Generating title...")
        try:
            generate_title(script)
            log("Title generated and saved.")
        except Exception as e:
            log(f"⚠ Title generation failed: {e}. Continuing without title.")

        # ======================================================
        # 3. OPTIONALLY HANDLE IMAGE OVERLAYS
        # ======================================================
        use_images = (image_overlay_radio == "Yes")

        if use_images:
            # 3A. Extract image prompts
            status_text.text("🧠 Extracting image prompts from script...")
            progress_bar.progress(20)
            log("Extracting image prompts...")
            try:
                raw_json = extract_image_prompts(script)
                image_prompts_dict = json.loads(raw_json)
            except Exception as e:
                st.error(f"Image prompt extraction failed: {e}")
                st.stop()

            image_keywords = list(image_prompts_dict.keys())
            image_prompts_list = list(image_prompts_dict.values())
            log(f"Got {len(image_prompts_list)} image prompts.")

            # 3B. Generate images
            status_text.text("🎨 Generating AI images...")
            progress_bar.progress(30)
            log("Generating AI images via Gemini...")
            try:
                image_paths = generate_images(image_prompts_list)
                log(f"Generated {len(image_paths)} images.")
                
                image_prompts_dict_with_paths = {}
                for idx, keyword in enumerate(image_keywords):
                    if idx < len(image_paths):
                        image_prompts_dict_with_paths[keyword] = image_paths[idx]
                log(f"Mapped keywords to image paths: {image_prompts_dict_with_paths}")
            except Exception as e:
                st.error(f"AI image generation failed: {e}")
                st.stop()
        else:
            image_prompts_dict = {}
            image_keywords = []
            image_paths = []
            log("Skipping AI image overlays (user selected 'No').")

        # ======================================================
        # 4. GENERATE AUDIO
        # ======================================================
        status_text.text("🎤 Generating TTS audio...")
        progress_bar.progress(45)
        log("Generating TTS audio...")
        try:
            generate(script)
            audio_path = "generated_audio0.wav"
            log(f"Audio generated at: {audio_path}")
        except Exception as e:
            st.error(f"Audio generation failed: {e}")
            st.stop()

        # ======================================================
        # 5. SRT & IMAGE TIMINGS (ONLY IF USING IMAGES)
        # ======================================================
        if use_images:
            status_text.text("📜 Transcribing audio for keyword timing...")
            progress_bar.progress(55)
            log("Transcribing audio with AssemblyAI for SRT...")
            try:
                srt_text = transcript_assembly()
                image_timings = get_segments_for_keywords(srt_text, image_keywords)
                log(f"Found {len(image_timings)} image timing segments.")
            except Exception as e:
                st.error(f"SRT transcription or keyword timing failed: {e}")
                st.stop()

        # ======================================================
        # 6. DIARIZATION
        # ======================================================
        status_text.text("🔊 Running speaker diarization...")
        progress_bar.progress(65)
        log("Running diarization...")
        try:
            diarization_tuple = diarize_audio()
            DIARIZATION_TIMINGS_PARSED = diarization_tuple[0]
            DIARIZATION_TEXT_ONLY = diarization_tuple[1]
            log(f"Diarization produced {len(DIARIZATION_TIMINGS_PARSED)} segments.")
        except Exception as e:
            st.error(f"Diarization failed: {e}")
            st.stop()

        # ======================================================
        # 7. EXPRESSION DETECTION
        # ======================================================
        status_text.text("😃 Detecting character expressions...")
        progress_bar.progress(75)
        log("Detecting expressions from dialogue text...")
        try:
            expression_list = detect_expressions(DIARIZATION_TEXT_ONLY)
            overlay_path_list = map_expression_to_overlay(expression_list)
            log(f"Mapped {len(expression_list)} expressions to overlay images.")
        except Exception as e:
            st.error(f"Expression detection or mapping failed: {e}")
            st.stop()

        # ======================================================
        # 8. RENDER VIDEO (WITH or WITHOUT AI IMAGES)
        # ======================================================
        status_text.text("🎞 Rendering video...")
        progress_bar.progress(85)
        log("Rendering video with ffmpeg...")

        try:
            if use_images:
                final_video_path = create_video_with_images_ffmpeg(
                    script=script,
                    audio_path=audio_path,
                    image_paths=None,
                    video_path=final_bg_video_path,
                    output_path=OUTPUT_VIDEO,
                    segments=image_timings,
                    keyword_to_imagepath=image_prompts_dict_with_paths,
                    diarization_timings_parsed=DIARIZATION_TIMINGS_PARSED,
                    overlay_path_list=overlay_path_list
                )

            else:
                final_video_path = create_video_without_images_ffmpeg(
                    script=script,
                    audio_path=audio_path,
                    video_path=final_bg_video_path,
                    output_path=OUTPUT_VIDEO,
                    diarization_timings_parsed=DIARIZATION_TIMINGS_PARSED,
                    overlay_path_list=overlay_path_list
                )

            log(f"Base video rendered: 'intermediate_render.mp4'")
        except Exception as e:
            st.error(f"Video rendering failed: {e}")
            st.stop()

        # ======================================================
        # 9. ADD CAPTIONS (ZAPCAP)
        # ======================================================
        status_text.text("💬 Adding captions via PyCaps...")
        progress_bar.progress(92)

        try:
            log("Adding captions via pycaps")
            add_captions('intermediate_render.mp4')
            final_output = UPLOADABLE_PATH
            log(f"Captioned video saved to: {final_output}")
        except Exception as e:
            log(f"⚠ Captioning failed ({e}), using non-captioned video.")
            final_output = 'intermediate_render.mp4'

        # ======================================================
        # 10. FINAL PREVIEW & DOWNLOAD
        # ======================================================
        progress_bar.progress(100)
        status_text.text("✨ Render complete!")
        st.success("🎉 Video rendered successfully!")

        st.session_state["final_video_path"] = final_output

        # Preview
        st.markdown("### 🎥 Final Video Preview")
        video_html = f"""
            <video width="320" controls>
                <source src="{final_output}" type="video/mp4">
            </video>
        """
        st.markdown(video_html, unsafe_allow_html=True)

        # Download button
        with open(final_output, "rb") as f:
            st.download_button(
                "⬇️ Download Final Video",
                f,
                file_name="PB_Final.mp4"
            )