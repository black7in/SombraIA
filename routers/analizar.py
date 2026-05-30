from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List

from middleware.auth import verify_token
from services import motor, gemini

router = APIRouter()


class SolicitudAnalisis(BaseModel):
    poligono: List[List[float]]
    cultivo: str
    modo: str = "agro"
    n_arboles: int = 5


@router.post("/analizar")
def analizar(solicitud: SolicitudAnalisis, user=Depends(verify_token)):
    try:
        resultado = motor.analizar(
            solicitud.poligono,
            solicitud.cultivo,
            solicitud.modo,
            solicitud.n_arboles,
        )

        datos = resultado["datos_para_gemini"]
        datos["ahorro_agua_pct"] = resultado["ahorro_agua_pct"]

        if resultado["zona_quemada"]:
            texto = gemini.recomendar_zona_quemada(datos, resultado["puntos"])
        else:
            texto = gemini.recomendar(datos, resultado["puntos"], resultado["cultivos_compatibles"])

        resultado["recomendacion_texto"] = texto
        del resultado["datos_para_gemini"]
        return resultado

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
