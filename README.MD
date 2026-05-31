# SombraAI

Plataforma de recomendación de plantación de árboles nativos para Santa Cruz, Bolivia.
Cualquier persona con un terreno puede analizar su parcela y recibir puntos estratégicos
de plantación, estimaciones de impacto ambiental y cuidados por especie.

---

## Casos de uso

**Modo ambiental** — para cualquier persona con terreno que quiera generar sombra,
capturar CO2 o reforestar. Los árboles se ubican dentro del terreno maximizando cobertura.
Incluye proyección de crecimiento a 1, 3, 5 y 10 años.

**Modo agro** — para agricultores. Los árboles se colocan en los bordes del campo
como cortinas rompevientos, sin competir con el cultivo.

**Zona quemada** — detectada automáticamente vía satélite (MODIS). Adapta las
recomendaciones a recuperación post-incendio en ambos modos.

---

## Stack

| Capa | Tecnología |
|---|---|
| Backend | Python 3.11+ · FastAPI · Cloud Run |
| Satélite | Google Earth Engine (Sentinel-2 NDVI, MODIS Fire/LST) |
| Solar | pvlib |
| IA | Gemini 2.5 Flash (Google AI Studio) |
| Base de datos | Cloud Firestore |
| Auth | Firebase Authentication |
| App móvil | React Native |

---

## Setup local

```bash
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt

cp .env.example .env
# Completar variables (ver sección Credenciales)

venv\Scripts\uvicorn main:app --port 8080 --reload
```

---

## Variables de entorno

| Variable | Descripción |
|---|---|
| `GOOGLE_CLOUD_PROJECT` | ID del proyecto GCP |
| `GOOGLE_APPLICATION_CREDENTIALS` | Ruta al serviceAccountKey.json |
| `FIRESTORE_DATABASE_ID` | ID de la base Firestore (usar `(default)`) |
| `GEMINI_API_KEY` | API key de Google AI Studio |
| `ENV` | `development` desactiva verificación de token Firebase |

---

## Credenciales necesarias

| Archivo / Variable | Dónde conseguirlo |
|---|---|
| `serviceAccountKey.json` | GCP Console → IAM → Service Accounts → Claves |
| `GEMINI_API_KEY` | [aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey) |
| `google-services.json` | Firebase Console → Project Settings → Android |
| `GoogleService-Info.plist` | Firebase Console → Project Settings → iOS |

### APIs a habilitar en GCP

- Cloud Firestore API
- Earth Engine API
- Cloud Resource Manager API

### Roles de la cuenta de servicio

- Editor (cubre Firestore + Earth Engine)

### Registro Earth Engine

El proyecto debe registrarse en [code.earthengine.google.com](https://code.earthengine.google.com) → Register a Cloud Project.

---

## API Reference

Base URL: `https://<cloud-run-url>/api`

Todos los endpoints (excepto `/health`) requieren:
```
Authorization: Bearer <firebase-id-token>
```
En `ENV=development` el token no se verifica (útil para pruebas locales).

> **Coordenadas**: el formato del polígono es `[lng, lat]` — longitud primero.
> Ejemplo Santa Cruz: `[-63.18, -17.78]`

---

### Health

#### `GET /health`

Sin autenticación.

```json
// Response 200
{ "status": "ok", "version": "2.0" }
```

---

### Auth

#### `POST /auth/register`

Registra al usuario tras el primer login con Firebase.

```json
// Body
{
  "nombre": "Juan Pérez",
  "departamento": "Santa Cruz"   // opcional, default "Santa Cruz"
}

// Response 201
{
  "uid": "abc123",
  "nombre": "Juan Pérez"
}
```

#### `GET /auth/me`

Perfil del usuario autenticado.

```json
// Response 200
{
  "uid": "abc123",
  "nombre": "Juan Pérez",
  "email": "juan@example.com",
  "departamento": "Santa Cruz",
  "created_at": "2025-01-15T14:30:00+00:00"
}

// Response 404 si el usuario nunca llamó a /auth/register
```

---

### Análisis de terreno

#### `POST /analizar`

Analiza el terreno vía satélite y devuelve puntos estratégicos de plantación con
recomendación de Gemini y cuidados por especie.

**Body — modo ambiental**

```json
{
  "poligono": [
    [-63.18, -17.78],
    [-63.17, -17.78],
    [-63.17, -17.77],
    [-63.18, -17.77]
  ],
  "modo": "ambiental",
  "n_arboles": 5
}
```

**Body — modo agro** (`cultivo` es requerido)

```json
{
  "poligono": [
    [-63.18, -17.78],
    [-63.17, -17.78],
    [-63.17, -17.77],
    [-63.18, -17.77]
  ],
  "modo": "agro",
  "cultivo": "soya",
  "n_arboles": 5
}
```

| Campo | Tipo | Default | Descripción |
|---|---|---|---|
| `poligono` | `[[float, float]]` | requerido | Polígono en `[lng, lat]`. Mínimo 3 puntos. |
| `modo` | `"ambiental"` \| `"agro"` | `"ambiental"` | Modo de plantación |
| `cultivo` | `string` | `null` | Cultivo actual. Requerido si `modo="agro"` |
| `n_arboles` | `int` | `5` | Cantidad de árboles a recomendar |

**Response — modo ambiental**

```json
{
  "modo": "ambiental",
  "puntos": [
    {
      "lat": -17.7747,
      "lng": -63.1783,
      "especie": "Mapajo",
      "posicion": "norte",
      "distancia_borde_m": 185.0
    }
  ],
  "cobertura_sombra_pct": 0.3,
  "co2_estimado_kg_anual": 325,
  "reduccion_temp_suelo_c": 2.1,
  "ndvi": 0.179,
  "zona_quemada": false,
  "proyeccion_crecimiento": {
    "año_1":  { "altura_media_m": 0.7,  "cobertura_pct": 0.0 },
    "año_3":  { "altura_media_m": 4.1,  "cobertura_pct": 0.0 },
    "año_5":  { "altura_media_m": 6.9,  "cobertura_pct": 0.1 },
    "año_10": { "altura_media_m": 13.8, "cobertura_pct": 0.3 }
  },
  "recomendacion_texto": "Texto generado por Gemini...",
  "cuidados": [
    "Riega cada 2-3 días los primeros 3 meses.",
    "Coloca tutores firmes hasta que el árbol se afirme.",
    "Poda de formación al primer año.",
    "Planta al inicio de lluvias (noviembre-diciembre).",
    "El árbol está establecido cuando brota sin riego artificial."
  ]
}
```

**Response — modo agro**

```json
{
  "modo": "agro",
  "puntos": [
    {
      "lat": -17.7700,
      "lng": -63.1783,
      "especie": "Tajibo",
      "posicion": "cortina_norte",
      "distancia_borde_m": 2.2
    }
  ],
  "ahorro_agua_pct": 32,
  "reduccion_temp_suelo_c": 2.1,
  "ndvi": 0.179,
  "zona_quemada": false,
  "cultivos_compatibles": ["poroto", "maní", "yuca"],
  "cobertura_recomendada": "pasto nativo entre hileras",
  "recomendacion_texto": "Texto generado por Gemini...",
  "cuidados": [
    "Riega cada 2-3 días los primeros 3 meses.",
    "..."
  ]
}
```

> Si `zona_quemada: true`, la `recomendacion_texto` y los `puntos` se adaptan
> automáticamente a recuperación post-incendio.

---

### Parcelas

#### `GET /parcelas`

Lista las parcelas guardadas del usuario autenticado (máx. 50).

```json
// Response 200
[
  {
    "id": "abc123",
    "nombre": "Campo norte",
    "poligono": [[-63.18, -17.78], ["..."]],
    "modo": "agro",
    "cultivo": "soya",
    "resultado": { "...resultado de /analizar..." },
    "user_id": "uid_del_usuario",
    "created_at": "2025-01-15T14:30:00+00:00"
  }
]
```

#### `GET /parcelas/{id}`

Devuelve una parcela por ID.

```json
// Response 200 — misma estructura que un item de GET /parcelas
// Response 403 si la parcela pertenece a otro usuario
// Response 404 si no existe
```

#### `POST /parcelas`

Guarda una parcela con su resultado de análisis.

```json
// Body
{
  "nombre": "Campo norte",
  "poligono": [[-63.18, -17.78], [-63.17, -17.78], [-63.17, -17.77], [-63.18, -17.77]],
  "modo": "agro",
  "cultivo": "soya",           // opcional
  "resultado": { "...resultado completo de /analizar..." }  // opcional
}

// Response 201
{ "id": "abc123" }
```

| Campo | Tipo | Descripción |
|---|---|---|
| `nombre` | `string` | requerido |
| `poligono` | `[[float, float]]` | requerido, `[lng, lat]` |
| `modo` | `string` | opcional, default `"ambiental"` |
| `cultivo` | `string` | opcional |
| `resultado` | `object` | opcional, resultado de `/analizar` para guardar |

#### `PUT /parcelas/{id}`

Actualiza el nombre o notas de una parcela.

```json
// Body (todos los campos son opcionales)
{
  "nombre": "Campo norte — 2025",
  "notas": "Pendiente leve al este"
}

// Response 200
{ "id": "abc123" }
```

#### `DELETE /parcelas/{id}`

Elimina una parcela.

```
// Response 204 No Content
```

#### `GET /parcelas/{id}/calendario`

Genera un calendario mensual de plantación para las especies guardadas en el resultado.
Requiere que la parcela tenga `resultado.puntos` con campo `especie`.

| Query param | Default | Descripción |
|---|---|---|
| `municipio` | `Santa Cruz` | Municipio para ajustar el calendario estacional |

```json
// Response 200
{
  "calendario": "Noviembre - Tajibo - Plantar al inicio de lluvias\nDiciembre - Toborochi - Plantar\n...",
  "especies": ["Tajibo", "Toborochi"],
  "municipio": "Santa Cruz"
}

// Response 400 si la parcela no tiene árboles guardados
```

---

### Chat

#### `POST /chat`

Chatbot agronómico. Si se provee `parcela_id`, la respuesta se personaliza con el
contexto de esa parcela.

```json
// Body
{
  "pregunta": "Cuándo debo regar los árboles?",
  "parcela_id": "abc123"   // opcional
}

// Response 200
{
  "respuesta": "Con el Tajibo en tu parcela, durante los primeros 6 meses..."
}
```

| Campo | Tipo | Descripción |
|---|---|---|
| `pregunta` | `string` | requerido |
| `parcela_id` | `string` | opcional, ID de parcela para contexto |

---

## Licencia

MIT — Hackathon 2025
