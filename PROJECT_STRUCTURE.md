# Geofenced Intelligent Attendance System - Project Structure

## Overview

This is a comprehensive Django-based attendance management system that combines geofencing technology with facial recognition for accurate student attendance tracking.

## Project Structure

```
Major-Project/
├── attendance_system/                 # Main Django project
│   ├── __init__.py
│   ├── settings.py                   # Django settings configuration
│   ├── urls.py                       # Main URL configuration
│   ├── wsgi.py                       # WSGI configuration
│   ├── asgi.py                       # ASGI configuration
│   └── celery.py                     # Celery configuration
├── users/                            # Users app
│   ├── __init__.py
│   ├── apps.py                       # App configuration
│   ├── models.py                     # User models (User, StudentProfile, etc.)
│   ├── views.py                      # User views and API endpoints
│   ├── serializers.py                # DRF serializers
│   ├── urls.py                       # User app URLs
│   ├── admin.py                      # Django admin configuration
│   └── management/                   # Management commands
│       └── commands/
│           └── seed_superadmin.py    # Create super admin user
├── attendance/                       # Attendance app
│   ├── __init__.py
│   ├── apps.py                       # App configuration
│   ├── models.py                     # Attendance models
│   ├── views.py                      # Attendance views and API endpoints
│   ├── serializers.py                # DRF serializers
│   ├── urls.py                       # Attendance app URLs
│   └── admin.py                      # Django admin configuration
├── analytics/                        # Analytics app
│   ├── __init__.py
│   └── apps.py                       # App configuration
├── face_service/                     # FastAPI face recognition service
│   ├── main.py                       # FastAPI application
│   └── requirements.txt              # Face service dependencies
├── templates/                        # HTML templates
│   ├── base.html                     # Base template with navigation
│   ├── users/                        # User templates
│   │   └── login.html                # Login page
│   ├── super/                        # Super admin templates
│   │   └── dashboard.html            # Super admin dashboard
│   ├── admin/                        # Admin templates
│   └── student/                      # Student templates
│       └── dashboard.html            # Student dashboard
├── static/                           # Static files (CSS, JS, images)
├── media/                            # User uploaded files
├── logs/                             # Application logs
├── manage.py                         # Django management script
├── requirements.txt                  # Python dependencies
├── env.example                       # Environment configuration template
├── setup.py                          # Project setup script
├── README.md                         # Project documentation
└── PROJECT_STRUCTURE.md              # This file
```

## Key Components

### 1. Django Backend (`attendance_system/`)

- **Settings**: Configured for MySQL, JWT authentication, CORS, and geofencing
- **URLs**: Centralized routing for all apps
- **Celery**: Background task processing with Redis

### 2. Users App (`users/`)

- **Models**: Custom User model with role-based access control
- **Views**: Authentication, user management, and role-specific dashboards
- **Serializers**: API data validation and transformation
- **Admin**: Django admin interface configuration

### 3. Attendance App (`attendance/`)

- **Models**: Attendance logs, geofence settings, system settings
- **Views**: Attendance marking, student management, analytics
- **Serializers**: API endpoints for attendance operations
- **Geofencing**: GPS-based location verification

### 4. Face Recognition Service (`face_service/`)

- **FastAPI**: High-performance face recognition microservice
- **Endpoints**: Face enrollment and verification
- **Integration**: Communicates with Django backend via HTTP

### 5. Templates (`templates/`)

- **Bootstrap 5**: Modern, responsive UI design
- **Role-based**: Different interfaces for each user role
- **Charts**: Chart.js integration for analytics

## Database Schema

### Core Tables

1. **users** - User accounts with role-based access
2. **student_profiles** - Extended student information and face data
3. **attendance_logs** - Daily attendance records with verification results
4. **geofence_settings** - Company-specific geofence configurations
5. **system_settings** - Global system parameters
6. **contact_messages** - Student-admin communication
7. **admin_invites** - Admin account invitation system
8. **email_verifications** - Student email verification tokens

## API Endpoints

### Authentication

- `POST /api/auth/login/` - User login
- `POST /api/auth/logout/` - User logout
- `POST /api/auth/refresh/` - Refresh JWT token

### Attendance

- `POST /api/attendance/mark/` - Mark attendance
- `GET /api/attendance/history/` - Get attendance history

### Face Recognition

- `POST /face/enroll` - Enroll new face
- `POST /face/verify` - Verify face against stored encoding

## Security Features

- **JWT Authentication**: Secure token-based authentication
- **Role-based Access Control**: Super-Admin, Admin, Student roles
- **Geofencing**: GPS location verification
- **Face Recognition**: AI-powered identity verification
- **Input Validation**: Comprehensive data validation and sanitization
- **Rate Limiting**: Protection against abuse

## Technology Stack

- **Backend**: Django 4.2 + Django REST Framework
- **Database**: MySQL 8.0
- **Cache**: Redis
- **Task Queue**: Celery
- **Face Recognition**: FastAPI + face_recognition library
- **Frontend**: Bootstrap 5 + Chart.js
- **Authentication**: JWT tokens
- **Geolocation**: Geopy library

## Setup Instructions

1. **Install Dependencies**: `pip install -r requirements.txt`
2. **Configure Environment**: Copy `env.example` to `.env` and update values
3. **Setup Database**: Create MySQL database and run migrations
4. **Create Super Admin**: `python manage.py seed_superadmin`
5. **Start Services**: Django, FastAPI, Redis, Celery

## Development Workflow

1. **Models**: Define data structure in Django models
2. **Migrations**: Generate and apply database changes
3. **Views**: Implement business logic and API endpoints
4. **Templates**: Create user interface templates
5. **Testing**: Verify functionality and security
6. **Deployment**: Configure production environment

## Future Enhancements

- **Mobile App**: Native mobile applications
- **Real-time Notifications**: WebSocket-based updates
- **Advanced Analytics**: Machine learning insights
- **Multi-language Support**: Internationalization
- **API Documentation**: Swagger/OpenAPI integration
- **Performance Monitoring**: Application performance tracking
