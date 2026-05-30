const functions = require('@google-cloud/functions-framework');
const admin = require('firebase-admin');
const { responderChatbot } = require('./index');

admin.initializeApp();
const db = admin.firestore();

functions.http('chatbot', async (req, res) => {
  res.set('Access-Control-Allow-Origin', '*');

  const { pregunta, parcela_id } = req.body;

  if (!pregunta) {
    return res.status(400).json({ error: 'Pregunta requerida' });
  }

  let contextoParcela = { cultivo: 'cultivo', municipio: 'Santa Cruz' };
  if (parcela_id) {
    const doc = await db.collection('parcelas').doc(parcela_id).get();
    if (doc.exists) contextoParcela = doc.data();
  }

  const respuesta = await responderChatbot(pregunta, contextoParcela);
  res.json({ respuesta });
});
