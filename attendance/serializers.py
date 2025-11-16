"""
Serializers for the attendance app.
"""

from rest_framework import serializers
from .models import AttendanceLog, GeofenceSettings, SystemSettings, ContactMessage
from users.models import StudentProfile


class AttendanceLogSerializer(serializers.ModelSerializer):
    """Attendance log serializer."""
    student_name = serializers.CharField(source='student.name', read_only=True)
    student_jntu = serializers.CharField(source='student.jntu_no', read_only=True)
    company = serializers.CharField(source='student.company', read_only=True)
    
    class Meta:
        model = AttendanceLog
        fields = [
            'id', 'student', 'student_name', 'student_jntu', 'company',
            'date', 'time', 'lat', 'lon', 'accuracy', 'geofence_verified',
            'face_verified', 'status', 'device_info', 'ip_address', 'created_at'
        ]
        read_only_fields = ['id', 'geofence_verified', 'face_verified', 'status', 'created_at']


class AttendanceMarkSerializer(serializers.Serializer):
    """Enhanced attendance marking serializer with check-in/check-out support."""
    lat = serializers.DecimalField(max_digits=9, decimal_places=6)
    lon = serializers.DecimalField(max_digits=9, decimal_places=6)
    accuracy = serializers.DecimalField(max_digits=9, decimal_places=2)  # Increased to handle large values
    selfie_image = serializers.ImageField()
    device_info = serializers.CharField(required=False, allow_blank=True)
    attendance_type = serializers.ChoiceField(choices=[('check_in', 'Check In'), ('check_out', 'Check Out')], default='check_in')
    
    def validate_accuracy(self, value):
        # Allow very large accuracy values (they will be handled in verify_geofence)
        # GPS can return default/invalid values that are very large
        if value > 1000000:  # 1000km - definitely invalid
            raise serializers.ValidationError('GPS accuracy value is invalid. Please try again.')
        return value
    
    def validate_selfie_image(self, value):
        # Check file size (2MB limit)
        if value.size > 2 * 1024 * 1024:
            raise serializers.ValidationError('Image file size must be under 2MB.')
        
        # Check file type
        allowed_types = ['image/jpeg', 'image/png', 'image/jpg']
        if value.content_type not in allowed_types:
            raise serializers.ValidationError('Only JPEG and PNG images are allowed.')
        
        return value


class GeofenceSettingsSerializer(serializers.ModelSerializer):
    """Geofence settings serializer."""
    
    class Meta:
        model = GeofenceSettings
        fields = [
            'id', 'company', 'radius', 'accuracy_threshold',
            'center_lat', 'center_lon', 'is_active', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class SystemSettingsSerializer(serializers.ModelSerializer):
    """System settings serializer."""
    
    class Meta:
        model = SystemSettings
        fields = ['id', 'key', 'value', 'description', 'is_active', 'created_at']
        read_only_fields = ['id', 'created_at']


class ContactMessageSerializer(serializers.ModelSerializer):
    """Contact message serializer."""
    student_name = serializers.CharField(source='student.name', read_only=True)
    student_jntu = serializers.CharField(source='student.jntu_no', read_only=True)
    admin_name = serializers.CharField(source='responded_by.get_full_name', read_only=True)
    
    class Meta:
        model = ContactMessage
        fields = [
            'id', 'student', 'student_name', 'student_jntu', 'subject', 'message',
            'status', 'admin_response', 'admin_name', 'responded_at', 'created_at'
        ]
        read_only_fields = ['id', 'student', 'status', 'admin_response', 'admin_name', 'responded_at', 'created_at']


class ContactMessageResponseSerializer(serializers.ModelSerializer):
    """Contact message response serializer for admins."""
    
    class Meta:
        model = ContactMessage
        fields = ['admin_response']
    
    def update(self, instance, validated_data):
        instance.admin_response = validated_data.get('admin_response', instance.admin_response)
        instance.responded_by = self.context['request'].user
        instance.status = 'resolved'
        instance.save()
        return instance


class StudentUploadSerializer(serializers.Serializer):
    """Student data upload serializer."""
    file = serializers.FileField()
    
    def validate_file(self, value):
        # Check file extension
        allowed_extensions = ['.csv', '.xlsx', '.xls']
        file_extension = value.name.lower()
        
        if not any(file_extension.endswith(ext) for ext in allowed_extensions):
            raise serializers.ValidationError(
                'Only CSV and Excel files (.csv, .xlsx, .xls) are allowed.'
            )
        
        # Check file size (10MB limit for uploads)
        if value.size > 10 * 1024 * 1024:
            raise serializers.ValidationError('File size must be under 10MB.')
        
        return value


class StudentLocationUpdateSerializer(serializers.Serializer):
    """Student location update serializer."""
    student_id = serializers.UUIDField()
    lat = serializers.DecimalField(max_digits=9, decimal_places=6)
    lon = serializers.DecimalField(max_digits=9, decimal_places=6)
    
    def validate_student_id(self, value):
        try:
            StudentProfile.objects.get(id=value)
            return value
        except StudentProfile.DoesNotExist:
            raise serializers.ValidationError('Student not found.')


class BulkLocationUpdateSerializer(serializers.Serializer):
    """Bulk location update serializer."""
    company = serializers.CharField(required=False, allow_blank=True)
    lat = serializers.DecimalField(max_digits=9, decimal_places=6)
    lon = serializers.DecimalField(max_digits=9, decimal_places=6)
    
    def validate(self, attrs):
        if not attrs.get('company'):
            raise serializers.ValidationError('Company is required for bulk updates.')
        return attrs


class AttendanceExportSerializer(serializers.Serializer):
    """Attendance export serializer."""
    from_date = serializers.DateField(required=False)
    to_date = serializers.DateField(required=False)
    company = serializers.CharField(required=False, allow_blank=True)
    student_id = serializers.UUIDField(required=False)
    
    def validate(self, attrs):
        from_date = attrs.get('from_date')
        to_date = attrs.get('to_date')
        
        if from_date and to_date and from_date > to_date:
            raise serializers.ValidationError('From date must be before or equal to to date.')
        
        return attrs
