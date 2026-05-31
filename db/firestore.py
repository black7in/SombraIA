import os
import firebase_admin
from google.cloud import firestore as gf
from google.oauth2 import service_account


_SCOPES = ["https://www.googleapis.com/auth/datastore"]


def get_db():
    db_id = os.getenv("FIRESTORE_DATABASE_ID", "(default)")
    key_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "./serviceAccountKey.json")
    project = os.getenv("GOOGLE_CLOUD_PROJECT")

    if os.path.isfile(key_path):
        creds = service_account.Credentials.from_service_account_file(
            key_path, scopes=_SCOPES
        )
    else:
        app = firebase_admin.get_app()
        creds = app.credential.get_credential()

    return gf.Client(project=project, credentials=creds, database=db_id)
