"""
Management command to start face service.
"""
import subprocess
import sys
import os
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Start the face recognition service'

    def handle(self, *args, **options):
        face_service_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'face_service')
        face_service_main = os.path.join(face_service_dir, 'main.py')
        
        if not os.path.exists(face_service_main):
            self.stdout.write(
                self.style.ERROR(f"Face service not found at {face_service_main}")
            )
            return
        
        self.stdout.write("Starting face recognition service...")
        self.stdout.write(f"Service directory: {face_service_dir}")
        
        try:
            # Start the face service
            process = subprocess.Popen(
                [sys.executable, face_service_main],
                cwd=face_service_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            self.stdout.write(
                self.style.SUCCESS("Face service started successfully!")
            )
            self.stdout.write("Service is running at http://localhost:8001")
            self.stdout.write("Press Ctrl+C to stop the service")
            
            # Wait for the process
            process.wait()
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"Failed to start face service: {str(e)}")
            )
