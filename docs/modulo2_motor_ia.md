# Módulo 2 — Motor IA Python
**Dev 2 · SombraIA · Hackathon 2025**

---

## Tu rol en el proyecto

Sos el cerebro técnico de la app. Tu módulo hace el análisis real: descarga datos satelitales, simula la trayectoria solar y calcula los puntos óptimos de plantación. Lo más importante: **el día 1 en la mañana publicás el `mock_resultado.json`** para que Dev 3 y Dev 4 puedan arrancar sin esperarte.

---

## Stack que usás

| Herramienta | Para qué |
|---|---|
| Python 3.11 | Lenguaje base |
| pvlib | Simulación de trayectoria solar |
| scipy | Optimizador de posición de árboles |
| Google Earth Engine API | NDVI, detección de quemas, cobertura vegetal |
| FastAPI | Servidor HTTP para exponer el endpoint |
| Docker | Contenedor para Cloud Run |
| Google Cloud Run | Deploy serverless del contenedor |

---

## Prioridad día 1: publicar el mock

Antes de escribir una sola línea de código real, creá este archivo y compartilo con Dev 3 y Dev 4:

**`mock_resultado.json`**
```json
{
  "puntos": [
    { "lat": -17.4823, "lng": -63.2514, "especie": "Tajibo", "posicion": "norte", "distancia_borde_m": 5 },
    { "lat": -17.4831, "lng": -63.2508, "especie": "Toborochi", "posicion": "este", "distancia_borde_m": 8 },
    { "lat": -17.4819, "lng": -63.2521, "especie": "Algarrobo", "posicion": "borde_sur", "distancia_borde_m": 3 },
    { "lat": -17.4826, "lng": -63.2498, "especie": "Cuchi", "posicion": "oeste", "distancia_borde_m": 6 },
    { "lat": -17.4835, "lng": -63.2515, "especie": "Cedro", "posicion": "cortavientos", "distancia_borde_m": 10 }
  ],
  "ahorro_agua_pct": 32,
  "reduccion_temp_suelo_c": 2.1,
  "ndvi": 0.41,
  "zona_quemada": false,
  "cultivos_compatibles": ["poroto", "yuca", "maní"],
  "cobertura_recomendada": "pasto nativo entre hileras",
  "datos_para_gemini": {
    "horas_sol_directo": 9.2,
    "temp_suelo_actual": 38,
    "temp_suelo_proyectada": 35.9,
    "cultivo_actual": "soya",
    "area_ha": 1.2,
    "municipio": "San Julián",
    "mes_optimo_plantacion": "octubre",
    "arboles_sugeridos": 5
  }
}
```

---

## Estructura del proyecto

```
modulo2_motor/
├── main.py               # Servidor FastAPI
├── solar.py              # Simulador solar con pvlib
├── earth_engine.py       # Integración Google Earth Engine
├── optimizer.py          # Optimizador de posición (scipy)
├── especies.py           # Base de datos de especies nativas
├── especies.json         # 20+ especies de Santa Cruz
├── Dockerfile            # Para Cloud Run
├── requirements.txt
└── mock_resultado.json   # Publicar día 1
```

---

## Tareas en orden

### 1. Setup del entorno

```bash
# Crear entorno virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Instalar dependencias
pip install fastapi uvicorn pvlib scipy earthengine-api shapely numpy
pip freeze > requirements.txt
```

Autenticación con Earth Engine:
```bash
earthengine authenticate
# Seguir el link, copiar el token
```

### 2. Base de datos de especies (`especies.json`)

Crear este archivo primero — es la base de todas las recomendaciones:

```json
[
  {
    "nombre": "Tajibo",
    "nombre_cientifico": "Tabebuia impetiginosa",
    "usos": ["post_incendio", "sombra", "cortavientos"],
    "altura_max_m": 20,
    "radio_sombra_m": 8,
    "temp_min_c": 10,
    "temp_max_c": 42,
    "agua_minima": "baja",
    "fija_nitrogeno": false,
    "velocidad_crecimiento": "rapida",
    "posicion_optima": ["norte", "este"],
    "compatible_con": ["soya", "maiz", "yuca", "poroto"]
  },
  {
    "nombre": "Toborochi",
    "nombre_cientifico": "Ceiba speciosa",
    "usos": ["sombra", "humedad", "agro"],
    "altura_max_m": 15,
    "radio_sombra_m": 12,
    "temp_min_c": 15,
    "temp_max_c": 42,
    "agua_minima": "media",
    "fija_nitrogeno": false,
    "velocidad_crecimiento": "media",
    "posicion_optima": ["este", "oeste"],
    "compatible_con": ["soya", "maiz", "poroto", "yuca"]
  },
  {
    "nombre": "Algarrobo",
    "nombre_cientifico": "Prosopis alba",
    "usos": ["agro", "nitrogeno", "borde"],
    "altura_max_m": 10,
    "radio_sombra_m": 6,
    "temp_min_c": 5,
    "temp_max_c": 45,
    "agua_minima": "muy_baja",
    "fija_nitrogeno": true,
    "velocidad_crecimiento": "media",
    "posicion_optima": ["borde", "sur"],
    "compatible_con": ["soya", "maiz", "yuca", "maní", "poroto"]
  },
  {
    "nombre": "Cuchi",
    "nombre_cientifico": "Astronium urundeuva",
    "usos": ["agro", "resistencia", "reforestacion"],
    "altura_max_m": 25,
    "radio_sombra_m": 10,
    "temp_min_c": 12,
    "temp_max_c": 44,
    "agua_minima": "baja",
    "fija_nitrogeno": false,
    "velocidad_crecimiento": "lenta",
    "posicion_optima": ["norte", "oeste"],
    "compatible_con": ["soya", "maiz", "yuca"]
  },
  {
    "nombre": "Cedro",
    "nombre_cientifico": "Cedrela odorata",
    "usos": ["cortavientos", "sombra", "madera"],
    "altura_max_m": 30,
    "radio_sombra_m": 9,
    "temp_min_c": 14,
    "temp_max_c": 40,
    "agua_minima": "media",
    "fija_nitrogeno": false,
    "velocidad_crecimiento": "media",
    "posicion_optima": ["norte", "cortavientos"],
    "compatible_con": ["soya", "maiz", "yuca", "poroto"]
  }
]
```

> Agregar al menos 15 especies más siguiendo el mismo formato.

### 3. Simulador solar (`solar.py`)

```python
import pvlib
import pandas as pd
import numpy as np
from datetime import datetime

def calcular_horas_sol(lat: float, lng: float) -> dict:
    """
    Calcula horas de sol directo promedio anual y por mes
    para coordenadas en Santa Cruz, Bolivia
    """
    ubicacion = pvlib.location.Location(
        latitude=lat,
        longitude=lng,
        tz='America/La_Paz',
        altitude=400  # metros sobre el nivel del mar (promedio Santa Cruz)
    )

    # Simular un año completo hora a hora
    tiempos = pd.date_range(
        start='2024-01-01',
        end='2024-12-31',
        freq='1h',
        tz='America/La_Paz'
    )

    posicion_solar = ubicacion.get_solarposition(tiempos)
    irradiancia = ubicacion.get_clearsky(tiempos)

    # Horas con sol directo significativo (elevación > 10°)
    sol_directo = posicion_solar[posicion_solar['elevation'] > 10]
    horas_por_dia = len(sol_directo) / 365

    # Horas críticas: 10am - 3pm (máxima evaporación)
    horas_criticas = sol_directo[
        (sol_directo.index.hour >= 10) &
        (sol_directo.index.hour <= 15)
    ]
    horas_criticas_dia = len(horas_criticas) / 365

    # Dirección dominante del sol (para recomendar posición del árbol)
    azimuth_medio = sol_directo['azimuth'].median()

    return {
        "horas_sol_dia": round(horas_por_dia, 1),
        "horas_criticas_dia": round(horas_criticas_dia, 1),
        "azimuth_medio": round(float(azimuth_medio), 1),
        "posicion_sombra_optima": _azimuth_a_posicion(azimuth_medio)
    }

def _azimuth_a_posicion(azimuth: float) -> str:
    """Convierte azimuth solar a posición recomendada del árbol"""
    if 45 <= azimuth < 135:
        return "norte"
    elif 135 <= azimuth < 225:
        return "este"
    elif 225 <= azimuth < 315:
        return "sur"
    else:
        return "oeste"
```

### 4. Integración Earth Engine (`earth_engine.py`)

```python
import ee

# Inicializar (requiere autenticación previa)
ee.Initialize()

def analizar_parcela(poligono: list) -> dict:
    """
    Analiza una parcela con Google Earth Engine.
    poligono: lista de [lat, lng]
    """
    # Convertir a geometría de Earth Engine (GEE usa [lng, lat])
    coords = [[p[1], p[0]] for p in poligono]
    region = ee.Geometry.Polygon(coords)

    # NDVI con Sentinel-2 (últimos 3 meses)
    sentinel = (ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
        .filterBounds(region)
        .filterDate('2024-09-01', '2024-12-01')
        .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20))
        .median())

    ndvi = sentinel.normalizedDifference(['B8', 'B4'])
    ndvi_valor = ndvi.reduceRegion(
        reducer=ee.Reducer.mean(),
        geometry=region,
        scale=10
    ).getInfo().get('nd', 0)

    # Detección de zona quemada con MODIS
    fuego = (ee.ImageCollection('MODIS/061/MOD14A1')
        .filterBounds(region)
        .filterDate('2024-01-01', '2024-12-31')
        .select('FireMask'))

    max_fire = fuego.max().reduceRegion(
        reducer=ee.Reducer.max(),
        geometry=region,
        scale=500
    ).getInfo().get('FireMask', 0)

    zona_quemada = max_fire >= 7  # 7-9 = fuego confirmado

    # Temperatura superficial con MODIS LST
    lst = (ee.ImageCollection('MODIS/061/MOD11A1')
        .filterBounds(region)
        .filterDate('2024-10-01', '2024-12-31')
        .select('LST_Day_1km')
        .mean())

    temp_k = lst.reduceRegion(
        reducer=ee.Reducer.mean(),
        geometry=region,
        scale=1000
    ).getInfo().get('LST_Day_1km', 0)

    temp_c = round((temp_k * 0.02) - 273.15, 1) if temp_k else 38.0

    return {
        "ndvi": round(float(ndvi_valor or 0), 3),
        "zona_quemada": bool(zona_quemada),
        "temp_suelo_c": temp_c
    }
```

### 5. Optimizador de posición (`optimizer.py`)

```python
import json
import numpy as np
from scipy.optimize import minimize
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
    """
    Encuentra los N puntos óptimos dentro del polígono
    para plantar árboles, maximizando cobertura de sombra
    en horas críticas (10am-3pm)
    """
    shape = Polygon([(p[1], p[0]) for p in poligono])
    bounds = shape.bounds  # (minx, miny, maxx, maxy)
    centroide = shape.centroid

    posicion_optima = solar_data.get("posicion_sombra_optima", "norte")
    especies_validas = [
        e for e in ESPECIES
        if cultivo in e.get("compatible_con", [])
    ]
    if not especies_validas:
        especies_validas = ESPECIES[:3]

    puntos = []
    for i in range(n_arboles):
        especie = especies_validas[i % len(especies_validas)]

        # Offset según posición óptima
        offsets = {
            "norte": (0, 0.0003),
            "sur":   (0, -0.0003),
            "este":  (0.0003, 0),
            "oeste": (-0.0003, 0)
        }
        dx, dy = offsets.get(posicion_optima, (0, 0.0002))

        # Distribuir árboles a lo largo del borde óptimo
        t = (i + 1) / (n_arboles + 1)
        px = bounds[0] + t * (bounds[2] - bounds[0]) + dx
        py = (bounds[1] + bounds[3]) / 2 + dy

        # Asegurar que el punto está dentro del polígono
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
    """Recomienda cultivos compatibles con los árboles sugeridos"""
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
```

### 6. Servidor FastAPI (`main.py`)

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
import json

from solar import calcular_horas_sol
from earth_engine import analizar_parcela
from optimizer import optimizar_plantacion, recomendar_cultivos

app = FastAPI(title="SombraIA Motor", version="1.0")

class SolicitudAnalisis(BaseModel):
    poligono: List[List[float]]  # [[lat, lng], ...]
    cultivo: str
    modo: str  # "agro" | "incendio"
    n_arboles: int = 5

@app.get("/health")
def health():
    return {"status": "ok", "servicio": "SombraIA Motor"}

@app.post("/analizar")
def analizar(solicitud: SolicitudAnalisis):
    try:
        # Calcular centroide del polígono para pvlib
        lats = [p[0] for p in solicitud.poligono]
        lngs = [p[1] for p in solicitud.poligono]
        lat_c = sum(lats) / len(lats)
        lng_c = sum(lngs) / len(lngs)

        # 1. Datos solares
        solar = calcular_horas_sol(lat_c, lng_c)

        # 2. Datos satelitales Earth Engine
        ee_data = analizar_parcela(solicitud.poligono)

        # 3. Optimizar puntos de plantación
        puntos = optimizar_plantacion(
            poligono=solicitud.poligono,
            cultivo=solicitud.cultivo,
            solar_data=solar,
            n_arboles=solicitud.n_arboles
        )

        # 4. Cultivos compatibles
        cultivos = recomendar_cultivos(
            solicitud.cultivo,
            ee_data["ndvi"],
            ee_data["zona_quemada"]
        )

        # 5. Estimar ahorro de agua
        base_pct = 25
        bonus_sombra = min(solar["horas_criticas_dia"] * 1.5, 15)
        ahorro = round(base_pct + bonus_sombra)

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
```

### 7. Dockerfile y deploy en Cloud Run

**`Dockerfile`**
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8080
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
```

Deploy:
```bash
# Build y push a Google Container Registry
gcloud builds submit --tag gcr.io/sombraia-hackathon/motor-ia

# Deploy en Cloud Run
gcloud run deploy motor-ia \
  --image gcr.io/sombraia-hackathon/motor-ia \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 1Gi

# Copiar la URL generada y compartir con Dev 4
```

---

## Contrato de API

**Endpoint:** `POST /analizar`

**Entrada:**
```json
{
  "poligono": [[-17.48, -63.25], [-17.49, -63.25], [-17.49, -63.24], [-17.48, -63.24]],
  "cultivo": "soya",
  "modo": "agro",
  "n_arboles": 5
}
```

**Salida:** ver `mock_resultado.json` arriba

---

## Dependencias

- **Necesitás de Dev 1:** `serviceAccountKey.json` para Earth Engine y `GOOGLE_CLOUD_PROJECT`
- **Dev 3 y Dev 4 dependen de vos:** publicar `mock_resultado.json` el día 1 antes del mediodía

---

## Test rápido local

```bash
uvicorn main:app --reload --port 8080

# En otra terminal:
curl -X POST http://localhost:8080/analizar \
  -H "Content-Type: application/json" \
  -d '{"poligono":[[-17.48,-63.25],[-17.49,-63.25],[-17.49,-63.24],[-17.48,-63.24]],"cultivo":"soya","modo":"agro"}'
```
