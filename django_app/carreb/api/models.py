from django.db import models

# Create your models here.
class CarMakes(models.Model):
    car_make_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    slug = models.CharField(max_length=255)
    popular = models.BooleanField(default=0)
    active = models.BooleanField(default=1)

    class Meta:
        db_table = 'car_makes'

    def __str__(self):
        return self.name


# Car Details
class CarDetails(models.Model):
    car_model_id = models.AutoField(primary_key=True)
    make = models.CharField(max_length=23)    # field5
    family = models.CharField(max_length=25)    # field6
    variant = models.CharField(max_length=31)    # field7
    series = models.CharField(max_length=23)    # field8
    style = models.CharField(max_length=23)    # field9
    engine = models.CharField(max_length=25)   # field10
    cc = models.CharField(max_length=5)    # field11
    size = models.CharField(max_length=6)    # field12
    transmission = models.CharField(max_length=21)   # field13
    cylinder = models.CharField(max_length=5)    # field14
    width = models.CharField(max_length=6)    # field15
    year = models.CharField(max_length=5)    # field17
    month = models.CharField(max_length=4)     # field4

    class Meta:
        db_table = 'car_details'

    def __str__(self):
        return f"{self.make} {self.family}"

# States
class States(models.Model):
    state_id  = models.AutoField(primary_key=True)
    short_name = models.CharField(max_length=5)
    name = models.CharField(max_length=50)

    class Meta:
        db_table = "states"

    def __str__(self):
        return self.name

# Vehicles
class Vehicles(models.Model):
    id = models.AutoField(primary_key=True)
    vehicle_id = models.CharField(max_length=20, null=True, blank=True)
    year = models.CharField(max_length=5, null=True, blank=True)
    make = models.CharField(max_length=255, null=True, blank=True)
    make_name = models.CharField(max_length=255, null=True, blank=True)
    model = models.CharField(max_length=255, null=True, blank=True)
    vehicle_class = models.CharField(max_length=50, null=True, blank=True)
    body = models.CharField(max_length=50, null=True, blank=True)
    doors = models.IntegerField()
    seats = models.IntegerField()
    engine = models.CharField(max_length=255, null=True, blank=True)
    engine_capacity = models.CharField(max_length=100, null=True, blank=True)
    engine_cylinder = models.CharField(max_length=50, null=True, blank=True)
    induction = models.CharField(max_length=100, null=True, blank=True)
    engine_type = models.CharField(max_length=100, null=True, blank=True)
    fuel_grade = models.CharField(max_length=50, null=True, blank=True)
    transmission = models.CharField(max_length=255, null=True, blank=True)
    transmission_speed = models.IntegerField()
    transmission_type = models.CharField(max_length=50, null=True, blank=True)
    drivetrain = models.CharField(max_length=50, null=True, blank=True)
    tailpipe_comb = models.CharField(max_length=100, null=True, blank=True)
    tailpipe_comb_value = models.CharField(max_length=50, null=True, blank=True)
    tailpipe_comb_note = models.CharField(max_length=100, null=True, blank=True)
    tailpipe_urban = models.CharField(max_length=100, null=True, blank=True)
    tailpipe_urban_value = models.CharField(max_length=50, null=True, blank=True)
    tailpipe_urban_note = models.CharField(max_length=100, null=True, blank=True)
    tailpipe_extra = models.CharField(max_length=100, null=True, blank=True)
    tailpipe_extra_value = models.CharField(max_length=50, null=True, blank=True)
    tailpipe_extra_note = models.CharField(max_length=100, null=True, blank=True)
    annual_cost = models.DecimalField(max_digits=12, decimal_places=2)
    fuel_consumption_comb = models.DecimalField(max_digits=10, decimal_places=2)
    fuel_consumption_urban = models.DecimalField(max_digits=12, decimal_places=2)
    fuel_consumption_extra = models.DecimalField(max_digits=12, decimal_places=2)
    energy_consumption = models.DecimalField(max_digits=12, decimal_places=2)
    electric_range = models.DecimalField(max_digits=12, decimal_places=2)
    air_pollution_standard = models.CharField(max_length=100, null=True, blank=True)
    annual_tailpipe_co2 = models.DecimalField(max_digits=10, decimal_places=2)
    fuel_lifecycle_co2 = models.IntegerField()
    noise_data = models.CharField(max_length=100, null=True, blank=True)

    class Meta:
        db_table = "vehicles"

    def __str__(self):
        return f"{self.id} {self.year} {self.make} {self.model}"


# Car search log - UPDATED to support customer and payment relationships
class CarSearchLog(models.Model):
    id = models.AutoField(primary_key=True)
    uid = models.CharField(max_length=50, null=True, blank=True)
    save_money = models.BooleanField(default=False)
    greener_car = models.BooleanField(default=False)
    good_all_rounder = models.BooleanField(default=False)
    budget = models.DecimalField(max_digits=10, decimal_places=2)
    state = models.CharField(max_length=5, null=True, blank=True)
    have_car = models.BooleanField(default=False)
    make = models.CharField(max_length=100, null=True, blank=True)
    model = models.CharField(max_length=100, null=True, blank=True)
    year = models.CharField(max_length=4, null=True, blank=True)
    engine_type = models.CharField(max_length=100, null=True, blank=True)
    vehicle_id = models.CharField(max_length=20, null=True, blank=True)
    ip_address = models.GenericIPAddressField()
    referral_code = models.CharField(max_length=255, blank=True, null=True)
    user_agent = models.TextField(blank=True, null=True)
    
    # NEW FIELDS for payment integration
    customer_id = models.IntegerField(null=True, blank=True)  # Reference to payments.Customer
    payment_id = models.CharField(max_length=255, null=True, blank=True)  # UUID string reference
    is_migrated_to_garage = models.BooleanField(default=False)
    migrated_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'car_search_logs'
        
    def __str__(self):
        return f"{self.ip_address} - {self.referral_code}"
    


# Vehicle Images
class VehicleImages(models.Model):
    id = models.AutoField(primary_key=True)
    vehicle_id = models.CharField(max_length=20, null=True, blank=True)
    image_name = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        db_table = "vehicle_images"

    def __str__(self):
        return f"{self.vehicle_id} - {self.image_name}"