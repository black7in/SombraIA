const axios = require('axios');

const BASE = process.env.GATEWAY_URL || 'http://localhost:8080';

const PARCELA_TEST = {
  poligono: [
    [-17.4823, -63.2514],
    [-17.4831, -63.2514],
    [-17.4831, -63.2498],
    [-17.4823, -63.2498],
    [-17.4823, -63.2514]
  ],
  cultivo: 'soya',
  modo: 'agro'
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
    const { data: resultado } = await axios.post(`${BASE}/api/analizar`, PARCELA_TEST, {
      headers: { Authorization: 'Bearer test_token' }
    });
    expect(resultado.puntos.length).toBeGreaterThan(0);

    const { data: guardado } = await axios.post(`${BASE}/api/parcelas`, {
      ...PARCELA_TEST,
      resultado
    }, {
      headers: { Authorization: 'Bearer test_token' }
    });
    expect(guardado.id).toBeTruthy();
  });
});
