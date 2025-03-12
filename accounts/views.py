from django.shortcuts import render
from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

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
