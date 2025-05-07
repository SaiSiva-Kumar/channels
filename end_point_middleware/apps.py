import os
import json
import firebase_admin
from firebase_admin import credentials
from django.apps import AppConfig


class EndPointMiddlewareConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'end_point_middleware'

    def ready(self):
        if not firebase_admin._apps:
            firebase_json = os.environ.get("FIREBASE_CREDENTIALS_JSON")
            if firebase_json:
                firebase_dict = json.loads(firebase_json)
                cred = credentials.Certificate(firebase_dict)
                firebase_admin.initialize_app(cred)
                print("Firebase initialized via environment variable")
            else:
                print("Firebase credentials not found in environment variables")
