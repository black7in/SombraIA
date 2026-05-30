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


# --- Modo agro ---

def recomendar_agro(datos: dict, puntos: list, cultivos: list) -> str:
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


def recomendar_agro_zona_quemada(datos: dict, puntos: list) -> str:
    especies_txt = ", ".join(p["especie"] for p in puntos)
    return _generar(f"""
Sos un experto en recuperación de suelos agrícolas post-incendio en Santa Cruz, Bolivia.
Explicá el plan de recuperación para este terreno afectado que el dueño quiere volver a cultivar.
Lenguaje simple, máximo 4 oraciones, como si le hablaras al agricultor.

Situación:
- Zona afectada por incendio reciente
- NDVI actual: {datos['ndvi']} (muy bajo = suelo dañado)
- Temperatura del suelo: {datos['temp_suelo_actual']}°C
- Árboles pioneros recomendados: {datos['arboles_sugeridos']}
- Especies: {especies_txt}

Incluí: qué hacer primero, por qué estas especies ayudan al suelo y qué esperar en 12 meses.
Respondé solo con el texto, sin títulos.
""".strip())


# --- Modo ambiental ---

def recomendar_ambiental(datos: dict, puntos: list) -> str:
    arboles_txt = "\n".join(
        f"- {p['especie']} al {p['posicion']}, a {p['distancia_borde_m']}m del borde"
        for p in puntos
    )
    return _generar(f"""
Sos un especialista en reforestación y medio ambiente en Santa Cruz, Bolivia.
Explicá a esta persona por qué estos árboles son la mejor elección para su terreno
y qué impacto van a tener. Usá lenguaje simple y entusiasta. Máximo 4 oraciones.

Datos del terreno:
- Temperatura del suelo: {datos['temp_suelo_actual']}°C
- Horas de sol intenso por día: {datos['horas_criticas_dia']} horas
- NDVI actual (salud del suelo): {datos['ndvi']}
- Árboles recomendados: {datos['arboles_sugeridos']}
- Cobertura de sombra proyectada: {datos['cobertura_sombra_pct']}% del terreno
- CO2 que van a capturar por año: {datos['co2_estimado_kg_anual']} kg
- Temperatura proyectada con sombra: {datos['temp_suelo_proyectada']}°C

Árboles específicos:
{arboles_txt}

Destacá el impacto ambiental real y por qué son especies nativas valiosas para la región.
Respondé solo con el texto, sin títulos ni listas.
""".strip())


def recomendar_ambiental_zona_quemada(datos: dict, puntos: list) -> str:
    especies_txt = ", ".join(p["especie"] for p in puntos)
    return _generar(f"""
Sos un especialista en reforestación post-incendio en Santa Cruz, Bolivia.
Explicá el plan de recuperación ambiental para este terreno quemado.
Lenguaje simple y esperanzador, máximo 4 oraciones, como si le hablaras al dueño.

Situación:
- Terreno afectado por incendio reciente
- NDVI actual: {datos['ndvi']} (suelo muy dañado)
- Temperatura del suelo: {datos['temp_suelo_actual']}°C
- Árboles pioneros recomendados: {datos['arboles_sugeridos']}
- Especies: {especies_txt}
- CO2 que van a capturar por año una vez establecidos: {datos['co2_estimado_kg_anual']} kg

Incluí: qué hacer primero, por qué estas especies son ideales para recuperar el ecosistema
y qué transformación puede esperar en 12-24 meses.
Respondé solo con el texto, sin títulos.
""".strip())


# --- Chatbot y calendario (ambos modos) ---

def chatbot(pregunta: str, contexto: dict) -> str:
    modo = contexto.get("modo", "ambiental")
    if modo == "agro":
        ctx_txt = f"""- Cultivo: {contexto.get('cultivo', 'no registrado')}
- Árboles plantados: {', '.join(contexto.get('especies', [])) or 'no registrado'}
- Ahorro de agua: {contexto.get('ahorro_agua_pct', 0)}%"""
    else:
        ctx_txt = f"""- Tipo de terreno: uso ambiental / reforestación
- Árboles plantados: {', '.join(contexto.get('especies', [])) or 'no registrado'}
- Cobertura de sombra: {contexto.get('cobertura_sombra_pct', 0)}%
- CO2 capturado por año: {contexto.get('co2_estimado_kg_anual', 0)} kg"""

    return _generar(f"""
Sos un experto en árboles nativos y agroforestería de Santa Cruz, Bolivia.
Respondé esta pregunta de forma concisa (máximo 3 oraciones).
Usá el contexto del terreno para personalizar la respuesta.

Contexto del terreno:
{ctx_txt}

Pregunta: "{pregunta}"

Respondé directamente sin presentarte.
""".strip())


def cuidados(puntos: list, modo: str, zona_quemada: bool) -> list:
    import re, json as _json
    especies = list({p["especie"] for p in puntos})
    ctx_modo = "agroforestal (cortina en borde del cultivo)" if modo == "agro" else "plantación ambiental"
    ctx_fuego = " en zona post-incendio" if zona_quemada else ""

    texto = _generar(f"""
Sos un experto en árboles nativos de Santa Cruz, Bolivia.
Para las siguientes especies en una plantación {ctx_modo}{ctx_fuego},
generá exactamente 5 instrucciones de cuidado cortas y prácticas.

Especies: {', '.join(especies)}

Respondé ÚNICAMENTE con un JSON array de 5 strings, sin texto adicional ni markdown.
Ejemplo: ["instrucción 1", "instrucción 2", "instrucción 3", "instrucción 4", "instrucción 5"]

Incluí: riego inicial, protección/tutores, primera poda, época óptima de plantación,
señal de que el árbol se estableció correctamente.
""".strip())

    match = re.search(r'\[.*?\]', texto, re.DOTALL)
    if match:
        try:
            return _json.loads(match.group())
        except Exception:
            pass
    return [l.strip('- •\n"') for l in texto.split("\n") if l.strip()][:5]


def calendario(especies: list, municipio: str) -> str:
    return _generar(f"""
Creá un calendario mensual de plantación para estas especies en {municipio},
Santa Cruz, Bolivia. Considerá lluvias (nov-mar) y sequía (abr-oct).
Formato: mes - especie - acción. Máximo 12 líneas, una por mes relevante.

Especies: {', '.join(especies)}

Solo el calendario, sin explicaciones adicionales.
""".strip())
