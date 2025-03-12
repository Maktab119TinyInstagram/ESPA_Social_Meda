from django.utils.functional import SimpleLazyObject
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.contrib.auth import login

User = get_user_model()

class JWTAuthenticationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # If user is already authenticated via session, we don't need to do anything
        if request.user.is_authenticated:
            return self.get_response(request)

        # Try to authenticate with JWT
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        if auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
            jwt_auth = JWTAuthentication()
            try:
                validated_token = jwt_auth.get_validated_token(token)
                user = jwt_auth.get_user(validated_token)
                if user:
                    # Login user to create a session
                    login(request, user)
                    request.user = user
            except Exception:
                # If JWT authentication fails, continue with AnonymousUser
                pass

        return self.get_response(request) 