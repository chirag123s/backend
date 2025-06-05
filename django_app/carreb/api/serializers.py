from rest_framework import serializers
from .models import CarMakes, CarDetails, States, Vehicles, CarSearchLog, VehicleImages, MyGarage, UserSubscription

class CampaignsSerializer(serializers.ModelSerializer):
    class Meta:
        model = CarMakes
        fields = '__all__'

class CarDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = CarDetails
        fields = '__all__'

class StatesSerializer(serializers.ModelSerializer):
    class Meta:
        model = States
        fields = '__all__'

class VehiclesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vehicles
        fields = ['vehicle_id', 'year', 'make', 'make_name', 'model', 'vehicle_class', 'body', 'doors', 'seats', 'engine', 'engine_capacity', 'engine_cylinder', 'induction', 'engine_type', 'fuel_grade', 'transmission', 'transmission_speed', 'transmission_type', 'drivetrain', 'tailpipe_comb', 'tailpipe_comb_value', 'tailpipe_comb_note', 'tailpipe_urban', 'tailpipe_urban_value', 'tailpipe_urban_note', 'tailpipe_extra', 'tailpipe_extra_value', 'tailpipe_extra_note', 'annual_cost', 'fuel_consumption_comb', 'fuel_consumption_urban', 'fuel_consumption_extra', 'energy_consumption', 'electric_range', 'air_pollution_standard', 'annual_tailpipe_co2', 'fuel_lifecycle_co2', 'noise_data']


class CarSearchLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = CarSearchLog
        fields = ['id',
            'uid',
            'save_money',
            'greener_car',
            'good_all_rounder',
            'budget',
            'state',
            'have_car',
            'make',
            'model',
            'year',
            'engine_type',
            'ip_address',
            'referral_code',
            'user_agent',
            'created_at',
            'updated_at'
        ]



class VehicleImagesSerializer(serializers.ModelSerializer):
    class Meta:
        model = VehicleImages
        fields = '__all__'

class MyGarageSerializer(serializers.ModelSerializer):
    class Meta:
        model = MyGarage
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at')


class UserSubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserSubscription
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at')


class SearchToGarageSerializer(serializers.Serializer):
    """Serializer for moving search log to user's garage"""
    search_uid = serializers.CharField(max_length=50)
    user_id = serializers.CharField(max_length=255)
    user_email = serializers.EmailField()
    nickname = serializers.CharField(max_length=100, required=False, allow_blank=True)
    is_current_car = serializers.BooleanField(default=False)
