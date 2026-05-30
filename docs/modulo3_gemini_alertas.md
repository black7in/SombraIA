# Módulo 3 — Gemini + Alertas
**Dev 3 · SombraIA · Hackathon 2025**

---

## Tu rol en el proyecto

Sos la voz de la app. Tu trabajo convierte datos técnicos en recomendaciones que cualquier agricultor entiende, y detecta incendios antes de que lleguen. Podés arrancar desde el día 1 usando el `mock_resultado.json` de Dev 2 — no necesitás esperar a que el motor real esté listo.

---

## Stack que usás

| Herramienta | Para qué |
|---|---|
| Vertex AI / Gemini API | Generación de texto en español natural |
| Google Cloud Functions | Función de alertas de incendios (corre diariamente) |
| Google Earth Engine | Detección de fuego para las alertas |
| Firebase Admin SDK | Guardar alertas en Firestore |
| Node.js | Runtime de las Cloud Functions |

---

## Prioridad día 1: trabajar con el mock

Dev 2 te entrega este JSON antes del mediodía. Arrancá con él:

```json
{
  "datos_para_gemini": {
    "horas_sol_directo": 9.2,
    "horas_criticas_dia": 5.1,
    "temp_suelo_actual": 38,
    "temp_suelo_proyectada": 35.9,
    "cultivo_actual": "soya",
    "ndvi": 0.41,
    "zona_quemada": false,
    "arboles_sugeridos": 5
  },
  "puntos": [
    { "especie": "Tajibo", "posicion": "norte", "distancia_borde_m": 5 },
    { "especie": "Toborochi", "posicion": "este", "distancia_borde_m": 8 }
  ],
  "ahorro_agua_pct": 32,
  "cultivos_compatibles": ["poroto", "yuca", "maní"]
}
```

---

## Estructura del proyecto

```
modulo3_gemini/
├── gemini_service.js      # Integración Gemini API
├── prompts.js             # Todos los prompts del sistema
├── alertas/
│   └── index.js           # Cloud Function de alertas
├── calendario.js          # Calendario de plantación
├── chatbot.js             # Chatbot de consultas
└── package.json
```

---

## Tareas en orden

### 1. Setup Gemini API

```bash
npm init -y
npm install @google-cloud/vertexai firebase-admin axios
```

**`gemini_service.js`**
```javascript
const { VertexAI } = require('@google-cloud/vertexai');

const vertexAI = new VertexAI({
  project: process.env.GOOGLE_CLOUD_PROJECT,
  location: 'us-central1'
});

const modelo = vertexAI.getGenerativeModel({
  model: 'gemini-1.5-flash',  // Flash es gratis con límites generosos
});

async function generarTexto(prompt) {
  const resultado = await modelo.generateContent(prompt);
  const respuesta = resultado.response;
  return respuesta.candidates[0].content.parts[0].text;
}

module.exports = { generarTexto };
```

### 2. Prompts del sistema (`prompts.js`)

```javascript
// Prompt para recomendación principal de parcela
function promptRecomendacion(datos) {
  return `
Sos un agrónomo experto en Santa Cruz, Bolivia. Explicá la siguiente recomendación 
de plantación de árboles a un agricultor local. Usá lenguaje simple y directo, 
como si le hablaras en persona. Máximo 4 oraciones. No uses jerga técnica.

Datos de la parcela:
- Cultivo actual: ${datos.cultivo_actual}
- Temperatura del suelo: ${datos.temp_suelo_actual}°C
- Horas de sol crítico por día (10am-3pm): ${datos.horas_criticas_dia} horas
- NDVI (salud del suelo, 0-1): ${datos.ndvi}
- Árboles recomendados: ${datos.arboles_sugeridos}
- Ahorro de agua proyectado: ${datos.ahorro_agua_pct}%
- Temperatura proyectada con sombra: ${datos.temp_suelo_proyectada}°C

Árboles específicos:
${datos.puntos.map(p => `- ${p.especie} al ${p.posicion}, a ${p.distancia_borde_m}m del borde`).join('\n')}

Cultivos recomendados junto a los árboles: ${datos.cultivos_compatibles.join(', ')}

Respondé solo con el texto de la recomendación, sin títulos ni listas.
`;
}

// Prompt para zona quemada
function promptZonaQuemada(datos) {
  return `
Sos un experto en reforestación post-incendio en Santa Cruz, Bolivia.
Explicá el plan de recuperación para esta zona afectada.
Lenguaje simple, máximo 4 oraciones, como si le hablaras al dueño del terreno.

Situación:
- Zona afectada por incendio reciente
- NDVI actual: ${datos.ndvi} (muy bajo = suelo dañado)
- Temperatura del suelo: ${datos.temp_suelo_actual}°C
- Árboles pioneros recomendados: ${datos.arboles_sugeridos}
- Especies: ${datos.puntos.map(p => p.especie).join(', ')}

Incluí: qué hacer primero, por qué estas especies y qué esperar en 12 meses.
Respondé solo con el texto, sin títulos.
`;
}

// Prompt para chatbot de consultas
function promptChatbot(pregunta, contextoParcela) {
  return `
Sos un agrónomo de Santa Cruz, Bolivia. Respondé esta pregunta del agricultor 
sobre su parcela de forma concisa (máximo 3 oraciones). Usá el contexto de su 
parcela para dar una respuesta personalizada.

Contexto de su parcela:
- Cultivo: ${contextoParcela.cultivo}
- Ubicación: ${contextoParcela.municipio || 'Santa Cruz'}
- Árboles plantados: ${contextoParcela.especies?.join(', ') || 'no registrado'}
- Último análisis: ahorro de agua ${contextoParcela.ahorro_agua_pct || 0}%

Pregunta del agricultor: "${pregunta}"

Respondé directamente sin presentarte.
`;
}

// Prompt para calendario de plantación
function promptCalendario(especies, municipio) {
  return `
Creá un calendario mensual de plantación para estas especies en ${municipio}, 
Santa Cruz, Bolivia. Considerá lluvias (nov-mar) y sequía (abr-oct).
Formato: mes - especie - acción. Máximo 12 líneas, una por mes relevante.

Especies: ${especies.join(', ')}

Solo el calendario, sin explicaciones adicionales.
`;
}

module.exports = { 
  promptRecomendacion, 
  promptZonaQuemada,
  promptChatbot,
  promptCalendario
};
```

### 3. Servicio principal (`index.js` del módulo)

```javascript
const { generarTexto } = require('./gemini_service');
const { 
  promptRecomendacion, 
  promptZonaQuemada,
  promptChatbot,
  promptCalendario
} = require('./prompts');

// Genera el texto de recomendación a partir del resultado del Motor (Dev 2)
async function generarRecomendacion(resultadoMotor) {
  const datos = {
    ...resultadoMotor.datos_para_gemini,
    puntos: resultadoMotor.puntos,
    ahorro_agua_pct: resultadoMotor.ahorro_agua_pct,
    cultivos_compatibles: resultadoMotor.cultivos_compatibles
  };

  const prompt = datos.zona_quemada
    ? promptZonaQuemada(datos)
    : promptRecomendacion(datos);

  const texto = await generarTexto(prompt);
  return texto.trim();
}

// Responde pregunta del chatbot con contexto de la parcela guardada
async function responderChatbot(pregunta, contextoParcela) {
  const prompt = promptChatbot(pregunta, contextoParcela);
  return await generarTexto(prompt);
}

// Genera calendario de plantación para las especies recomendadas
async function generarCalendario(especies, municipio = 'San Julián') {
  const prompt = promptCalendario(especies, municipio);
  return await generarTexto(prompt);
}

module.exports = { generarRecomendacion, responderChatbot, generarCalendario };
```

### 4. Cloud Function de alertas (`alertas/index.js`)

Esta función corre automáticamente cada día a las 7am y chequea incendios activos.

```javascript
const functions = require('@google-cloud/functions-framework');
const admin = require('firebase-admin');
const ee = require('@google/earthengine');

admin.initializeApp();
const db = admin.firestore();

// Zona de interés: Santa Cruz, Bolivia
const SANTA_CRUZ_BBOX = [-63.5, -18.5, -60.0, -15.5];

functions.http('checkIncendios', async (req, res) => {
  try {
    await verificarIncendios();
    res.json({ ok: true, mensaje: 'Verificación completada' });
  } catch (e) {
    console.error(e);
    res.status(500).json({ error: e.message });
  }
});

async function verificarIncendios() {
  // Autenticar con Earth Engine usando service account
  await new Promise((resolve, reject) => {
    ee.authenticate({ client_id: process.env.EE_CLIENT_ID }, (err) => {
      err ? reject(err) : resolve();
    });
  });
  ee.initialize();

  const hoy = new Date();
  const ayer = new Date(hoy - 86400000);
  const fechaHoy = hoy.toISOString().split('T')[0];
  const fechaAyer = ayer.toISOString().split('T')[0];

  const region = ee.Geometry.Rectangle(SANTA_CRUZ_BBOX);

  // Detección de fuego activo con MODIS
  const fuego = ee.ImageCollection('MODIS/061/MOD14A1')
    .filterBounds(region)
    .filterDate(fechaAyer, fechaHoy)
    .select('FireMask')
    .max();

  const zonasFuego = fuego.gt(6);  // Confianza alta de fuego

  // Obtener puntos de fuego
  const puntos = zonasFuego.reduceToVectors({
    geometry: region,
    scale: 1000,
    maxPixels: 1e6
  });

  const geojson = puntos.getInfo();

  if (!geojson?.features?.length) {
    console.log('Sin incendios activos hoy');
    return;
  }

  // Guardar alertas en Firestore
  const batch = db.batch();
  for (const feature of geojson.features.slice(0, 20)) {
    const coords = feature.geometry.coordinates[0][0];
    const ref = db.collection('alertas').doc();
    batch.set(ref, {
      tipo: 'incendio',
      lat: coords[1],
      lng: coords[0],
      radio_km: 5,
      descripcion: `Incendio activo detectado cerca de ${coords[1].toFixed(2)}, ${coords[0].toFixed(2)}`,
      activa: true,
      created_at: admin.firestore.FieldValue.serverTimestamp()
    });
  }

  await batch.commit();
  console.log(`${geojson.features.length} alertas guardadas`);
}
```

Deploy de la Cloud Function:
```bash
gcloud functions deploy checkIncendios \
  --runtime nodejs20 \
  --trigger-http \
  --allow-unauthenticated \
  --region us-central1 \
  --source ./alertas

# Programar ejecución diaria a las 7am (Santa Cruz)
gcloud scheduler jobs create http sombraia-check-incendios \
  --schedule="0 11 * * *" \
  --uri=URL_DE_TU_CLOUD_FUNCTION \
  --time-zone="America/La_Paz"
```

### 5. Endpoint del chatbot (`chatbot.js`)

```javascript
const functions = require('@google-cloud/functions-framework');
const admin = require('firebase-admin');
const { responderChatbot } = require('./index');

admin.initializeApp();
const db = admin.firestore();

functions.http('chatbot', async (req, res) => {
  res.set('Access-Control-Allow-Origin', '*');

  const { pregunta, parcela_id, user_id } = req.body;

  if (!pregunta) {
    return res.status(400).json({ error: 'Pregunta requerida' });
  }

  // Obtener contexto de la parcela guardada
  let contextoParcela = { cultivo: 'cultivo', municipio: 'Santa Cruz' };
  if (parcela_id) {
    const doc = await db.collection('parcelas').doc(parcela_id).get();
    if (doc.exists) contextoParcela = doc.data();
  }

  const respuesta = await responderChatbot(pregunta, contextoParcela);
  res.json({ respuesta });
});
```

---

## Contrato de API — lo que exponés a Dev 4

```
POST /gemini/recomendar
Body: { resultado_motor: { ...JSON de Dev 2... } }
Response: { recomendacion_texto: "string" }

POST /gemini/chatbot
Body: { pregunta: "string", parcela_id: "string" }
Response: { respuesta: "string" }

GET  /gemini/calendario?especies=Tajibo,Toborochi&municipio=SanJulian
Response: { calendario: "string" }

GET  /alertas
Response: [{ tipo, lat, lng, descripcion, created_at }]
```

---

## Test rápido

```javascript
// test.js — correr con: node test.js
const { generarRecomendacion } = require('./index');
const mock = require('./mock_resultado.json');

generarRecomendacion(mock).then(texto => {
  console.log('RECOMENDACIÓN GENERADA:');
  console.log(texto);
});
```

Ejemplo de salida esperada:
> *"Tu parcela en San Julián recibe más de 9 horas de sol intenso por día, lo que hace que el suelo llegue a 38°C y el agua se evapore rápido. Te recomendamos plantar un Tajibo al norte y un Toborochi al este — con esos dos árboles vas a reducir tu riego en un 32% porque van a dar sombra justo en las horas más calurosas. También podés sembrar poroto o yuca en las zonas con sombra para aprovechar mejor el espacio."*

---

## Dependencias

- **Necesitás de Dev 1:** credenciales GCP, `GOOGLE_CLOUD_PROJECT`
- **Necesitás de Dev 2:** `mock_resultado.json` el día 1 (después el endpoint real)
- **Dev 4 depende de vos:** URLs de tus Cloud Functions para el Gateway
