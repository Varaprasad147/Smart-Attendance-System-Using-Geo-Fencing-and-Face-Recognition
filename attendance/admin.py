"""
Admin configuration for the attendance app.
"""

from django.contrib import admin
from .models import AttendanceLog, GeofenceSettings, SystemSettings, ContactMessage


@admin.register(AttendanceLog)
class AttendanceLogAdmin(admin.ModelAdmin):
    """Attendance log admin."""
    list_display = ['student', 'date', 'time', 'status', 'geofence_verified', 'face_verified', 'created_at']
    list_filter = ['status', 'date', 'geofence_verified', 'face_verified', 'created_at']
    search_fields = ['student__name', 'student__jntu_no', 'student__company']
    ordering = ['-date', '-time']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Student Information', {'fields': ('student',)}),
        ('Attendance Details', {'fields': ('date', 'time', 'status')}),
        ('Location Data', {'fields': ('lat', 'lon', 'accuracy')}),
        ('Verification Results', {'fields': ('geofence_verified', 'face_verified')}),
        ('Device Information', {'fields': ('device_info', 'ip_address')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )
    
    def has_add_permission(self, request):
        """Prevent manual creation of attendance logs."""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Prevent editing of attendance logs."""
        return False


@admin.register(GeofenceSettings)
class GeofenceSettingsAdmin(admin.ModelAdmin):
    """Geofence settings admin."""
    list_display = ['company', 'radius', 'accuracy_threshold', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['company']
    ordering = ['company']
    
    fieldsets = (
        ('Company Information', {'fields': ('company', 'is_active')}),
        ('Geofence Configuration', {'fields': ('radius', 'accuracy_threshold')}),
        ('Center Coordinates', {'fields': ('center_lat', 'center_lon')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )
    
    readonly_fields = ['created_at', 'updated_at']


@admin.register(SystemSettings)
class SystemSettingsAdmin(admin.ModelAdmin):
    """System settings admin."""
    list_display = ['key', 'value', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['key', 'description']
    ordering = ['key']
    
    fieldsets = (
        ('Setting Information', {'fields': ('key', 'value', 'description', 'is_active')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )
    
    readonly_fields = ['created_at', 'updated_at']


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    """Contact message admin."""
    list_display = ['student', 'subject', 'status', 'created_at', 'responded_at']
    list_filter = ['status', 'created_at', 'responded_at']
    search_fields = ['student__name', 'subject', 'message']
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Student Information', {'fields': ('student',)}),
        ('Message Details', {'fields': ('subject', 'message', 'status')}),
        ('Admin Response', {'fields': ('admin_response', 'responded_by', 'responded_at')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )
    
    def save_model(self, request, obj, form, change):
        """Auto-update response timestamp when admin responds."""
        if obj.admin_response and not obj.responded_at:
            obj.responded_by = request.user
        super().save_model(request, obj, form, change)
