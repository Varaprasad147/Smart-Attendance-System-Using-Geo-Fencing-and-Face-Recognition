"""
User models for the attendance system.
"""

import uuid
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import EmailValidator
from django.utils import timezone


class User(AbstractUser):
    """
    Custom User model with role-based access control.
    """
    ROLE_CHOICES = [
        ('superadmin', 'Super Admin'),
        ('admin', 'Admin'),
        ('student', 'Student'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True, validators=[EmailValidator()])
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='student')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Override username to use email
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']
    
    class Meta:
        db_table = 'users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
    
    def __str__(self):
        return f"{self.email} ({self.get_role_display()})"
    
    @property
    def is_superadmin(self):
        return self.role == 'superadmin'
    
    @property
    def is_admin(self):
        return self.role == 'admin'
    
    @property
    def is_student(self):
        return self.role == 'student'


class StudentProfile(models.Model):
    """
    Extended profile for students with geolocation and face data.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student_profile')
    jntu_no = models.CharField(max_length=20, unique=True, help_text="JNTU Number")
    name = models.CharField(max_length=100)
    company = models.CharField(max_length=100, blank=True, help_text="Company/Organization")
    lat = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True, help_text="Latitude")
    lon = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True, help_text="Longitude")
    face_enrolled = models.BooleanField(default=False, help_text="Whether face is enrolled")
    reference_image_url = models.URLField(blank=True, help_text="URL to reference face image")
    face_encoding = models.JSONField(null=True, blank=True, help_text="Face encoding data")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'student_profiles'
        verbose_name = 'Student Profile'
        verbose_name_plural = 'Student Profiles'
    
    def __str__(self):
        return f"{self.name} ({self.jntu_no})"
    
    @property
    def full_name(self):
        return f"{self.user.first_name} {self.user.last_name}".strip() or self.name


class AdminInvite(models.Model):
    """
    Admin account invitation system.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(validators=[EmailValidator()])
    invite_code = models.CharField(max_length=100, unique=True)
    expires_at = models.DateTimeField()
    used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'admin_invites'
        verbose_name = 'Admin Invite'
        verbose_name_plural = 'Admin Invites'
    
    def __str__(self):
        return f"Invite for {self.email}"
    
    @property
    def is_expired(self):
        return timezone.now() > self.expires_at
    
    @property
    def is_valid(self):
        return not self.used and not self.is_expired


class EmailVerification(models.Model):
    """
    Email verification tokens for students.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='email_verifications')
    token = models.CharField(max_length=100, unique=True)
    expires_at = models.DateTimeField()
    verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'email_verifications'
        verbose_name = 'Email Verification'
        verbose_name_plural = 'Email Verifications'
    
    def __str__(self):
        return f"Verification for {self.user.email}"
    
    @property
    def is_expired(self):
        return timezone.now() > self.expires_at
    
    @property
    def is_valid(self):
        return not self.verified and not self.is_expired
