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

_VELOCIDAD_M_ANIO = {"rapida": 1.5, "media": 0.9, "lenta": 0.4}


def analizar(poligono: list, modo: str, n_arboles: int, cultivo: str = None) -> dict:
    lats = [p[0] for p in poligono]
    lngs = [p[1] for p in poligono]
    lat_c = sum(lats) / len(lats)
    lng_c = sum(lngs) / len(lngs)

    solar = _calcular_horas_sol(lat_c, lng_c)
    ee_data = _analizar_parcela(poligono)

    if modo == "agro":
        return _resultado_agro(poligono, cultivo, solar, ee_data, n_arboles)
    return _resultado_ambiental(poligono, solar, ee_data, n_arboles)


def _resultado_agro(poligono, cultivo, solar, ee_data, n_arboles):
    shape = Polygon([(p[1], p[0]) for p in poligono])
    posicion_optima = solar.get("posicion_sombra_optima", "norte")

    especies_validas = [e for e in _ESPECIES if cultivo in e.get("compatible_con", [])]
    if not especies_validas:
        especies_validas = _ESPECIES[:3]

    puntos = _puntos_en_borde(shape, posicion_optima, n_arboles, especies_validas)
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
            "posicion_cortina": posicion_optima,
        },
    }


def _resultado_ambiental(poligono, solar, ee_data, n_arboles):
    shape = Polygon([(p[1], p[0]) for p in poligono])
    posicion_optima = solar.get("posicion_sombra_optima", "norte")

    especies_validas = sorted(_ESPECIES, key=lambda e: e.get("radio_sombra_m", 0), reverse=True)
    puntos = _puntos_interior(shape, posicion_optima, n_arboles, especies_validas)

    impacto = _calcular_impacto_ambiental(shape, puntos)
    proyeccion = _proyectar_crecimiento(shape, puntos)

    return {
        "modo": "ambiental",
        "puntos": puntos,
        "cobertura_sombra_pct": impacto["cobertura_sombra_pct"],
        "co2_estimado_kg_anual": impacto["co2_estimado_kg_anual"],
        "reduccion_temp_suelo_c": 2.1,
        "ndvi": ee_data["ndvi"],
        "zona_quemada": ee_data["zona_quemada"],
        "proyeccion_crecimiento": proyeccion,
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


def _puntos_en_borde(shape: Polygon, posicion: str, n_arboles: int, especies: list) -> list:
    """Agro: árboles en el borde óptimo como cortina rompevientos, no adentro del cultivo."""
    minx, miny, maxx, maxy = shape.bounds
    OFFSET = 0.00002  # ~2m adentro del borde

    puntos = []
    for i in range(n_arboles):
        especie = especies[i % len(especies)]
        t = (i + 1) / (n_arboles + 1)

        if posicion == "norte":
            px, py = minx + t * (maxx - minx), maxy - OFFSET
        elif posicion == "sur":
            px, py = minx + t * (maxx - minx), miny + OFFSET
        elif posicion == "este":
            px, py = maxx - OFFSET, miny + t * (maxy - miny)
        else:
            px, py = minx + OFFSET, miny + t * (maxy - miny)

        punto = Point(px, py)
        if not shape.contains(punto):
            punto = shape.centroid

        puntos.append({
            "lat": round(punto.y, 6),
            "lng": round(punto.x, 6),
            "especie": especie["nombre"],
            "posicion": f"cortina_{posicion}",
            "distancia_borde_m": round(shape.exterior.distance(punto) * 111000, 1),
        })

    return puntos


def _puntos_interior(shape: Polygon, posicion_optima: str, n_arboles: int, especies: list) -> list:
    """Ambiental: distribuye árboles dentro del polígono maximizando cobertura."""
    bounds = shape.bounds
    offsets = {
        "norte": (0, 0.0003),
        "sur": (0, -0.0003),
        "este": (0.0003, 0),
        "oeste": (-0.0003, 0),
    }
    posiciones = [posicion_optima, "borde", "cortavientos", "borde_este", "borde_oeste"]
    puntos = []

    for i in range(n_arboles):
        especie = especies[i % len(especies)]
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


def _proyectar_crecimiento(shape: Polygon, puntos: list) -> dict:
    """Proyección matemática de altura y cobertura por año según velocidad de cada especie."""
    area_m2 = max(shape.area * (111_000 ** 2), 1)
    especies_por_nombre = {e["nombre"]: e for e in _ESPECIES}
    proyeccion = {}

    for anio, factor in [(1, 0.5), (3, 1.0), (5, 1.0), (10, 1.0)]:
        sombra_m2 = 0
        altura_total = 0
        for p in puntos:
            esp = especies_por_nombre.get(p["especie"], {})
            vel = _VELOCIDAD_M_ANIO.get(esp.get("velocidad_crecimiento", "media"), 0.9)
            h_max = esp.get("altura_max_m", 10)
            r_max = esp.get("radio_sombra_m", 5)
            h = min(vel * anio * factor, h_max)
            r = r_max * (h / h_max)
            sombra_m2 += math.pi * r ** 2
            altura_total += h

        n = max(len(puntos), 1)
        proyeccion[f"año_{anio}"] = {
            "altura_media_m": round(altura_total / n, 1),
            "cobertura_pct": min(100, round(sombra_m2 / area_m2 * 100, 1)),
        }

    return proyeccion


def _calcular_impacto_ambiental(shape: Polygon, puntos: list) -> dict:
    area_m2 = max(shape.area * (111_000 ** 2), 1)
    especies_por_nombre = {e["nombre"]: e for e in _ESPECIES}
    sombra_m2 = 0
    co2 = 0
    for p in puntos:
        esp = especies_por_nombre.get(p["especie"], {})
        sombra_m2 += math.pi * esp.get("radio_sombra_m", 6) ** 2
        co2 += round(20 + esp.get("altura_max_m", 10) * 1.8)
    return {
        "cobertura_sombra_pct": min(100, round(sombra_m2 / area_m2 * 100, 1)),
        "co2_estimado_kg_anual": round(co2),
    }


def _calcular_horas_sol(lat: float, lng: float) -> dict:
    ubicacion = pvlib.location.Location(latitude=lat, longitude=lng, tz="America/La_Paz", altitude=400)
    tiempos = pd.date_range(start="2024-01-01", end="2024-12-31", freq="1h", tz="America/La_Paz")
    pos = ubicacion.get_solarposition(tiempos)
    sol = pos[pos["elevation"] > 10]
    criticas = sol[(sol.index.hour >= 10) & (sol.index.hour <= 15)]
    azimuth = sol["azimuth"].median()
    return {
        "horas_sol_dia": round(len(sol) / 365, 1),
        "horas_criticas_dia": round(len(criticas) / 365, 1),
        "azimuth_medio": round(float(azimuth), 1),
        "posicion_sombra_optima": _azimuth_a_posicion(azimuth),
    }


def _azimuth_a_posicion(azimuth: float) -> str:
    if 45 <= azimuth < 135:
        return "norte"
    elif 135 <= azimuth < 225:
        return "este"
    elif 225 <= azimuth < 315:
        return "sur"
    return "oeste"


def _analizar_parcela(poligono: list) -> dict:
    coords = [[p[1], p[0]] for p in poligono]
    region = ee.Geometry.Polygon(coords)

    ndvi_valor = (
        ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
        .filterBounds(region).filterDate("2024-09-01", "2024-12-01")
        .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 20)).median()
        .normalizedDifference(["B8", "B4"])
        .reduceRegion(reducer=ee.Reducer.mean(), geometry=region, scale=10)
        .getInfo().get("nd", 0)
    )
    max_fire = (
        ee.ImageCollection("MODIS/061/MOD14A1")
        .filterBounds(region).filterDate("2024-01-01", "2024-12-31")
        .select("FireMask").max()
        .reduceRegion(reducer=ee.Reducer.max(), geometry=region, scale=500)
        .getInfo().get("FireMask", 0)
    )
    temp_k = (
        ee.ImageCollection("MODIS/061/MOD11A1")
        .filterBounds(region).filterDate("2024-10-01", "2024-12-31")
        .select("LST_Day_1km").mean()
        .reduceRegion(reducer=ee.Reducer.mean(), geometry=region, scale=1000)
        .getInfo().get("LST_Day_1km", 0)
    )
    return {
        "ndvi": round(float(ndvi_valor or 0), 3),
        "zona_quemada": bool(max_fire >= 7),
        "temp_suelo_c": round((temp_k * 0.02) - 273.15, 1) if temp_k else 38.0,
    }


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
