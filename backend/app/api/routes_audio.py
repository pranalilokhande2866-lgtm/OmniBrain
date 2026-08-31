"""
Voice input: transcribes an uploaded audio clip using the same LLM
already configured for the rest of the app (Gemini is natively
multimodal - no separate speech-to-text service needed).
"""
from __future__ import annotations

import base64

from fastapi import APIRouter, HTTPException, UploadFile
from langchain_core.messages import HumanMessage

from app.agents.llm import extract_text, get_vision_llm
from app.models.schemas import TranscribeResponse

router = APIRouter()

TRANSCRIBE_PROMPT = """Transcribe the speech in this audio clip exactly as spoken, in its original language \
(do not translate). Reply with ONLY the transcription - no preamble, no quotes, no commentary. \
If the audio is silent or unintelligible, reply with exactly: [inaudible]"""


@router.post("/audio/transcribe", response_model=TranscribeResponse)
async def transcribe_audio(file: UploadFile) -> TranscribeResponse:
    contents = await file.read()
    if not contents:
        raise HTTPException(status_code=400, detail="Empty audio upload.")

    b64 = base64.b64encode(contents).decode()
    mime_type = file.content_type or "audio/wav"

    message = HumanMessage(
        content=[
            {"type": "text", "text": TRANSCRIBE_PROMPT},
            {"type": "file", "source_type": "base64", "mime_type": mime_type, "data": b64},
        ]
    )

    try:
        llm = get_vision_llm()
        response = llm.invoke([message])
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Transcription failed: {e}") from e

    text = extract_text(response).strip()
    if text == "[inaudible]" or not text:
        raise HTTPException(status_code=422, detail="Couldn't make out any speech in that recording - try again.")

    return TranscribeResponse(text=text)