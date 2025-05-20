import uuid
from django.db.models import Min
from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .services import ParseCarDetailsFromGG
from rest_framework.decorators import api_view
from .models import CarMakes, CarDetails, States
from .serializers import CarDetailsSerializer


class PraseCDGG(APIView):
    def get(self, request):
        file = request.FILES.get('file')

        if not file:
            return Response({"error": "No file uploaded."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            result = ParseCarDetailsFromGG(file)
            return Response(result, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
class StateListView(APIView):
    def get(self, request):
        states = State.objects.values('state_id', 'short_name', 'name').order_by('name')

        return Response({"states": list(states)}, status=status.HTTP_201_CREATED)

class CarMakes(APIView):
    def get(self, request):

        popular_cars = CarMake.objects.filter(popular=True).values("car_make_id", "name").order_by('name')
        all_cars = CarMake.objects.values("car_make_id", "name").order_by('name')

        # Replace 'car_make_id' with a random UUID
        popular_cars = [
            {
                "key": str(uuid.uuid4()),  # Generate random UUID
                "car_make_id": car["name"],
                "name": car["name"]
            }
            for car in popular_cars
        ]
        # Replace 'car_make_id' with a random UUID
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
        })

class CarModelListView(APIView):
    #def geT(self, request, make_name):
    def post(self, request):
        car_make = request.data.get('make')
        
        if car_make.startswith("p-"):
            car_make = car_make[2:]  # Remove the first two characters

        car_models = (
            CarDetail.objects
            .filter(make__icontains=car_make)
            .values("family")
            .annotate(car_model_id=Min("car_model_id"))  # Ensures distinct entries by selecting the smallest ID for each name
            .order_by("family")
        )
        return Response({"models": list(car_models)})

class CarVariantListView(APIView):
    #def get(self, request, make_name, model_name):
    def post(self, request):

        car_make = request.data.get('make')
        car_model = request.data.get('model')
    
        if car_make.startswith("p-"):
            car_make = car_make[2:] 

        car_variants = (
            CarDetail.objects
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

        return Response({"variants": list(car_variants)})

class CarSeriesListView(APIView):
    def post(self, request):

        car_make = request.data.get('make')
        car_model = request.data.get('model')
        car_variant = request.data.get('variant')
        #car_variant = '' if (car_variant == 'no variant') else car_variant

        if car_make.startswith("p-"):
            car_make = car_make[2:]  # Remove the first two characters

        if (car_variant == 'no variant'):
            car_series = (
                CarDetail.objects
                .filter(make__icontains=car_make, family__icontains=car_model, variant__exact='')
                .values("series")
                .annotate(car_model_id=Min("car_model_id"))
                .order_by("series")
            )
        else:
            car_series = (
                CarDetail.objects
                .filter(make__icontains=car_make, family__icontains=car_model, variant__icontains=car_variant)
                .values("series")
                .annotate(car_model_id=Min("car_model_id"))
                .order_by("series")
            )

        return Response({"series": list(car_series)})        


class CarMatchesListView(APIView):
    def post(self, request):

        car_make = request.data.get('make')
        car_model = request.data.get('model')
        car_variant = request.data.get('variant')
        car_series = request.data.get('series')

        if car_make.startswith("p-"):
            car_make = car_make[2:]  # Remove the first two characters

        if (car_variant == 'no variant'):
            matches = (
                CarDetail.objects
                .filter(make__icontains=car_make, family__icontains=car_model, variant__exact='', series__icontains=car_series)
                .all()
            )
        else:
            matches = (
                CarDetail.objects
                .filter(make__icontains=car_make, family__icontains=car_model, variant__icontains=car_variant, series__icontains=car_series)
                .all()
            )
        
        serializer = CarDetailSerializer(matches, many=True)
        return Response(serializer.data)
    
# Get suggested cars
class CarSuggestionListView(APIView):
    
    def post(self, request):

        car_id = request.data.get('car_id')

        matches = (
            CarDetail.objects
            .filter(car_model_id__icontains=car_id)
            .all()[:1]
        )

        for match in matches:
            suggestions = (
                CarDetail.objects
                .filter(style__icontains=match.style)
                .all()[:5]
            )

        #WHERE style='4D SPORTBACK' AND engine='TURBO DIRECT F/INJ' AND transmission='7 SP AUTO S-TRONIC'
        
        serializer = CarDetailSerializer(suggestions, many=True)
        return Response(serializer.data) 
    
