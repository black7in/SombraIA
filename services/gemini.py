import os
import vertexai
from vertexai.generative_models import GenerativeModel

_model = None


def _get_model() -> GenerativeModel:
    global _model
    if _model is None:
        vertexai.init(
            project=os.environ["GOOGLE_CLOUD_PROJECT"],
            location="us-central1",
        )
        _model = GenerativeModel("gemini-1.5-flash")
    return _model


def _generar(prompt: str) -> str:
    response = _get_model().generate_content(prompt)
    return response.candidates[0].content.parts[0].text


def recomendar(datos: dict, puntos: list, cultivos: list) -> str:
    arboles_txt = "\n".join(
        f"- {p['especie']} al {p['posicion']}, a {p['distancia_borde_m']}m del borde"
        for p in puntos
    )
    return _generar(f"""
Sos un agrónomo experto en Santa Cruz, Bolivia. Explicá la siguiente recomendación
de plantación de árboles a un agricultor local. Usá lenguaje simple y directo,
como si le hablaras en persona. Máximo 4 oraciones. No uses jerga técnica.

Datos de la parcela:
- Cultivo actual: {datos['cultivo_actual']}
- Temperatura del suelo: {datos['temp_suelo_actual']}°C
- Horas de sol crítico por día (10am-3pm): {datos['horas_criticas_dia']} horas
- NDVI (salud del suelo, 0-1): {datos['ndvi']}
- Árboles recomendados: {datos['arboles_sugeridos']}
- Ahorro de agua proyectado: {datos.get('ahorro_agua_pct', 0)}%
- Temperatura proyectada con sombra: {datos['temp_suelo_proyectada']}°C

Árboles específicos:
{arboles_txt}

Cultivos recomendados junto a los árboles: {', '.join(cultivos)}

Respondé solo con el texto de la recomendación, sin títulos ni listas.
""".strip())


def recomendar_zona_quemada(datos: dict, puntos: list) -> str:
    especies_txt = ", ".join(p["especie"] for p in puntos)
    return _generar(f"""
Sos un experto en reforestación post-incendio en Santa Cruz, Bolivia.
Explicá el plan de recuperación para esta zona afectada.
Lenguaje simple, máximo 4 oraciones, como si le hablaras al dueño del terreno.

Situación:
- Zona afectada por incendio reciente
- NDVI actual: {datos['ndvi']} (muy bajo = suelo dañado)
- Temperatura del suelo: {datos['temp_suelo_actual']}°C
- Árboles pioneros recomendados: {datos['arboles_sugeridos']}
- Especies: {especies_txt}

Incluí: qué hacer primero, por qué estas especies y qué esperar en 12 meses.
Respondé solo con el texto, sin títulos.
""".strip())


def chatbot(pregunta: str, contexto: dict) -> str:
    return _generar(f"""
Sos un agrónomo de Santa Cruz, Bolivia. Respondé esta pregunta del agricultor
sobre su parcela de forma concisa (máximo 3 oraciones). Usá el contexto de su
parcela para dar una respuesta personalizada.

Contexto de su parcela:
- Cultivo: {contexto.get('cultivo', 'no registrado')}
- Ubicación: {contexto.get('municipio', 'Santa Cruz')}
- Árboles plantados: {', '.join(contexto.get('especies', [])) or 'no registrado'}
- Último análisis: ahorro de agua {contexto.get('ahorro_agua_pct', 0)}%

Pregunta del agricultor: "{pregunta}"

Respondé directamente sin presentarte.
""".strip())


def calendario(especies: list, municipio: str) -> str:
    return _generar(f"""
Creá un calendario mensual de plantación para estas especies en {municipio},
Santa Cruz, Bolivia. Considerá lluvias (nov-mar) y sequía (abr-oct).
Formato: mes - especie - acción. Máximo 12 líneas, una por mes relevante.

Especies: {', '.join(especies)}

Solo el calendario, sin explicaciones adicionales.
""".strip())
