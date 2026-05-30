const functions = require('@google-cloud/functions-framework');
const { generarCalendario } = require('./index');

functions.http('calendario', async (req, res) => {
  res.set('Access-Control-Allow-Origin', '*');

  const { especies, municipio = 'San Julián' } = req.query;

  if (!especies) {
    return res.status(400).json({ error: 'Parámetro especies requerido' });
  }

  const lista = especies.split(',').map(e => e.trim());
  const calendario = await generarCalendario(lista, municipio);
  res.json({ calendario });
});
