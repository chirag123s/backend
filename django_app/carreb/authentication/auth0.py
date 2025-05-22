import json
import jwt
import requests
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.conf import settings
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from functools import lru_cache
import logging

logger = logging.getLogger(__name__)
User = get_user_model()

class Auth0JSONWebTokenAuthentication(BaseAuthentication):
    """
    Production-ready Auth0 JWT Authentication for Django REST Framework
    
    This class handles:
    - JWT token validation using Auth0's public keys
    - Automatic user creation/retrieval
    - Proper error handling and logging
    - JWKS caching for performance
    """
    
    authentication_header_prefix = 'Bearer'
    
    def authenticate(self, request):
        """
        Authenticate the request and return a two-tuple of (user, token).
        """
        auth_header = self.get_authorization_header(request)
        if not auth_header:
            return None
            
        try:
            token = self.get_token_from_header(auth_header)
            if not token:
                return None
                
            payload = self.decode_jwt(token)
            user = self.get_or_create_user(payload)
            
            return (user, token)
            
        except AuthenticationFailed:
            raise
        except Exception as e:
            logger.error(f"Unexpected authentication error: {str(e)}", exc_info=True)
            raise AuthenticationFailed('Authentication failed')
    
    def get_authorization_header(self, request):
        """Extract authorization header from request"""
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        return auth_header.encode('iso-8859-1') if auth_header else None
    
    def get_token_from_header(self, auth_header):
        """Extract JWT token from authorization header"""
        try:
            auth_header = auth_header.decode('iso-8859-1')
            auth = auth_header.split()
            
            if not auth or auth[0].lower() != self.authentication_header_prefix.lower():
                return None
                
            if len(auth) == 1:
                raise AuthenticationFailed('Invalid token header. No credentials provided.')
            
            if len(auth) > 2:
                raise AuthenticationFailed('Invalid token header. Token string should not contain spaces.')
                
            return auth[1]
            
        except UnicodeError:
            raise AuthenticationFailed('Invalid token header. Token string should not contain invalid characters.')
    
    @lru_cache(maxsize=1)
    def get_jwks(self):
        """Fetch and cache JWKS from Auth0"""
        try:
            jwks_url = f"https://{settings.AUTH0_DOMAIN}/.well-known/jwks.json"
            response = requests.get(jwks_url, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch JWKS: {str(e)}")
            raise AuthenticationFailed('Unable to verify token')
    
    def get_rsa_key(self, token):
        """Get RSA public key for token verification"""
        try:
            unverified_header = jwt.get_unverified_header(token)
            jwks = self.get_jwks()
            
            for key in jwks['keys']:
                if key['kid'] == unverified_header['kid']:
                    return {
                        'kty': key['kty'],
                        'kid': key['kid'],
                        'use': key['use'],
                        'n': key['n'],
                        'e': key['e']
                    }
            
            raise AuthenticationFailed('Unable to find appropriate key')
            
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token header: {str(e)}")
            raise AuthenticationFailed('Invalid token header')
        except KeyError as e:
            logger.error(f"JWKS key error: {str(e)}")
            raise AuthenticationFailed('Invalid token')
    
    def decode_jwt(self, token):
        """Decode and validate JWT token"""
        try:
            rsa_key = self.get_rsa_key(token)
            
            # Convert RSA key to PEM format for PyJWT
            public_key = jwt.algorithms.RSAAlgorithm.from_jwk(json.dumps(rsa_key))
            
            # Decode and validate token
            payload = jwt.decode(
                token,
                public_key,
                algorithms=['RS256'],
                audience=settings.AUTH0_API_IDENTIFIER,
                issuer=f"https://{settings.AUTH0_DOMAIN}/"
            )
            
            return payload
            
        except jwt.ExpiredSignatureError:
            raise AuthenticationFailed('Token has expired')
        except jwt.InvalidAudienceError:
            raise AuthenticationFailed('Invalid token audience')
        except jwt.InvalidIssuerError:
            raise AuthenticationFailed('Invalid token issuer')
        except jwt.InvalidSignatureError:
            raise AuthenticationFailed('Invalid token signature')
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token: {str(e)}")
            raise AuthenticationFailed('Invalid token')
    
    def get_or_create_user(self, payload):
        """Get or create Django user from Auth0 payload"""
        try:
            # Extract user info from payload
            auth0_user_id = payload.get('sub')
            email = payload.get('email', '')
            username = payload.get('nickname', auth0_user_id)
            
            if not auth0_user_id:
                raise AuthenticationFailed('Token missing user identifier')
            
            # Try to get existing user
            try:
                user = User.objects.get(username=auth0_user_id)
                # Update email if changed
                if email and user.email != email:
                    user.email = email
                    user.save()
                return user
            except User.DoesNotExist:
                # Create new user
                user = User.objects.create_user(
                    username=auth0_user_id,
                    email=email,
                    first_name=payload.get('given_name', ''),
                    last_name=payload.get('family_name', '')
                )
                logger.info(f"Created new user from Auth0: {auth0_user_id}")
                return user
                
        except Exception as e:
            logger.error(f"Error creating/retrieving user: {str(e)}", exc_info=True)
            raise AuthenticationFailed('Authentication failed')
