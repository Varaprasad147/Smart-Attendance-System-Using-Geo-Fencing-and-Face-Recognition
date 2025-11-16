"""
Django management command to seed super admin user.
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.conf import settings

User = get_user_model()

class Command(BaseCommand):
    help = 'Create a super admin user for the attendance system'

    def add_arguments(self, parser):
        parser.add_argument(
            '--email',
            type=str,
            default='admin@college.edu',
            help='Email for super admin (default: admin@college.edu)'
        )
        parser.add_argument(
            '--password',
            type=str,
            default='admin123',
            help='Password for super admin (default: admin123)'
        )
        parser.add_argument(
            '--first-name',
            type=str,
            default='Super',
            help='First name for super admin (default: Super)'
        )
        parser.add_argument(
            '--last-name',
            type=str,
            default='Admin',
            help='Last name for super admin (default: Admin)'
        )

    def handle(self, *args, **options):
        email = options['email']
        password = options['password']
        first_name = options['first_name']
        last_name = options['last_name']

        # Check if super admin already exists
        if User.objects.filter(role='superadmin').exists():
            self.stdout.write(
                self.style.WARNING('Super admin already exists. Skipping creation.')
            )
            return

        try:
            # Create super admin user
            user = User.objects.create_user(
                email=email,
                username=email,
                first_name=first_name,
                last_name=last_name,
                role='superadmin',
                is_staff=True,
                is_superuser=True
            )
            user.set_password(password)
            user.save()

            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully created super admin user:\n'
                    f'Email: {email}\n'
                    f'Password: {password}\n'
                    f'Role: Super Admin'
                )
            )
            
            self.stdout.write(
                self.style.WARNING(
                    'IMPORTANT: Change the password after first login for security!'
                )
            )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Failed to create super admin: {str(e)}')
            )
