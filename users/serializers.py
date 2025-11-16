"""
Serializers for the users app.
"""

from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from .models import User, StudentProfile, AdminInvite, EmailVerification


class UserSerializer(serializers.ModelSerializer):
    """Base user serializer."""
    
    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'role', 'is_active', 'created_at']
        read_only_fields = ['id', 'created_at']


class StudentProfileSerializer(serializers.ModelSerializer):
    """Student profile serializer."""
    user = UserSerializer(read_only=True)
    full_name = serializers.CharField(read_only=True)
    
    class Meta:
        model = StudentProfile
        fields = [
            'id', 'user', 'jntu_no', 'name', 'company', 'lat', 'lon',
            'face_enrolled', 'reference_image_url', 'full_name', 'created_at'
        ]
        read_only_fields = ['id', 'user', 'face_enrolled', 'created_at']


class LoginSerializer(serializers.Serializer):
    """Login serializer."""
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    
    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')
        
        if email and password:
            user = authenticate(request=self.context.get('request'), username=email, password=password)
            if not user:
                raise serializers.ValidationError('Invalid email or password.')
            if not user.is_active:
                raise serializers.ValidationError('User account is disabled.')
            
            attrs['user'] = user
            return attrs
        else:
            raise serializers.ValidationError('Must include email and password.')


class UserRegistrationSerializer(serializers.ModelSerializer):
    """User registration serializer."""
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = ['email', 'first_name', 'last_name', 'password', 'password_confirm']
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Passwords don't match.")
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        user = User.objects.create_user(**validated_data)
        return user


class AdminInviteSerializer(serializers.ModelSerializer):
    """Admin invite serializer."""
    
    class Meta:
        model = AdminInvite
        fields = ['id', 'email', 'invite_code', 'expires_at', 'used', 'created_at']
        read_only_fields = ['id', 'invite_code', 'expires_at', 'used', 'created_at']


class EmailVerificationSerializer(serializers.ModelSerializer):
    """Email verification serializer."""
    
    class Meta:
        model = EmailVerification
        fields = ['id', 'user', 'token', 'expires_at', 'verified', 'created_at']
        read_only_fields = ['id', 'user', 'token', 'expires_at', 'verified', 'created_at']


class PasswordResetSerializer(serializers.Serializer):
    """Password reset serializer."""
    email = serializers.EmailField()
    
    def validate_email(self, value):
        try:
            User.objects.get(email=value)
            return value
        except User.DoesNotExist:
            raise serializers.ValidationError('No user found with this email address.')


class PasswordChangeSerializer(serializers.Serializer):
    """Password change serializer."""
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, validators=[validate_password])
    new_password_confirm = serializers.CharField(write_only=True)
    
    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError("New passwords don't match.")
        return attrs
    
    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('Old password is incorrect.')
        return value


class FaceEnrollmentSerializer(serializers.Serializer):
    """Face enrollment serializer."""
    image = serializers.ImageField()
    
    def validate_image(self, value):
        # Check file size (2MB limit)
        if value.size > 2 * 1024 * 1024:
            raise serializers.ValidationError('Image file size must be under 2MB.')
        
        # Check file type
        allowed_types = ['image/jpeg', 'image/png', 'image/jpg']
        if value.content_type not in allowed_types:
            raise serializers.ValidationError('Only JPEG and PNG images are allowed.')
        
        return value
