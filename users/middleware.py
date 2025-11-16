from django.shortcuts import redirect


class BlockAdminForNonSuperuserMiddleware:
	"""
	Redirect authenticated non-superuser users away from Django admin (/admin).
	Allows only superusers to access the Django admin site.
	"""

	def __init__(self, get_response):
		self.get_response = get_response

	def __call__(self, request):
		# Intercept ONLY Django admin (namespace 'admin'), not our app routes
		if request.path.startswith('/admin/'):
			user = getattr(request, 'user', None)
			match = getattr(request, 'resolver_match', None)
			is_django_admin = False
			if match is not None:
				# Django admin URLs are namespaced as 'admin'
				is_django_admin = (getattr(match, 'namespace', '') == 'admin') or ('admin' in getattr(match, 'app_names', []))

			# Only redirect when it's truly Django admin and user is not superuser
			if is_django_admin and user is not None and user.is_authenticated and not user.is_superuser:
				# Avoid redirect loop if already at the destination
				from django.urls import reverse
				dest = reverse('users:admin_dashboard')
				if request.path != dest:
					return redirect('users:admin_dashboard')

		return self.get_response(request)


