# Módulo 1 — Infraestructura base
**Dev 1 · SombraIA · Hackathon 2025**

---

## Tu rol en el proyecto

Eres el desbloqueador del equipo. Sin tu módulo, nadie puede arrancar. Tu prioridad es terminar el setup básico el **día 1 en la mañana** y publicar las credenciales y URLs para los demás devs.

---

## Stack que usás

| Herramienta | Para qué |
|---|---|
| Google Cloud Platform (GCP) | Proyecto base, credenciales, facturación |
| Firebase Auth | Autenticación con Google Login |
| Firestore | Base de datos principal (usuarios, parcelas, resultados) |
| Supabase | Queries geoespaciales con PostGIS |
| GitHub | Repositorio compartido del equipo |

---

## Tareas en orden

### 1. Crear proyecto GCP

1. Ir a [console.cloud.google.com](https://console.cloud.google.com)
2. Crear nuevo proyecto: `sombraia-hackathon`
3. Activar las siguientes APIs:
   - Firebase Authentication API
   - Cloud Firestore API
   - Cloud Run API
   - Earth Engine API
   - Vertex AI API
   - Maps JavaScript API
4. Crear cuenta de servicio con rol `Editor`
5. Descargar el archivo `serviceAccountKey.json`
6. **Compartir inmediatamente** con el equipo via canal seguro (no subir a GitHub)

### 2. Configurar Firebase Auth

```bash
# Instalar Firebase CLI
npm install -g firebase-tools

# Login
firebase login

# Inicializar proyecto
firebase init
# Seleccionar: Firestore, Authentication, Functions
# Proyecto: sombraia-hackathon
```

Activar proveedor de autenticación:
1. Firebase Console → Authentication → Sign-in method
2. Activar **Google**
3. Guardar el `Web client ID` — lo necesitan Dev 3 y Dev 4

Configuración de tokens JWT en `functions/index.js`:

```javascript
const admin = require('firebase-admin');
admin.initializeApp();

// Middleware para verificar token en cada request
exports.verifyToken = async (req, res, next) => {
  const token = req.headers.authorization?.split('Bearer ')[1];
  if (!token) return res.status(401).json({ error: 'Sin token' });
  try {
    const decoded = await admin.auth().verifyIdToken(token);
    req.user = decoded;
    next();
  } catch (e) {
    return res.status(401).json({ error: 'Token inválido' });
  }
};
```

### 3. Esquema de Firestore

Crear las siguientes colecciones con los campos indicados.

**Colección `users`**
```json
{
  "uid": "string (Firebase UID)",
  "nombre": "string",
  "email": "string",
  "created_at": "timestamp",
  "departamento": "Santa Cruz"
}
```

**Colección `parcelas`**
```json
{
  "id": "string (auto)",
  "user_id": "string (ref a users)",
  "nombre": "string",
  "poligono": [[lat, lng], [lat, lng], "..."],
  "cultivo": "string",
  "modo": "agro | incendio",
  "area_ha": "number",
  "created_at": "timestamp"
}
```

**Colección `resultados`**
```json
{
  "id": "string (auto)",
  "parcela_id": "string (ref a parcelas)",
  "user_id": "string",
  "puntos": [{ "lat": 0, "lng": 0, "especie": "string", "posicion": "string" }],
  "ahorro_agua_pct": "number",
  "cultivos_compatibles": ["string"],
  "recomendacion_texto": "string (generado por Gemini)",
  "ndvi": "number",
  "created_at": "timestamp"
}
```

**Colección `alertas`**
```json
{
  "id": "string (auto)",
  "tipo": "incendio | sequia",
  "lat": "number",
  "lng": "number",
  "radio_km": "number",
  "descripcion": "string",
  "activa": "boolean",
  "created_at": "timestamp"
}
```

Reglas de seguridad en `firestore.rules`:

```
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    match /users/{userId} {
      allow read, write: if request.auth.uid == userId;
    }
    match /parcelas/{parcelaId} {
      allow read, write: if request.auth != null &&
        resource.data.user_id == request.auth.uid;
    }
    match /resultados/{resultadoId} {
      allow read: if request.auth != null &&
        resource.data.user_id == request.auth.uid;
      allow write: if false; // Solo el backend escribe
    }
    match /alertas/{alertaId} {
      allow read: if request.auth != null;
      allow write: if false; // Solo Cloud Function escribe
    }
  }
}
```

### 4. Configurar Supabase (PostGIS)

1. Crear cuenta en [supabase.com](https://supabase.com) — plan gratuito
2. Crear proyecto: `sombraia`
3. Ir a SQL Editor y ejecutar:

```sql
-- Activar extensión geoespacial
CREATE EXTENSION IF NOT EXISTS postgis;

-- Tabla de parcelas con geometría
CREATE TABLE parcelas_geo (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  firestore_id TEXT NOT NULL,
  user_id TEXT NOT NULL,
  geom GEOMETRY(POLYGON, 4326) NOT NULL,
  area_ha FLOAT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Índice espacial para queries rápidas
CREATE INDEX parcelas_geo_geom_idx ON parcelas_geo USING GIST(geom);

-- Función: parcelas dentro de radio (km) de un punto
CREATE OR REPLACE FUNCTION parcelas_cercanas(
  lat FLOAT, lng FLOAT, radio_km FLOAT
)
RETURNS TABLE(firestore_id TEXT, distancia_m FLOAT) AS $$
  SELECT
    firestore_id,
    ST_Distance(
      geom::geography,
      ST_Point(lng, lat)::geography
    ) AS distancia_m
  FROM parcelas_geo
  WHERE ST_DWithin(
    geom::geography,
    ST_Point(lng, lat)::geography,
    radio_km * 1000
  )
  ORDER BY distancia_m;
$$ LANGUAGE sql;
```

4. Ir a Settings → API → copiar `URL` y `anon key`

### 5. Publicar variables de entorno para el equipo

Crear archivo `env.example` en el repositorio (sin valores reales):

```env
# GCP
GOOGLE_CLOUD_PROJECT=sombraia-hackathon
GOOGLE_APPLICATION_CREDENTIALS=./serviceAccountKey.json

# Firebase
FIREBASE_WEB_CLIENT_ID=xxx
FIREBASE_API_KEY=xxx
FIREBASE_AUTH_DOMAIN=sombraia-hackathon.firebaseapp.com
FIREBASE_PROJECT_ID=sombraia-hackathon

# Supabase
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_ANON_KEY=xxx
```

Compartir el `.env` real con los valores por canal privado del equipo.

---

## Entregable para el equipo

Al terminar, publicar en el canal del equipo:

- [ ] URL de Firestore + reglas activas
- [ ] URL de Supabase + función `parcelas_cercanas` funcionando
- [ ] `GOOGLE_CLIENT_ID` para Auth
- [ ] `serviceAccountKey.json` compartida de forma segura
- [ ] Archivo `env.example` en el repo
- [ ] Colecciones de Firestore creadas con documentos de ejemplo

---

## Dependencias

**Nadie depende de otro módulo.** Este módulo es la base — los demás te esperan a vos.

---

## Contacto de integración

Cuando Dev 2, Dev 3 o Dev 4 tengan dudas sobre la estructura de Firestore o las credenciales, ese es tu trabajo. Sos el punto de referencia técnico del equipo.
