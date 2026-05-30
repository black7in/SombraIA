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

    if (lat && lng) {
      alertas = alertas.filter(a => {
        const dist = distanciaKm(parseFloat(lat), parseFloat(lng), a.lat, a.lng);
        return dist <= parseFloat(radio_km);
      });
    }

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
