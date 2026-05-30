import json
import math
import pvlib
import pandas as pd
import ee
from pathlib import Path
from shapely.geometry import Polygon, Point

_ESPECIES = json.loads(
    (Path(__file__).parent.parent / "data" / "especies.json").read_text(encoding="utf-8")
)


def analizar(poligono: list, modo: str, n_arboles: int, cultivo: str = None) -> dict:
    lats = [p[0] for p in poligono]
    lngs = [p[1] for p in poligono]
    lat_c = sum(lats) / len(lats)
    lng_c = sum(lngs) / len(lngs)

    solar = _calcular_horas_sol(lat_c, lng_c)
    ee_data = _analizar_parcela(poligono)

    if modo == "agro":
        return _resultado_agro(poligono, cultivo, solar, ee_data, n_arboles)
    else:
        return _resultado_ambiental(poligono, solar, ee_data, n_arboles)


def _resultado_agro(poligono, cultivo, solar, ee_data, n_arboles):
    puntos = _optimizar_plantacion(poligono, solar, n_arboles, cultivo=cultivo)
    cultivos = _recomendar_cultivos(cultivo, ee_data["ndvi"], ee_data["zona_quemada"])
    ahorro = round(25 + min(solar["horas_criticas_dia"] * 1.5, 15))

    return {
        "modo": "agro",
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
            "cultivo_actual": cultivo,
            "ndvi": ee_data["ndvi"],
            "zona_quemada": ee_data["zona_quemada"],
            "arboles_sugeridos": len(puntos),
            "ahorro_agua_pct": ahorro,
        },
    }


def _resultado_ambiental(poligono, solar, ee_data, n_arboles):
    puntos = _optimizar_plantacion(poligono, solar, n_arboles, cultivo=None)
    impacto = _calcular_impacto_ambiental(poligono, puntos)

    return {
        "modo": "ambiental",
        "puntos": puntos,
        "cobertura_sombra_pct": impacto["cobertura_sombra_pct"],
        "co2_estimado_kg_anual": impacto["co2_estimado_kg_anual"],
        "reduccion_temp_suelo_c": 2.1,
        "ndvi": ee_data["ndvi"],
        "zona_quemada": ee_data["zona_quemada"],
        "datos_para_gemini": {
            "horas_sol_directo": solar["horas_sol_dia"],
            "horas_criticas_dia": solar["horas_criticas_dia"],
            "temp_suelo_actual": ee_data["temp_suelo_c"],
            "temp_suelo_proyectada": round(ee_data["temp_suelo_c"] - 2.1, 1),
            "ndvi": ee_data["ndvi"],
            "zona_quemada": ee_data["zona_quemada"],
            "arboles_sugeridos": len(puntos),
            "cobertura_sombra_pct": impacto["cobertura_sombra_pct"],
            "co2_estimado_kg_anual": impacto["co2_estimado_kg_anual"],
        },
    }


def _calcular_impacto_ambiental(poligono: list, puntos: list) -> dict:
    shape = Polygon([(p[1], p[0]) for p in poligono])
    area_m2 = shape.area * (111_000 ** 2)

    especies_por_nombre = {e["nombre"]: e for e in _ESPECIES}
    sombra_total_m2 = 0
    co2_total = 0

    for p in puntos:
        especie = especies_por_nombre.get(p["especie"], {})
        radio = especie.get("radio_sombra_m", 6)
        altura = especie.get("altura_max_m", 10)
        sombra_total_m2 += math.pi * radio ** 2
        co2_total += round(20 + altura * 1.8)

    cobertura_pct = min(100, round(sombra_total_m2 / area_m2 * 100, 1)) if area_m2 > 0 else 0

    return {
        "cobertura_sombra_pct": cobertura_pct,
        "co2_estimado_kg_anual": round(co2_total),
    }


def _calcular_horas_sol(lat: float, lng: float) -> dict:
    ubicacion = pvlib.location.Location(
        latitude=lat,
        longitude=lng,
        tz="America/La_Paz",
        altitude=400,
    )
    tiempos = pd.date_range(
        start="2024-01-01",
        end="2024-12-31",
        freq="1h",
        tz="America/La_Paz",
    )
    posicion_solar = ubicacion.get_solarposition(tiempos)
    sol_directo = posicion_solar[posicion_solar["elevation"] > 10]
    horas_por_dia = len(sol_directo) / 365

    horas_criticas = sol_directo[
        (sol_directo.index.hour >= 10) & (sol_directo.index.hour <= 15)
    ]
    horas_criticas_dia = len(horas_criticas) / 365
    azimuth_medio = sol_directo["azimuth"].median()

    return {
        "horas_sol_dia": round(horas_por_dia, 1),
        "horas_criticas_dia": round(horas_criticas_dia, 1),
        "azimuth_medio": round(float(azimuth_medio), 1),
        "posicion_sombra_optima": _azimuth_a_posicion(azimuth_medio),
    }


def _azimuth_a_posicion(azimuth: float) -> str:
    if 45 <= azimuth < 135:
        return "norte"
    elif 135 <= azimuth < 225:
        return "este"
    elif 225 <= azimuth < 315:
        return "sur"
    else:
        return "oeste"


def _analizar_parcela(poligono: list) -> dict:
    coords = [[p[1], p[0]] for p in poligono]
    region = ee.Geometry.Polygon(coords)

    sentinel = (
        ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
        .filterBounds(region)
        .filterDate("2024-09-01", "2024-12-01")
        .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 20))
        .median()
    )
    ndvi = sentinel.normalizedDifference(["B8", "B4"])
    ndvi_valor = (
        ndvi.reduceRegion(reducer=ee.Reducer.mean(), geometry=region, scale=10)
        .getInfo()
        .get("nd", 0)
    )

    fuego = (
        ee.ImageCollection("MODIS/061/MOD14A1")
        .filterBounds(region)
        .filterDate("2024-01-01", "2024-12-31")
        .select("FireMask")
    )
    max_fire = (
        fuego.max()
        .reduceRegion(reducer=ee.Reducer.max(), geometry=region, scale=500)
        .getInfo()
        .get("FireMask", 0)
    )

    lst = (
        ee.ImageCollection("MODIS/061/MOD11A1")
        .filterBounds(region)
        .filterDate("2024-10-01", "2024-12-31")
        .select("LST_Day_1km")
        .mean()
    )
    temp_k = (
        lst.reduceRegion(reducer=ee.Reducer.mean(), geometry=region, scale=1000)
        .getInfo()
        .get("LST_Day_1km", 0)
    )
    temp_c = round((temp_k * 0.02) - 273.15, 1) if temp_k else 38.0

    return {
        "ndvi": round(float(ndvi_valor or 0), 3),
        "zona_quemada": bool(max_fire >= 7),
        "temp_suelo_c": temp_c,
    }


def _optimizar_plantacion(poligono: list, solar: dict, n_arboles: int, cultivo: str = None) -> list:
    shape = Polygon([(p[1], p[0]) for p in poligono])
    bounds = shape.bounds
    posicion_optima = solar.get("posicion_sombra_optima", "norte")

    if cultivo:
        especies_validas = [e for e in _ESPECIES if cultivo in e.get("compatible_con", [])]
        if not especies_validas:
            especies_validas = _ESPECIES[:3]
    else:
        # Modo ambiental: priorizar mayor radio de sombra y diversidad nativa
        especies_validas = sorted(_ESPECIES, key=lambda e: e.get("radio_sombra_m", 0), reverse=True)

    offsets = {
        "norte": (0, 0.0003),
        "sur": (0, -0.0003),
        "este": (0.0003, 0),
        "oeste": (-0.0003, 0),
    }
    posiciones = [posicion_optima, "borde", "cortavientos", "borde_este", "borde_oeste"]
    puntos = []

    for i in range(n_arboles):
        especie = especies_validas[i % len(especies_validas)]
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
            "posicion": posiciones[i % len(posiciones)],
            "distancia_borde_m": round(shape.exterior.distance(punto) * 111000, 1),
        })

    return puntos


def _recomendar_cultivos(cultivo_actual: str, ndvi: float, zona_quemada: bool) -> list:
    compatibles = {
        "soya": ["poroto", "maní", "yuca"],
        "maiz": ["poroto", "zapallo", "yuca"],
        "yuca": ["poroto", "maní", "soya"],
    }
    base = compatibles.get(cultivo_actual.lower(), ["poroto", "yuca", "maní"])
    if zona_quemada:
        return ["pasto nativo (cobertura)", "leguminosas pioneras"] + base[:1]
    if ndvi < 0.2:
        return ["cobertura vegetal primero"] + base[:2]
    return base
