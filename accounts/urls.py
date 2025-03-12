from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    RegisterView, OTPVerificationView, OTPRequestView,
    UserProfileView, UserProfileUpdateView, PasswordChangeView,
    UserDetailView, UserSearchView, LoginAPIView
)

app_name = 'accounts'

urlpatterns = [
    # Authentication
    path('login/', LoginAPIView.as_view(), name='login'),
    path('register/', RegisterView.as_view(), name='register'),
    path('otp/verify/', OTPVerificationView.as_view(), name='otp-verify'),
    path('otp/request/', OTPRequestView.as_view(), name='otp-request'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    
    # User profile
    path('profile/', UserProfileView.as_view(), name='profile'),
    path('profile/update/', UserProfileUpdateView.as_view(), name='profile-update'),
    path('profile/password-change/', PasswordChangeView.as_view(), name='password-change'),
    
    # User details
    path('users/<int:pk>/', UserDetailView.as_view(), name='user-detail'),
    path('users/search/', UserSearchView.as_view(), name='user-search'),
] 