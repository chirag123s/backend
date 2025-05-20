import re
from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction
from api.models import Vehicles

from .services import parse_vehicle_engine_spec, parse_vehicle_transmission_spec, parse_vehicle_tailpipe, normalize_liter_string, generate_vehicle_id
from scraper_app.models import GVGVehicleData
# from .serializers import GVGVehicleDataSerializer

# Create your views here.
#
class GVGDataParser(APIView):
    def post(self, request):
        gvg_data = GVGVehicleData.objects.all().order_by('id') #[:10]

        stored_data = []

        for vehicle in gvg_data:
            match = re.search(r'(\d+)\s*door', vehicle.body, re.IGNORECASE)
            doors = int(match.group(1)) if match else None
            match = re.search(r'(\d+)\s*seat', vehicle.body, re.IGNORECASE)
            seats = int(match.group(1)) if match else None
            body = re.sub(r'\d+\s*door\s*\d+\s*seat\s*', '', vehicle.body, flags=re.IGNORECASE).strip()
        
            engine = parse_vehicle_engine_spec(vehicle.engine)
            transmission = parse_vehicle_transmission_spec(vehicle.transmission)
            tailpipe_comb = parse_vehicle_tailpipe(vehicle.tailpipe_comb)
            tailpipe_urban = parse_vehicle_tailpipe(vehicle.tailpipe_urban)
            tailpipe_extra = parse_vehicle_tailpipe(vehicle.tailpipe_extra)

            data = Vehicle.objects.create(
                #id = vehicle.id,
                year = vehicle.year,
                make = vehicle.make,
                make_name = vehicle.make_name,
                model = vehicle.model,
                vehicle_class = vehicle.vehicle_class,
                body = body,
                doors = doors,
                seats = seats,
                engine = vehicle.engine,
                engine_capacity = normalize_liter_string(engine['engine_capacity']),
                engine_cylinder = engine['engine_cylinder'],
                induction = engine['induction'],
                engine_type = engine['engine_type'],
                fuel_grade = engine['fuel_grade'],
                transmission = vehicle.transmission,
                transmission_speed = transmission['speed'],
                transmission_type = transmission['type'],
                drivetrain = vehicle.drivetrain,
                tailpipe_comb = vehicle.tailpipe_comb if (vehicle.tailpipe_comb != 'N/A') else '',
                tailpipe_comb_value = tailpipe_comb['value'] if (tailpipe_comb['value'] != 'N/A') else '',
                tailpipe_comb_note = tailpipe_comb['note'] if (tailpipe_comb['note'] != 'N/A') else '',
                tailpipe_urban = vehicle.tailpipe_urban if (vehicle.tailpipe_urban != 'N/A') else '',
                tailpipe_urban_value = tailpipe_urban['value'] if (tailpipe_urban['value'] != 'N/A') else '',
                tailpipe_urban_note = tailpipe_urban['note'] if (tailpipe_urban['note'] != 'N/A') else '',
                tailpipe_extra = vehicle.tailpipe_extra if (vehicle.tailpipe_extra != 'N/A') else '',
                tailpipe_extra_value = tailpipe_extra['value'] if (tailpipe_extra['value'] != 'N/A') else '',
                tailpipe_extra_note = tailpipe_extra['note'] if (tailpipe_extra['note'] != 'N/A') else '',
                annual_cost = vehicle.annual_cost if (vehicle.annual_cost != 'N/A') else 0,
                fuel_consumption_comb = vehicle.fuel_consumption_comb if (vehicle.fuel_consumption_comb != 'N/A') else 0,
                fuel_consumption_urban = vehicle.fuel_consumption_urban if (vehicle.fuel_consumption_urban != 'N/A') else 0,
                fuel_consumption_extra = vehicle.fuel_consumption_extra if (vehicle.fuel_consumption_extra != 'N/A') else 0,
                energy_consumption = vehicle.energy_consumption if (vehicle.energy_consumption != 'N/A') else 0,
                electric_range = vehicle.electric_range if (vehicle.electric_range != 'N/A') else 0,
                air_pollution_standard = vehicle.air_pollution_standard,
                annual_tailpipe_co2 = vehicle.annual_tailpipe_co2,
                fuel_lifecycle_co2 = vehicle.fuel_lifecycle_co2,
                noise_data = vehicle.noise_data
            )
            #data.save()
            v = Vehicle.objects.get(id=data.id)
            v.vehicle_id = generate_vehicle_id(data.year, data.id )
            v.save()

            stored_data.append({
                "id": data.id,
                "year": data.year,
                "make": data.make,
                "make_name": data.make_name,
                "model": data.model,
                "vehicle_class": data.vehicle_class,
                "body": data.body,
                "doors": data.doors,
                "seats": data.seats,
                "engine": data.engine,
                "engine_capacity": data.engine_capacity,
                "engine_cylinder": data.engine_cylinder,
                "induction": data.induction,
                "engine_type": data.engine_type,
                "fuel_grade": data.fuel_grade,
                "transmission": data.transmission,
                "transmission_speed": data.transmission_speed,
                "transmission_type": data.transmission_speed,
                "drivetrain": data.drivetrain,
                "tailpipe_comb": data.tailpipe_comb,
                "tailpipe_comb_value": data.tailpipe_comb_value,
                "tailpipe_comb_note": data.tailpipe_comb_note,
                "tailpipe_urban": data.tailpipe_urban,
                "tailpipe_urban_value": data.tailpipe_urban_value,
                "tailpipe_urban_note": data.tailpipe_urban_note,
                "tailpipe_extra": data.tailpipe_extra,
                "tailpipe_extra_value": data.tailpipe_extra_value,
                "tailpipe_extra_note": data.tailpipe_extra_note,
                "annual_cost": data.annual_cost,
                "fuel_consumption_comb": data.fuel_consumption_comb,
                "fuel_consumption_urban": data.fuel_consumption_urban,
                "fuel_consumption_extra": data.fuel_consumption_extra,
                "energy_consumption": data.energy_consumption,
                "electric_range": data.electric_range,
                "air_pollution_standard": data.air_pollution_standard,
                "annual_tailpipe_co2": data.annual_tailpipe_co2,
                "fuel_lifecycle_co2": data.fuel_lifecycle_co2,
                "noise_data": data.noise_data
            })

            print(f"{vehicle.id} {vehicle.year} {vehicle.make} {vehicle.model}")

        return Response({"message": "Data fetched and stored successfully", "models": stored_data}, status=status.HTTP_201_CREATED)
    
        #serializer = GVGVehicleDataSerializer(gvg_data, many=True)
        #return Response(serializer.data, status=status.HTTP_201_CREATED) 
