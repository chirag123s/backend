from django.db import models
from django.utils import timezone

# Create your models here.
class CarMakes(models.Model):
    car_make_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    slug = models.CharField(max_length=255)
    is_popular = models.BooleanField(default=0)
    is_active = models.BooleanField(default=1)
    grok_json = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now) #auto_now_add=True, 
    updated_at = models.DateTimeField(default=timezone.now) #auto_now=True, 
    grok_json_fuel_battery_capacity = models.JSONField(null=True, blank=True)

    class Meta:
        db_table = 'car_makes'

    def __str__(self):
        return self.name

class CarVariants(models.Model):
    car_make = models.ForeignKey(CarMakes, on_delete=models.CASCADE, related_name='variants')
    year = models.CharField(max_length=5, null=True, blank=True)
    model = models.CharField(max_length=255)
    variant = models.CharField(max_length=255)
    image_url = models.URLField(blank=True, null=True)
    image = models.ImageField(upload_to='car_variants/', blank=True, null=True)
    sub_variant = models.CharField(max_length=100, null=True)
    sub_variants = models.JSONField(default=list, blank=True)
    no_doors = models.IntegerField(default=0)
    no_seats = models.IntegerField(default=0)
    fuel_capacity = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    battery_capacity_kwh = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    drivetrain = models.CharField(max_length=100, null=True)
    body_type = models.CharField(max_length=100, null=True)
    total_range_km = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    co2_emissions_combined_g_km = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    fuel_efficiency_combined_l_100km = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    estimated_5yr_dealer_servicing_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    estimated_5yr_resale_value = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    is_active = models.BooleanField(default=1)
    created_at = models.DateTimeField(default=timezone.now)  #auto_now_add=True, 
    updated_at = models.DateTimeField(default=timezone.now)  #auto_now=True, 

    class Meta:
        db_table = 'car_variants'
        #unique_together = ['car_make', 'model', 'variant']

    def __str__(self):
        return f"{self.car_make.name} {self.model} {self.variant}"

    def download_image(self):
        """Download image from image_url and save to image field"""
        if self.image_url and not self.image:
            try:
                response = requests.get(self.image_url, timeout=30)
                response.raise_for_status()
                
                # Get filename from URL
                parsed_url = urlparse(self.image_url)
                filename = os.path.basename(parsed_url.path)
                if not filename:
                    filename = f"{self.car_make.name}_{self.model}_{self.variant}.jpg"
                
                # Save image
                self.image.save(
                    filename,
                    ContentFile(response.content),
                    save=True
                )
                return True
            except Exception as e:
                print(f"Error downloading image for {self}: {e}")
                return False
        return False

class CarPricing(models.Model):
    id = models.AutoField(primary_key=True)
    car_variant = models.ForeignKey(CarVariants, on_delete=models.CASCADE, related_name='prices', default=1)
    variant_id = models.IntegerField(default=0)
    state = models.CharField(max_length=50, blank=True, null=True)
    msrp = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    drive_away_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    drive_away_price_with_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    stamp_duty = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    registration = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    ctp = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    govt_incentives = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    dealer_delivery_charges = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    class Meta:
        db_table = 'car_pricing'

    def __str__(self):
        return f"{self.id} {self.car_variant_id} {self.state} {self.msrp}"

class CarDataRaw(models.Model):
    id = models.AutoField(primary_key=True)
    make = models.CharField(max_length=100)
    model = models.CharField(max_length=100)
    year = models.CharField(max_length=5, null=True, blank=True)
    vehicle_class = models.CharField(max_length=100, null=True, blank=True)
    grok_raw = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now) #auto_now_add=True, 
    updated_at = models.DateTimeField(default=timezone.now) #auto_now=True, 

    class Meta:
        db_table = 'car_data_raw'

    def __str__(self):
        return f"{self.id} {self.make} {self.model}  {self.year}"

class CarModels(models.Model):
    id = models.AutoField(primary_key=True)
    make = models.CharField(max_length=100)
    model = models.CharField(max_length=100)
    year = models.CharField(max_length=5, null=True, blank=True)
    vehicle_class = models.CharField(max_length=100, null=True, blank=True)
    grok_raw = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now) #auto_now_add=True, 
    updated_at = models.DateTimeField(default=timezone.now) #auto_now=True, 

    class Meta:
        db_table = 'car_models'

    def __str__(self):
        return f"{self.id} {self.make} {self.model}  {self.year}"

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
        return self.name

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


# Car search log
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
        return f"{self.id} {self.year} {self.make} {self.model}"

# Car Body type costs
class CarBodyCost(models.Model):
    id = models.AutoField(primary_key=True)
    type = models.CharField(max_length=100, null=True, blank=True)
    insurance_cost_comprehensive_annual_min = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    insurance_cost_comprehensive_annual_max = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tyre_change_cost_per_tyre_min = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tyre_change_cost_per_tyre_max = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    source = models.CharField(max_length=50, null=True, blank=True)
    is_active = models.BooleanField(default=1)
    created_at = models.DateTimeField(default=timezone.now)  #auto_now_add=True, 
    updated_at = models.DateTimeField(default=timezone.now)  #auto_now=True, 

    class Meta:
        db_table = "car_body_cost"

    def __str__(self):
        return f"{self.id} {self.type} {self.insurance_cost_comprehensive_annual_min} {self.insurance_cost_comprehensive_annual_max} {self.tyre_change_cost_per_tyre_min} {self.tyre_change_cost_per_tyre_max} {self.source}"

class FuelRetailPrice(models.Model):
    FUEL_PETROL = 'petrol'
    FUEL_DIESEL = 'diesel'
    FUEL_TYPE_CHOICES = [
        (FUEL_PETROL, 'Petrol'),
        (FUEL_DIESEL, 'Diesel'),
    ]

    YEAR_CY = 'cy'
    YEAR_FY = 'fy'
    YEAR_TYPE_CHOICES = [
        (YEAR_CY, 'Calendar Year'),
        (YEAR_FY, 'Financial Year'),
    ]

    id = models.AutoField(primary_key=True)
    fuel_type = models.CharField(max_length=10, choices=FUEL_TYPE_CHOICES, default=FUEL_PETROL)
    year_type = models.CharField(max_length=2, choices=YEAR_TYPE_CHOICES, default=YEAR_CY)
    year_from = models.IntegerField(null=True)
    year_to = models.IntegerField(null=True)
    nsw = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    vic = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    qld = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    sa = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    wa = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    nt = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tas = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    act = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    national = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    is_active = models.BooleanField(default=1)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "fuel_retail_price"

    def __str__(self):
        return f"{self.id} {self.fuel_type} {self.year_type} {self.year_from} {self.year_to} {self.nsw} {self.vic} {self.qld} {self.sa} {self.wa} {self.nt} {self.tas} {self.act} {self.national}"
    
class ElectricityGridEmissions(models.Model):
    state = models.CharField(max_length=50, unique=True)
    emissions_factor_kg_per_kwh = models.DecimalField(max_digits=10, decimal_places=4)

    class Meta:
        db_table = 'electricity_grid_emissions'

    def __str__(self):
        return self.state

