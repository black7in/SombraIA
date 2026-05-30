from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from google.cloud.firestore_v1 import SERVER_TIMESTAMP

from middleware.auth import verify_token
from db.firestore import get_db

router = APIRouter()


class RegistroUsuario(BaseModel):
    nombre: str
    departamento: str = "Santa Cruz"


@router.post("/auth/register", status_code=201)
def registrar(datos: RegistroUsuario, user=Depends(verify_token)):
    db = get_db()
    db.collection("users").document(user["uid"]).set(
        {
            "uid": user["uid"],
            "nombre": datos.nombre,
            "email": user.get("email", ""),
            "departamento": datos.departamento,
            "created_at": SERVER_TIMESTAMP,
        },
        merge=True,
    )
    return {"uid": user["uid"], "nombre": datos.nombre}


@router.get("/auth/me")
def perfil(user=Depends(verify_token)):
    db = get_db()
    doc = db.collection("users").document(user["uid"]).get()
    if not doc.exists:
        raise HTTPException(status_code=404, detail="Usuario no registrado")
    return doc.to_dict()
