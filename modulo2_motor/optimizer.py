import json
from shapely.geometry import Polygon, Point
from typing import List

with open('especies.json') as f:
    ESPECIES = json.load(f)

def optimizar_plantacion(
    poligono: list,
    cultivo: str,
    solar_data: dict,
    n_arboles: int = 5
) -> list:
    shape = Polygon([(p[1], p[0]) for p in poligono])
    bounds = shape.bounds
    posicion_optima = solar_data.get("posicion_sombra_optima", "norte")

    especies_validas = [e for e in ESPECIES if cultivo in e.get("compatible_con", [])]
    if not especies_validas:
        especies_validas = ESPECIES[:3]

    puntos = []
    for i in range(n_arboles):
        especie = especies_validas[i % len(especies_validas)]

        offsets = {
            "norte": (0, 0.0003),
            "sur":   (0, -0.0003),
            "este":  (0.0003, 0),
            "oeste": (-0.0003, 0)
        }
        dx, dy = offsets.get(posicion_optima, (0, 0.0002))

        t = (i + 1) / (n_arboles + 1)
        px = bounds[0] + t * (bounds[2] - bounds[0]) + dx
        py = (bounds[1] + bounds[3]) / 2 + dy

        punto = Point(px, py)
        if not shape.contains(punto):
            punto = shape.centroid

        puntos.append({
            "lat": round(punto.y, 6),
            "lng": round(punto.x, 6),
            "especie": especie["nombre"],
            "posicion": _indice_a_posicion(i, posicion_optima),
            "distancia_borde_m": round(shape.exterior.distance(punto) * 111000, 1)
        })

    return puntos

def _indice_a_posicion(i: int, base: str) -> str:
    posiciones = [base, "borde", "cortavientos", "borde_este", "borde_oeste"]
    return posiciones[i % len(posiciones)]

def recomendar_cultivos(cultivo_actual: str, ndvi: float, zona_quemada: bool) -> list:
    compatibles_base = {
        "soya":  ["poroto", "maní", "yuca"],
        "maiz":  ["poroto", "zapallo", "yuca"],
        "yuca":  ["poroto", "maní", "soya"],
        "default": ["poroto", "yuca", "maní"]
    }
    base = compatibles_base.get(cultivo_actual.lower(), compatibles_base["default"])
    if zona_quemada:
        return ["pasto nativo (cobertura)", "leguminosas pioneras"] + base[:1]
    if ndvi < 0.2:
        return ["cobertura vegetal primero"] + base[:2]
    return base
