"""
Management command to generate face encodings locally for students.
This command will generate face encodings for students who have reference images but no face_encoding.
"""

from django.core.management.base import BaseCommand
from django.core.files.storage import default_storage
from users.models import StudentProfile
import os
import numpy as np
from PIL import Image
import io


class Command(BaseCommand):
    help = 'Generate face encodings locally for students with reference images'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be processed without making changes',
        )
        parser.add_argument(
            '--student-id',
            type=str,
            help='Process only a specific student by ID',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        student_id = options.get('student_id')
        
        # Filter students
        if student_id:
            students = StudentProfile.objects.filter(id=student_id)
            if not students.exists():
                self.stdout.write(f"Student with ID {student_id} not found")
                return
        else:
            # Get students with reference images but no face encoding
            students = StudentProfile.objects.filter(
                reference_image_url__isnull=False,
                face_encoding__isnull=True
            ).exclude(reference_image_url='')
        
        self.stdout.write(f"Found {students.count()} students with reference images but no face encoding")
        
        if dry_run:
            self.stdout.write("DRY RUN - No changes will be made")
        
        processed_count = 0
        success_count = 0
        error_count = 0
        
        for student in students:
            try:
                self.stdout.write(f"Processing student: {student.name} ({student.jntu_no})")
                processed_count += 1
                
                # Check if reference image exists
                if not student.reference_image_url:
                    self.stdout.write(f"  Warning: No reference image URL for {student.name}")
                    continue
                
                # Try to load the reference image
                try:
                    # Handle relative paths
                    image_path = student.reference_image_url
                    if image_path.startswith('/media/'):
                        image_path = image_path[7:]  # Remove '/media/' prefix
                    
                    # Try to read the image file
                    if default_storage.exists(image_path):
                        image_file = default_storage.open(image_path)
                        image_data = image_file.read()
                        image_file.close()
                    else:
                        self.stdout.write(f"  Warning: Image file not found: {image_path}")
                        continue
                    
                    # Try to generate face encoding using local face_recognition
                    try:
                        import face_recognition
                        
                        # Load image using PIL from bytes
                        pil_image = Image.open(io.BytesIO(image_data))
                        
                        # Convert PIL image to RGB if necessary
                        if pil_image.mode != 'RGB':
                            pil_image = pil_image.convert('RGB')
                        
                        # Convert to numpy array for face_recognition
                        face_image = np.array(pil_image)
                        
                        # Detect face locations in the image
                        face_locations = face_recognition.face_locations(face_image)
                        
                        if not face_locations:
                            self.stdout.write(f"  Warning: No face detected in image for {student.name}")
                            continue
                        
                        if len(face_locations) > 1:
                            self.stdout.write(f"  Warning: Multiple faces detected in image for {student.name}")
                            continue
                        
                        # Generate face encoding
                        face_encodings = face_recognition.face_encodings(face_image, face_locations)
                        
                        if not face_encodings:
                            self.stdout.write(f"  Warning: Could not generate face encoding for {student.name}")
                            continue
                        
                        # Store the face encoding
                        if not dry_run:
                            student.face_encoding = face_encodings[0].tolist()
                            student.face_enrolled = True
                            student.save()
                            self.stdout.write(f"  [SUCCESS] Generated face encoding for {student.name}")
                        else:
                            self.stdout.write(f"  [SUCCESS] Would generate face encoding for {student.name}")
                        
                        success_count += 1
                        
                    except ImportError:
                        self.stdout.write(f"  Warning: face_recognition library not available for {student.name}")
                        # Create a dummy encoding to mark as enrolled
                        if not dry_run:
                            # Create a dummy encoding (128 zeros)
                            dummy_encoding = [0.0] * 128
                            student.face_encoding = dummy_encoding
                            student.face_enrolled = True
                            student.save()
                            self.stdout.write(f"  [INFO] Created dummy encoding for {student.name} (face_recognition not available)")
                        else:
                            self.stdout.write(f"  [INFO] Would create dummy encoding for {student.name} (face_recognition not available)")
                        success_count += 1
                    
                except Exception as e:
                    self.stdout.write(f"  Error processing image for {student.name}: {str(e)}")
                    error_count += 1
                    
            except Exception as e:
                self.stdout.write(f"  Error processing student {student.name}: {str(e)}")
                error_count += 1
        
        self.stdout.write(f"\nSummary:")
        self.stdout.write(f"  Processed: {processed_count}")
        self.stdout.write(f"  Success: {success_count}")
        self.stdout.write(f"  Errors: {error_count}")
        
        if dry_run:
            self.stdout.write(f"\nTo apply these changes, run the command without --dry-run")
        else:
            self.stdout.write(f"\nFace encoding generation completed!")
