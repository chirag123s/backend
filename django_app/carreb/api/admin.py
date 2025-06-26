from django.contrib import admin
from .models import CarMakes, CarVariants, CarModels, CarPricing
# Register your models here.


@admin.register(CarMakes)
class CarMakesAdmin(admin.ModelAdmin):
    list_display = ['car_make_id','name','slug','is_popular','is_active','grok_json','created_at','updated_at']
    search_fields = ['name']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(CarVariants)
class CarVariantsAdmin(admin.ModelAdmin):
    list_display = ['id', 'car_make', 'model','variant', 'image_url', 'image', 'sub_variant', 'sub_variants', 'no_doors', 'no_seats', 'battery_capacity_kwh', 'drivetrain', 'body_type', 'total_range_km', 'co2_emissions_combined_g_km', 'fuel_efficiency_combined_l_100km', 'estimated_5yr_dealer_servicing_cost', 'estimated_5yr_resale_value', 'is_active', 'created_at', 'updated_at' ]
    list_filter = ['car_make', 'model', 'variant']
    search_fields = ['car_make', 'model', 'variant']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(CarPricing)
class CarPricingAdmin(admin.ModelAdmin):
    list_display = ['id','car_variant_id','state','msrp','drive_away_price','drive_away_price_with_cost','stamp_duty','registration','ctp','govt_incentives','dealer_delivery_charges']
    #list_filter = ['car_make', 'model']
    #search_fields = ['car_make__name', 'model', 'variant']
    #readonly_fields = ['created_at', 'updated_at']

@admin.register(CarModels)
class CarModelsAdmin(admin.ModelAdmin):
    list_display = ['id', 'make','model','year','vehicle_class','grok_raw','created_at','updated_at']
    list_filter = ['make', 'model']
    list_filter = ['make', 'model']
    readonly_fields = ['created_at', 'updated_at']