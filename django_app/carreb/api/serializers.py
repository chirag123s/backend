from rest_framework import serializers
from .models import CarMakes, CarDetails, States, Vehicles

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
        fields = '__all__'

