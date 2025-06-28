# calc_app/services/car_calculations.py

from django.conf import settings
from api.models import CarMakes, CarPricing, FuelRetailPrice
from api.models import Vehicles, CarBodyCost, ElectricityGridEmissions
import math

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

def calculate_vehicle_cost_with_finance(
    variant_id: int,
    state: str,
    kilometers_per_annum: int,
    off_grid_energy_percent: float,
    finance_type: str,
    deposit: float,
    trade_in_value: float,
    interest_rate_apr: float,
    loan_term_months: int,
    balloon_payment_percent: float,
    loan_establishment_fee: float,
    admin_fee_monthly: float,
    dealer_incentive: float
):

    try:
        vehicle = Vehicles.objects.get(pk=variant_id)
        pricing = CarPricing.objects.get(car_variant_id=variant_id, state=state)
        fuel_prices = FuelRetailPrice.objects.get(state=state)
        grid_emissions = ElectricityGridEmissions.objects.get(state=state)
        body_cost = CarBodyCost.objects.filter(type=vehicle.body).first()

    except Vehicles.DoesNotExist:
        raise ValueError(f"Vehicle with ID {variant_id} not found.")
    except CarPricing.DoesNotExist:
        raise ValueError(f"Pricing for vehicle {variant_id} in state {state} not found.")
    except FuelRetailPrice.DoesNotExist:
        raise ValueError(f"State fuel cost data for '{state}' not found.")
    except ElectricityGridEmissions.DoesNotExist:
        raise ValueError(f"State grid emissions data for '{state}' not found.")


    # Vehicle specifications
    fuel_efficiency = float(vehicle.fuel_consumption_comb)
    drivetrain = vehicle.drivetrain
    drive_away_price = float(pricing.drive_away_price)
    registration_cost = float(pricing.registration)

    # Using dummy values if they don't exist. Replace with actual model fields.
    estimated_service_cost_5yr = getattr(vehicle, 'estimated_5yr_dealer_servicing_cost', 2500.0)
    estimated_resale_value_5yr = getattr(vehicle, 'estimated_5yr_resale_value', drive_away_price * 0.45)
    co2_emissions_g_km = float(vehicle.annual_tailpipe_co2 / (kilometers_per_annum or 17000) * 1000) if kilometers_per_annum else 0

    # Electricity efficiency
    if drivetrain == 'EV':
        electricity_efficiency_kwh_per_km = 0.15
    elif drivetrain in ['PHEV', 'Hybrid']:
        electricity_efficiency_kwh_per_km = 0.12
    else:
        electricity_efficiency_kwh_per_km = 0.0

    # Insurance cost
    if body_cost:
        insurance_annual = (float(body_cost.insurance_cost_comprehensive_annual_min) + float(body_cost.insurance_cost_comprehensive_annual_max)) / 2
    else:
        insurance_annual = 2450.0 if drivetrain == 'EV' else 2050.0

    # Fuel & Electricity Calculations
    fuel_litres_pa = (fuel_efficiency * kilometers_per_annum) / 100
    fuel_cost_pa = float(fuel_prices.petrol_price_per_litre) * fuel_litres_pa

    # NOTE: This part needs electricity price data which is not available in the new models.
    # I'll set electricity_cost_pa to 0 for now.
    electricity_kwh_pa = electricity_efficiency_kwh_per_km * kilometers_per_annum
    electricity_cost_pa = 0.0
    # float(electricity_price.price_per_kwh) * electricity_kwh_pa * (1 - off_grid_energy_percent / 100)

    total_fuel_electricity = fuel_cost_pa + electricity_cost_pa

    # Other Running Costs
    maintenance_annual = estimated_service_cost_5yr / 5
    other_running_costs = insurance_annual + registration_cost + maintenance_annual

    # Annual Cost of Ownership (Base)
    annual_coo_base = total_fuel_electricity + other_running_costs

    # Depreciation
    depreciation_5yr = drive_away_price - estimated_resale_value_5yr
    depreciation_percent = (depreciation_5yr / drive_away_price) * 100 if drive_away_price > 0 else 0

    # CO2 Emissions
    co2_tailpipe_pa = (co2_emissions_g_km * kilometers_per_annum) / 1000
    co2_electricity_pa = electricity_kwh_pa * float(grid_emissions.emissions_factor_kg_per_kwh) * (1 - off_grid_energy_percent / 100)
    co2_total_pa = co2_tailpipe_pa + co2_electricity_pa

    # Finance Calculations
    drive_away_price_after_incentive = drive_away_price - dealer_incentive
    loan_amount = drive_away_price_after_incentive - deposit - trade_in_value
    balloon_payment_amount = drive_away_price_after_incentive * (balloon_payment_percent / 100)

    # PMT calculation for monthly payment
    monthly_rate = (interest_rate_apr / 100) / 12
    if monthly_rate > 0:
        factor = (1 + monthly_rate) ** loan_term_months
        pmt_principal = (loan_amount - balloon_payment_amount) * (monthly_rate * factor) / (factor - 1)
        pmt_balloon = balloon_payment_amount * monthly_rate / (factor - 1)
        monthly_payment = pmt_principal + pmt_balloon + admin_fee_monthly
    else:
        monthly_payment = (loan_amount - balloon_payment_amount) / loan_term_months + admin_fee_monthly

    total_loan_cost = (monthly_payment * loan_term_months) + balloon_payment_amount + loan_establishment_fee - loan_amount
    annualized_loan_cost = total_loan_cost / (loan_term_months / 12) if loan_term_months > 0 else 0

    # Final COO with Finance
    annual_coo_with_finance = annual_coo_base + annualized_loan_cost

    return {
        "variant_id": variant_id,
        "state": state,
        "kilometers_per_annum": kilometers_per_annum,
        "drive_away_price": drive_away_price_after_incentive,
        "finance_type": finance_type,
        "deposit": deposit,
        "trade_in_value": trade_in_value,
        "loan_amount": loan_amount,
        "interest_rate_apr": interest_rate_apr,
        "loan_term_months": loan_term_months,
        "balloon_payment_amount": balloon_payment_amount,
        "balloon_payment_percent": balloon_payment_percent,
        "monthly_repayment_total": monthly_payment,
        "total_loan_cost": total_loan_cost,
        "annualized_loan_cost": annualized_loan_cost,
        "annual_coo_without_finance": annual_coo_base,
        "annual_coo_with_finance": annual_coo_with_finance,
        "fuel_electricity_total": total_fuel_electricity,
        "fuel_cost_annual": fuel_cost_pa,
        "electricity_cost_annual": electricity_cost_pa,
        "other_running_costs_total": other_running_costs,
        "insurance_annual": insurance_annual,
        "registration_annual": registration_cost,
        "maintenance_annual": maintenance_annual,
        "depreciation_5yr_amount": depreciation_5yr,
        "depreciation_5yr_percent": depreciation_percent,
        "estimated_resale_value": estimated_resale_value_5yr,
        "co2_emissions_total_kg": co2_total_pa,
        "co2_tailpipe_kg": co2_tailpipe_pa,
        "co2_electricity_kg": co2_electricity_pa
    }

def calculate_vehicle_cost_no_finance(
    variant_id: int,
    state: str,
    kilometers_per_annum: int,
    off_grid_energy_percent: float
):
    try:
        vehicle = Vehicles.objects.get(pk=variant_id)
        pricing = CarPricing.objects.get(car_variant_id=variant_id, state=state)
        fuel_prices = FuelRetailPrice.objects.get(state=state)
        grid_emissions = ElectricityGridEmissions.objects.get(state=state)
        body_cost = CarBodyCost.objects.filter(type=vehicle.body).first()

    except Vehicles.DoesNotExist:
        raise ValueError(f"Vehicle with ID {variant_id} not found.")
    except CarPricing.DoesNotExist:
        raise ValueError(f"Pricing for vehicle {variant_id} in state {state} not found.")
    except FuelRetailPrice.DoesNotExist:
        raise ValueError(f"State cost data for '{state}' not found.")
    except ElectricityGridEmissions.DoesNotExist:
        raise ValueError(f"State grid emissions data for '{state}' not found.")

    # Vehicle specifications
    fuel_efficiency = float(vehicle.fuel_consumption_comb)
    drivetrain = vehicle.drivetrain
    drive_away_price = float(pricing.drive_away_price)
    registration_cost = float(pricing.registration)

    # Estimated values from the model
    estimated_service_cost_5yr = getattr(vehicle, 'estimated_5yr_dealer_servicing_cost', 2500.0)
    estimated_resale_value_5yr = getattr(vehicle, 'estimated_5yr_resale_value', drive_away_price * 0.45)
    co2_emissions_g_km = float(vehicle.annual_tailpipe_co2 / (kilometers_per_annum or 17000) * 1000) if kilometers_per_annum else 0

    # Electricity efficiency
    if drivetrain == 'EV':
        electricity_efficiency_kwh_per_km = 0.15
    elif drivetrain in ['PHEV', 'Hybrid']:
        electricity_efficiency_kwh_per_km = 0.12
    else:
        electricity_efficiency_kwh_per_km = 0.0

    # Insurance cost
    if body_cost:
        insurance_annual = (float(body_cost.insurance_cost_comprehensive_annual_min) + float(body_cost.insurance_cost_comprehensive_annual_max)) / 2
    else:
        insurance_annual = 2450.0 if drivetrain == 'EV' else 2050.0

    # Fuel & Electricity Calculations
    fuel_litres_pa = (fuel_efficiency * kilometers_per_annum) / 100
    fuel_cost_pa = float(fuel_prices.petrol_price_per_litre) * fuel_litres_pa

    # NOTE: This part needs electricity price data which is not available in the new models.
    # I'll set electricity_cost_pa to 0 for now.
    electricity_kwh_pa = electricity_efficiency_kwh_per_km * kilometers_per_annum
    electricity_cost_pa = 0.0
    # float(electricity_price.price_per_kwh) * electricity_kwh_pa * (1 - off_grid_energy_percent / 100)

    total_fuel_electricity = fuel_cost_pa + electricity_cost_pa

    # Other Running Costs
    maintenance_annual = estimated_service_cost_5yr / 5
    other_running_costs = insurance_annual + registration_cost + maintenance_annual

    # Annual Cost of Ownership (Base)
    annual_coo_base = total_fuel_electricity + other_running_costs

    # Depreciation
    depreciation_5yr = drive_away_price - estimated_resale_value_5yr
    depreciation_percent = (depreciation_5yr / drive_away_price) * 100 if drive_away_price > 0 else 0

    # CO2 Emissions
    co2_tailpipe_pa = (co2_emissions_g_km * kilometers_per_annum) / 1000
    co2_electricity_pa = electricity_kwh_pa * float(grid_emissions.emissions_factor_kg_per_kwh) * (1 - off_grid_energy_percent / 100)
    co2_total_pa = co2_tailpipe_pa + co2_electricity_pa

    # Return a dictionary with all calculated values
    return {
        "variant_id": variant_id,
        "state": state,
        "kilometers_per_annum": kilometers_per_annum,
        "drive_away_price": drive_away_price,
        "annual_coo_base": annual_coo_base,
        "fuel_electricity_total": total_fuel_electricity,
        "fuel_cost_annual": fuel_cost_pa,
        "electricity_cost_annual": electricity_cost_pa,
        "other_running_costs_total": other_running_costs,
        "insurance_annual": insurance_annual,
        "registration_annual": registration_cost,
        "maintenance_annual": maintenance_annual,
        "depreciation_5yr_amount": depreciation_5yr,
        "depreciation_5yr_percent": depreciation_percent,
        "estimated_resale_value": estimated_resale_value_5yr,
        "co2_emissions_total_kg": co2_total_pa,
        "co2_tailpipe_kg": co2_tailpipe_pa,
        "co2_electricity_kg": co2_electricity_pa
    }
def calculate_vehicle_emissions(
    vehicle_id: int = None,
    make: str = None,
    model: str = None,
    state: str = None,
    annual_km: int = None,
    drivetrain: str = None,
    year: str = None
):
    """
    Translates the calculate_vehicle_emissions stored procedure into Python,
    using the schema from the provided SQL dump file.
    """
    # Default values from the stored procedure
    calc_state = state or 'QLD'
    calc_annual_km = annual_km or 14000

    try:
        grid_emissions = ElectricityGridEmissions.objects.get(state=calc_state)
        a17_electricity_factor = float(grid_emissions.emissions_factor_kg_per_kwh)
    except ElectricityGridEmissions.DoesNotExist:
        # Fallback to a default value if the state is not found
        a17_electricity_factor = 0.73 # Default for QLD

    queryset = Vehicles.objects.select_related('make').all()

    if vehicle_id:
        queryset = queryset.filter(id=vehicle_id)
    if make:
        queryset = queryset.filter(make__name__icontains=make)
    if model:
        queryset = queryset.filter(model__icontains=model)
    if drivetrain:
        queryset = queryset.filter(drivetrain__icontains=drivetrain)
    if year:
        queryset = queryset.filter(year=year)
    results = []
    for vehicle in queryset:
        # --- Value Extraction & Calculation ---
        p_tailpipe_co2_g_km = float(vehicle.annual_tailpipe_co2 / (calc_annual_km or 17000) * 1000) if calc_annual_km else 0
        n_energy_consumption_wh_km = float(vehicle.energy_consumption or 0) * 10

        # A12: Annual Tailpipe Emissions in kg
        a12_tailpipe_kg_pa = (p_tailpipe_co2_g_km * calc_annual_km) / 1000

        # A13: Annual Electricity Emissions in kg
        a13_electricity_kg_pa = (n_energy_consumption_wh_km / 1000) * a17_electricity_factor * calc_annual_km

        total_co2_kg_pa = a12_tailpipe_kg_pa + a13_electricity_kg_pa
        total_co2_tonnes_pa = total_co2_kg_pa / 1000
        results.append({
            # Vehicle Information
            "vehicle_id": vehicle.id,
            "make_name": vehicle.make.name,
            "model": vehicle.model,
            "body": vehicle.body,
            "engine": vehicle.engine,
            "drivetrain": vehicle.drivetrain,
            "year": vehicle.year,

            # Input Parameters
            "calculation_state": calc_state,
            "annual_km_used": calc_annual_km,

            # Raw Data Values (from the numeric fields in the DB)
            "P_tailpipe_co2_g_km": round(p_tailpipe_co2_g_km, 2),
            "N_energy_consumption_wh_km": round(n_energy_consumption_wh_km, 2),

            # A17 Value (Electricity Generation Factor)
            "A17_electricity_factor_kg_kwh": a17_electricity_factor,
            # A12 Calculation Breakdown
            "A12_formula": "A12 = P × Annual_KM ÷ 1000",
            "A12_calculation": f"{round(p_tailpipe_co2_g_km, 2)} × {calc_annual_km} ÷ 1000",
            "A12_tailpipe_kg_pa": round(a12_tailpipe_kg_pa, 2),
            # A13 Calculation Breakdown
            "A13_formula": "A13 = (N ÷ 1000) × A17 × Annual_KM",
            "A13_calculation": f"({round(n_energy_consumption_wh_km, 2)} ÷ 1000) × {a17_electricity_factor} × {calc_annual_km}",
            "A13_electricity_kg_pa": round(a13_electricity_kg_pa, 2),
            # Total Emissions
            "total_formula": "Total = A12 + A13",
            "total_co2_kg_pa": round(total_co2_kg_pa, 2),
            "total_co2_tonnes_pa": round(total_co2_tonnes_pa, 3)
        })
    # Sort the final list by total emissions, descending
    sorted_results = sorted(results, key=lambda x: x['total_co2_kg_pa'], reverse=True)
    return sorted_results

def calculate_core_rating(
    variant_id: int,
    state: str,
    kilometers_per_annum: int,
    off_grid_energy_percent: float,
    with_finance: bool,
    finance_params: dict = None
):
    # Default values from the stored procedure
    calc_kilometers_per_annum = kilometers_per_annum or 17000
    calc_off_grid_energy_percent = off_grid_energy_percent if off_grid_energy_percent is not None else 20.0

    # Min/Max normalization values from the stored procedure
    e_min, e_max = 10000, 50000
    if with_finance:
        p_min, p_max = 20000, 65000
    else:
        p_min, p_max = 15000, 55000

    if with_finance:
        if not finance_params:
            # Default finance parameters if not provided
            finance_params = {
                'finance_type': 'Loan',
                'deposit': 10000,
                'trade_in_value': 0,
                'interest_rate_apr': 7.5,
                'loan_term_months': 60,
                'balloon_payment_percent': 30,
                'loan_establishment_fee': 500,
                'admin_fee_monthly': 10,
                'dealer_incentive': 0
            }
        cost_data = calculate_vehicle_cost_with_finance(
            variant_id=variant_id,
            state=state,
            kilometers_per_annum=calc_kilometers_per_annum,
            off_grid_energy_percent=calc_off_grid_energy_percent,
            **finance_params
        )
        annual_coo = cost_data['annual_coo_with_finance']
        emissions_annual_kg = cost_data['co2_emissions_total_kg']
    else:
        cost_data = calculate_vehicle_cost_no_finance(
            variant_id=variant_id,
            state=state,
            kilometers_per_annum=calc_kilometers_per_annum,
            off_grid_energy_percent=calc_off_grid_energy_percent
        )
        annual_coo = cost_data['annual_coo_base']
        emissions_annual_kg = cost_data['co2_emissions_total_kg']

    # Calculate 5-year totals
    coo_5yr = annual_coo * 5
    emissions_5yr = emissions_annual_kg * 5

    # Calculate normalized scores ---
    # Cost score (P_score)
    p_score = 1 - ((coo_5yr - p_min) / (p_max - p_min)) if (p_max - p_min) != 0 else 0
    p_score = max(0, min(1, p_score)) # Clamp between 0 and 1

    # Emissions score (E_score)
    e_score = 1 - ((emissions_5yr - e_min) / (e_max - e_min)) if (e_max - e_min) != 0 else 0
    e_score = max(0, min(1, e_score)) # Clamp between 0 and 1

    # Calculate CORE rating ---
    core_rating = (0.8 * p_score) + (0.2 * e_score)

    # Convert to star rating ---
    if core_rating >= 0.8:
        star_rating = 5
        description = 'EXCEPTIONAL: Among the best on the market'
    elif core_rating >= 0.6:
        star_rating = 4
        description = 'STRONG: Great ownership savings and responsible emissions'
    elif core_rating >= 0.4:
        star_rating = 3
        description = 'MODERATE: Solid overall with fair balance'
    elif core_rating >= 0.2:
        star_rating = 2
        description = 'LOW: Higher ownership costs or emissions'
    else:
        star_rating = 1
        description = 'LIMITED: Better options exist'

    return {
        'cost_of_ownership_5yr': round(coo_5yr, 2),
        'emissions_5yr_kg': round(emissions_5yr, 2),
        'coo_score': round(p_score, 4),
        'emissions_score': round(e_score, 4),
        'core_rating': round(core_rating, 4),
        'star_rating': star_rating,
        'rating_description': description
    }
