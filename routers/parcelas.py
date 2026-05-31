from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from google.cloud.firestore_v1 import SERVER_TIMESTAMP

from middleware.auth import verify_token
from db.firestore import get_db
from services import gemini

router = APIRouter()


class NuevaParcela(BaseModel):
    nombre: str
    poligono: List[List[float]]
    modo: str = "ambiental"
    cultivo: Optional[str] = None
    resultado: Optional[dict] = None


class ActualizarParcela(BaseModel):
    nombre: Optional[str] = None
    notas: Optional[str] = None


def _verificar_acceso(doc, uid: str):
    if not doc.exists:
        raise HTTPException(status_code=404, detail="Parcela no encontrada")
    if doc.to_dict().get("user_id") != uid:
        raise HTTPException(status_code=403, detail="Sin permiso")


def _poly_save(poligono: List[List[float]]):
    return [{"lng": p[0], "lat": p[1]} for p in poligono]


def _poly_load(data: dict) -> dict:
    raw = data.get("poligono")
    if isinstance(raw, list) and raw and isinstance(raw[0], dict):
        data["poligono"] = [[p["lng"], p["lat"]] for p in raw]
    return data


@router.get("/parcelas")
def listar_parcelas(user=Depends(verify_token)):
    db = get_db()
    docs = db.collection("parcelas").where("user_id", "==", user["uid"]).limit(50).stream()
    return [{"id": d.id, **_poly_load(d.to_dict())} for d in docs]


@router.get("/parcelas/{parcela_id}")
def obtener_parcela(parcela_id: str, user=Depends(verify_token)):
    db = get_db()
    doc = db.collection("parcelas").document(parcela_id).get()
    _verificar_acceso(doc, user["uid"])
    return {"id": doc.id, **_poly_load(doc.to_dict())}


@router.post("/parcelas", status_code=201)
def guardar_parcela(parcela: NuevaParcela, user=Depends(verify_token)):
    db = get_db()
    _, ref = db.collection("parcelas").add({
        "user_id": user["uid"],
        "nombre": parcela.nombre,
        "poligono": _poly_save(parcela.poligono),
        "modo": parcela.modo,
        "cultivo": parcela.cultivo,
        "resultado": parcela.resultado,
        "created_at": SERVER_TIMESTAMP,
    })
    return {"id": ref.id}


@router.put("/parcelas/{parcela_id}")
def actualizar_parcela(parcela_id: str, datos: ActualizarParcela, user=Depends(verify_token)):
    db = get_db()
    doc = db.collection("parcelas").document(parcela_id).get()
    _verificar_acceso(doc, user["uid"])
    update = {k: v for k, v in datos.model_dump().items() if v is not None}
    if update:
        db.collection("parcelas").document(parcela_id).update(update)
    return {"id": parcela_id}


@router.delete("/parcelas/{parcela_id}", status_code=204)
def eliminar_parcela(parcela_id: str, user=Depends(verify_token)):
    db = get_db()
    doc = db.collection("parcelas").document(parcela_id).get()
    _verificar_acceso(doc, user["uid"])
    db.collection("parcelas").document(parcela_id).delete()


@router.get("/parcelas/{parcela_id}/calendario")
def calendario_parcela(
    parcela_id: str,
    municipio: str = Query("Santa Cruz"),
    user=Depends(verify_token),
):
    db = get_db()
    doc = db.collection("parcelas").document(parcela_id).get()
    _verificar_acceso(doc, user["uid"])

    puntos = (doc.to_dict().get("resultado") or {}).get("puntos", [])
    especies = list({p["especie"] for p in puntos if "especie" in p})

    if not especies:
        raise HTTPException(status_code=400, detail="Esta parcela no tiene árboles guardados")

    return {
        "calendario": gemini.calendario(especies, municipio),
        "especies": especies,
        "municipio": municipio,
    }
