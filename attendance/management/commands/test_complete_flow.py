"""
Comprehensive test for the attendance flow.
This test simulates the exact scenario from the user's terminal output.
"""

from django.core.management.base import BaseCommand
from users.models import StudentProfile
from attendance.models import AttendanceLog
from attendance.views import verify_geofence, verify_face
from django.core.files.uploadedfile import SimpleUploadedFile
from datetime import date, time, datetime
import io
from PIL import Image


class Command(BaseCommand):
    help = 'Comprehensive test for the attendance flow'

    def add_arguments(self, parser):
        parser.add_argument(
            '--student-name',
            type=str,
            default='sai sudharsan',
            help='Test with a specific student name',
        )

    def handle(self, *args, **options):
        student_name = options.get('student_name')
        
        try:
            student = StudentProfile.objects.get(name=student_name)
        except StudentProfile.DoesNotExist:
            self.stdout.write(f"Student '{student_name}' not found")
            return
        
        self.stdout.write(f"Testing attendance flow for: {student.name} ({student.jntu_no})")
        self.stdout.write("=" * 60)
        
        # Test 1: Geofencing with exact coordinates from terminal output
        self.stdout.write("1. Testing Geofencing:")
        test_lat = 18.464719
        test_lon = 83.659387
        test_accuracy = 72.9
        
        geofence_result = verify_geofence(student, test_lat, test_lon, test_accuracy)
        self.stdout.write(f"   Result: {geofence_result}")
        
        # Test 2: Face verification with proper image
        self.stdout.write("2. Testing Face Verification:")
        
        # Create a proper test image
        img = Image.new('RGB', (300, 300), color='lightblue')
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='JPEG')
        img_bytes.seek(0)
        
        test_image = SimpleUploadedFile(
            'test_selfie.jpg',
            img_bytes.getvalue(),
            'image/jpeg'
        )
        
        face_result = verify_face(student, test_image)
        self.stdout.write(f"   Result: {face_result}")
        
        # Test 3: Check student's face encoding status
        self.stdout.write("3. Student Face Encoding Status:")
        self.stdout.write(f"   Face enrolled: {student.face_enrolled}")
        self.stdout.write(f"   Face encoding exists: {student.face_encoding is not None}")
        if student.face_encoding:
            is_dummy = all(x == 0.0 for x in student.face_encoding)
            self.stdout.write(f"   Is dummy encoding: {is_dummy}")
            self.stdout.write(f"   Encoding length: {len(student.face_encoding)}")
        
        # Test 4: Simulate attendance marking
        self.stdout.write("4. Simulating Attendance Marking:")
        
        if geofence_result and face_result:
            # Both verifications passed - should mark as present
            status = 'present'
            self.stdout.write(f"   Both verifications passed - Status: {status}")
            
            # Create a test attendance log
            attendance_log = AttendanceLog.objects.create(
                student=student,
                date=date.today(),
                time=datetime.now().time(),
                attendance_type='check_in',
                lat=test_lat,
                lon=test_lon,
                accuracy=test_accuracy,
                geofence_verified=geofence_result,
                face_verified=face_result,
                device_info='Test device',
                check_in_time=datetime.now().time()
            )
            
            self.stdout.write(f"   Created attendance log with ID: {attendance_log.id}")
            self.stdout.write(f"   Final status: {attendance_log.status}")
            self.stdout.write(f"   Geofence verified: {attendance_log.geofence_verified}")
            self.stdout.write(f"   Face verified: {attendance_log.face_verified}")
            
        else:
            # One or both verifications failed
            if not geofence_result and not face_result:
                status = 'fail_both'
            elif not geofence_result:
                status = 'fail_geo'
            else:
                status = 'fail_face'
            
            self.stdout.write(f"   Verification failed - Status: {status}")
            self.stdout.write(f"   Geofence: {'PASS' if geofence_result else 'FAIL'}")
            self.stdout.write(f"   Face: {'PASS' if face_result else 'FAIL'}")
        
        # Test 5: Check existing attendance logs
        self.stdout.write("5. Existing Attendance Logs:")
        existing_logs = AttendanceLog.objects.filter(
            student=student,
            date=date.today()
        ).order_by('-created_at')
        
        self.stdout.write(f"   Today's logs: {existing_logs.count()}")
        for i, log in enumerate(existing_logs[:3], 1):
            self.stdout.write(f"   Log {i}: {log.attendance_type} - {log.status}")
            self.stdout.write(f"           Geo: {log.geofence_verified}, Face: {log.face_verified}")
            self.stdout.write(f"           Coords: {log.lat}, {log.lon}, Accuracy: {log.accuracy}m")
        
        self.stdout.write("=" * 60)
        self.stdout.write("Test completed successfully!")
