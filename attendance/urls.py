"""
URL patterns for the attendance app.
"""

from django.urls import path
from . import views

app_name = 'attendance'
 
# Template-based URLs
urlpatterns = [
    # Admin URLs
    path('admin/students/upload/', views.upload_students, name='upload_students'),
    path('admin/students/manage/', views.manage_students, name='manage_students'),
    path('admin/companies/', views.manage_companies, name='manage_companies'),
    path('admin/companies/<uuid:company_id>/edit/', views.edit_company, name='edit_company'),
    path('admin/companies/<uuid:company_id>/delete/', views.delete_company, name='delete_company'),
    path('admin/analytics/', views.attendance_analytics, name='attendance_analytics'),
    path('admin/export/', views.export_attendance, name='export_attendance'),
    path('admin/contact-messages/', views.contact_messages, name='contact_messages'),
    
    # Student URLs
    path('student/attendance/mark/', views.mark_attendance_view, name='mark_attendance_view'),
]

# API URLs
api_urlpatterns = [
    path('attendance/mark/', views.api_mark_attendance, name='api_mark_attendance'),
    path('attendance/history/', views.api_attendance_history, name='api_attendance_history'),
]

urlpatterns += api_urlpatterns
