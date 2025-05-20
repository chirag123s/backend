from django.db import models

class GVGVehicleData(models.Model):
    id = models.AutoField(primary_key=True)
    year = models.CharField(max_length=5, null=True, blank=True)
    make = models.CharField(max_length=255, null=True, blank=True)
    make_name = models.CharField(max_length=255, null=True, blank=True)
    model = models.CharField(max_length=255, null=True, blank=True)
    vehicle_class = models.CharField(max_length=50, null=True, blank=True)
    body = models.CharField(max_length=255, null=True, blank=True)
    engine = models.CharField(max_length=255, null=True, blank=True)
    transmission = models.CharField(max_length=255, null=True, blank=True)
    drivetrain = models.CharField(max_length=255, null=True, blank=True)
    tailpipe_comb = models.CharField(max_length=255, null=True, blank=True)
    tailpipe_urban = models.CharField(max_length=255, null=True, blank=True)
    tailpipe_extra = models.CharField(max_length=255, null=True, blank=True)
    annual_cost = models.CharField(max_length=255, null=True, blank=True)
    fuel_consumption_comb = models.CharField(max_length=255, null=True, blank=True)
    fuel_consumption_urban = models.CharField(max_length=255, null=True, blank=True)
    fuel_consumption_extra = models.CharField(max_length=255, null=True, blank=True)
    energy_consumption = models.CharField(max_length=255, null=True, blank=True)
    electric_range = models.CharField(max_length=255, null=True, blank=True)
    air_pollution_standard = models.CharField(max_length=255, null=True, blank=True)
    annual_tailpipe_co2 = models.CharField(max_length=255, null=True, blank=True)
    fuel_lifecycle_co2 = models.CharField(max_length=255, null=True, blank=True)
    noise_data = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        db_table = 'gvg_vehicles'
        managed = False

    _use_external = True