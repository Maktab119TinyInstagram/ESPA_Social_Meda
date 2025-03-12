from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.utils.translation import gettext_lazy as _

from .models import OTP
from .utils import create_otp, send_otp_email, verify_otp

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for the User model.
    """
    followers_count = serializers.SerializerMethodField()
    following_count = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'phone', 'bio', 'profile_picture', 'location', 'website',
            'date_joined', 'followers_count', 'following_count'
        ]
        read_only_fields = ['id', 'date_joined', 'followers_count', 'following_count']
    
    def get_followers_count(self, obj):
        """
        Get the number of followers for this user.
        """
        return obj.followers.count()
    
    def get_following_count(self, obj):
        """
        Get the number of users this user is following.
        """
        return obj.following.count()


class UserProfileUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating user profile information.
    """
    class Meta:
        model = User
        fields = [
            'first_name', 'last_name', 'phone', 'bio',
            'profile_picture', 'location', 'website'
        ]


class PasswordChangeSerializer(serializers.Serializer):
    """
    Serializer for changing a user's password.
    """
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)
    
    def validate_new_password(self, value):
        """
        Validate the new password.
        """
        validate_password(value)
        return value


class RegisterSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration.
    """
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)
    
    class Meta:
        model = User
        fields = [
            'username', 'email', 'password', 'password2',
            'first_name', 'last_name'
        ]
        extra_kwargs = {
            'first_name': {'required': True},
            'last_name': {'required': True},
            'email': {'required': True}
        }
    
    def validate(self, attrs):
        """
        Validate that the passwords match.
        """
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": _("Password fields didn't match.")})
        return attrs
    
    def create(self, validated_data):
        """
        Create a new user with the validated data.
        """
        # Remove password2 from the validated data
        validated_data.pop('password2')
        
        # Create the user
        user = User.objects.create_user(**validated_data)
        
        # Create and send OTP for email verification
        otp = create_otp(user.email)
        send_otp_email(user.email, otp.code, is_verification=True)
        
        return user


class OTPVerificationSerializer(serializers.Serializer):
    """
    Serializer for OTP verification.
    """
    email = serializers.EmailField(required=True)
    code = serializers.CharField(required=True, min_length=6, max_length=6)
    
    def validate(self, attrs):
        """
        Validate the OTP.
        """
        email = attrs.get('email')
        code = attrs.get('code')
        
        if not verify_otp(email, code):
            raise serializers.ValidationError(_("Invalid or expired OTP."))
        
        return attrs


class OTPRequestSerializer(serializers.Serializer):
    """
    Serializer for requesting an OTP.
    """
    email = serializers.EmailField(required=True)
    
    def validate_email(self, value):
        """
        Validate that the email exists in the system.
        """
        try:
            User.objects.get(email=value)
        except User.DoesNotExist:
            raise serializers.ValidationError(_("No user found with this email address."))
        
        return value
    
    def create(self, validated_data):
        """
        Create a new OTP and send it to the user.
        """
        email = validated_data.get('email')
        
        # Create and send OTP
        otp = create_otp(email)
        send_otp_email(email, otp.code, is_verification=False)
        
        return validated_data 