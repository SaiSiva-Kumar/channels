from django.apps import AppConfig
import firebase_admin
from firebase_admin import credentials


class EndPointMiddlewareConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'end_point_middleware'

    def ready(self):
        cred_path = "E:/Downloads/sign-in-or-sign-up-58b7f-firebase-adminsdk-fbsvc-43dab7dd86.json"
        if not firebase_admin._apps:
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred)
            print("firebase started")