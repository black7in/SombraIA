import os
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from firebase_admin import auth

_security = HTTPBearer(auto_error=False)


def verify_token(credentials: HTTPAuthorizationCredentials = Depends(_security)):
    if os.getenv("ENV") == "development":
        return {"uid": "dev_user"}
    if not credentials:
        raise HTTPException(status_code=401, detail="Sin token")
    try:
        return auth.verify_id_token(credentials.credentials)
    except Exception:
        raise HTTPException(status_code=401, detail="Token inválido")
