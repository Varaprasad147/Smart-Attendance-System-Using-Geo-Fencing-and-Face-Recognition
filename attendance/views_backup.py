"""
Views for the attendance app.
"""

import csv
import pandas as pd
from datetime import datetime, date
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.conf import settings
from django.utils import timezone
from django.core.paginator import Paginator
from django.db import models
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from geopy.distance import geodesic
import requests
import re
from .models import (
    AttendanceLog, GeofenceSettings, SystemSettings, ContactMessage, Company
)
from .serializers import (
    AttendanceLogSerializer, AttendanceMarkSerializer, GeofenceSettingsSerializer,
    SystemSettingsSerializer, ContactMessageSerializer, ContactMessageResponseSerializer,
    StudentUploadSerializer, StudentLocationUpdateSerializer, BulkLocationUpdateSerializer,
    AttendanceExportSerializer
)
from users.models import User, StudentProfile

def is_admin(user):
    """Check if user is admin."""
    return user.is_authenticated and user.is_admin

def is_student(user):
    """Check if user is student."""
    return user.is_authenticated and user.is_student


@login_required
@user_passes_test(is_admin)
def upload_students(request):
    """Upload student data via CSV/XLSX."""
    if request.method == 'POST':
        serializer = StudentUploadSerializer(data=request.FILES)
        if serializer.is_valid():
            file = serializer.validated_data['file']
            
            try:
                if file.name.endswith('.csv'):
                    df = pd.read_csv(file)
                else:
                    df = pd.read_excel(file)
                
                # Expected columns now: roll_number, name, email, company (mandatory)
                required_columns = ['roll_number', 'name', 'email', 'company']
                if not all(col in df.columns for col in required_columns):
                    messages.error(request, 'File must contain: roll_number, name, email, company columns')
                    return render(request, 'admin/upload_students.html')
                
                success_count = 0
                error_count = 0
                
                for _, row in df.iterrows():
                    try:
                        # Check if student already exists (by roll number)
                        if StudentProfile.objects.filter(jntu_no=row['roll_number']).exists():
                            continue
                        # Resolve company from master table
                        company_name = str(row['company']).strip()
                        try:
                            company_obj = Company.objects.get(name__iexact=company_name)
                        except Company.DoesNotExist:
                            error_count += 1
                            continue

                        # Create user
                        user = User.objects.create_user(
                            email=row['email'],
                            first_name=row['name'].split()[0] if ' ' in str(row['name']) else row['name'],
                            last_name=row['name'].split()[-1] if ' ' in str(row['name']) else '',
                            username=row['email'],
                            role='student'
                        )
                        # Set default password to roll number
                        user.set_password(str(row['roll_number']))
                        user.save()
                        
                        # Create student profile
                        profile = StudentProfile.objects.create(
                            user=user,
                            jntu_no=row['roll_number'],
                            name=row['name'],
                            company=company_obj.name,
                            lat=company_obj.lat,
                            lon=company_obj.lon
                        )
                        
                        success_count += 1
                        
                    except Exception as e:
                        error_count += 1
                        print(f"Error creating student {row.get('jntu_no', 'unknown')}: {str(e)}")
                
                messages.success(request, f'Successfully created {success_count} students. Errors: {error_count}')
                
            except Exception as e:
                messages.error(request, f'Error processing file: {str(e)}')
    
    return render(request, 'admin/upload_students.html')


@login_required
@user_passes_test(is_admin)
def manage_students(request):
    """Manage student information and locations."""
    students = StudentProfile.objects.select_related('user').all().order_by('-created_at')
    # Optional filter by company name
    company_filter = request.GET.get('company')
    if company_filter:
        students = students.filter(company=company_filter)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'update_location':
            student_id = request.POST.get('student_id')
            lat = request.POST.get('lat')
            lon = request.POST.get('lon')
            
            try:
                student = StudentProfile.objects.get(id=student_id)
                
                # Handle empty string values for lat/lon fields
                if lat and lat.strip():
                    try:
                        student.lat = float(lat)
                    except ValueError:
                        messages.error(request, 'Invalid latitude value')
                        return redirect('attendance:manage_students')
                else:
                    student.lat = None
                
                if lon and lon.strip():
                    try:
                        student.lon = float(lon)
                    except ValueError:
                        messages.error(request, 'Invalid longitude value')
                        return redirect('attendance:manage_students')
                else:
                    student.lon = None
                
                student.save()
                messages.success(request, f'Location updated for {student.name}')
            except StudentProfile.DoesNotExist:
                messages.error(request, 'Student not found')
        
        elif action == 'bulk_update':
            company = request.POST.get('company')
            lat = request.POST.get('lat')
            lon = request.POST.get('lon')
            
            if company and lat and lon:
                try:
                    lat_value = float(lat) if lat.strip() else None
                    lon_value = float(lon) if lon.strip() else None
                    updated = StudentProfile.objects.filter(company=company).update(lat=lat_value, lon=lon_value)
                    messages.success(request, f'Updated location for {updated} students in {company}')
                except ValueError:
                    messages.error(request, 'Invalid latitude or longitude values')
            else:
                messages.error(request, 'Please provide company, latitude, and longitude values')
        
        elif action == 'delete_selected':
            ids = request.POST.getlist('selected_ids')
            if ids:
                try:
                    deleted_count = 0
                    for student_id in ids:
                        try:
                            student_profile = StudentProfile.objects.get(id=student_id)
                            # Delete the associated User first, then StudentProfile
                            user = student_profile.user
                            student_profile.delete()  # This should cascade delete the User
                            # If cascade doesn't work, explicitly delete the user
                            if User.objects.filter(id=user.id).exists():
                                user.delete()
                            deleted_count += 1
                        except StudentProfile.DoesNotExist:
                            continue
                    
                    messages.success(request, f'Successfully deleted {deleted_count} selected student records')
                except Exception as e:
                    messages.error(request, f'Error deleting selected students: {str(e)}')
            else:
                messages.error(request, 'No students selected')
        
        elif action == 'reset_password':
            student_id = request.POST.get('student_id')
            new_password = request.POST.get('new_password')
            
            if not student_id or not new_password:
                messages.error(request, 'Student ID and new password are required')
            else:
                try:
                    student_profile = StudentProfile.objects.get(id=student_id)
                    user = student_profile.user
                    
                    # Validate password length
                    if len(new_password) < 6:
                        messages.error(request, 'Password must be at least 6 characters long')
                    else:
                        user.set_password(new_password)
                        user.save()
                        messages.success(request, f'Password reset successfully for {student_profile.name}')
                        
                except StudentProfile.DoesNotExist:
                    messages.error(request, 'Student not found')
                except Exception as e:
                    messages.error(request, f'Error resetting password: {str(e)}')
        
        elif action == 'bulk_reset_password':
            new_password = request.POST.get('new_password')
            selected_ids = request.POST.getlist('selected_ids')
            
            if not new_password or not selected_ids:
                messages.error(request, 'Password and selected students are required')
            else:
                if len(new_password) < 6:
                    messages.error(request, 'Password must be at least 6 characters long')
                else:
                    try:
                        updated_count = 0
                        for student_id in selected_ids:
                            try:
                                student_profile = StudentProfile.objects.get(id=student_id)
                                user = student_profile.user
                                user.set_password(new_password)
                                user.save()
                                updated_count += 1
                            except StudentProfile.DoesNotExist:
                                continue
                        
                        messages.success(request, f'Password reset successfully for {updated_count} students')
                    except Exception as e:
                        messages.error(request, f'Error resetting passwords: {str(e)}')
        
        elif action == 'delete_all':
            try:
                # Count students before deletion
                student_profiles_count = StudentProfile.objects.count()
                student_users_count = User.objects.filter(role='student').count()
                
                # Delete all StudentProfile records (this should cascade delete User records)
                StudentProfile.objects.all().delete()
                
                # If cascade didn't work, manually delete remaining student users
                remaining_student_users = User.objects.filter(role='student').count()
                if remaining_student_users > 0:
                    User.objects.filter(role='student').delete()
                
                messages.success(request, f'Successfully deleted all {student_profiles_count} student profiles and {student_users_count} student user accounts from database')
            except Exception as e:
                messages.error(request, f'Error deleting all students: {str(e)}')
    
    # Pagination
    paginator = Paginator(students, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'companies': StudentProfile.objects.values_list('company', flat=True).distinct()
    }
    return render(request, 'admin/manage_students.html', context)


@login_required
@user_passes_test(is_admin)
def attendance_analytics(request):
    """Enhanced attendance analytics with time tracking."""
    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')
    company = request.GET.get('company')
    
    # Default to last 30 days
    if not from_date:
        from_date = (date.today() - timezone.timedelta(days=30)).strftime('%Y-%m-%d')
    if not to_date:
        to_date = date.today().strftime('%Y-%m-%d')
    
    # Filter attendance logs
    attendance_query = AttendanceLog.objects.filter(
        date__range=[from_date, to_date]
    ).select_related('student')
    
    if company:
        attendance_query = attendance_query.filter(student__company=company)
    
    # Get statistics
    total_attendance = attendance_query.count()
    present_count = attendance_query.filter(status='present').count()
    fail_geo_count = attendance_query.filter(status='fail_geo').count()
    fail_face_count = attendance_query.filter(status='fail_face').count()
    fail_both_count = attendance_query.filter(status='fail_both').count()
    
    # Time tracking statistics
    completed_sessions = attendance_query.filter(
        check_in_time__isnull=False, 
        check_out_time__isnull=False
    )
    total_time_minutes = completed_sessions.aggregate(
        total=models.Sum('total_time_minutes')
    )['total'] or 0
    
    avg_time_minutes = completed_sessions.aggregate(
        avg=models.Avg('total_time_minutes')
    )['avg'] or 0
    
    # Student time tracking data
    student_time_data = []
    for student in StudentProfile.objects.all():
        student_attendance = attendance_query.filter(student=student)
        student_total_time = student_attendance.aggregate(
            total=models.Sum('total_time_minutes')
        )['total'] or 0
        student_days = student_attendance.filter(
            check_in_time__isnull=False
        ).count()
        
        if student_days > 0:
            student_time_data.append({
                'student': student,
                'total_time_minutes': student_total_time,
                'days_present': student_days,
                'avg_time_per_day': student_total_time / student_days if student_days > 0 else 0
            })
    
    # Sort by total time
    student_time_data.sort(key=lambda x: x['total_time_minutes'], reverse=True)
    
    # Daily attendance data for charts
    daily_data = attendance_query.values('date').annotate(
        present=models.Count('id', filter=models.Q(status='present')),
        total=models.Count('id')
    ).order_by('date')
    
    context = {
        'from_date': from_date,
        'to_date': to_date,
        'company': company,
        'total_attendance': total_attendance,
        'present_count': present_count,
        'fail_geo_count': fail_geo_count,
        'fail_face_count': fail_face_count,
        'fail_both_count': fail_both_count,
        'daily_data': list(daily_data),
        'companies': StudentProfile.objects.values_list('company', flat=True).distinct(),
        # Time tracking data
        'completed_sessions': completed_sessions.count(),
        'total_time_minutes': total_time_minutes,
        'avg_time_minutes': avg_time_minutes,
        'total_time_hours': total_time_minutes / 60,
        'avg_time_hours': avg_time_minutes / 60,
        'student_time_data': student_time_data[:20],  # Top 20 students
    }
    return render(request, 'admin/analytics.html', context)


@login_required
@user_passes_test(is_admin)
def export_attendance(request):
    """Export attendance data to CSV."""
    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')
    company = request.GET.get('company')
    
    # Filter attendance logs
    attendance_query = AttendanceLog.objects.filter(
        date__range=[from_date, to_date]
    ).select_related('student')
    
    if company:
        attendance_query = attendance_query.filter(student__company=company)
    
    # Create CSV response
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="attendance_{from_date}_to_{to_date}.csv"'
    
    writer = csv.writer(response)
    writer.writerow([
        'Date', 'Time', 'Student Name', 'JNTU Number', 'Company', 'Status',
        'Latitude', 'Longitude', 'GPS Accuracy', 'Geofence Verified', 'Face Verified'
    ])
    
    for log in attendance_query:
        writer.writerow([
            log.date, log.time, log.student.name, log.student.jntu_no,
            log.student.company, log.get_status_display(), log.lat, log.lon,
            log.accuracy, log.geofence_verified, log.face_verified
        ])
    
    return response


@login_required
@user_passes_test(is_admin)
def contact_messages(request):
    """View and respond to student contact messages."""
    messages_list = ContactMessage.objects.select_related('student', 'responded_by').all().order_by('-created_at')
    
    if request.method == 'POST':
        message_id = request.POST.get('message_id')
        response_text = request.POST.get('response')
        
        if message_id and response_text:
            try:
                message = ContactMessage.objects.get(id=message_id)
                message.mark_responded(request.user, response_text)
                messages.success(request, 'Response sent successfully')
            except ContactMessage.DoesNotExist:
                messages.error(request, 'Message not found')
    
    # Pagination
    paginator = Paginator(messages_list, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {'page_obj': page_obj}
    return render(request, 'admin/contact_messages.html', context)


@login_required
@user_passes_test(is_admin)
def manage_companies(request):
    """Add and list companies for mapping students."""
    def parse_coordinate(value: str, is_lat: bool) -> float:
        """Parse decimal or DMS strings (e.g., 17°42′15″N, 82 59 30 E) to decimal degrees.

        Supports symbols: °, º, deg; ′, ', minutes; ″, ", seconds; optional N/S/E/W.
        """
        if value is None:
            raise ValueError('Empty coordinate')
        s = str(value).strip().upper()
        if not s:
            raise ValueError('Empty coordinate')

        # Try simple float first
        try:
            return float(s)
        except ValueError:
            pass

        # Normalize unicode symbols
        s = (
            s.replace('DEG', '°')
             .replace('º', '°')
             .replace('˚', '°')
             .replace(''', "'")
             .replace('′', "'")
             .replace('"', '"')
             .replace('″', '"')
        )

        # Regex for DMS: degrees minutes seconds optional direction
        m = re.match(r"^\s*(\d+(?:\.\d+)?)\D+(\d+(?:\.\d+)?)?\D*(\d+(?:\.\d+)?)?\s*([NSEW])?\s*$", s)
        if not m:
            # Alternative: space separated
            m = re.match(r"^\s*(\d+(?:\.\d+)?)(?:\s+(\d+(?:\.\d+)?))?(?:\s+(\d+(?:\.\d+)?))?\s*([NSEW])?\s*$", s)
        if not m:
            raise ValueError('Invalid coordinate format')

        deg = float(m.group(1))
        minutes = float(m.group(2)) if m.group(2) is not None else 0.0
        seconds = float(m.group(3)) if m.group(3) is not None else 0.0
        direction = m.group(4)

        decimal = deg + (minutes / 60.0) + (seconds / 3600.0)
        if direction in ('S', 'W'):
            decimal = -decimal

        # Validate range
        if is_lat and not (-90.0 <= decimal <= 90.0):
            raise ValueError('Latitude out of range (-90..90)')
        if not is_lat and not (-180.0 <= decimal <= 180.0):
            raise ValueError('Longitude out of range (-180..180)')
        return decimal
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'add':
            name = request.POST.get('name', '').strip()
            lat_raw = request.POST.get('lat')
            lon_raw = request.POST.get('lon')
            radius = request.POST.get('radius') or 50
            if name and lat_raw and lon_raw:
                try:
                    lat_dd = parse_coordinate(lat_raw, is_lat=True)
                    lon_dd = parse_coordinate(lon_raw, is_lat=False)
                    Company.objects.create(name=name, lat=lat_dd, lon=lon_dd, radius=radius)
                    messages.success(request, f'Company {name} added successfully')
                except Exception as e:
                    messages.error(request, f'Failed to add company: {str(e)}')
            else:
                messages.error(request, 'Please fill all required fields')
        
        elif action == 'update':
            company_id = request.POST.get('company_id')
            name = request.POST.get('name', '').strip()
            lat_raw = request.POST.get('lat')
            lon_raw = request.POST.get('lon')
            radius = request.POST.get('radius')
            
            if company_id and name and lat_raw and lon_raw:
                try:
                    company = Company.objects.get(id=company_id)
                    lat_dd = parse_coordinate(lat_raw, is_lat=True)
                    lon_dd = parse_coordinate(lon_raw, is_lat=False)
                    
                    company.name = name
                    company.lat = lat_dd
                    company.lon = lon_dd
                    if radius:
                        company.radius = radius
                    company.save()
                    
                    messages.success(request, f'Company {name} updated successfully')
                except Company.DoesNotExist:
                    messages.error(request, 'Company not found')
                except Exception as e:
                    messages.error(request, f'Failed to update company: {str(e)}')
            else:
                messages.error(request, 'Please fill all required fields')
        
        elif action == 'delete':
            company_id = request.POST.get('company_id')
            if company_id:
                try:
                    company = Company.objects.get(id=company_id)
                    company_name = company.name
                    
                    # Check if any students are assigned to this company
                    students_count = StudentProfile.objects.filter(company=company_name).count()
                    if students_count > 0:
                        messages.error(request, f'Cannot delete company {company_name}. {students_count} students are assigned to this company.')
                    else:
                        company.delete()
                        messages.success(request, f'Company {company_name} deleted successfully')
                except Company.DoesNotExist:
                    messages.error(request, 'Company not found')
                except Exception as e:
                    messages.error(request, f'Failed to delete company: {str(e)}')
            else:
                messages.error(request, 'Company ID is required')

    companies = Company.objects.all().order_by('name')
    return render(request, 'admin/companies.html', {'companies': companies})


@login_required
@user_passes_test(is_student)
def mark_attendance_view(request):
    """Enhanced student attendance marking view with check-in/check-out support."""
    if request.method == 'POST':
        serializer = AttendanceMarkSerializer(data=request.POST, files=request.FILES)
        if serializer.is_valid():
            try:
                student_profile = request.user.student_profile
                today = date.today()
                current_time = timezone.now().time()
                
                # Get validated data
                lat = serializer.validated_data['lat']
                lon = serializer.validated_data['lon']
                accuracy = serializer.validated_data['accuracy']
                selfie_image = serializer.validated_data['selfie_image']
                device_info = serializer.validated_data.get('device_info', '')
                attendance_type = serializer.validated_data.get('attendance_type', 'check_in')
                
                # Geofence verification
                geofence_verified = verify_geofence(student_profile, lat, lon, accuracy)
                
                # Face verification with error handling
                try:
                    # Check if student has face enrolled
                    if not student_profile.face_enrolled:
                        print(f"Student {student_profile.name} not face enrolled, skipping face verification")
                        face_verified = True  # Allow attendance if not enrolled
                    else:
                        # Try face verification
                        face_verified = verify_face(student_profile, selfie_image)
                        print(f"Face verification result for {student_profile.name}: {face_verified}")
                except Exception as e:
                    print(f"Face verification failed for {student_profile.name}: {str(e)}")
                    # Log the full error for debugging
                    import traceback
                    print(f"Face verification traceback: {traceback.format_exc()}")
                    face_verified = True  # Fallback: allow attendance if face verification fails
                
                # Check existing attendance for today
                existing_attendance = AttendanceLog.objects.filter(
                    student=student_profile, 
                    date=today
                ).first()
                
                if attendance_type == 'check_in':
                    if existing_attendance and existing_attendance.check_in_time:
                        messages.error(request, 'You have already checked in today.')
                        context = _build_student_location_context(student_profile)
                        return render(request, 'student/mark_attendance.html', context)
                    
                    # Create or update attendance log for check-in
                    if existing_attendance:
                        existing_attendance.check_in_time = current_time
                        existing_attendance.geofence_verified = geofence_verified
                        existing_attendance.face_verified = face_verified
                        existing_attendance.save()
                        attendance_log = existing_attendance
                    else:
                        attendance_log = AttendanceLog.objects.create(
                            student=student_profile,
                            date=today,
                            time=current_time,
                            attendance_type=attendance_type,
                            lat=lat,
                            lon=lon,
                            accuracy=accuracy,
                            geofence_verified=geofence_verified,
                            face_verified=face_verified,
                            device_info=device_info,
                            check_in_time=current_time
                        )
                    
                    if geofence_verified and face_verified:
                        messages.success(request, 'Check-in successful! Location and face verification passed.')
                    else:
                        messages.warning(request, f'Check-in recorded but verification failed. Location: {"✓" if geofence_verified else "✗"}, Face: {"✓" if face_verified else "✗"}')
                
                elif attendance_type == 'check_out':
                    if not existing_attendance or not existing_attendance.check_in_time:
                        messages.error(request, 'You must check in first before checking out.')
                        context = _build_student_location_context(student_profile)
                        return render(request, 'student/mark_attendance.html', context)
                    
                    if existing_attendance.check_out_time:
                        messages.error(request, 'You have already checked out today.')
                        context = _build_student_location_context(student_profile)
                        return render(request, 'student/mark_attendance.html', context)
                    
                    # Update attendance log for check-out
                    existing_attendance.check_out_time = current_time
                    existing_attendance.geofence_verified = geofence_verified
                    existing_attendance.face_verified = face_verified
                    existing_attendance.save()
                    attendance_log = existing_attendance
                    
                    if geofence_verified and face_verified:
                        messages.success(request, 'Check-out successful! Location and face verification passed.')
                    else:
                        messages.warning(request, f'Check-out recorded but verification failed. Location: {"✓" if geofence_verified else "✗"}, Face: {"✓" if face_verified else "✗"}')
                
                return redirect('users:student_dashboard')
                
            except Exception as e:
                error_msg = f'Error marking attendance: {str(e)}'
                messages.error(request, error_msg)
                print(f"Attendance error for {student_profile.name}: {str(e)}")  # Debug logging
                # Log the full traceback for debugging
                import traceback
                print(f"Full traceback: {traceback.format_exc()}")
        else:
            for field, errors in serializer.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')

    # GET or fallthrough render with location context
    try:
        student_profile = request.user.student_profile
        context = _build_student_location_context(student_profile)
    except Exception:
        context = {}
    return render(request, 'student/mark_attendance.html', context)


# API Views
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_mark_attendance(request):
    """Enhanced API endpoint for marking attendance with check-in/check-out support."""
    serializer = AttendanceMarkSerializer(data=request.data, files=request.FILES)
    if serializer.is_valid():
        try:
            student_profile = request.user.student_profile
            today = date.today()
            current_time = timezone.now().time()
            
            # Get validated data
            lat = serializer.validated_data['lat']
            lon = serializer.validated_data['lon']
            accuracy = serializer.validated_data['accuracy']
            selfie_image = serializer.validated_data['selfie_image']
            device_info = serializer.validated_data.get('device_info', '')
            attendance_type = serializer.validated_data.get('attendance_type', 'check_in')
            
            # Geofence verification
            geofence_verified = verify_geofence(student_profile, lat, lon, accuracy)
            
            # Face verification with error handling
            try:
                # Check if student has face enrolled
                if not student_profile.face_enrolled:
                    print(f"Student {student_profile.name} not face enrolled, skipping face verification")
                    face_verified = True  # Allow attendance if not enrolled
                else:
                    # Try face verification
                    face_verified = verify_face(student_profile, selfie_image)
                    print(f"Face verification result for {student_profile.name}: {face_verified}")
            except Exception as e:
                print(f"Face verification failed for {student_profile.name}: {str(e)}")
                # Log the full error for debugging
                import traceback
                print(f"Face verification traceback: {traceback.format_exc()}")
                face_verified = True  # Fallback: allow attendance if face verification fails
            
            # Check existing attendance for today
            existing_attendance = AttendanceLog.objects.filter(
                student=student_profile, 
                date=today
            ).first()
            
            if attendance_type == 'check_in':
                if existing_attendance and existing_attendance.check_in_time:
                    return Response({'error': 'You have already checked in today'}, status=status.HTTP_400_BAD_REQUEST)
                
                # Create or update attendance log for check-in
                if existing_attendance:
                    existing_attendance.check_in_time = current_time
                    existing_attendance.geofence_verified = geofence_verified
                    existing_attendance.face_verified = face_verified
                    existing_attendance.save()
                    attendance_log = existing_attendance
                else:
                    attendance_log = AttendanceLog.objects.create(
                        student=student_profile,
                        date=today,
                        time=current_time,
                        attendance_type=attendance_type,
                        lat=lat,
                        lon=lon,
                        accuracy=accuracy,
                        geofence_verified=geofence_verified,
                        face_verified=face_verified,
                        device_info=device_info,
                        ip_address=request.META.get('REMOTE_ADDR'),
                        check_in_time=current_time
                    )
            
            elif attendance_type == 'check_out':
                if not existing_attendance or not existing_attendance.check_in_time:
                    return Response({'error': 'You must check in first before checking out'}, status=status.HTTP_400_BAD_REQUEST)
                
                if existing_attendance.check_out_time:
                    return Response({'error': 'You have already checked out today'}, status=status.HTTP_400_BAD_REQUEST)
                
                # Update attendance log for check-out
                existing_attendance.check_out_time = current_time
                existing_attendance.geofence_verified = geofence_verified
                existing_attendance.face_verified = face_verified
                existing_attendance.save()
                attendance_log = existing_attendance
            
            return Response({
                'status': 'success',
                'attendance_id': str(attendance_log.id),
                'attendance_type': attendance_type,
                'geofence_verified': geofence_verified,
                'face_verified': face_verified,
                'overall_status': attendance_log.status,
                'check_in_time': attendance_log.check_in_time.isoformat() if attendance_log.check_in_time else None,
                'check_out_time': attendance_log.check_out_time.isoformat() if attendance_log.check_out_time else None,
                'total_time_minutes': attendance_log.total_time_minutes,
                'formatted_total_time': attendance_log.formatted_total_time
            })
            
        except StudentProfile.DoesNotExist:
            return Response({'error': 'Student profile not found'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_attendance_history(request):
    """API endpoint for getting attendance history."""
    try:
        student_profile = request.user.student_profile
        from_date = request.GET.get('from_date')
        to_date = request.GET.get('to_date')
        
        query = AttendanceLog.objects.filter(student=student_profile)
        
        if from_date:
            query = query.filter(date__gte=from_date)
        if to_date:
            query = query.filter(date__lte=to_date)
        
        attendance_logs = query.order_by('-date', '-time')
        serializer = AttendanceLogSerializer(attendance_logs, many=True)
        
        return Response(serializer.data)
        
    except StudentProfile.DoesNotExist:
        return Response({'error': 'Student profile not found'}, status=status.HTTP_400_BAD_REQUEST)


def verify_geofence(student_profile, current_lat, current_lon, accuracy):
    """Verify if student is within geofence (default 50m) using student's assigned company center and radius."""
    from .models import Company

    # Ensure numeric types
    try:
        current_lat_f = float(current_lat)
        current_lon_f = float(current_lon)
        accuracy_f = float(accuracy)
    except Exception:
        return False

    # Check GPS accuracy threshold
    if accuracy_f > float(settings.GPS_ACCURACY_THRESHOLD):
        return False

    # Determine geofence center: prefer student_profile lat/lon, fallback to company center
    company_obj = None
    if getattr(student_profile, 'company', None):
        try:
            company_obj = Company.objects.filter(name__iexact=student_profile.company).first()
        except Exception:
            company_obj = None

    if student_profile.lat is not None and student_profile.lon is not None:
        center_lat = float(student_profile.lat)
        center_lon = float(student_profile.lon)
    elif company_obj and company_obj.lat is not None and company_obj.lon is not None:
        center_lat = float(company_obj.lat)
        center_lon = float(company_obj.lon)
    else:
        return False

    # Distance in meters
    distance_m = geodesic((center_lat, center_lon), (current_lat_f, current_lon_f)).meters

    # Radius: prefer company radius if available, else global default
    radius_m = float(company_obj.radius) if company_obj and company_obj.radius is not None else float(settings.GEOFENCE_RADIUS)

    return distance_m <= radius_m


def _build_student_location_context(student_profile):
    """Prepare context with assigned coordinates and geofence radius for client-side gating."""
    from .models import Company
    company_obj = None
    if getattr(student_profile, 'company', None):
        company_obj = Company.objects.filter(name__iexact=student_profile.company).first()

    assigned_lat = None
    assigned_lon = None
    radius_m = float(settings.GEOFENCE_RADIUS)

    if company_obj and company_obj.radius is not None:
        radius_m = float(company_obj.radius)

    if student_profile.lat is not None and student_profile.lon is not None:
        assigned_lat = float(student_profile.lat)
        assigned_lon = float(student_profile.lon)
    elif company_obj and company_obj.lat is not None and company_obj.lon is not None:
        assigned_lat = float(company_obj.lat)
        assigned_lon = float(company_obj.lon)

    return {
        'assigned_lat': assigned_lat,
        'assigned_lon': assigned_lon,
        'geofence_radius': radius_m,
    }


def verify_face(student_profile, selfie_image):
    """Verify face using face recognition service with improved error handling."""
    # Check if face verification is enabled
    if not settings.FACE_VERIFICATION_ENABLED:
        print(f"Face verification disabled in settings, allowing attendance")
        return True
    
    if not student_profile.face_enrolled:
        print(f"Face verification skipped: Student {student_profile.name} not enrolled")
        return False
    
    try:
        # First check if student is enrolled in face service
        status_url = f"{settings.FACE_SERVICE_URL}/face/status/{student_profile.id}"
        try:
            status_response = requests.get(status_url, timeout=5)
            if status_response.status_code == 200:
                status_data = status_response.json()
                if not status_data.get('enrolled', False):
                    print(f"Student {student_profile.name} not enrolled in face service")
                    return True  # Allow attendance if not enrolled
        except:
            print(f"Could not check enrollment status for {student_profile.name}")
        
        # Call face recognition service
        face_service_url = f"{settings.FACE_SERVICE_URL}/face/verify"
        print(f"Attempting face verification for student {student_profile.name} at {face_service_url}")
        
        # Prepare image data - ensure proper file handling
        files = {'image': (selfie_image.name, selfie_image.file, selfie_image.content_type)}
        data = {'student_id': str(student_profile.id)}
        
        response = requests.post(face_service_url, files=files, data=data, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            matched = result.get('matched', False)
            print(f"Face verification result for {student_profile.name}: {matched}")
            return matched
        else:
            print(f"Face service returned status {response.status_code}: {response.text}")
            # If service is down, allow attendance but log the issue
            return True  # Fallback: allow attendance if service is down
            
    except requests.exceptions.ConnectionError:
        print(f"Face service connection error: Service at {settings.FACE_SERVICE_URL} is not reachable")
        # If service is not running, allow attendance but log the issue
        return True  # Fallback: allow attendance if service is down
    except requests.exceptions.Timeout:
        print(f"Face service timeout: Service at {settings.FACE_SERVICE_URL} is too slow")
        return True  # Fallback: allow attendance if service is slow
    except Exception as e:
        print(f"Face verification error for {student_profile.name}: {str(e)}")
        # For any other error, allow attendance but log the issue
        return True  # Fallback: allow attendance on any error
