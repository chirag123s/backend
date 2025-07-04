from rest_framework import serializers
from .models import CarMakes, CarModels, CarVariants, CarPricing, CarDataRaw, CarDetails, CarBodyCost, States, Vehicles, CarSearchLog, VehicleImages, FuelRetailPrice

class CarMakesSerializer(serializers.ModelSerializer):
    class Meta:
        model = CarMakes
        fields = '__all__'

class CarVariantsSerializer(serializers.ModelSerializer):
    class Meta:
        model = CarVariants
        fields = '__all__'

class CarModelsSerializer(serializers.ModelSerializer):
    class Meta:
        model = CarModels
        fields = '__all__'

class CarPricingSerializer(serializers.ModelSerializer):
    class Meta:
        model = CarPricing
        fields = '__all__'

class CarDataRawSerializer(serializers.ModelSerializer):
    class Meta:
        model = CarDataRaw
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

class CarBodyCostSerializer(serializers.ModelSerializer):
    class Meta:
        model = CarBodyCost
        fields = ['id',
            'id',
            'type',
            'insurance_cost_comprehensive_annual_min',
            'insurance_cost_comprehensive_annual_max',
            'tyre_change_cost_per_tyre_min',
            'tyre_change_cost_per_tyre_max',
            'source'
        ]

class FuelRetailPriceSerializer(serializers.ModelSerializer):
    class Meta:
        model = FuelRetailPrice
        fields = ['id',
            'id',
            'fuel_type',
            'year_type',
            'year_from',
            'year_to',
            'nsw',
            'qld',
            'sa',
            'wa',
            'nt',
            'tas',
            'act',
            'national',
            'is_active'
        ]
