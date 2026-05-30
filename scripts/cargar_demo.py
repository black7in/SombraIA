import firebase_admin
from firebase_admin import credentials, firestore

firebase_admin.initialize_app(credentials.ApplicationDefault())
db = firestore.client()

PARCELAS_DEMO = [
    {
        "user_id": "demo_user",
        "nombre": "Parcela San Julián — Soya",
        "poligono": [[-17.4823, -63.2514], [-17.4831, -63.2514], [-17.4831, -63.2498], [-17.4823, -63.2498]],
        "cultivo": "soya",
        "modo": "agro",
    },
    {
        "user_id": "demo_user",
        "nombre": "Zona quemada — Warnes",
        "poligono": [[-17.5100, -63.1800], [-17.5200, -63.1800], [-17.5200, -63.1700], [-17.5100, -63.1700]],
        "cultivo": "reforestacion",
        "modo": "incendio",
    },
]

for p in PARCELAS_DEMO:
    _, ref = db.collection("parcelas").add({**p, "created_at": firestore.SERVER_TIMESTAMP})
    print(f"Cargada: {p['nombre']} (id: {ref.id})")
