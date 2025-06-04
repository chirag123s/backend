import uuid
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .services import download_duck_image
from rest_framework.decorators import api_view
from api.models import Vehicles, VehicleImages


class DownloadCarImageFromDDG(APIView):
    def get(self, request):

        cars = Vehicles.objects.all()

        for car in cars:
            filename = '-'
            car_image = VehicleImages.objects.get(vehicle_id=car.vehicle_id)

            if car_image.image_name != '-' :
                if not car_image.image_name:
                    response = download_duck_image( car.make_name, car.model, car.year )

                    if 'filename' in response:
                        filename = response['filename']
                    else:
                        filename = '-'

                    v = VehicleImages.objects.get(vehicle_id=car.vehicle_id)
                    v.image_name = filename
                    v.save()

                    print(f'{response}')
        
        return Response({"status": 'done'}, status=200)