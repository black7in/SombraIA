const axios = require('axios');
const mockResultado = require('../mock/resultado.json');

const MOTOR_URL = process.env.MOTOR_URL || null;
const GEMINI_URL = process.env.GEMINI_URL || null;

module.exports = async function analizar(req, res) {
  const { poligono, cultivo, modo = 'agro', n_arboles = 5 } = req.body;

  if (!poligono || !cultivo) {
    return res.status(400).json({ error: 'Faltan poligono y cultivo' });
  }

  try {
    let resultadoMotor;
    if (MOTOR_URL) {
      const { data } = await axios.post(`${MOTOR_URL}/analizar`, { poligono, cultivo, modo, n_arboles });
      resultadoMotor = data;
    } else {
      console.log('[MOCK] Usando mock del motor IA');
      resultadoMotor = { ...mockResultado };
    }

    let recomendacionTexto;
    if (GEMINI_URL) {
      const { data } = await axios.post(`${GEMINI_URL}/recomendar`, { resultado_motor: resultadoMotor });
      recomendacionTexto = data.recomendacion_texto;
    } else {
      console.log('[MOCK] Usando texto de recomendación mock');
      recomendacionTexto = resultadoMotor.recomendacion_texto;
    }

    return res.json({ ...resultadoMotor, recomendacion_texto: recomendacionTexto });

  } catch (e) {
    console.error('Error en /analizar:', e.message);
    return res.json({ ...mockResultado, _fallback: true, _error: e.message });
  }
};
