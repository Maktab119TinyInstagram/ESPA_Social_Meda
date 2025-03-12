from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.db.models import Q

User = get_user_model()

class EmailOrUsernameModelBackend(ModelBackend):
    """
    Authentication backend that allows users to authenticate with either username or email.
    """
    def authenticate(self, request, username=None, password=None, **kwargs):
        # If username parameter is provided, try to authenticate with either username or email
        if username is not None:
            try:
                # Check if user exists with this username or email
                user = User.objects.get(
                    Q(username=username) | Q(email=username)
                )
                
                # Check password
                if user.check_password(password) and self.user_can_authenticate(user):
                    return user
            except User.DoesNotExist:
                return None
        
        # If email parameter is provided (from the custom LoginAPIView)
        email = kwargs.get('email')
        if email is not None:
            try:
                user = User.objects.get(email=email)
                if user.check_password(password) and self.user_can_authenticate(user):
                    return user
            except User.DoesNotExist:
                return None
                
        return None 