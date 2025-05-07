from firebase_admin import auth
from django.http import JsonResponse

def verify_firebase_token(get_response):
    def middleware(request):
        path = request.path
        if path.startswith('/health/') or path.startswith('/public/'):
            return get_response(request)

        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return JsonResponse({"detail": "Authorization token missing or malformed."}, status=401)

        id_token = auth_header.split('Bearer ')[1]

        try:
            decoded_token = auth.verify_id_token(id_token)
            request.user_uid = decoded_token.get("uid")
        except Exception:
            return JsonResponse({"detail": "Invalid or expired token."}, status=401)

        return get_response(request)

    return middleware
