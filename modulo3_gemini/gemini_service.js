const { VertexAI } = require('@google-cloud/vertexai');

const vertexAI = new VertexAI({
  project: process.env.GOOGLE_CLOUD_PROJECT,
  location: 'us-central1'
});

const modelo = vertexAI.getGenerativeModel({
  model: 'gemini-1.5-flash',
});

async function generarTexto(prompt) {
  const resultado = await modelo.generateContent(prompt);
  const respuesta = resultado.response;
  return respuesta.candidates[0].content.parts[0].text;
}

module.exports = { generarTexto };
