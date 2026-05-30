from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from db.firestore import get_db
from middleware.auth import verify_token
from services import gemini

router = APIRouter()


class PreguntaChat(BaseModel):
    pregunta: str
    parcela_id: Optional[str] = None


@router.post("/chat")
def chat(body: PreguntaChat, user=Depends(verify_token)):
    contexto = {}
    if body.parcela_id:
        db = get_db()
        doc = db.collection("parcelas").document(body.parcela_id).get()
        if doc.exists:
            data = doc.to_dict()
            contexto = data.get("resultado") or {}
            contexto["cultivo"] = data.get("cultivo", "")

    try:
        respuesta = gemini.chatbot(body.pregunta, contexto)
    except Exception:
        respuesta = "Por ahora no tengo acceso al análisis, pero podés consultarme sobre cultivos y árboles nativos de Santa Cruz."

    return {"respuesta": respuesta}
