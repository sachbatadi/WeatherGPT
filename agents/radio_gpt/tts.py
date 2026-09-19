import os
import asyncio

from gtts import gTTS
import edge_tts


EDGE_VOICE_MAP = {
    "Hindi": {
        "male": "hi-IN-MadhurNeural",
        "female": "hi-IN-SwaraNeural",
    },
    "English": {
        "male": "en-IN-PrabhatNeural",
        "female": "en-IN-NeerjaNeural",
    },
}


def generate_speech(
    text: str,
    language: str,
    gender: str = "male"
):
    language = language.strip().title()
    gender = gender.strip().lower()

    # audio folder is:
    # radio-gpt/.venv/audio/
    app_dir = os.path.dirname(os.path.abspath(__file__))
    venv_dir = os.path.dirname(app_dir)

    audio_dir = os.path.join(
        venv_dir,
        "audio"
    )

    os.makedirs(audio_dir, exist_ok=True)

    # -------------------------
    # PUNJABI
    # -------------------------
    if language == "Punjabi":

        file_path = os.path.join(
            audio_dir,
            f"radio_alert_punjabi_{gender}.mp3"
        )

        tts = gTTS(
            text=text,
            lang="pa",
            slow=False
        )

        tts.save(file_path)

        return {
            "status": "audio_generated",
            "language": "Punjabi",
            "voice": "gTTS Punjabi",
            "gender": gender,
            "file": file_path
        }

    # -------------------------
    # FALLBACK
    # -------------------------
    if language not in EDGE_VOICE_MAP:
        language = "English"

    if gender not in EDGE_VOICE_MAP[language]:
        gender = "male"

    voice = EDGE_VOICE_MAP[language][gender]

    file_path = os.path.join(
        audio_dir,
        f"radio_alert_{language.lower()}_{gender}.mp3"
    )

    # -------------------------
    # EDGE TTS
    # -------------------------
    async def generate_edge_audio():

        communicate = edge_tts.Communicate(
            text=text,
            voice=voice
        )

        await communicate.save(file_path)

    asyncio.run(
        generate_edge_audio()
    )

    return {
        "status": "audio_generated",
        "language": language,
        "voice": voice,
        "gender": gender,
        "file": file_path
    }