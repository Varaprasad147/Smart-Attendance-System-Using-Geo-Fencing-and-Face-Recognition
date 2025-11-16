"""
URL patterns for the users app.
"""

from django.urls import path
from django.views.generic import RedirectView
from . import views

app_name = 'users'

# Template-based URLs
urlpatterns = [
    path('accounts/login/', RedirectView.as_view(url='/login/', permanent=False)),
    path('', views.dashboard_redirect, name='dashboard'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('super/dashboard/', views.super_dashboard, name='super_dashboard'),
    path('super/admins/', views.manage_admins, name='manage_admins'),
    path('super/admins/<uuid:admin_id>/edit/', views.edit_admin, name='edit_admin'),
    path('super/admins/<uuid:admin_id>/delete/', views.delete_admin, name='delete_admin'),
    path('super/settings/', views.admin_settings, name='admin_settings'),
    path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('student/dashboard/', views.student_dashboard, name='student_dashboard'),
    path('student/onboarding/', views.student_onboarding, name='student_onboarding'),
    path('student/profile/', views.student_profile, name='student_profile'),
    path('student/contact/', views.contact_admin, name='contact_admin'),
]

# API URLs
urlpatterns += []
