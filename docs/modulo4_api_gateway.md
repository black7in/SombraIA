# Módulo 4 — API Gateway + Tests
**Dev 4 · SombraIA · Hackathon 2025**

---

## Tu rol en el proyecto

Sos el integrador. Tu módulo es el único punto de entrada para la app móvil — todas las llamadas pasan por vos. También sos el responsable de que la demo no muera en vivo: preparás los datos mock, los tests y el fallback de emergencia.

Podés arrancar desde el día 1 con los contratos (JSONs) que publican Dev 2 y Dev 3, sin esperar a que sus módulos estén completos.

---

## Stack que usás

| Herramienta | Para qué |
|---|---|
| Google Cloud Functions (Node.js) | Gateway principal |
| Firebase Admin SDK | Leer/escribir Firestore |
| axios | Llamar a los módulos internos |
| Swagger / swagger-jsdoc | Documentación de endpoints |
| Jest | Tests de integración |
| Node.js 20 | Runtime |

---

## Estructura del proyecto

```
modulo4_gateway/
├── gateway.js           # Función principal — enruta todo
├── routes/
│   ├── analizar.js      # POST /api/analizar
│   ├── parcelas.js      # GET/POST/DELETE /api/parcelas
│   ├── alertas.js       # GET /api/alertas
│   └── chat.js          # POST /api/chat
├── middleware/
│   └── auth.js          # Verificación de token Firebase
├── mock/
│   ├── resultado.json   # Mock del motor (Dev 2)
│   └── alertas.json     # Mock de alertas (Dev 3)
├── tests/
│   ├── analizar.test.js
│   ├── parcelas.test.js
│   └── integracion.test.js
├── swagger.js           # Documentación automática
└── package.json
```

---

## Tareas en orden

### 1. Setup del proyecto

```bash
npm init -y
npm install @google-cloud/functions-framework firebase-admin axios express cors jest
npm install --save-dev swagger-jsdoc swagger-ui-express
```

### 2. Cargar los mocks desde el día 1

Mientras Dev 2 y Dev 3 terminan sus módulos, usás estos archivos:

**`mock/resultado.json`** — pedíselo a Dev 2 el día 1
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
  "recomendacion_texto": "Tu parcela recibe más de 9 horas de sol intenso por día. Con los árboles recomendados vas a reducir el riego en un 32% y la temperatura del suelo bajará unos 2 grados."
}
```

**`mock/alertas.json`**
```json
[
  {
    "id": "alerta_001",
    "tipo": "incendio",
    "lat": -17.52,
    "lng": -63.18,
    "radio_km": 15,
    "descripcion": "Incendio activo detectado cerca de Pailón. Zona de riesgo en 15km.",
    "activa": true,
    "created_at": "2025-06-01T07:00:00Z"
  }
]
```

### 3. Middleware de autenticación (`middleware/auth.js`)

```javascript
const admin = require('firebase-admin');

module.exports = async function verificarAuth(req, res, next) {
  // Saltar auth en desarrollo
  if (process.env.NODE_ENV === 'development') {
    req.user = { uid: 'dev_user_test' };
    return next();
  }

  const authHeader = req.headers.authorization;
  if (!authHeader?.startsWith('Bearer ')) {
    return res.status(401).json({ error: 'Token requerido' });
  }

  const token = authHeader.split('Bearer ')[1];
  try {
    const decoded = await admin.auth().verifyIdToken(token);
    req.user = decoded;
    next();
  } catch (e) {
    return res.status(401).json({ error: 'Token inválido' });
  }
};
```

### 4. Ruta: analizar parcela (`routes/analizar.js`)

```javascript
const axios = require('axios');
const mockResultado = require('../mock/resultado.json');

const MOTOR_URL = process.env.MOTOR_URL || null;       // Dev 2 — Cloud Run
const GEMINI_URL = process.env.GEMINI_URL || null;     // Dev 3 — Cloud Function

module.exports = async function analizar(req, res) {
  const { poligono, cultivo, modo = 'agro', n_arboles = 5 } = req.body;

  if (!poligono || !cultivo) {
    return res.status(400).json({ error: 'Faltan poligono y cultivo' });
  }

  try {
    // 1. Llamar al motor IA (Dev 2) — o usar mock si no está listo
    let resultadoMotor;
    if (MOTOR_URL) {
      const { data } = await axios.post(`${MOTOR_URL}/analizar`, {
        poligono, cultivo, modo, n_arboles
      });
      resultadoMotor = data;
    } else {
      console.log('[MOCK] Usando mock del motor IA');
      resultadoMotor = { ...mockResultado };
    }

    // 2. Llamar a Gemini para texto natural (Dev 3) — o usar texto del mock
    let recomendacionTexto;
    if (GEMINI_URL) {
      const { data } = await axios.post(`${GEMINI_URL}/recomendar`, {
        resultado_motor: resultadoMotor
      });
      recomendacionTexto = data.recomendacion_texto;
    } else {
      console.log('[MOCK] Usando texto de recomendación mock');
      recomendacionTexto = resultadoMotor.recomendacion_texto;
    }

    // 3. Respuesta unificada para la app
    return res.json({
      ...resultadoMotor,
      recomendacion_texto: recomendacionTexto
    });

  } catch (e) {
    console.error('Error en /analizar:', e.message);
    // Fallback de emergencia para la demo
    return res.json({
      ...mockResultado,
      _fallback: true,
      _error: e.message
    });
  }
};
```

### 5. Ruta: parcelas guardadas (`routes/parcelas.js`)

```javascript
const admin = require('firebase-admin');
const db = admin.firestore();

// GET /api/parcelas — listar parcelas del usuario
async function listar(req, res) {
  const snap = await db.collection('parcelas')
    .where('user_id', '==', req.user.uid)
    .orderBy('created_at', 'desc')
    .limit(50)
    .get();

  const parcelas = snap.docs.map(d => ({ id: d.id, ...d.data() }));
  res.json({ parcelas });
}

// POST /api/parcelas — guardar nueva parcela + resultado
async function guardar(req, res) {
  const { poligono, cultivo, modo, resultado } = req.body;

  // Guardar parcela
  const parcelaRef = await db.collection('parcelas').add({
    user_id: req.user.uid,
    poligono,
    cultivo,
    modo: modo || 'agro',
    created_at: admin.firestore.FieldValue.serverTimestamp()
  });

  // Guardar resultado asociado
  if (resultado) {
    await db.collection('resultados').add({
      parcela_id: parcelaRef.id,
      user_id: req.user.uid,
      ...resultado,
      created_at: admin.firestore.FieldValue.serverTimestamp()
    });
  }

  res.json({ id: parcelaRef.id, mensaje: 'Parcela guardada' });
}

// DELETE /api/parcelas/:id
async function eliminar(req, res) {
  const { id } = req.params;
  const doc = await db.collection('parcelas').doc(id).get();

  if (!doc.exists || doc.data().user_id !== req.user.uid) {
    return res.status(404).json({ error: 'Parcela no encontrada' });
  }

  await db.collection('parcelas').doc(id).delete();
  res.json({ mensaje: 'Parcela eliminada' });
}

module.exports = { listar, guardar, eliminar };
```

### 6. Ruta: alertas (`routes/alertas.js`)

```javascript
const admin = require('firebase-admin');
const mockAlertas = require('../mock/alertas.json');
const db = admin.firestore();

module.exports = async function alertas(req, res) {
  const { lat, lng, radio_km = 50 } = req.query;

  try {
    const snap = await db.collection('alertas')
      .where('activa', '==', true)
      .orderBy('created_at', 'desc')
      .limit(20)
      .get();

    let alertas = snap.docs.map(d => ({ id: d.id, ...d.data() }));

    // Filtrar por proximidad si se pasan coordenadas
    if (lat && lng) {
      alertas = alertas.filter(a => {
        const dist = distanciaKm(parseFloat(lat), parseFloat(lng), a.lat, a.lng);
        return dist <= parseFloat(radio_km);
      });
    }

    // Fallback al mock si Firestore está vacío
    if (!alertas.length) alertas = mockAlertas;

    res.json({ alertas });
  } catch (e) {
    res.json({ alertas: mockAlertas, _fallback: true });
  }
};

function distanciaKm(lat1, lon1, lat2, lon2) {
  const R = 6371;
  const dLat = (lat2 - lat1) * Math.PI / 180;
  const dLon = (lon2 - lon1) * Math.PI / 180;
  const a = Math.sin(dLat/2) ** 2 +
            Math.cos(lat1 * Math.PI/180) * Math.cos(lat2 * Math.PI/180) *
            Math.sin(dLon/2) ** 2;
  return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
}
```

### 7. Gateway principal (`gateway.js`)

```javascript
const functions = require('@google-cloud/functions-framework');
const admin = require('firebase-admin');
const express = require('express');
const cors = require('cors');

const verificarAuth = require('./middleware/auth');
const analizar = require('./routes/analizar');
const { listar, guardar, eliminar } = require('./routes/parcelas');
const alertas = require('./routes/alertas');

admin.initializeApp();

const app = express();
app.use(cors({ origin: '*' }));
app.use(express.json());

// Health check — sin auth
app.get('/api/health', (req, res) => {
  res.json({
    status: 'ok',
    version: '1.0',
    modulos: {
      motor: process.env.MOTOR_URL ? 'conectado' : 'mock',
      gemini: process.env.GEMINI_URL ? 'conectado' : 'mock'
    }
  });
});

// Rutas protegidas
app.post('/api/analizar', verificarAuth, analizar);
app.get('/api/parcelas', verificarAuth, listar);
app.post('/api/parcelas', verificarAuth, guardar);
app.delete('/api/parcelas/:id', verificarAuth, eliminar);
app.get('/api/alertas', verificarAuth, alertas);

functions.http('gateway', app);
```

Deploy:
```bash
gcloud functions deploy gateway \
  --runtime nodejs20 \
  --trigger-http \
  --allow-unauthenticated \
  --region us-central1 \
  --set-env-vars MOTOR_URL=URL_DEV2,GEMINI_URL=URL_DEV3

# Guardar la URL del gateway — es lo que recibe la app móvil
```

### 8. Tests de integración (`tests/integracion.test.js`)

```javascript
const axios = require('axios');

const BASE = process.env.GATEWAY_URL || 'http://localhost:8080';

// Parcela de prueba real en San Julián, Santa Cruz
const PARCELA_TEST = {
  poligono: [
    [-17.4823, -63.2514],
    [-17.4831, -63.2514],
    [-17.4831, -63.2498],
    [-17.4823, -63.2498],
    [-17.4823, -63.2514]
  ],
  cultivo: "soya",
  modo: "agro"
};

describe('SombraIA Gateway', () => {
  test('Health check responde OK', async () => {
    const { data } = await axios.get(`${BASE}/api/health`);
    expect(data.status).toBe('ok');
  });

  test('POST /api/analizar devuelve puntos de plantación', async () => {
    const { data } = await axios.post(`${BASE}/api/analizar`, PARCELA_TEST, {
      headers: { Authorization: 'Bearer test_token' }
    });
    expect(data.puntos).toBeDefined();
    expect(data.puntos.length).toBeGreaterThan(0);
    expect(data.puntos[0]).toHaveProperty('lat');
    expect(data.puntos[0]).toHaveProperty('especie');
    expect(data.ahorro_agua_pct).toBeGreaterThan(0);
    expect(data.recomendacion_texto).toBeTruthy();
  });

  test('GET /api/alertas devuelve lista', async () => {
    const { data } = await axios.get(`${BASE}/api/alertas`, {
      headers: { Authorization: 'Bearer test_token' }
    });
    expect(data.alertas).toBeDefined();
    expect(Array.isArray(data.alertas)).toBe(true);
  });

  test('Flujo completo: analizar + guardar', async () => {
    // 1. Analizar
    const { data: resultado } = await axios.post(`${BASE}/api/analizar`, PARCELA_TEST, {
      headers: { Authorization: 'Bearer test_token' }
    });
    expect(resultado.puntos.length).toBeGreaterThan(0);

    // 2. Guardar
    const { data: guardado } = await axios.post(`${BASE}/api/parcelas`, {
      ...PARCELA_TEST,
      resultado
    }, {
      headers: { Authorization: 'Bearer test_token' }
    });
    expect(guardado.id).toBeTruthy();
  });
});
```

Correr tests:
```bash
# Tests locales con mock (sin necesitar otros módulos)
NODE_ENV=development npx jest

# Tests contra el gateway deployado
GATEWAY_URL=https://tu-gateway.run.app npx jest
```

### 9. Datos mock precargados para la demo

Cargar estas parcelas de ejemplo en Firestore antes de la presentación:

```javascript
// scripts/cargar_demo.js
const admin = require('firebase-admin');
admin.initializeApp();
const db = admin.firestore();

const PARCELAS_DEMO = [
  {
    user_id: 'demo_user',
    nombre: 'Parcela San Julián — Soya',
    poligono: [[-17.4823,-63.2514],[-17.4831,-63.2514],[-17.4831,-63.2498],[-17.4823,-63.2498]],
    cultivo: 'soya',
    modo: 'agro',
    created_at: admin.firestore.FieldValue.serverTimestamp()
  },
  {
    user_id: 'demo_user',
    nombre: 'Zona quemada — Warnes',
    poligono: [[-17.5100,-63.1800],[-17.5200,-63.1800],[-17.5200,-63.1700],[-17.5100,-63.1700]],
    cultivo: 'reforestacion',
    modo: 'incendio',
    created_at: admin.firestore.FieldValue.serverTimestamp()
  }
];

async function cargar() {
  for (const p of PARCELAS_DEMO) {
    await db.collection('parcelas').add(p);
    console.log(`Cargada: ${p.nombre}`);
  }
}

cargar();
```

```bash
node scripts/cargar_demo.js
```

---

## Resumen de endpoints — para el equipo de app

| Método | Endpoint | Descripción |
|---|---|---|
| GET | `/api/health` | Estado del sistema |
| POST | `/api/analizar` | Análisis de parcela completo |
| GET | `/api/parcelas` | Listar parcelas del usuario |
| POST | `/api/parcelas` | Guardar parcela + resultado |
| DELETE | `/api/parcelas/:id` | Eliminar parcela |
| GET | `/api/alertas` | Alertas de incendios activas |

**URL base:** publicar en el canal del equipo cuando esté deployado.

---

## Dependencias

- **Necesitás de Dev 1:** credenciales Firebase, `serviceAccountKey.json`
- **Necesitás de Dev 2:** `mock_resultado.json` el día 1, URL de Cloud Run después
- **Necesitás de Dev 3:** URL de Cloud Functions de Gemini y alertas
- **La app móvil te necesita a vos:** tu URL del gateway es el único punto de entrada

---

## Plan B para la demo

Si algo falla en vivo, el gateway tiene fallback automático a los mocks. La demo **nunca va a quedar en pantalla blanca**. Antes de presentar, correr:

```bash
npx jest && echo "TODO OK — demo lista"
```
