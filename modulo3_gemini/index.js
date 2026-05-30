const { generarTexto } = require('./gemini_service');
const { promptRecomendacion, promptZonaQuemada, promptChatbot, promptCalendario } = require('./prompts');

async function generarRecomendacion(resultadoMotor) {
  const datos = {
    ...resultadoMotor.datos_para_gemini,
    puntos: resultadoMotor.puntos,
    ahorro_agua_pct: resultadoMotor.ahorro_agua_pct,
    cultivos_compatibles: resultadoMotor.cultivos_compatibles
  };

  const prompt = datos.zona_quemada
    ? promptZonaQuemada(datos)
    : promptRecomendacion(datos);

  return (await generarTexto(prompt)).trim();
}

async function responderChatbot(pregunta, contextoParcela) {
  return await generarTexto(promptChatbot(pregunta, contextoParcela));
}

async function generarCalendario(especies, municipio = 'San Julián') {
  return await generarTexto(promptCalendario(especies, municipio));
}

module.exports = { generarRecomendacion, responderChatbot, generarCalendario };
