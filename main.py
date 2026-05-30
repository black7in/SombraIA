import os
import ee
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import firebase_admin
from firebase_admin import credentials

from routers import analizar, parcelas, chat


@asynccontextmanager
async def lifespan(app: FastAPI):
    if not firebase_admin._apps:
        firebase_admin.initialize_app(credentials.ApplicationDefault())
    try:
        ee.Initialize(project=os.environ["GOOGLE_CLOUD_PROJECT"])
    except Exception:
        pass  # sin credenciales en dev local
    yield


app = FastAPI(title="SombraIA API", version="1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(analizar.router, prefix="/api")
app.include_router(parcelas.router, prefix="/api")
app.include_router(chat.router, prefix="/api")


@app.get("/api/health")
def health():
    return {"status": "ok", "version": "1.0"}
