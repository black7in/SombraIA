import math
from datetime import date, timedelta
from typing import Optional

import ee
from fastapi import APIRouter, Depends, HTTPException, Query
from firebase_admin import firestore
from pydantic import BaseModel

from db.firestore import get_db
from middleware.auth import verify_token
from services import gemini

router = APIRouter()

_SANTA_CRUZ_BBOX = [-63.5, -18.5, -60.0, -15.5]


@router.get("/alertas")
def listar_alertas(
    lat: Optional[float] = Query(None),
    lng: Optional[float] = Query(None),
    radio_km: float = Query(50),
    user=Depends(verify_token),
):
    db = get_db()
    docs = db.collection("alertas").where("activa", "==", True).limit(20).stream()
    alertas = [{"id": d.id, **d.to_dict()} for d in docs]

    if lat is not None and lng is not None:
        alertas = [
            a for a in alertas
            if _haversine(lat, lng, a["lat"], a["lng"]) <= radio_km
        ]
    return alertas


@router.post("/alertas/detectar")
def detectar_incendios(user=Depends(verify_token)):
    """Llamado por Cloud Scheduler una vez al día (0 11 * * *)."""
    hoy = date.today().isoformat()
    ayer = (date.today() - timedelta(days=1)).isoformat()

    region = ee.Geometry.Rectangle(_SANTA_CRUZ_BBOX)
    fuego = (
        ee.ImageCollection("MODIS/061/MOD14A1")
        .filterBounds(region)
        .filterDate(ayer, hoy)
        .select("FireMask")
        .max()
    )
    geojson = fuego.gt(6).reduceToVectors(
        geometry=region, scale=1000, maxPixels=1e6
    ).getInfo()

    if not geojson or not geojson.get("features"):
        return {"guardadas": 0, "mensaje": "Sin incendios activos"}

    db = get_db()
    batch = db.batch()
    guardadas = 0

    for feature in geojson["features"][:20]:
        coords = feature["geometry"]["coordinates"][0][0]
        lat_f, lng_f = coords[1], coords[0]
        descripcion = gemini.alerta_incendio(lat_f, lng_f)
        ref = db.collection("alertas").document()
        batch.set(ref, {
            "tipo": "incendio",
            "lat": lat_f,
            "lng": lng_f,
            "radio_km": 5,
            "descripcion": descripcion,
            "activa": True,
            "created_at": firestore.SERVER_TIMESTAMP,
        })
        guardadas += 1

    batch.commit()
    return {"guardadas": guardadas}


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


def _haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371
    d_lat = math.radians(lat2 - lat1)
    d_lon = math.radians(lon2 - lon1)
    a = (
        math.sin(d_lat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(d_lon / 2) ** 2
    )
    return R * 2 * math.asin(math.sqrt(a))
