# calc_app/management/commands/calculate_ratings.py
# python3 manage.py calculate_ratings 
from django.core.management.base import BaseCommand
from calc_app.services.car_calculations import CarCalculationsProcessor


class Command(BaseCommand):
    help = 'Calculate car related ratings (e.g., CORE Rating, COO, COOF, etc)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--car-make',
            type=str,
            help='Specific car make to process',
        )
        parser.add_argument(
            '--car-model',
            type=str,
            help='Specific car model to process',
        )

    def handle(self, *args, **options):
        processor = CarCalculationsProcessor()
        
        if options['car_make']:
            # Process single car make
            from api.models import CarMakes
            from api.models import CarVariants
            try:
                car_make = CarMakes.objects.get(name__iexact=options['car_make'])

                result = processor.process_single_car_make_data(car_make)
                
            except CarMakes.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'Car make "{options["car_make"]}" not found')
                )
        else:
            # Process all car makes
            results = processor.process_all_car_make_data()
            
            print(results)