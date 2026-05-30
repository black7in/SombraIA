from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from google.cloud.firestore_v1 import SERVER_TIMESTAMP

from middleware.auth import verify_token
from db.firestore import get_db

router = APIRouter()


class NuevaParcela(BaseModel):
    nombre: str
    poligono: List[List[float]]
    cultivo: str
    modo: str = "agro"
    resultado: Optional[dict] = None


@router.get("/parcelas")
def listar_parcelas(user=Depends(verify_token)):
    db = get_db()
    docs = (
        db.collection("parcelas")
        .where("user_id", "==", user["uid"])
        .limit(50)
        .stream()
    )
    return [{"id": d.id, **d.to_dict()} for d in docs]


@router.post("/parcelas", status_code=201)
def guardar_parcela(parcela: NuevaParcela, user=Depends(verify_token)):
    db = get_db()
    _, ref = db.collection("parcelas").add({
        "user_id": user["uid"],
        "nombre": parcela.nombre,
        "poligono": parcela.poligono,
        "cultivo": parcela.cultivo,
        "modo": parcela.modo,
        "resultado": parcela.resultado,
        "created_at": SERVER_TIMESTAMP,
    })
    return {"id": ref.id}


@router.delete("/parcelas/{parcela_id}", status_code=204)
def eliminar_parcela(parcela_id: str, user=Depends(verify_token)):
    db = get_db()
    doc = db.collection("parcelas").document(parcela_id).get()
    if not doc.exists:
        raise HTTPException(status_code=404, detail="Parcela no encontrada")
    if doc.to_dict().get("user_id") != user["uid"]:
        raise HTTPException(status_code=403, detail="Sin permiso")
    db.collection("parcelas").document(parcela_id).delete()
