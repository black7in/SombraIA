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
  process.exit(0);
}

cargar();
