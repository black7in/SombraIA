from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, model_validator
from typing import List, Literal, Optional

from middleware.auth import verify_token
from services import motor, gemini

router = APIRouter()


class SolicitudAnalisis(BaseModel):
    poligono: List[List[float]]
    modo: Literal["agro", "ambiental"] = "ambiental"
    cultivo: Optional[str] = None

    @model_validator(mode="after")
    def cultivo_requerido_en_agro(self):
        if self.modo == "agro" and not self.cultivo:
            raise ValueError("El campo 'cultivo' es requerido en modo agro")
        return self


@router.post("/analizar")
def analizar(solicitud: SolicitudAnalisis, user=Depends(verify_token)):
    try:
        resultado = motor.analizar(
            solicitud.poligono,
            solicitud.modo,
            solicitud.cultivo,
        )

        datos = resultado["datos_para_gemini"]
        zona_quemada = resultado["zona_quemada"]
        puntos = resultado["puntos"]

        if solicitud.modo == "agro":
            texto = (
                gemini.recomendar_agro_zona_quemada(datos, puntos)
                if zona_quemada
                else gemini.recomendar_agro(datos, puntos, resultado["cultivos_compatibles"])
            )
        else:
            texto = (
                gemini.recomendar_ambiental_zona_quemada(datos, puntos)
                if zona_quemada
                else gemini.recomendar_ambiental(datos, puntos)
            )

        resultado["recomendacion_texto"] = texto
        resultado["cuidados"] = gemini.cuidados(puntos, solicitud.modo, zona_quemada)
        del resultado["datos_para_gemini"]
        return resultado

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
