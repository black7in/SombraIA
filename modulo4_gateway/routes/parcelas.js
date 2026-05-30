const admin = require('firebase-admin');
const db = admin.firestore();

async function listar(req, res) {
  const snap = await db.collection('parcelas')
    .where('user_id', '==', req.user.uid)
    .orderBy('created_at', 'desc')
    .limit(50)
    .get();

  const parcelas = snap.docs.map(d => ({ id: d.id, ...d.data() }));
  res.json({ parcelas });
}

async function guardar(req, res) {
  const { poligono, cultivo, modo, resultado } = req.body;

  const parcelaRef = await db.collection('parcelas').add({
    user_id: req.user.uid,
    poligono,
    cultivo,
    modo: modo || 'agro',
    created_at: admin.firestore.FieldValue.serverTimestamp()
  });

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
