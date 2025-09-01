from django.apps import AppConfig

class AuthAppConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "auth_app"

    def ready(self):
        # Import firebase initialization
        from .firebase_app import initialize_firebase
        initialize_firebase()
        print("Firebase ready() called from AuthAppConfig")
        

class AccountsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "accounts"

    def ready(self):
        # Import firebase initialization
        from . import firebase_app