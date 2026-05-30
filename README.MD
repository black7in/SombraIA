# SombraIA 🌳

**Plantaciones inteligentes para Santa Cruz, Bolivia**

SombraIA es una plataforma móvil que analiza parcelas agrícolas y zonas afectadas por incendios en Santa Cruz, y genera recomendaciones precisas de dónde plantar árboles nativos y qué cultivar — reduciendo el consumo de agua hasta un 35% y acelerando la recuperación de suelos degradados.

---

## El problema

Santa Cruz enfrenta dos crisis silenciosas:

- **70%** del agua agrícola se pierde por evaporación en suelos expuestos al sol
- **4.2 millones de hectáreas** quemadas en los últimos 5 años sin plan de reforestación inteligente

Los agricultores saben que los árboles ayudan. El problema es saber **dónde** plantarlos.

---

## La solución

SombraIA cruza datos satelitales (Google Earth Engine), simulación solar (pvlib) y optimización espacial (scipy) para devolver en segundos:

- Mapa con puntos GPS exactos donde plantar árboles
- Especies nativas de Santa Cruz recomendadas por posición
- Cultivos compatibles para sembrar junto a los árboles
- Estimación de ahorro de agua semanal
- Plan de reforestación por fases para zonas quemadas
- Recomendaciones en lenguaje natural generadas por Gemini

---

## Funcionalidades

### Modo agricultor
El usuario dibuja o ubica su parcela. La app analiza el microclima, la trayectoria solar y el estado del suelo para recomendar una combinación de árboles y cultivos que maximiza el aprovechamiento del agua disponible.

### Modo reforestación
Para zonas afectadas por incendios. La app detecta el área quemada con satélite, genera un plan de plantación por fases (pioneras primero, nativas de mayor porte después) y diseña corredores de humedad que conectan con parcelas vecinas.

### Alertas de incendios
Una Cloud Function corre diariamente, detecta focos activos en Santa Cruz con MODIS/Earth Engine y envía notificaciones push a usuarios en el área afectada.

### Chatbot agronómico
El usuario puede hacer preguntas sobre su parcela guardada y Gemini responde con contexto personalizado en español natural.

---

## Stack tecnológico

| Capa | Tecnología | Uso |
|---|---|---|
| App móvil | Expo + React Native | iOS y Android desde un solo código |
| Mapas | Google Maps SDK | Visualización y dibujo de parcelas |
| Base de datos | Firebase Firestore | Usuarios, parcelas, resultados, alertas |
| Geo queries | Supabase + PostGIS | Búsqueda de parcelas por proximidad |
| Motor IA | Python en Cloud Run | pvlib + scipy + Earth Engine |
| Datos satelitales | Google Earth Engine | NDVI, detección de quemas, temperatura |
| IA generativa | Vertex AI — Gemini | Recomendaciones en lenguaje natural |
| Alertas | Cloud Functions + Scheduler | Detección diaria de incendios |
| API Gateway | Cloud Functions | Punto de entrada unificado para la app |

Todo el stack usa planes gratuitos y escala sin cambios de código.

---

## Arquitectura

```
App Expo (React Native)
        │
        ▼
API Gateway (Cloud Functions)
        │
   ┌────┴────────────────┐
   │                     │
   ▼                     ▼
Motor IA              Gemini API
(Cloud Run)         (Vertex AI)
   │
   ├── pvlib (simulación solar)
   ├── scipy (optimizador)
   └── Earth Engine (satélite)
        │
   ┌────┴────────────────┐
   │                     │
   ▼                     ▼
Firestore           Supabase
(datos app)         (geo queries)
```

---

## Estructura del repositorio

```
sombraia/
├── modulo1_infraestructura/   # Firebase, Firestore, Supabase, Auth
├── modulo2_motor_ia/          # Python: pvlib, scipy, Earth Engine
├── modulo3_gemini_alertas/    # Gemini API, Cloud Functions, alertas
├── modulo4_api_gateway/       # Gateway, CRUD, tests, mock data
├── app/                       # Expo React Native (fase 2)
├── docs/
│   ├── modulo1_infraestructura.md
│   ├── modulo2_motor_ia.md
│   ├── modulo3_gemini_alertas.md
│   └── modulo4_api_gateway.md
└── README.md
```

---

## Setup rápido

### Requisitos previos

- Node.js 20+
- Python 3.11+
- Google Cloud SDK (`gcloud`)
- Cuenta en [Firebase](https://firebase.google.com) y [Supabase](https://supabase.com)
- Acceso a [Google Earth Engine](https://earthengine.google.com) (cuenta gratuita de investigación)

### 1. Clonar el repositorio

```bash
git clone https://github.com/tu-equipo/sombraia.git
cd sombraia
```

### 2. Configurar variables de entorno

Copiar el archivo de ejemplo y completar con las credenciales reales (pedirlas a Dev 1):

```bash
cp .env.example .env
```

```env
# GCP
GOOGLE_CLOUD_PROJECT=sombraia-hackathon
GOOGLE_APPLICATION_CREDENTIALS=./serviceAccountKey.json

# Firebase
FIREBASE_WEB_CLIENT_ID=
FIREBASE_API_KEY=
FIREBASE_AUTH_DOMAIN=
FIREBASE_PROJECT_ID=

# Supabase
SUPABASE_URL=
SUPABASE_ANON_KEY=

# URLs de módulos (se completan al hacer deploy)
MOTOR_URL=
GEMINI_URL=
GATEWAY_URL=
```

### 3. Setup por módulo

Cada módulo tiene sus propias instrucciones detalladas en `/docs/`:

```bash
# Módulo 1 — Infraestructura
cat docs/modulo1_infraestructura.md

# Módulo 2 — Motor IA
cat docs/modulo2_motor_ia.md

# Módulo 3 — Gemini + Alertas
cat docs/modulo3_gemini_alertas.md

# Módulo 4 — API Gateway
cat docs/modulo4_api_gateway.md
```

---

## API

Todos los endpoints pasan por el Gateway. URL base publicada en el canal del equipo.

### Autenticación

Todos los endpoints requieren token Firebase en el header:

```
Authorization: Bearer <firebase_id_token>
```

### Endpoints

#### `GET /api/health`
Estado del sistema. Sin autenticación.

```json
{
  "status": "ok",
  "version": "1.0",
  "modulos": {
    "motor": "conectado",
    "gemini": "conectado"
  }
}
```

#### `POST /api/analizar`
Análisis completo de una parcela.

**Body:**
```json
{
  "poligono": [[-17.48, -63.25], [-17.49, -63.25], [-17.49, -63.24], [-17.48, -63.24]],
  "cultivo": "soya",
  "modo": "agro",
  "n_arboles": 5
}
```

**Respuesta:**
```json
{
  "puntos": [
    { "lat": -17.4823, "lng": -63.2514, "especie": "Tajibo", "posicion": "norte", "distancia_borde_m": 5 }
  ],
  "ahorro_agua_pct": 32,
  "ndvi": 0.41,
  "zona_quemada": false,
  "cultivos_compatibles": ["poroto", "yuca", "maní"],
  "recomendacion_texto": "Con los árboles recomendados vas a reducir tu riego en un 32%..."
}
```

#### `GET /api/parcelas`
Lista las parcelas guardadas del usuario autenticado.

#### `POST /api/parcelas`
Guarda una parcela y su resultado de análisis en Firestore.

#### `DELETE /api/parcelas/:id`
Elimina una parcela del usuario.

#### `GET /api/alertas?lat=-17.48&lng=-63.25&radio_km=50`
Alertas de incendios activas. Filtra por proximidad si se pasan coordenadas.

---

## Especies nativas

El motor recomienda exclusivamente especies nativas de Santa Cruz:

| Especie | Nombre científico | Uso principal |
|---|---|---|
| Tajibo | *Tabebuia impetiginosa* | Post-incendio, pionera |
| Toborochi | *Ceiba speciosa* | Sombra amplia, retiene humedad |
| Cuchi | *Astronium urundeuva* | Resistente al calor y sequía |
| Algarrobo | *Prosopis alba* | Fija nitrógeno, mejora suelo |
| Cedro | *Cedrela odorata* | Cortavientos, crecimiento rápido |

---

## Equipo de desarrollo

| Dev | Módulo | Responsabilidad |
|---|---|---|
| Dev 1 | Infraestructura | Firebase, Firestore, Supabase, credenciales GCP |
| Dev 2 | Motor IA | pvlib, Earth Engine, optimizador, Cloud Run |
| Dev 3 | Gemini + Alertas | Recomendaciones en lenguaje natural, alertas de incendios |
| Dev 4 | API Gateway | Punto de entrada unificado, tests, datos de demo |

---

## Regla de trabajo en paralelo

Dev 2 publica `mock_resultado.json` el día 1 antes del mediodía. Dev 3 y Dev 4 trabajan contra ese mock desde el primer momento. Cuando el módulo real esté listo, solo se actualiza la variable de entorno — el código no cambia.

---

## Tests

```bash
# Tests del gateway (incluye fallback a mocks)
cd modulo4_api_gateway
NODE_ENV=development npx jest

# Tests contra el gateway deployado
GATEWAY_URL=https://tu-gateway.run.app npx jest

# Verificar que la demo está lista
npx jest && echo "Todo OK — demo lista"
```

---

## Demo

Dos escenarios precargados para la presentación:

- **Parcela San Julián** — Soya, modo agro, 1.2 ha
- **Zona quemada Warnes** — Post-incendio, reforestación por fases

```bash
# Cargar datos de demo en Firestore
cd modulo4_api_gateway
node scripts/cargar_demo.js
```

---

## Licencia

MIT — Hackathon Google 2025
