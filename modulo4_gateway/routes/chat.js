const axios = require('axios');

const GEMINI_URL = process.env.GEMINI_URL || null;

module.exports = async function chat(req, res) {
  const { pregunta, parcela_id } = req.body;

  if (!pregunta) {
    return res.status(400).json({ error: 'Pregunta requerida' });
  }

  if (!GEMINI_URL) {
    return res.json({
      respuesta: 'El servicio de chatbot estará disponible pronto. Mientras tanto, consultá las recomendaciones de tu parcela.',
      _mock: true
    });
  }

  try {
    const { data } = await axios.post(`${GEMINI_URL}/chatbot`, { pregunta, parcela_id });
    res.json(data);
  } catch (e) {
    res.status(500).json({ error: 'Error al contactar el chatbot' });
  }
};
