from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List

from solar import calcular_horas_sol
from earth_engine import analizar_parcela
from optimizer import optimizar_plantacion, recomendar_cultivos

app = FastAPI(title="SombraIA Motor", version="1.0")

class SolicitudAnalisis(BaseModel):
    poligono: List[List[float]]
    cultivo: str
    modo: str = "agro"
    n_arboles: int = 5

@app.get("/health")
def health():
    return {"status": "ok", "servicio": "SombraIA Motor"}

@app.post("/analizar")
def analizar(solicitud: SolicitudAnalisis):
    try:
        lats = [p[0] for p in solicitud.poligono]
        lngs = [p[1] for p in solicitud.poligono]
        lat_c = sum(lats) / len(lats)
        lng_c = sum(lngs) / len(lngs)

        solar = calcular_horas_sol(lat_c, lng_c)
        ee_data = analizar_parcela(solicitud.poligono)

        puntos = optimizar_plantacion(
            poligono=solicitud.poligono,
            cultivo=solicitud.cultivo,
            solar_data=solar,
            n_arboles=solicitud.n_arboles
        )

        cultivos = recomendar_cultivos(
            solicitud.cultivo,
            ee_data["ndvi"],
            ee_data["zona_quemada"]
        )

        ahorro = round(25 + min(solar["horas_criticas_dia"] * 1.5, 15))

        return {
            "puntos": puntos,
            "ahorro_agua_pct": ahorro,
            "reduccion_temp_suelo_c": 2.1,
            "ndvi": ee_data["ndvi"],
            "zona_quemada": ee_data["zona_quemada"],
            "cultivos_compatibles": cultivos,
            "cobertura_recomendada": "pasto nativo entre hileras",
            "datos_para_gemini": {
                "horas_sol_directo": solar["horas_sol_dia"],
                "horas_criticas_dia": solar["horas_criticas_dia"],
                "temp_suelo_actual": ee_data["temp_suelo_c"],
                "temp_suelo_proyectada": round(ee_data["temp_suelo_c"] - 2.1, 1),
                "cultivo_actual": solicitud.cultivo,
                "ndvi": ee_data["ndvi"],
                "zona_quemada": ee_data["zona_quemada"],
                "arboles_sugeridos": len(puntos)
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
