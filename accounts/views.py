from django.shortcuts import render, get_object_or_404
from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model, authenticate
from django.utils.translation import gettext_lazy as _
from django.db import models
from rest_framework.parsers import JSONParser, FormParser, MultiPartParser
from django.views.generic import TemplateView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy

from .models import OTP
from .serializers import (
    UserSerializer, UserProfileUpdateSerializer, PasswordChangeSerializer,
    RegisterSerializer, OTPVerificationSerializer, OTPRequestSerializer
)
from .utils import create_otp, send_otp_email, verify_otp

User = get_user_model()


class RegisterView(generics.CreateAPIView):
    """
    API view for user registration.
    """
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]


class OTPVerificationView(APIView):
    """
    API view for OTP verification.
    """
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        """
        Verify an OTP and return tokens if valid.
        """
        serializer = OTPVerificationSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data.get('email')
            
            try:
                user = User.objects.get(email=email)
                
                # Generate tokens
                refresh = RefreshToken.for_user(user)
                
                return Response({
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                    'user': UserSerializer(user).data
                }, status=status.HTTP_200_OK)
            except User.DoesNotExist:
                return Response({
                    'error': _('User not found.')
                }, status=status.HTTP_404_NOT_FOUND)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class OTPRequestView(APIView):
    """
    API view for requesting an OTP.
    """
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        """
        Request an OTP for login.
        """
        serializer = OTPRequestSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data.get('email')
            
            # Create and send OTP
            otp = create_otp(email)
            send_otp_email(email, otp.code, is_verification=False)
            
            return Response({
                'message': _('OTP sent successfully.')
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserProfileView(generics.RetrieveAPIView):
    """
    API view for retrieving a user's profile.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        """
        Get the user object.
        """
        return self.request.user


class UserProfileUpdateView(generics.UpdateAPIView):
    """
    API view for updating a user's profile.
    """
    serializer_class = UserProfileUpdateSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        """
        Get the user object.
        """
        return self.request.user


class PasswordChangeView(APIView):
    """
    API view for changing a user's password.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        """
        Change a user's password.
        """
        serializer = PasswordChangeSerializer(data=request.data)
        if serializer.is_valid():
            user = request.user
            
            # Check old password
            if not user.check_password(serializer.validated_data.get('old_password')):
                return Response({
                    'old_password': [_('Wrong password.')]
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Set new password
            user.set_password(serializer.validated_data.get('new_password'))
            user.save()
            
            return Response({
                'message': _('Password changed successfully.')
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserDetailView(generics.RetrieveAPIView):
    """
    API view for retrieving a user's profile by ID.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]


class UserSearchView(generics.ListAPIView):
    """
    API view for searching users by username.
    """
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """
        Filter users by username.
        """
        username = self.request.query_params.get('username', '')
        if username:
            return User.objects.filter(username__icontains=username, is_active=True, is_deleted=False)
        return User.objects.none()


class LoginAPIView(APIView):
    """
    API view for user login.
    """
    permission_classes = [permissions.AllowAny]
    parser_classes = [JSONParser, FormParser, MultiPartParser]
    
    def post(self, request):
        """
        Authenticate user and return tokens if valid.
        """
        import logging
        import traceback
        logger = logging.getLogger(__name__)
        
        try:
            logger.debug(f"Request Content-Type: {request.content_type}")
            logger.debug(f"Request body: {request.body}")
            logger.debug(f"Request data: {request.data}")
            logger.debug(f"Request POST: {request.POST}")
            
            # Try to get credentials from request.data (JSON), or from request.POST (form data)
            if request.data:
                username = request.data.get('username')
                password = request.data.get('password')
            else:
                username = request.POST.get('username')
                password = request.POST.get('password')
            
            logger.debug(f"Login attempt for username: {username}")  # Debug
            
            if not username or not password:
                error_msg = 'Please provide both username/email and password.'
                logger.debug(f"Error: {error_msg}")
                return Response({
                    'error': _(error_msg)
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Try to find user by username or email
            user = None
            try:
                # First try exact username match
                try:
                    user = User.objects.get(username=username)
                    logger.debug(f"Found user by username: {user.username}")  # Debug
                except User.DoesNotExist:
                    # If not found, try email
                    try:
                        user = User.objects.get(email=username)
                        logger.debug(f"Found user by email: {user.email}")  # Debug
                    except User.DoesNotExist:
                        # If still not found, try case-insensitive username match
                        try:
                            user = User.objects.get(username__iexact=username)
                            logger.debug(f"Found user by case-insensitive username: {user.username}")  # Debug
                        except (User.DoesNotExist, User.MultipleObjectsReturned):
                            # If still not found or multiple matches, return error
                            logger.debug(f"No user found for: {username}")  # Debug
                            return Response({
                                'error': _('Invalid username/email or password.')
                            }, status=status.HTTP_401_UNAUTHORIZED)
                
                # Check password
                if user.check_password(password):
                    if user.is_deleted:
                        return Response({
                            'error': _('This account has been deactivated.')
                        }, status=status.HTTP_401_UNAUTHORIZED)
                    
                    # Generate tokens
                    refresh = RefreshToken.for_user(user)
                    
                    # Create Django session for the user
                    from django.contrib.auth import login
                    from django.contrib.auth import get_backends
                    backends = get_backends()
                    logger.debug(f"Available authentication backends: {[f'{b.__module__}.{b.__class__.__name__}' for b in backends]}")
                    backend = backends[0]  # Use the first backend
                    backend_path = f"{backend.__module__}.{backend.__class__.__name__}"
                    logger.debug(f"Using authentication backend: {backend_path}")
                    user.backend = backend_path
                    login(request, user)
                    
                    logger.debug(f"Login successful for user: {user.username}")  # Debug
                    
                    return Response({
                        'refresh': str(refresh),
                        'access': str(refresh.access_token),
                        'user': UserSerializer(user).data
                    }, status=status.HTTP_200_OK)
                else:
                    logger.debug(f"Invalid password for user: {user.username}")  # Debug
                    return Response({
                        'error': _('Invalid username/email or password.')
                    }, status=status.HTTP_401_UNAUTHORIZED)
                    
            except Exception as e:
                logger.debug(f"Exception in user lookup: {str(e)}")  # Debug
                return Response({
                    'error': _('Invalid username/email or password.')
                }, status=status.HTTP_401_UNAUTHORIZED)
        except Exception as e:
            logger.error(f"Exception during login: {str(e)}")
            logger.error(traceback.format_exc())
            return Response({
                'error': _('Login failed. Please try again later.')
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ProfileView(LoginRequiredMixin, DetailView):
    """
    View for the user profile page.
    """
    model = User
    template_name = 'accounts/profile.html'
    context_object_name = 'user'
    login_url = reverse_lazy('login')
    
    def get_object(self, queryset=None):
        """
        Get the user object. If no pk is provided in the URL, return the current user.
        """
        if 'pk' in self.kwargs:
            return get_object_or_404(User, pk=self.kwargs['pk'])
        return self.request.user
    
    def get_context_data(self, **kwargs):
        """
        Add additional context data.
        """
        context = super().get_context_data(**kwargs)
        user = self.get_object()
        
        # Count posts
        posts_count = user.posts.count()
        
        # Count followers and following
        followers_count = user.followers.count()
        following_count = user.following.count()
        
        # Get user's posts
        posts = user.posts.filter(is_deleted=False).order_by('-created_at')
        
        # Add to context
        context.update({
            'posts_count': posts_count,
            'followers_count': followers_count,
            'following_count': following_count,
            'posts': posts,
        })
        
        return context
