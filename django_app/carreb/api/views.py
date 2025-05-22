import uuid
from django.db.models import Min
from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .services import ParseCarDetailsFromGG
from rest_framework.decorators import api_view
from .models import CarMakes, CarDetails, States, Vehicles
from .serializers import CarDetailsSerializer

# Import authentication and permissions
from rest_framework.decorators import permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
# Note: Comment out these imports until you implement the authentication app
# from authentication.permissions import HasRequiredScope, requires_scope

import logging

logger = logging.getLogger(__name__)


class PraseCDGG(APIView):
    """
    File parsing endpoint - typically should be admin-only in production
    """
    permission_classes = [IsAuthenticated]  # Protect this endpoint
    
    def post(self, request):  # Changed from GET to POST as it's processing file uploads
        try:
            file = request.FILES.get('file')

            if not file:
                return Response(
                    {"error": "No file uploaded."}, 
                    status=status.HTTP_400_BAD_REQUEST
                )

            result = ParseCarDetailsFromGG(file)
            logger.info(f"File parsed successfully by user {request.user.username}")
            return Response(result, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"File parsing error: {str(e)}", exc_info=True)
            return Response(
                {"error": "File processing failed"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class StateListView(APIView):
    """
    Public endpoint to get list of states
    """
    permission_classes = [AllowAny]  # Public endpoint
    
    def get(self, request):
        try:
            states = States.objects.values('state_id', 'short_name', 'name').order_by('name')
            return Response({"states": list(states)}, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error fetching states: {str(e)}", exc_info=True)
            return Response(
                {"error": "Failed to fetch states"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class GetCarMakesListView(APIView):
    """
    Protected endpoint to get car makes
    """
    permission_classes = [IsAuthenticated]  # Requires authentication
    
    def get(self, request):
        try:
            # The user is available as request.user (Auth0 user ID)
            user_id = request.user.username
            logger.info(f"Car makes requested by user: {user_id}")
            
            popular_cars = CarMakes.objects.filter(popular=True).values("car_make_id", "name").order_by('name')
            all_cars = CarMakes.objects.values("car_make_id", "name").order_by('name')

            # Replace 'car_make_id' with a random UUID
            popular_cars = [
                {
                    "key": str(uuid.uuid4()),  # Generate random UUID
                    "car_make_id": car["name"],
                    "name": car["name"]
                }
                for car in popular_cars
            ]
            
            all_cars = [
                {
                    "key": str(uuid.uuid4()),  # Generate random UUID
                    "car_make_id": car["name"],
                    "name": car["name"]
                }
                for car in all_cars
            ]

            return Response({
                "popular": list(popular_cars),
                "all": list(all_cars)
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error fetching car makes: {str(e)}", exc_info=True)
            return Response(
                {"error": "Failed to fetch car makes"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class GetCarModelListView(APIView):
    """
    Protected endpoint to get car models based on make
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            car_make = request.data.get('make')
            
            if not car_make:
                return Response(
                    {"error": "Make parameter is required"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            if car_make.startswith("p-"):
                car_make = car_make[2:]  # Remove the first two characters

            car_models = (
                Vehicles.objects
                .filter(make_name__icontains=car_make)
                .values("model")
                .annotate(id=Min("id"))  # Ensures distinct entries
                .order_by("model")
            )
            
            return Response({"models": list(car_models)}, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error fetching car models: {str(e)}", exc_info=True)
            return Response(
                {"error": "Failed to fetch car models"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class GetCarYearListView(APIView):
    """
    Protected endpoint to get car years based on make and model
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            car_make = request.data.get('make')
            car_model = request.data.get('model')
            
            if not car_make or not car_model:
                return Response(
                    {"error": "Make and model parameters are required"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            if car_make.startswith("p-"):
                car_make = car_make[2:]  # Remove the first two characters

            car_years = (
                Vehicles.objects
                .filter(make_name__icontains=car_make, model__icontains=car_model)
                .values("year")
                .annotate(id=Min("id"))  # Ensures distinct entries
                .order_by("-year")
            )
            
            return Response({"years": list(car_years)}, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error fetching car years: {str(e)}", exc_info=True)
            return Response(
                {"error": "Failed to fetch car years"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class GetCarEngineTypeListView(APIView):
    """
    Protected endpoint to get engine types based on make, model, and year
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            car_make = request.data.get('make')
            car_model = request.data.get('model')
            car_year = request.data.get('year')
            
            if not all([car_make, car_model, car_year]):
                return Response(
                    {"error": "Make, model, and year parameters are required"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            if car_make.startswith("p-"):
                car_make = car_make[2:]  # Remove the first two characters

            car_engine_types = (
                Vehicles.objects
                .filter(make_name__icontains=car_make, model__icontains=car_model, year__icontains=car_year)
                .values("engine_type")
                .annotate(id=Min("id"))  # Ensures distinct entries
                .order_by("engine_type")
            )
            
            return Response({"engine_types": list(car_engine_types)}, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error fetching engine types: {str(e)}", exc_info=True)
            return Response(
                {"error": "Failed to fetch engine types"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class CarVariantListView(APIView):
    """
    Protected endpoint to get car variants
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            car_make = request.data.get('make')
            car_model = request.data.get('model')
            
            if not car_make or not car_model:
                return Response(
                    {"error": "Make and model parameters are required"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
        
            if car_make.startswith("p-"):
                car_make = car_make[2:] 

            car_variants = (
                CarDetails.objects
                .filter(make__icontains=car_make, family__icontains=car_model)
                .values("variant")
                .annotate(car_model_id=Min("car_model_id"))
                .order_by("variant")
            )

            car_variants = [
                {
                    "car_model_id": car["car_model_id"],
                    "variant": 'no variant' if (car["variant"] == '') else car["variant"],
                }
                for car in car_variants
            ]

            return Response({"variants": list(car_variants)}, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error fetching car variants: {str(e)}", exc_info=True)
            return Response(
                {"error": "Failed to fetch car variants"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class CarSeriesListView(APIView):
    """
    Protected endpoint to get car series
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            car_make = request.data.get('make')
            car_model = request.data.get('model')
            car_variant = request.data.get('variant')
            
            if not all([car_make, car_model, car_variant]):
                return Response(
                    {"error": "Make, model, and variant parameters are required"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )

            if car_make.startswith("p-"):
                car_make = car_make[2:]  # Remove the first two characters

            if car_variant == 'no variant':
                car_series = (
                    CarDetails.objects
                    .filter(make__icontains=car_make, family__icontains=car_model, variant__exact='')
                    .values("series")
                    .annotate(car_model_id=Min("car_model_id"))
                    .order_by("series")
                )
            else:
                car_series = (
                    CarDetails.objects
                    .filter(make__icontains=car_make, family__icontains=car_model, variant__icontains=car_variant)
                    .values("series")
                    .annotate(car_model_id=Min("car_model_id"))
                    .order_by("series")
                )

            return Response({"series": list(car_series)}, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error fetching car series: {str(e)}", exc_info=True)
            return Response(
                {"error": "Failed to fetch car series"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class CarMatchesListView(APIView):
    """
    Protected endpoint with scope requirement to get car matches
    """
    permission_classes = [IsAuthenticated]
    # Uncomment when you implement the authentication app:
    # permission_classes = [IsAuthenticated, HasRequiredScope]
    # required_scopes = ['read:cars']  # Requires 'read:cars' scope
    
    def post(self, request):
        try:
            car_make = request.data.get('make')
            car_model = request.data.get('model')
            car_variant = request.data.get('variant')
            car_series = request.data.get('series')

            if not all([car_make, car_model, car_variant, car_series]):
                return Response(
                    {"error": "Make, model, variant, and series parameters are required"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )

            if car_make.startswith("p-"):
                car_make = car_make[2:]  # Remove the first two characters

            if car_variant == 'no variant':
                matches = (
                    CarDetails.objects
                    .filter(make__icontains=car_make, family__icontains=car_model, variant__exact='', series__icontains=car_series)
                    .all()
                )
            else:
                matches = (
                    CarDetails.objects
                    .filter(make__icontains=car_make, family__icontains=car_model, variant__icontains=car_variant, series__icontains=car_series)
                    .all()
                )
            
            serializer = CarDetailsSerializer(matches, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error fetching car matches: {str(e)}", exc_info=True)
            return Response(
                {"error": "Failed to fetch car matches"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class CarSuggestionListView(APIView):
    """
    Protected endpoint to get car suggestions
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            car_id = request.data.get('car_id')
            
            if not car_id:
                return Response(
                    {"error": "car_id parameter is required"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Get the car to base suggestions on
            matches = (
                CarDetails.objects
                .filter(car_model_id__icontains=car_id)
                .all()[:1]
            )

            if not matches:
                return Response(
                    {"error": "Car not found"}, 
                    status=status.HTTP_404_NOT_FOUND
                )

            # Get suggestions based on the first match
            match = matches[0]
            suggestions = (
                CarDetails.objects
                .filter(style__icontains=match.style)
                .exclude(car_model_id=car_id)  # Exclude the original car
                .all()[:5]
            )
            
            serializer = CarDetailsSerializer(suggestions, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error fetching car suggestions: {str(e)}", exc_info=True)
            return Response(
                {"error": "Failed to fetch car suggestions"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# Test endpoints for authentication
class TestAuthView(APIView):
    """
    Test endpoint to verify authentication is working
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        return Response({
            'message': 'Hello authenticated user!',
            'user_id': request.user.username,
            'email': getattr(request.user, 'email', 'N/A'),
            'is_authenticated': request.user.is_authenticated
        }, status=status.HTTP_200_OK)


class TestPublicView(APIView):
    """
    Test endpoint that doesn't require authentication
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        return Response({
            'message': 'Hello from public endpoint!',
            'is_authenticated': request.user.is_authenticated if hasattr(request, 'user') else False
        }, status=status.HTTP_200_OK)