import uuid
import random
from django.conf import settings
from django.db.models import Min
from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .services import ParseCarDetailsFromGG
from rest_framework.decorators import api_view
from .models import CarMakes, CarDetails, States, Vehicles, CarSearchLog, VehicleImages
from .serializers import CarDetailsSerializer, VehiclesSerializer, CarSearchLogSerializer
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from .models import MyGarage, UserSubscription
from .serializers import MyGarageSerializer, UserSubscriptionSerializer, SearchToGarageSerializer
from .integration_service import CarRebIntegrationService

class ParseCDGG(APIView):
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
        states = States.objects.values('state_id', 'short_name', 'name').order_by('name')

        return Response({"states": list(states)}, status=status.HTTP_201_CREATED)

class GetCarMakesListView(APIView):
    def get(self, request):

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

class GetCarModelListView(APIView):
    #def geT(self, request, make_name):
    def post(self, request):
        car_make = request.data.get('make')
        
        if car_make.startswith("p-"):
            car_make = car_make[2:]  # Remove the first two characters

        car_models = (
            Vehicles.objects
            .filter(make_name__icontains=car_make)
            .values("model")
            .annotate(id=Min("id"))  # Ensures distinct entries by selecting the smallest ID for each name
            .order_by("model")
        )
        return Response({"models": list(car_models)})


# Return Year list based on vehicle Make and Model
class GetCarYearListView(APIView):
    #def geT(self, request, make_name):
    def post(self, request):
        
        car_make = request.data.get('make')
        car_model = request.data.get('model')
        
        if car_make.startswith("p-"):
            car_make = car_make[2:]  # Remove the first two characters

        car_years = (
            Vehicles.objects
            .filter(make_name__icontains=car_make, model__icontains=car_model)
            .values("year")
            .annotate(id=Min("id"))  # Ensures distinct entries by selecting the smallest ID for each name
            .order_by("-year")
        )
        return Response({"years": list(car_years)})

# Return Engine Type list based on vehicle Make, Model and Year
class GetCarEngineTypeListView(APIView):
    #def geT(self, request, make_name):
    def post(self, request):
        
        car_make = request.data.get('make')
        car_model = request.data.get('model')
        car_year = request.data.get('year')
        
        if car_make.startswith("p-"):
            car_make = car_make[2:]  # Remove the first two characters

        car_engine_types = (
            Vehicles.objects
            .filter(make_name__icontains=car_make, model__icontains=car_model, year__icontains=car_year)
            .values("engine_type")
            .annotate(id=Min("id"))  # Ensures distinct entries by selecting the smallest ID for each name
            .order_by("engine_type")
        )
        return Response({"engine_types": list(car_engine_types)})
    

class CarVariantListView(APIView):
    #def get(self, request, make_name, model_name):
    def post(self, request):

        car_make = request.data.get('make')
        car_model = request.data.get('model')
    
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
        return Response(serializer.data)
    
# Get suggested cars
class CarSuggestionListView(APIView):
    
    def post(self, request):

        car_id = request.data.get('car_id')

        matches = (
            CarDetails.objects
            .filter(car_model_id__icontains=car_id)
            .all()[:1]
        )

        for match in matches:
            suggestions = (
                CarDetails.objects
                .filter(style__icontains=match.style)
                .all()[:5]
            )

        #WHERE style='4D SPORTBACK' AND engine='TURBO DIRECT F/INJ' AND transmission='7 SP AUTO S-TRONIC'
        
        serializer = CarDetailsSerializer(suggestions, many=True)
        return Response(serializer.data) 
    


# Get suggested match
class GetCarMatchView(APIView):
    
    def post(self, request, *args, **kwargs):

        save_money = request.data.get('save_money')
        greener_car = request.data.get('greener_car')
        good_all_rounder = request.data.get('good_all_rounder')
        budget = round(float(request.data.get('budget')), 2) if (request.data.get('budget')) else 0
        state = request.data.get('state')
        have_car = request.data.get('have_car')
        make = request.data.get('make')
        model = request.data.get('model')
        year = request.data.get('year')
        engine_type = request.data.get('engine_type')
        #return Response({"data": request.data }, status=status.HTTP_201_CREATED)
    
        if make.startswith("p-"):
            make = make[2:]  # Remove the first two characters

        """
        match = (
            Vehicles.objects
            .filter(make_name=make, model=model, year=year, engine_type=engine_type)
            # .all()[:1]
        )

        if match: 
            serializer = VehiclesSerializer(match, many=True)
            return Response({"data": serializer.data}, status=status.HTTP_201_CREATED)
            
        else:
            return Response({"data": 'none'}, status=status.HTTP_201_CREATED)"""

        ip = self.get_client_ip(request)
        ref = request.data.get('ref') or request.query_params.get('ref')
        user_agent = request.META.get('HTTP_USER_AGENT', '')

        log = CarSearchLog.objects.create(
            uid=str(uuid.uuid4()),
            save_money=save_money,
            greener_car=greener_car,
            good_all_rounder=good_all_rounder,
            budget=budget,
            state=state,
            have_car=have_car,
            make=make,
            model=model,
            year=year,
            engine_type=engine_type,
            ip_address=ip,
            referral_code=ref,
            user_agent=user_agent
        )

        #serializer = CarSearchLogSerializer(log)
        #return Response(serializer.data, status=status.HTTP_201_CREATED)

        response = Response({'status': 'ok', 'crb_uid': log.uid}, status=status.HTTP_200_OK)
        response.set_cookie(
            key='crb_uid',
            value=log.uid,
            httponly=False,       # Set to False if you want client-side access
            secure=False,           #settings.COOKIE_SECURE,         # Set to True if using HTTPS
            samesite='Lax',       # Or 'Strict'/'None'
            max_age=60 * 60 * 24,  # 1 day
            path='/'
        )
        response['Access-Control-Allow-Credentials'] = 'true'
        return response
    
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


# Get suggested match
class GetCarMatchBySIDView(APIView):
    def post(self, request):
        search_id = request.data.get('sid')
        have_car = False
        data = {}

        try:
            search_log = CarSearchLog.objects.get(uid=search_id)
            have_car = search_log.have_car
            serializer = CarSearchLogSerializer(search_log)
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        except ObjectDoesNotExist:
            return Response({"detail": "Search log not found."}, status=status.HTTP_404_NOT_FOUND)
            have_car = False

        """
        except MultipleObjectsReturned:
            return Response({"detail": "Multiple entries found."}, status=status.HTTP_400_BAD_REQUEST)"""        

        response = 'ok'
        if (have_car):
            vehicle = Vehicles.objects.filter(
                make_name=search_log.make, 
                model=search_log.model, 
                year=search_log.year, 
                engine_type=search_log.engine_type).first()
                
        else:
            if search_log.vehicle_id:
                vehicle = Vehicles.objects.filter(vehicle_id=search_log.vehicle_id).first()

            else:

                # temporary car selection
                # replace with actual car search based on car score
                vehicle = Vehicles.objects.order_by('?').first()

        if vehicle:
            if not search_log.vehicle_id:
                search_log.vehicle_id = vehicle.vehicle_id
                search_log.save()

            serializer = VehiclesSerializer(vehicle)
            data = serializer.data
            
            image = VehicleImages.objects.filter(vehicle_id=vehicle.vehicle_id).first()

            if (image and image.image_name and image.image_name.strip() != '-'):
                data['image'] = image.image_name
            else:
                data['image'] = '/images/car-icon-1.png'

            # temp, replace with actual value
            data['coo'] = random.randint(10000, 999999)
            data['co2'] = data['tailpipe_comb_value']
            data['rating'] = random.randint(10000, 999999)
            data['starRating']= random.randint(1, 5)
            data['savings'] = random.randint(10, 9999)

        else:
            response = 'empty'
            data = {
                'make': 'no matching car'
            }
        
        return Response({"status": response, 'data': data }, status=status.HTTP_200_OK)

class MoveSearchToGarageView(APIView):
    """Move a search log entry to user's garage after successful signup"""
    
    def post(self, request):
        serializer = SearchToGarageSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            search_log = CarSearchLog.objects.get(uid=serializer.validated_data['search_uid'])
            
            garage_entry = MyGarage.objects.create(
                user_id=serializer.validated_data['user_id'],
                user_email=serializer.validated_data['user_email'],
                save_money=search_log.save_money,
                greener_car=search_log.greener_car,
                good_all_rounder=search_log.good_all_rounder,
                budget=search_log.budget,
                state=search_log.state,
                have_car=search_log.have_car,
                make=search_log.make,
                model=search_log.model,
                year=search_log.year,
                engine_type=search_log.engine_type,
                vehicle_id=search_log.vehicle_id,
                original_search_uid=serializer.validated_data['search_uid'],
                is_current_car=serializer.validated_data.get('is_current_car', False),
                nickname=serializer.validated_data.get('nickname', ''),
                ip_address=search_log.ip_address,
                user_agent=search_log.user_agent
            )
            
            return Response({
                'status': 'success',
                'garage_entry': MyGarageSerializer(garage_entry).data
            }, status=status.HTTP_201_CREATED)
            
        except CarSearchLog.DoesNotExist:
            return Response({'error': 'Search log not found'}, status=status.HTTP_404_NOT_FOUND)

class UserGarageView(APIView):
    """List user's garage entries"""
    
    def get(self, request):
        user_id = request.query_params.get('user_id')
        if not user_id:
            return Response({'error': 'user_id parameter required'}, status=status.HTTP_400_BAD_REQUEST)
        
        garage_entries = MyGarage.objects.filter(user_id=user_id).order_by('-created_at')
        serializer = MyGarageSerializer(garage_entries, many=True)
        
        return Response({'garage': serializer.data}, status=status.HTTP_200_OK)


class UserSubscriptionView(APIView):
    """Create user subscription record with search link"""
    
    def post(self, request):
        try:
            user_id = request.data.get('user_id')
            user_email = request.data.get('user_email')
            payment_uuid = request.data.get('payment_uuid')
            search_uid = request.data.get('search_uid')
            plan_name = request.data.get('plan_name')
            
            if not all([user_id, user_email, plan_name]):
                return Response({
                    'error': 'user_id, user_email, and plan_name are required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            subscription = UserSubscription.objects.create(
                user_id=user_id,
                user_email=user_email,
                payment_uuid=payment_uuid,
                search_uid=search_uid,
                plan_name=plan_name
            )
            
            serializer = UserSubscriptionSerializer(subscription)
            return Response({
                'status': 'success',
                'subscription': serializer.data
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response({
                'status': 'error',
                'message': f'Error creating subscription: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class SearchShareableView(APIView):
    """Get shareable search data by uid (for social sharing)"""
    
    def get(self, request, search_uid):
        try:
            search_log = CarSearchLog.objects.get(uid=search_uid)
            
            # Get vehicle data if available
            vehicle_data = None
            if search_log.vehicle_id:
                try:
                    vehicle = Vehicles.objects.get(vehicle_id=search_log.vehicle_id)
                    vehicle_serializer = VehiclesSerializer(vehicle)
                    vehicle_data = vehicle_serializer.data
                    
                    # Add image
                    image = VehicleImages.objects.filter(vehicle_id=vehicle.vehicle_id).first()
                    if image and image.image_name and image.image_name.strip() != '-':
                        vehicle_data['image'] = image.image_name
                    else:
                        vehicle_data['image'] = '/images/car-icon-1.png'
                        
                except Vehicles.DoesNotExist:
                    pass
            
            search_serializer = CarSearchLogSerializer(search_log)
            
            return Response({
                'status': 'success',
                'search_data': search_serializer.data,
                'vehicle_data': vehicle_data,
                'shareable_url': f"/smart-car-finder?sid={search_uid}"
            }, status=status.HTTP_200_OK)
            
        except CarSearchLog.DoesNotExist:
            return Response({
                'status': 'error',
                'message': 'Search not found'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                'status': 'error',
                'message': f'Error retrieving shareable data: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class PaymentSuccessIntegrationView(APIView):
    """Handle post-payment integration"""
    
    def post(self, request):
        payment_uuid = request.data.get('payment_uuid')
        user_id = request.data.get('user_id')
        user_email = request.data.get('user_email')
        search_uid = request.data.get('search_uid')  # Can come from payment metadata or direct
        
        if not all([user_id, user_email]):
            return Response({'error': 'user_id and user_email required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Create subscription record
            subscription = UserSubscription.objects.create(
                user_id=user_id,
                user_email=user_email,
                payment_uuid=payment_uuid,
                search_uid=search_uid,
                plan_name=request.data.get('plan_name', 'Unknown')
            )
            
            garage_entry = None
            if search_uid:
                try:
                    search_log = CarSearchLog.objects.get(uid=search_uid)
                    garage_entry = MyGarage.objects.create(
                        user_id=user_id,
                        user_email=user_email,
                        save_money=search_log.save_money,
                        greener_car=search_log.greener_car,
                        good_all_rounder=search_log.good_all_rounder,
                        budget=search_log.budget,
                        state=search_log.state,
                        have_car=search_log.have_car,
                        make=search_log.make,
                        model=search_log.model,
                        year=search_log.year,
                        engine_type=search_log.engine_type,
                        vehicle_id=search_log.vehicle_id,
                        original_search_uid=search_uid,
                        is_current_car=search_log.have_car,
                        nickname=f"{search_log.make} {search_log.model}" if search_log.make else "My Car",
                        ip_address=search_log.ip_address,
                        user_agent=search_log.user_agent
                    )
                except CarSearchLog.DoesNotExist:
                    pass
            
            return Response({
                'status': 'success',
                'subscription_id': subscription.id,
                'garage_entry_id': garage_entry.id if garage_entry else None
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



class UserDashboardView(APIView):
    """Get user dashboard data including garage and subscriptions"""
    
    def get(self, request):
        user_id = request.query_params.get('user_id')
        
        if not user_id:
            return Response({
                'status': 'error',
                'message': 'user_id parameter is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            dashboard_data = CarRebIntegrationService.get_user_dashboard_data(user_id)
            
            if dashboard_data['status'] == 'success':
                return Response(dashboard_data, status=status.HTTP_200_OK)
            else:
                return Response(dashboard_data, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            #logger.error(f"Error getting dashboard data: {str(e)}", exc_info=True)
            return Response({
                'status': 'error',
                'message': f'Dashboard error: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CreateShareableLinkView(APIView):
    """Create a shareable link for search results"""
    
    def post(self, request):
        search_uid = request.data.get('search_uid')
        
        if not search_uid:
            return Response({
                'status': 'error',
                'message': 'search_uid is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            result = CarRebIntegrationService.create_shareable_link(search_uid)
            
            if result['status'] == 'success':
                return Response(result, status=status.HTTP_200_OK)
            else:
                return Response(result, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            #logger.error(f"Error creating shareable link: {str(e)}", exc_info=True)
            return Response({
                'status': 'error',
                'message': f'Shareable link error: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

