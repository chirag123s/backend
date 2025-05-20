from rest_framework import serializers
from .models import GVGVehicleData

class GVGVehicleDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = GVGVehicleData
        fields = '__all__'
