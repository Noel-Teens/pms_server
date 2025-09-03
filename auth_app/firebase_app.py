import json
from django.conf import settings
import firebase_admin
from firebase_admin import credentials

def initialize_firebase():
    if not firebase_admin._apps:
        cred_data = getattr(settings, "FIREBASE_SERVICE_KEY", None)
        if not cred_data:
            raise RuntimeError("FIREBASE_SERVICE_KEY is not set in environment variables")

        try:
            # Parse the JSON string from environment
            cred_dict = json.loads(cred_data)
            cred = credentials.Certificate(cred_dict)
            firebase_admin.initialize_app(cred)
        except json.JSONDecodeError:
            raise RuntimeError("FIREBASE_SERVICE_KEY is not valid JSON")
        except Exception as e:
            raise RuntimeError(f"Failed to initialize Firebase: {e}")
