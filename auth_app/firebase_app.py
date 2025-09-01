from django.conf import settings
import os
import firebase_admin
from firebase_admin import credentials

def initialize_firebase():
    if not firebase_admin._apps:
        # Try settings first
        cred_path = getattr(settings, "FIREBASE_CREDENTIALS_FILE", None)

        # If missing, resolve relative to BASE_DIR
        if not cred_path:
            cred_path = os.path.join(settings.BASE_DIR, "paper-ms-firebase-adminsdk-fbsvc-5bcb4de51e.json")


        if not os.path.exists(cred_path):
            raise RuntimeError(f"FIREBASE_CREDENTIALS_FILE missing or not found: {cred_path}")

        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred)
