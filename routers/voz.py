import base64
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from google.cloud import speech, texttospeech

from middleware.auth import verify_token

router = APIRouter()


class AudioInput(BaseModel):
    audio_base64: str
    idioma: str = "es-419"


class TextoInput(BaseModel):
    texto: str
    idioma: str = "es-419"


@router.post("/voz/transcribir")
def transcribir(body: AudioInput, user=Depends(verify_token)):
    client = speech.SpeechClient()
    audio_bytes = base64.b64decode(body.audio_base64)

    audio = speech.RecognitionAudio(content=audio_bytes)
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.ENCODING_UNSPECIFIED,
        language_code=body.idioma,
        enable_automatic_punctuation=True,
    )

    response = client.recognize(config=config, audio=audio)
    texto = "".join(r.alternatives[0].transcript for r in response.results)
    return {"texto": texto}


@router.post("/voz/sintetizar")
def sintetizar(body: TextoInput, user=Depends(verify_token)):
    client = texttospeech.TextToSpeechClient()

    synthesis_input = texttospeech.SynthesisInput(text=body.texto)
    voice = texttospeech.VoiceSelectionParams(
        language_code=body.idioma,
        name="es-419-Standard-B",
    )
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3,
        speaking_rate=1.0,
    )

    response = client.synthesize_speech(
        input=synthesis_input, voice=voice, audio_config=audio_config
    )
    return {"audio_base64": base64.b64encode(response.audio_content).decode("utf-8")}
