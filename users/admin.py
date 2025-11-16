"""
Admin configuration for the users app.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, StudentProfile, AdminInvite, EmailVerification


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Custom user admin."""
    list_display = ['email', 'first_name', 'last_name', 'role', 'is_active', 'created_at']
    list_filter = ['role', 'is_active', 'created_at']
    search_fields = ['email', 'first_name', 'last_name']
    ordering = ['-created_at']
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'role')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'created_at')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'role', 'password1', 'password2'),
        }),
    )
    
    readonly_fields = ['created_at']


@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    """Student profile admin."""
    list_display = ['name', 'jntu_no', 'company', 'face_enrolled', 'created_at']
    list_filter = ['company', 'face_enrolled', 'created_at']
    search_fields = ['name', 'jntu_no', 'company']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Basic Information', {'fields': ('user', 'jntu_no', 'name', 'company')}),
        ('Location', {'fields': ('lat', 'lon')}),
        ('Face Recognition', {'fields': ('face_enrolled', 'reference_image_url', 'face_encoding')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )
    
    readonly_fields = ['created_at', 'updated_at']


@admin.register(AdminInvite)
class AdminInviteAdmin(admin.ModelAdmin):
    """Admin invite admin."""
    list_display = ['email', 'invite_code', 'expires_at', 'used', 'created_at']
    list_filter = ['used', 'expires_at', 'created_at']
    search_fields = ['email', 'invite_code']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Invite Details', {'fields': ('email', 'invite_code', 'expires_at')}),
        ('Status', {'fields': ('used',)}),
        ('Timestamps', {'fields': ('created_at',)}),
    )
    
    readonly_fields = ['created_at']


@admin.register(EmailVerification)
class EmailVerificationAdmin(admin.ModelAdmin):
    """Email verification admin."""
    list_display = ['user', 'token', 'expires_at', 'verified', 'created_at']
    list_filter = ['verified', 'expires_at', 'created_at']
    search_fields = ['user__email', 'token']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Verification Details', {'fields': ('user', 'token', 'expires_at')}),
        ('Status', {'fields': ('verified',)}),
        ('Timestamps', {'fields': ('created_at',)}),
    )
    
    readonly_fields = ['created_at']
