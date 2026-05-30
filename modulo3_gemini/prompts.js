function promptRecomendacion(datos) {
  return `
Sos un agrónomo experto en Santa Cruz, Bolivia. Explicá la siguiente recomendación
de plantación de árboles a un agricultor local. Usá lenguaje simple y directo,
como si le hablaras en persona. Máximo 4 oraciones. No uses jerga técnica.

Datos de la parcela:
- Cultivo actual: ${datos.cultivo_actual}
- Temperatura del suelo: ${datos.temp_suelo_actual}°C
- Horas de sol crítico por día (10am-3pm): ${datos.horas_criticas_dia} horas
- NDVI (salud del suelo, 0-1): ${datos.ndvi}
- Árboles recomendados: ${datos.arboles_sugeridos}
- Ahorro de agua proyectado: ${datos.ahorro_agua_pct}%
- Temperatura proyectada con sombra: ${datos.temp_suelo_proyectada}°C

Árboles específicos:
${datos.puntos.map(p => `- ${p.especie} al ${p.posicion}, a ${p.distancia_borde_m}m del borde`).join('\n')}

Cultivos recomendados junto a los árboles: ${datos.cultivos_compatibles.join(', ')}

Respondé solo con el texto de la recomendación, sin títulos ni listas.
`;
}

function promptZonaQuemada(datos) {
  return `
Sos un experto en reforestación post-incendio en Santa Cruz, Bolivia.
Explicá el plan de recuperación para esta zona afectada.
Lenguaje simple, máximo 4 oraciones, como si le hablaras al dueño del terreno.

Situación:
- Zona afectada por incendio reciente
- NDVI actual: ${datos.ndvi} (muy bajo = suelo dañado)
- Temperatura del suelo: ${datos.temp_suelo_actual}°C
- Árboles pioneros recomendados: ${datos.arboles_sugeridos}
- Especies: ${datos.puntos.map(p => p.especie).join(', ')}

Incluí: qué hacer primero, por qué estas especies y qué esperar en 12 meses.
Respondé solo con el texto, sin títulos.
`;
}

function promptChatbot(pregunta, contextoParcela) {
  return `
Sos un agrónomo de Santa Cruz, Bolivia. Respondé esta pregunta del agricultor
sobre su parcela de forma concisa (máximo 3 oraciones). Usá el contexto de su
parcela para dar una respuesta personalizada.

Contexto de su parcela:
- Cultivo: ${contextoParcela.cultivo}
- Ubicación: ${contextoParcela.municipio || 'Santa Cruz'}
- Árboles plantados: ${contextoParcela.especies?.join(', ') || 'no registrado'}
- Último análisis: ahorro de agua ${contextoParcela.ahorro_agua_pct || 0}%

Pregunta del agricultor: "${pregunta}"

Respondé directamente sin presentarte.
`;
}

function promptCalendario(especies, municipio) {
  return `
Creá un calendario mensual de plantación para estas especies en ${municipio},
Santa Cruz, Bolivia. Considerá lluvias (nov-mar) y sequía (abr-oct).
Formato: mes - especie - acción. Máximo 12 líneas, una por mes relevante.

Especies: ${especies.join(', ')}

Solo el calendario, sin explicaciones adicionales.
`;
}

module.exports = { promptRecomendacion, promptZonaQuemada, promptChatbot, promptCalendario };
