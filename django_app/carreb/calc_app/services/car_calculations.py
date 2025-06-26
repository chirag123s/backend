# calc_app/services/car_calculations.py

from django.conf import settings
from api.models import CarMakes, CarPricing, FuelRetailPrice

class CarCalculationsProcessor:
    def __init__(self):
        print(f"Starting process...")

    def process_all_car_make_data(self):
        print(f"Processing all cars...")

        car_makes = CarMakes.objects.filter(is_active=True).order_by('name')
        processed_makes = []
        failed_makes = []
        total_variants_created = 0
        
        for car_make in car_makes:
            
            self.process_single_car_make_data(car_make)


        return {
            'processed_makes': processed_makes,
            'failed_makes': failed_makes,
            'total_variants_created': total_variants_created
        }

    def process_single_car_make_data(self, car_make):
        """Process a single car make"""

        variants = car_make.variants.filter(is_active=True).order_by('model', 'variant', 'sub_variant')

        weight_price_percent = .8       #W(p)
        weight_emission_percent = .2    #W(e)


        for variant in variants:
            """prices = variant.prices
            for price in prices:
                print(f'{car_make.name} {variant.variant} {variant.variant} {price.state} {price.msrp}')"""

            user_entry = {
                'fuel_efficiency': variant.fuel_efficiency_combined_l_100km,
                'est_avg_km_pa': 17000
            }
            prices = CarPricing.objects.filter(car_variant_id=variant.id)
                
            for price in prices:
                #Cost of keeping this car on the road per year
                a_coktc = {
                    'sched_maintenance': 0,
                    'petrol_cost': 0,
                    'electricity_cost': 0,
                    'registration_fees': 0,
                    'insurance_cost': 0,        #incl Comprehensive
                }

                year_to = int(variant.year) - 1
                fuel_type = variant.drivetrain
                avg_fuel_retail = 0
                price_state = price.state
                price_state = price_state.strip().lower()

                if fuel_type is not None and bool(fuel_type):
                    fuel_type = fuel_type.strip().lower()
                    fuel_retail_price = FuelRetailPrice.objects.filter(year_type='cy', year_to=year_to, fuel_type=fuel_type).first()
                    if fuel_retail_price is not None:
                        avg_fuel_retail = getattr(fuel_retail_price, price_state)

                a_coktc['sched_maintenance'] = 2500 / 5     #='User Entry'!D11/5
                a_coktc['petrol_cost'] = user_entry['fuel_efficiency'] * user_entry['est_avg_km_pa'] / 100 * avg_fuel_retail / 100              #D17    #=D10*D15/100*'Average Petrol Retail'!D26/100

                cost_of_keeping_the_car = 0.00
                for k, v in a_coktc.items():
                    cost_of_keeping_the_car += float(v)
                

                #Total Cost Of Ownership (COO) over 5 years
                b_tcoo = cost_of_keeping_the_car * 5 / 100

                e = 0 #E

                # = 1 - [P - P(min)] / [P(max) - P(min)]
                p = 0 

                core_rating = (weight_price_percent * p) + (weight_emission_percent * e)  #W(p) * P + (W(e) * E

                
                print(f'{car_make.name} {variant.variant} {variant.variant} : CORE Rating = {core_rating} {user_entry['fuel_efficiency']} {a_coktc['petrol_cost'] }') 

"""
year_to = 2025 - 1
fuel_type = 'Petrol'
avg_fuel_retail = 0
if fuel_type is not None and bool(fuel_type):
    fuel_type = fuel_type.strip().lower()
    avg_fuel_retail = FuelRetailPrice.objects.filter(year_type='cy', year_to=year_to, fuel_type=fuel_type).first()
"""