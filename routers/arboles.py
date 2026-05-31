from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from google.cloud.firestore_v1 import SERVER_TIMESTAMP

from middleware.auth import verify_token
from db.firestore import get_db

router = APIRouter()


class NuevoArbol(BaseModel):
    especie: str
    lat: float
    lng: float
    plan_punto_idx: Optional[int] = None
    foto_url: Optional[str] = None
    notas: Optional[str] = None
    estado: str = "plantado"


class ActualizarArbol(BaseModel):
    notas: Optional[str] = None
    estado: Optional[str] = None


class AgregarFoto(BaseModel):
    foto_url: str


def _verificar_parcela(parcela_id: str, uid: str, db):
    doc = db.collection("parcelas").document(parcela_id).get()
    if not doc.exists:
        raise HTTPException(status_code=404, detail="Parcela no encontrada")
    if doc.to_dict().get("user_id") != uid:
        raise HTTPException(status_code=403, detail="Sin permiso")


@router.get("/parcelas/{parcela_id}/arboles")
def listar_arboles(parcela_id: str, user=Depends(verify_token)):
    db = get_db()
    _verificar_parcela(parcela_id, user["uid"], db)
    docs = db.collection("arboles").where("parcela_id", "==", parcela_id).stream()
    return [{"id": d.id, **d.to_dict()} for d in docs]


@router.post("/parcelas/{parcela_id}/arboles", status_code=201)
def registrar_arbol(parcela_id: str, arbol: NuevoArbol, user=Depends(verify_token)):
    db = get_db()
    _verificar_parcela(parcela_id, user["uid"], db)
    fotos = [arbol.foto_url] if arbol.foto_url else []
    _, ref = db.collection("arboles").add({
        "parcela_id": parcela_id,
        "user_id": user["uid"],
        "especie": arbol.especie,
        "lat": arbol.lat,
        "lng": arbol.lng,
        "plan_punto_idx": arbol.plan_punto_idx,
        "fotos": fotos,
        "notas": arbol.notas,
        "estado": arbol.estado,
        "fecha_plantado": SERVER_TIMESTAMP,
    })
    return {"id": ref.id}


@router.put("/parcelas/{parcela_id}/arboles/{arbol_id}")
def actualizar_arbol(parcela_id: str, arbol_id: str, datos: ActualizarArbol, user=Depends(verify_token)):
    db = get_db()
    _verificar_parcela(parcela_id, user["uid"], db)
    doc = db.collection("arboles").document(arbol_id).get()
    if not doc.exists or doc.to_dict().get("user_id") != user["uid"]:
        raise HTTPException(status_code=404, detail="Árbol no encontrado")
    update = {k: v for k, v in datos.model_dump().items() if v is not None}
    if update:
        db.collection("arboles").document(arbol_id).update(update)
    return {"id": arbol_id}


@router.post("/parcelas/{parcela_id}/arboles/{arbol_id}/fotos", status_code=201)
def agregar_foto(parcela_id: str, arbol_id: str, body: AgregarFoto, user=Depends(verify_token)):
    from google.cloud.firestore_v1 import ArrayUnion
    db = get_db()
    _verificar_parcela(parcela_id, user["uid"], db)
    doc = db.collection("arboles").document(arbol_id).get()
    if not doc.exists or doc.to_dict().get("user_id") != user["uid"]:
        raise HTTPException(status_code=404, detail="Árbol no encontrado")
    db.collection("arboles").document(arbol_id).update({"fotos": ArrayUnion([body.foto_url])})
    return {"ok": True}


@router.delete("/parcelas/{parcela_id}/arboles/{arbol_id}", status_code=204)
def eliminar_arbol(parcela_id: str, arbol_id: str, user=Depends(verify_token)):
    db = get_db()
    _verificar_parcela(parcela_id, user["uid"], db)
    doc = db.collection("arboles").document(arbol_id).get()
    if not doc.exists or doc.to_dict().get("user_id") != user["uid"]:
        raise HTTPException(status_code=404, detail="Árbol no encontrado")
    db.collection("arboles").document(arbol_id).delete()
