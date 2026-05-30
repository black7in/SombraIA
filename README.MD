# SombraAI

Plataforma de recomendación de plantación de árboles nativos para Santa Cruz, Bolivia.
Cualquier persona con un terreno puede analizar su parcela y recibir puntos estratégicos
de plantación, estimaciones de impacto ambiental y cuidados por especie.

---

## Casos de uso

**Modo ambiental** — para cualquier persona con terreno que quiera generar sombra,
capturar CO2 o reforestar. Los árboles se ubican dentro del terreno maximizando
cobertura. Incluye proyección de crecimiento a 1, 3, 5 y 10 años.

**Modo agro** — para agricultores. Los árboles se colocan en los bordes del campo
como cortinas rompevientos, sin competir con el cultivo ni su sistema de riego.

**Zona quemada** — detectada automáticamente vía satélite. Adapta las recomendaciones
a recuperación post-incendio en ambos modos.

---

## Stack

| Capa | Tecnología |
|---|---|
| Backend | Python 3.11 · FastAPI · Cloud Run |
| Satélite | Google Earth Engine (Sentinel-2, MODIS) |
| Solar | pvlib |
| IA | Vertex AI — Gemini 1.5 Flash |
| Base de datos | Cloud Firestore |
| Auth | Firebase Authentication |
| App móvil | React Native |

---

## Setup

```bash
# Requisitos: Python 3.11+, Google Cloud SDK

cp .env.example .env
# Completar con serviceAccountKey.json y GOOGLE_CLOUD_PROJECT

uvicorn main:app --reload --port 8080
```

Ver `.env.example` para instrucciones de credenciales y configuración React Native.

---

## API

Base URL: `https://<cloud-run-url>/api`

Todos los endpoints (excepto `/health`) requieren:
```
Authorization: Bearer <firebase-id-token>
```

---

### Health

| Método | Endpoint | Descripción |
|---|---|---|
| `GET` | `/health` | Estado del servidor. Sin autenticación. |

**Response**
```json
{ "status": "ok", "version": "2.0" }
```

---

### Auth

| Método | Endpoint | Descripción |
|---|---|---|
| `POST` | `/auth/register` | Registra al usuario tras el primer login |
| `GET` | `/auth/me` | Perfil del usuario autenticado |

#### `POST /auth/register`
```json
// Body
{ "nombre": "Juan Pérez", "departamento": "Santa Cruz" }

// Response 201
{ "uid": "abc123", "nombre": "Juan Pérez" }
```

#### `GET /auth/me`
```json
// Response 200
{ "uid": "abc123", "nombre": "Juan Pérez", "email": "juan@example.com", "departamento": "Santa Cruz" }
```

---

### Análisis

| Método | Endpoint | Descripción |
|---|---|---|
| `POST` | `/analizar` | Analiza el terreno y devuelve puntos de plantación |

#### `POST /analizar`

**Body — modo ambiental**
```json
{
  "poligono": [[-17.48, -63.25], [-17.49, -63.25], [-17.49, -63.24], [-17.48, -63.24]],
  "modo": "ambiental",
  "n_arboles": 5
}
```

**Body — modo agro** (`cultivo` requerido)
```json
{
  "poligono": [[-17.48, -63.25], [-17.49, -63.25], [-17.49, -63.24], [-17.48, -63.24]],
  "modo": "agro",
  "cultivo": "soya",
  "n_arboles": 5
}
```

**Response — modo ambiental**
```json
{
  "modo": "ambiental",
  "puntos": [
    { "lat": -17.483, "lng": -63.248, "especie": "Tipa", "posicion": "norte", "distancia_borde_m": 12.4 }
  ],
  "cobertura_sombra_pct": 42,
  "co2_estimado_kg_anual": 115,
  "reduccion_temp_suelo_c": 2.1,
  "ndvi": 0.38,
  "zona_quemada": false,
  "proyeccion_crecimiento": {
    "año_1":  { "altura_media_m": 0.9,  "cobertura_pct": 4  },
    "año_3":  { "altura_media_m": 4.1,  "cobertura_pct": 18 },
    "año_5":  { "altura_media_m": 6.8,  "cobertura_pct": 32 },
    "año_10": { "altura_media_m": 13.5, "cobertura_pct": 42 }
  },
  "cuidados": [
    "Regar cada 3 días los primeros 6 meses",
    "Colocar tutor de 1.5m hasta que el árbol se afirme",
    "Plantar al inicio de las lluvias (noviembre)",
    "Primera poda formativa al segundo año",
    "El árbol está establecido cuando brota sin riego artificial"
  ],
  "recomendacion_texto": "Tu terreno recibe más de 9 horas de sol intenso..."
}
```

**Response — modo agro**
```json
{
  "modo": "agro",
  "puntos": [
    { "lat": -17.483, "lng": -63.248, "especie": "Algarrobo", "posicion": "cortina_norte", "distancia_borde_m": 2.0 }
  ],
  "ahorro_agua_pct": 32,
  "reduccion_temp_suelo_c": 2.1,
  "ndvi": 0.41,
  "zona_quemada": false,
  "cultivos_compatibles": ["poroto", "maní", "yuca"],
  "cobertura_recomendada": "pasto nativo entre hileras",
  "cuidados": ["..."],
  "recomendacion_texto": "..."
}
```

> Si `zona_quemada: true`, los puntos y el texto se adaptan automáticamente
> a recuperación post-incendio en ambos modos.

---

### Parcelas

| Método | Endpoint | Descripción |
|---|---|---|
| `GET` | `/parcelas` | Lista las parcelas del usuario |
| `GET` | `/parcelas/{id}` | Devuelve una parcela con su resultado |
| `POST` | `/parcelas` | Guarda una parcela con su resultado |
| `PUT` | `/parcelas/{id}` | Actualiza nombre o notas |
| `DELETE` | `/parcelas/{id}` | Elimina una parcela |
| `GET` | `/parcelas/{id}/calendario` | Calendario de plantación por especie |

#### `POST /parcelas`
```json
// Body
{
  "nombre": "Campo norte",
  "poligono": [[-17.48, -63.25], ["..."]],
  "modo": "agro",
  "cultivo": "soya",
  "resultado": { "...resultado de /analizar..." }
}

// Response 201
{ "id": "xyz" }
```

#### `PUT /parcelas/{id}`
```json
// Body (todos los campos son opcionales)
{ "nombre": "Campo norte — 2025", "notas": "Pendiente leve al este" }

// Response 200
{ "id": "xyz" }
```

#### `GET /parcelas/{id}/calendario?municipio=San+Julián`

| Query param | Default | Descripción |
|---|---|---|
| `municipio` | `Santa Cruz` | Municipio para ajustar el calendario estacional |

```json
// Response 200
{
  "calendario": "Noviembre - Tipa - Plantar al inicio de lluvias\nDiciembre - ...",
  "especies": ["Tipa", "Algarrobo"],
  "municipio": "San Julián"
}
```

---

### Chat

| Método | Endpoint | Descripción |
|---|---|---|
| `POST` | `/chat` | Chatbot agronómico con contexto de la parcela |

#### `POST /chat`
```json
// Body
{
  "pregunta": "¿Cuándo debo regar los árboles?",
  "parcela_id": "xyz"
}

// Response 200
{ "respuesta": "Con el Algarrobo en tu parcela, en los primeros 6 meses..." }
```

---

## Credenciales necesarias

| Archivo / Variable | Dónde conseguirlo |
|---|---|
| `serviceAccountKey.json` | GCP Console → IAM → Service Accounts |
| `google-services.json` | Firebase Console → Project Settings → Android |
| `GoogleService-Info.plist` | Firebase Console → Project Settings → iOS |
| `MAPS_API_KEY` | GCP Console → APIs & Services → Credentials |

## APIs a habilitar en GCP

```
Firebase Authentication API
Cloud Firestore API
Earth Engine API
Vertex AI API
Cloud Run API
Maps SDK for Android / iOS
```

---

## Licencia

MIT — Hackathon 2025
