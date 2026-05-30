const functions = require('@google-cloud/functions-framework');
const admin = require('firebase-admin');
const ee = require('@google/earthengine');

admin.initializeApp();
const db = admin.firestore();

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

  const fuego = ee.ImageCollection('MODIS/061/MOD14A1')
    .filterBounds(region)
    .filterDate(fechaAyer, fechaHoy)
    .select('FireMask')
    .max();

  const zonasFuego = fuego.gt(6);

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
