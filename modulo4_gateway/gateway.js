const functions = require('@google-cloud/functions-framework');
const admin = require('firebase-admin');
const express = require('express');
const cors = require('cors');

const verificarAuth = require('./middleware/auth');
const analizar = require('./routes/analizar');
const { listar, guardar, eliminar } = require('./routes/parcelas');
const alertas = require('./routes/alertas');
const chat = require('./routes/chat');

admin.initializeApp();

const app = express();
app.use(cors({ origin: '*' }));
app.use(express.json());

app.get('/api/health', (req, res) => {
  res.json({
    status: 'ok',
    version: '1.0',
    modulos: {
      motor: process.env.MOTOR_URL ? 'conectado' : 'mock',
      gemini: process.env.GEMINI_URL ? 'conectado' : 'mock'
    }
  });
});

app.post('/api/analizar', verificarAuth, analizar);
app.get('/api/parcelas', verificarAuth, listar);
app.post('/api/parcelas', verificarAuth, guardar);
app.delete('/api/parcelas/:id', verificarAuth, eliminar);
app.get('/api/alertas', verificarAuth, alertas);
app.post('/api/chat', verificarAuth, chat);

functions.http('gateway', app);
