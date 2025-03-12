from django.shortcuts import render
from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model, authenticate
from django.utils.translation import gettext_lazy as _
from django.db import models

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
    
    def post(self, request):
        """
        Authenticate user and return tokens if valid.
        """
        username = request.data.get('username')
        password = request.data.get('password')
        
        if not username or not password:
            return Response({
                'error': _('Please provide both username/email and password.')
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Try to find user by username or email
        try:
            user = User.objects.get(
                models.Q(username=username) | models.Q(email=username)
            )
            
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
                login(request, user)
                
                return Response({
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                    'user': UserSerializer(user).data
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'error': _('Invalid username/email or password.')
                }, status=status.HTTP_401_UNAUTHORIZED)
                
        except User.DoesNotExist:
            return Response({
                'error': _('Invalid username/email or password.')
            }, status=status.HTTP_401_UNAUTHORIZED)
