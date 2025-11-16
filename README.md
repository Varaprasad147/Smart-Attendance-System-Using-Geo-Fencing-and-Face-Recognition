# Geofenced Intelligent Attendance System

A Django-based attendance system with geofencing and facial recognition.

## Features

- Multi-role system (Super-Admin, Admin, Student)
- GPS-based geofencing
- AI facial recognition
- Real-time analytics
- JWT authentication

## Setup

1. Install dependencies: `pip install -r requirements.txt`
2. Configure MySQL database
3. Run migrations: `python manage.py migrate`
4. Create super admin: `python manage.py seed_superadmin`
5. Start services: Django, FastAPI face service, Redis, Celery

## Usage

- Super-Admin: `/super/dashboard`
- Admin: `/admin/dashboard`
- Student: `/student/dashboard`
