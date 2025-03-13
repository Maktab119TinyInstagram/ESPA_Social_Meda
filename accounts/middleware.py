from django.utils.functional import SimpleLazyObject
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.contrib.auth import login
import logging

User = get_user_model()
logger = logging.getLogger(__name__)

class JWTAuthenticationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # If user is already authenticated via session, we don't need to do anything
        if request.user.is_authenticated:
            logger.debug(f"User already authenticated via session: {request.user.username}")
            return self.get_response(request)

        # Try to authenticate with JWT
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        if auth_header.startswith('Bearer '):
            logger.debug(f"Found Bearer token in Authorization header")
            token = auth_header.split(' ')[1]
            jwt_auth = JWTAuthentication()
            try:
                validated_token = jwt_auth.get_validated_token(token)
                user = jwt_auth.get_user(validated_token)
                if user:
                    logger.debug(f"Successfully authenticated user via JWT: {user.username}")
                    # Login user to create a session
                    login(request, user)
                    request.user = user
                else:
                    logger.debug("JWT token validated but user not found")
            except Exception as e:
                logger.debug(f"JWT authentication failed: {str(e)}")
                # If JWT authentication fails, continue with AnonymousUser
                pass
        else:
            # Check Authorization header for token
            token = request.COOKIES.get('access_token')
            if token:
                logger.debug(f"Found token in cookies")
                jwt_auth = JWTAuthentication()
                try:
                    validated_token = jwt_auth.get_validated_token(token)
                    user = jwt_auth.get_user(validated_token)
                    if user:
                        logger.debug(f"Successfully authenticated user via cookie token: {user.username}")
                        # Login user to create a session
                        login(request, user)
                        request.user = user
                    else:
                        logger.debug("Cookie token validated but user not found")
                except Exception as e:
                    logger.debug(f"Cookie token authentication failed: {str(e)}")
            else:
                logger.debug("No authentication token found in headers or cookies")

        return self.get_response(request) 