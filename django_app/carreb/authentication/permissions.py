from rest_framework.permissions import BasePermission
import jwt
import logging

logger = logging.getLogger(__name__)

class HasRequiredScope(BasePermission):
    """
    Custom permission to check Auth0 scopes
    Usage: @permission_classes([HasRequiredScope])
    Set required_scopes as class attribute or method parameter
    """
    required_scopes = []
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
            
        # Get token from request
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        if not auth_header.startswith('Bearer '):
            return False
            
        token = auth_header.split(' ')[1]
        
        try:
            # Decode token without verification (we already verified it in authentication)
            payload = jwt.decode(token, options={"verify_signature": False})
            token_scopes = payload.get('scope', '').split()
            
            # Check if any required scope is present
            required_scopes = getattr(view, 'required_scopes', self.required_scopes)
            if not required_scopes:
                return True
                
            return any(scope in token_scopes for scope in required_scopes)
            
        except Exception as e:
            logger.warning(f"Error checking scopes: {str(e)}")
            return False

def requires_scope(*scopes):
    """
    Decorator for view methods that require specific Auth0 scopes
    Usage: @requires_scope('read:cars', 'write:cars')
    """
    def decorator(view_func):
        def wrapped_view(self, request, *args, **kwargs):
            if not hasattr(self, 'required_scopes'):
                self.required_scopes = list(scopes)
            else:
                self.required_scopes.extend(scopes)
            return view_func(self, request, *args, **kwargs)
        return wrapped_view
    return decorator
