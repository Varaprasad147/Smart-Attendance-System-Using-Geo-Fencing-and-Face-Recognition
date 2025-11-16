"""
Management command to test face service connectivity.
"""
from django.core.management.base import BaseCommand
from django.conf import settings
import requests


class Command(BaseCommand):
    help = 'Test face service connectivity'

    def handle(self, *args, **options):
        face_service_url = f"{settings.FACE_SERVICE_URL}/health"
        
        try:
            self.stdout.write(f"Testing face service at {face_service_url}")
            response = requests.get(face_service_url, timeout=5)
            
            if response.status_code == 200:
                self.stdout.write(
                    self.style.SUCCESS(f"Face service is running: {response.text}")
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f"Face service returned status {response.status_code}")
                )
                
        except requests.exceptions.ConnectionError:
            self.stdout.write(
                self.style.ERROR(f"Face service is not reachable at {settings.FACE_SERVICE_URL}")
            )
        except requests.exceptions.Timeout:
            self.stdout.write(
                self.style.ERROR(f"Face service timeout at {settings.FACE_SERVICE_URL}")
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"Face service error: {str(e)}")
            )
