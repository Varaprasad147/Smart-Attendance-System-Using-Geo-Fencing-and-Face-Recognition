"""
Test script to verify the attendance flow with geofencing and face verification.
"""

from django.core.management.base import BaseCommand
from users.models import StudentProfile
from attendance.models import AttendanceLog
from attendance.views import verify_geofence, verify_face
from django.core.files.uploadedfile import SimpleUploadedFile
from datetime import date, time
import os


class Command(BaseCommand):
    help = 'Test the attendance flow with geofencing and face verification'

    def add_arguments(self, parser):
        parser.add_argument(
            '--student-id',
            type=str,
            help='Test with a specific student ID',
        )

    def handle(self, *args, **options):
        student_id = options.get('student_id')
        
        # Get students to test
        if student_id:
            students = StudentProfile.objects.filter(id=student_id)
            if not students.exists():
                self.stdout.write(f"Student with ID {student_id} not found")
                return
        else:
            # Get students with face enrolled
            students = StudentProfile.objects.filter(face_enrolled=True)
        
        self.stdout.write(f"Testing attendance flow for {students.count()} students")
        
        for student in students:
            self.stdout.write(f"\nTesting student: {student.name} ({student.jntu_no})")
            
            # Test geofencing
            self.stdout.write("  Testing geofencing...")
            test_lat = 18.465846  # From the terminal output
            test_lon = 83.65953   # From the terminal output
            test_accuracy = 72.9   # From the terminal output
            
            geofence_result = verify_geofence(student, test_lat, test_lon, test_accuracy)
            self.stdout.write(f"    Geofence result: {geofence_result}")
            
            # Test face verification
            self.stdout.write("  Testing face verification...")
            
            # Create a dummy image file for testing
            dummy_image_data = b'dummy_image_data'
            dummy_image = SimpleUploadedFile(
                'test_selfie.jpg',
                dummy_image_data,
                content_type='image/jpeg'
            )
            
            try:
                face_result = verify_face(student, dummy_image)
                self.stdout.write(f"    Face verification result: {face_result}")
            except Exception as e:
                self.stdout.write(f"    Face verification error: {str(e)}")
            
            # Check existing attendance logs
            today_logs = AttendanceLog.objects.filter(
                student=student,
                date=date.today()
            )
            
            self.stdout.write(f"    Today's attendance logs: {today_logs.count()}")
            for log in today_logs:
                self.stdout.write(f"      - {log.attendance_type}: {log.status} (geo: {log.geofence_verified}, face: {log.face_verified})")
        
        self.stdout.write(f"\nAttendance flow test completed!")
