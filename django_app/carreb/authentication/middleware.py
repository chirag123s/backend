# Create: django_app/carreb/authentication/middleware.py
from django.utils.deprecation import MiddlewareMixin
from django.http import JsonResponse
import logging

logger = logging.getLogger(__name__)

class Auth0ErrorMiddleware(MiddlewareMixin):
    """
    Middleware to handle Auth0 authentication errors gracefully
    """
    
    def process_exception(self, request, exception):
        """Handle authentication exceptions"""
        if request.path.startswith('/api/'):
            from rest_framework.exceptions import AuthenticationFailed
            
            if isinstance(exception, AuthenticationFailed):
                return JsonResponse({
                    'error': 'authentication_failed',
                    'message': str(exception)
                }, status=401)
        return None
