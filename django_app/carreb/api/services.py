
from .models import CarDetails, GvgVehicles
import math
from .models import Vehicles, StateFuelPrices, StateElectricityPrices, ElectricityGridEmissions, CarPricing, CarBodyCost

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
        
        fuel_prices = StateFuelPrices.objects.get(state=state)
        electricity_price = StateElectricityPrices.objects.get(state=state)
        grid_emissions = ElectricityGridEmissions.objects.get(state=state)

        body_cost = CarBodyCost.objects.filter(type=vehicle.body).first()

    except Vehicles.DoesNotExist:
        raise ValueError(f"Vehicle with ID {variant_id} not found.")
    except CarPricing.DoesNotExist:
        raise ValueError(f"Pricing for vehicle {variant_id} in state {state} not found.")
    except (StateFuelPrices.DoesNotExist, StateElectricityPrices.DoesNotExist, ElectricityGridEmissions.DoesNotExist):
        raise ValueError(f"State cost data for '{state}' not found.")

    # Vehicle specifications
    fuel_efficiency = float(vehicle.fuel_consumption_comb)
    drivetrain = vehicle.drivetrain
    drive_away_price = float(pricing.drive_away_price)
    registration_cost = float(pricing.registration)
    
    # Using dummy values if they don't exist. Replace with actual model fields.
    estimated_service_cost_5yr = getattr(vehicle, 'estimated_5yr_dealer_servicing_cost')
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

    electricity_kwh_pa = electricity_efficiency_kwh_per_km * kilometers_per_annum
    electricity_cost_pa = float(electricity_price.price_per_kwh) * electricity_kwh_pa * (1 - off_grid_energy_percent / 100)

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
        fuel_prices = StateFuelPrices.objects.get(state=state)
        electricity_price = StateElectricityPrices.objects.get(state=state)
        grid_emissions = ElectricityGridEmissions.objects.get(state=state)
        body_cost = CarBodyCost.objects.filter(type=vehicle.body).first()

    except Vehicles.DoesNotExist:
        raise ValueError(f"Vehicle with ID {variant_id} not found.")
    except CarPricing.DoesNotExist:
        raise ValueError(f"Pricing for vehicle {variant_id} in state {state} not found.")
    except (StateFuelPrices.DoesNotExist, StateElectricityPrices.DoesNotExist, ElectricityGridEmissions.DoesNotExist):
        raise ValueError(f"State cost data for '{state}' not found.")

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

    electricity_kwh_pa = electricity_efficiency_kwh_per_km * kilometers_per_annum
    electricity_cost_pa = float(electricity_price.price_per_kwh) * electricity_kwh_pa * (1 - off_grid_energy_percent / 100)

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
    
    # Electricity generation factors from the stored procedure
    ELECTRICITY_FACTORS = {
        'QLD': 0.73, 'NSW': 0.79, 'VIC': 0.85, 'SA': 0.43,
        'WA': 0.64, 'TAS': 0.13, 'NT': 0.53, 'ACT': 0.12
    }
    a17_electricity_factor = ELECTRICITY_FACTORS.get(calc_state, 0)

    queryset = GvgVehicles.objects.select_related('make').all()
    
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
        
        # P: Tailpipe CO2 in g/km (using the direct numeric field)
        p_tailpipe_co2_g_km = float(vehicle.co2_emissions_g_km or 0)
        
        # N: Energy Consumption in Wh/km (using the direct numeric field)
        n_energy_consumption_wh_km = float(vehicle.energy_consumption_wh_km or 0)
        
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
    with_finance: bool
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

    # \Convert to star rating ---
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

def ParseCarDetailsFromGG(file):
    """Reads a fixed-width data file starting from row 3 and stores the data in the database."""
    data_to_insert = []

    # Read and decode the file
    decoded_file = file.read().decode('utf-8').strip().split("\n")

    # Skip the first three rows
    data_rows = decoded_file[3:]

    #for idx, line in enumerate(file):
    for line in data_rows:
        # Skip first two rows
        """if idx < 3:
            continue"""

        print(f"make={line[32:55].strip()}")
        print(f"family={line[55:80].strip()}")
        print(f"variant={line[80:111].strip()}")
        print(f"series={line[111:134].strip()}")
        print(f"style={line[134:157].strip()}")
        print(f"engine={line[157:182].strip()}")
        print(f"cc={line[182:186].strip()}")
        print(f"size={line[187:193].strip()}")
        print(f"transmission={line[193:214].strip()}")
        print(f"cylinder={line[214:219].strip()}")
        print(f"width={line[219:225].strip()}")
        print(f"year={line[232:236].strip()}")
        print(f"month={line[28:32].strip()}")
        data = CarDetail(
            #field1=line[0:21].strip(),
            #field2=line[21:25].strip(),
            #field3=line[25:28].strip(),
            make=line[32:55].strip(),
            family=line[55:80].strip(),
            variant=line[80:111].strip(),
            series=line[111:134].strip(),
            style=line[134:157].strip(),
            engine=line[157:182].strip(),
            cc=line[182:186].strip(),
            size=line[187:193].strip(),
            transmission=line[193:214].strip(),
            cylinder=line[214:219].strip(),
            width=line[219:225].strip(),
            #field16=line[225:232].strip(),
            year=line[232:236].strip(),
            month=line[28:32].strip(),
            #field18=line[237:241].strip(),
            #field19=line[241:245].strip(),
            #field20=line[245:].strip()
        )
        data_to_insert.append(data)

    # Bulk insert for better performance
    CarDetails.objects.bulk_create(data_to_insert)
    return {"message": f"{len(data_to_insert)} records successfully stored."}


