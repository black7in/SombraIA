import os
import ee
from dotenv import load_dotenv
load_dotenv()
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import firebase_admin
from firebase_admin import credentials
from google.oauth2 import service_account

from routers import analizar, parcelas, chat, auth

_EE_SCOPES = [
    "https://www.googleapis.com/auth/earthengine",
    "https://www.googleapis.com/auth/cloud-platform",
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    if not firebase_admin._apps:
        firebase_admin.initialize_app(credentials.ApplicationDefault())
    key_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "./serviceAccountKey.json")
    if os.path.isfile(key_path):
        ee_creds = service_account.Credentials.from_service_account_file(
            key_path, scopes=_EE_SCOPES
        )
        ee.Initialize(credentials=ee_creds, project=os.environ["GOOGLE_CLOUD_PROJECT"])
    yield


app = FastAPI(title="SombraAI API", version="2.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api")
app.include_router(analizar.router, prefix="/api")
app.include_router(parcelas.router, prefix="/api")
app.include_router(chat.router, prefix="/api")


@app.get("/api/health")
def health():
    return {"status": "ok", "version": "2.0"}
