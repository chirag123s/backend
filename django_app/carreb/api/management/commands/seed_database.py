# django_app/carreb/api/management/__init__.py
# Create this empty file

# django_app/carreb/api/management/commands/__init__.py  
# Create this empty file

# django_app/carreb/api/management/commands/seed_database.py
import uuid
import random
from decimal import Decimal
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from api.models import (
    CarMakes, States, Vehicles, CarDetails, CarSearchLog, 
    MyGarage, UserSubscription, VehicleImages
)


class Command(BaseCommand):
    help = 'Seed the database with test data for CarReb'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing data before seeding',
        )
        parser.add_argument(
            '--minimal',
            action='store_true',
            help='Create minimal dataset for quick testing',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write('Clearing existing data...')
            self.clear_data()

        if options['minimal']:
            self.stdout.write('Creating minimal test dataset...')
            self.create_minimal_data()
        else:
            self.stdout.write('Creating comprehensive test dataset...')
            self.create_comprehensive_data()

        self.stdout.write(
            self.style.SUCCESS('Database seeding completed successfully!')
        )

    def clear_data(self):
        """Clear existing test data"""
        models_to_clear = [
            MyGarage, UserSubscription, CarSearchLog, VehicleImages,
            Vehicles, CarDetails, CarMakes, States
        ]
        
        for model in models_to_clear:
            count = model.objects.count()
            model.objects.all().delete()
            self.stdout.write(f'Cleared {count} {model.__name__} records')

    def create_minimal_data(self):
        """Create minimal dataset for quick testing"""
        # Create states
        self.create_states()
        
        # Create a few car makes
        car_makes = self.create_car_makes(minimal=True)
        
        # Create some vehicles
        vehicles = self.create_vehicles(minimal=True)
        
        # Create some search logs
        search_logs = self.create_search_logs(minimal=True)
        
        # Create sample garage entries
        self.create_garage_entries(search_logs, minimal=True)
        
        self.stdout.write('Minimal dataset created')

    def create_comprehensive_data(self):
        """Create comprehensive dataset for full testing"""
        # Create all data
        self.create_states()
        car_makes = self.create_car_makes()
        vehicles = self.create_vehicles()
        self.create_car_details()
        self.create_vehicle_images(vehicles)
        search_logs = self.create_search_logs()
        self.create_garage_entries(search_logs)
        self.create_subscriptions(search_logs)
        
        self.stdout.write('Comprehensive dataset created')

    def create_states(self):
        """Create Australian states"""
        states_data = [
            {'state_id': 1, 'short_name': 'NSW', 'name': 'New South Wales'},
            {'state_id': 2, 'short_name': 'VIC', 'name': 'Victoria'},
            {'state_id': 3, 'short_name': 'QLD', 'name': 'Queensland'},
            {'state_id': 4, 'short_name': 'SA', 'name': 'South Australia'},
            {'state_id': 5, 'short_name': 'WA', 'name': 'Western Australia'},
            {'state_id': 6, 'short_name': 'TAS', 'name': 'Tasmania'},
            {'state_id': 7, 'short_name': 'NT', 'name': 'Northern Territory'},
            {'state_id': 8, 'short_name': 'ACT', 'name': 'Australian Capital Territory'},
        ]
        
        for state_data in states_data:
            States.objects.get_or_create(**state_data)
        
        self.stdout.write(f'Created {len(states_data)} states')

    def create_car_makes(self, minimal=False):
        """Create car manufacturers"""
        makes_data = [
            {'name': 'Toyota', 'slug': 'toyota', 'popular': True},
            {'name': 'Mazda', 'slug': 'mazda', 'popular': True},
            {'name': 'Ford', 'slug': 'ford', 'popular': True},
            {'name': 'Hyundai', 'slug': 'hyundai', 'popular': True},
            {'name': 'Tesla', 'slug': 'tesla', 'popular': True},
            {'name': 'BMW', 'slug': 'bmw', 'popular': True},
            {'name': 'Mercedes-Benz', 'slug': 'mercedes-benz', 'popular': True},
            {'name': 'Audi', 'slug': 'audi', 'popular': True},
            {'name': 'Volkswagen', 'slug': 'volkswagen', 'popular': True},
            {'name': 'Subaru', 'slug': 'subaru', 'popular': True},
        ]
        
        if not minimal:
            makes_data.extend([
                {'name': 'Nissan', 'slug': 'nissan', 'popular': False},
                {'name': 'Honda', 'slug': 'honda', 'popular': False},
                {'name': 'Mitsubishi', 'slug': 'mitsubishi', 'popular': False},
                {'name': 'Kia', 'slug': 'kia', 'popular': False},
                {'name': 'Holden', 'slug': 'holden', 'popular': False},
                {'name': 'Volvo', 'slug': 'volvo', 'popular': False},
                {'name': 'Lexus', 'slug': 'lexus', 'popular': False},
                {'name': 'Infiniti', 'slug': 'infiniti', 'popular': False},
                {'name': 'Jaguar', 'slug': 'jaguar', 'popular': False},
                {'name': 'Land Rover', 'slug': 'land-rover', 'popular': False},
            ])
        
        car_makes = []
        for make_data in makes_data:
            make, created = CarMakes.objects.get_or_create(
                name=make_data['name'],
                defaults=make_data
            )
            car_makes.append(make)
        
        self.stdout.write(f'Created {len(makes_data)} car makes')
        return car_makes

    def create_vehicles(self, minimal=False):
        """Create vehicle records"""
        vehicles_data = [
            {
                'vehicle_id': 'VEH001',
                'year': '2024',
                'make': 'TOYOTA',
                'make_name': 'Toyota',
                'model': 'Corolla',
                'vehicle_class': 'Small',
                'body': 'Sedan',
                'doors': 4,
                'seats': 5,
                'engine': '1.8L 4cyl Hybrid',
                'engine_capacity': '1800',
                'engine_cylinder': '4',
                'induction': 'Naturally Aspirated',
                'engine_type': 'Hybrid',
                'fuel_grade': 'Premium Unleaded',
                'transmission': 'CVT Auto',
                'transmission_speed': 0,
                'transmission_type': 'CVT',
                'drivetrain': 'FWD',
                'tailpipe_comb': '4.2L/100km',
                'tailpipe_comb_value': '4.2',
                'tailpipe_urban': '4.5L/100km',
                'tailpipe_urban_value': '4.5',
                'tailpipe_extra': '3.9L/100km',
                'tailpipe_extra_value': '3.9',
                'annual_cost': Decimal('1890.00'),
                'fuel_consumption_comb': Decimal('4.2'),
                'fuel_consumption_urban': Decimal('4.5'),
                'fuel_consumption_extra': Decimal('3.9'),
                'energy_consumption': Decimal('0.0'),
                'electric_range': Decimal('0.0'),
                'air_pollution_standard': 'Euro 6',
                'annual_tailpipe_co2': Decimal('97.0'),
                'fuel_lifecycle_co2': 115,
                'noise_data': '68 dB',
            },
            {
                'vehicle_id': 'VEH002',
                'year': '2024',
                'make': 'TESLA',
                'make_name': 'Tesla',
                'model': 'Model 3',
                'vehicle_class': 'Medium',
                'body': 'Sedan',
                'doors': 4,
                'seats': 5,
                'engine': 'Electric Motor',
                'engine_capacity': '0',
                'engine_cylinder': '0',
                'induction': 'Electric',
                'engine_type': 'Electric',
                'fuel_grade': 'Electric',
                'transmission': 'Single Speed',
                'transmission_speed': 1,
                'transmission_type': 'Direct Drive',
                'drivetrain': 'AWD',
                'tailpipe_comb': '0L/100km',
                'tailpipe_comb_value': '0',
                'tailpipe_urban': '0L/100km',
                'tailpipe_urban_value': '0',
                'tailpipe_extra': '0L/100km',
                'tailpipe_extra_value': '0',
                'annual_cost': Decimal('756.00'),
                'fuel_consumption_comb': Decimal('0.0'),
                'fuel_consumption_urban': Decimal('0.0'),
                'fuel_consumption_extra': Decimal('0.0'),
                'energy_consumption': Decimal('15.8'),
                'electric_range': Decimal('435.0'),
                'air_pollution_standard': 'ZEV',
                'annual_tailpipe_co2': Decimal('0.0'),
                'fuel_lifecycle_co2': 0,
                'noise_data': '65 dB',
            },
            {
                'vehicle_id': 'VEH003',
                'year': '2024',
                'make': 'MAZDA',
                'make_name': 'Mazda',
                'model': 'CX-5',
                'vehicle_class': 'SUV Small',
                'body': 'SUV',
                'doors': 5,
                'seats': 5,
                'engine': '2.5L 4cyl',
                'engine_capacity': '2500',
                'engine_cylinder': '4',
                'induction': 'Naturally Aspirated',
                'engine_type': 'Petrol',
                'fuel_grade': 'Regular Unleaded',
                'transmission': '6 SP Auto',
                'transmission_speed': 6,
                'transmission_type': 'Automatic',
                'drivetrain': 'AWD',
                'tailpipe_comb': '7.8L/100km',
                'tailpipe_comb_value': '7.8',
                'tailpipe_urban': '9.1L/100km',
                'tailpipe_urban_value': '9.1',
                'tailpipe_extra': '7.0L/100km',
                'tailpipe_extra_value': '7.0',
                'annual_cost': Decimal('2457.00'),
                'fuel_consumption_comb': Decimal('7.8'),
                'fuel_consumption_urban': Decimal('9.1'),
                'fuel_consumption_extra': Decimal('7.0'),
                'energy_consumption': Decimal('0.0'),
                'electric_range': Decimal('0.0'),
                'air_pollution_standard': 'Euro 6',
                'annual_tailpipe_co2': Decimal('180.0'),
                'fuel_lifecycle_co2': 210,
                'noise_data': '70 dB',
            }
        ]
        
        if not minimal:
            # Add more vehicles for comprehensive testing
            additional_vehicles = [
                {
                    'vehicle_id': 'VEH004',
                    'year': '2023',
                    'make': 'HYUNDAI',
                    'make_name': 'Hyundai',
                    'model': 'i30',
                    'vehicle_class': 'Small',
                    'body': 'Hatchback',
                    'doors': 5,
                    'seats': 5,
                    'engine': '2.0L 4cyl',
                    'engine_capacity': '2000',
                    'engine_cylinder': '4',
                    'induction': 'Naturally Aspirated',
                    'engine_type': 'Petrol',
                    'fuel_grade': 'Regular Unleaded',
                    'transmission': '6 SP Auto',
                    'transmission_speed': 6,
                    'transmission_type': 'Automatic',
                    'drivetrain': 'FWD',
                    'tailpipe_comb': '6.8L/100km',
                    'tailpipe_comb_value': '6.8',
                    'tailpipe_urban': '8.2L/100km',
                    'tailpipe_urban_value': '8.2',
                    'tailpipe_extra': '5.9L/100km',
                    'tailpipe_extra_value': '5.9',
                    'annual_cost': Decimal('2142.00'),
                    'fuel_consumption_comb': Decimal('6.8'),
                    'fuel_consumption_urban': Decimal('8.2'),
                    'fuel_consumption_extra': Decimal('5.9'),
                    'energy_consumption': Decimal('0.0'),
                    'electric_range': Decimal('0.0'),
                    'air_pollution_standard': 'Euro 6',
                    'annual_tailpipe_co2': Decimal('157.0'),
                    'fuel_lifecycle_co2': 185,
                    'noise_data': '69 dB',
                },
                {
                    'vehicle_id': 'VEH005',
                    'year': '2024',
                    'make': 'BMW',
                    'make_name': 'BMW',
                    'model': 'X3',
                    'vehicle_class': 'SUV Medium',
                    'body': 'SUV',
                    'doors': 5,
                    'seats': 5,
                    'engine': '2.0L 4cyl Turbo',
                    'engine_capacity': '2000',
                    'engine_cylinder': '4',
                    'induction': 'Turbo',
                    'engine_type': 'Petrol',
                    'fuel_grade': 'Premium Unleaded',
                    'transmission': '8 SP Auto',
                    'transmission_speed': 8,
                    'transmission_type': 'Automatic',
                    'drivetrain': 'AWD',
                    'tailpipe_comb': '8.5L/100km',
                    'tailpipe_comb_value': '8.5',
                    'tailpipe_urban': '10.2L/100km',
                    'tailpipe_urban_value': '10.2',
                    'tailpipe_extra': '7.5L/100km',
                    'tailpipe_extra_value': '7.5',
                    'annual_cost': Decimal('3247.00'),
                    'fuel_consumption_comb': Decimal('8.5'),
                    'fuel_consumption_urban': Decimal('10.2'),
                    'fuel_consumption_extra': Decimal('7.5'),
                    'energy_consumption': Decimal('0.0'),
                    'electric_range': Decimal('0.0'),
                    'air_pollution_standard': 'Euro 6',
                    'annual_tailpipe_co2': Decimal('196.0'),
                    'fuel_lifecycle_co2': 230,
                    'noise_data': '71 dB',
                }
            ]
            vehicles_data.extend(additional_vehicles)
        
        vehicles = []
        for vehicle_data in vehicles_data:
            vehicle, created = Vehicles.objects.get_or_create(
                vehicle_id=vehicle_data['vehicle_id'],
                defaults=vehicle_data
            )
            vehicles.append(vehicle)
        
        self.stdout.write(f'Created {len(vehicles_data)} vehicles')
        return vehicles

    def create_car_details(self):
        """Create legacy car details for compatibility"""
        car_details_data = [
            {
                'make': 'Toyota',
                'family': 'Corolla',
                'variant': 'Hybrid',
                'series': 'ZR',
                'style': '4D SEDAN',
                'engine': '1.8L HYBRID',
                'cc': '1798',
                'size': 'SMALL',
                'transmission': 'CVT AUTO',
                'cylinder': '4CYL',
                'width': '1780',
                'year': '2024',
                'month': 'Jan'
            },
            {
                'make': 'Tesla',
                'family': 'Model 3',
                'variant': 'Standard Range Plus',
                'series': 'RWD',
                'style': '4D SEDAN',
                'engine': 'ELECTRIC MOTOR',
                'cc': '0',
                'size': 'MID',
                'transmission': 'SINGLE SPEED',
                'cylinder': '0CYL',
                'width': '1849',
                'year': '2024',
                'month': 'Jan'
            },
            {
                'make': 'Mazda',
                'family': 'CX-5',
                'variant': 'Touring',
                'series': 'AWD',
                'style': '5D SUV',
                'engine': '2.5L SKYACTIV-G',
                'cc': '2488',
                'size': 'SUV',
                'transmission': '6 SP AUTO',
                'cylinder': '4CYL',
                'width': '1842',
                'year': '2024',
                'month': 'Jan'
            }
        ]
        
        for detail_data in car_details_data:
            CarDetails.objects.get_or_create(**detail_data)
        
        self.stdout.write(f'Created {len(car_details_data)} car details')

    def create_vehicle_images(self, vehicles):
        """Create vehicle images"""
        default_images = [
            'toyota-corolla-2024.jpg',
            'tesla-model3-2024.jpg',
            'mazda-cx5-2024.jpg',
            'hyundai-i30-2023.jpg',
            'bmw-x3-2024.jpg'
        ]
        
        for i, vehicle in enumerate(vehicles[:5]):
            image_name = default_images[i] if i < len(default_images) else f'car-{vehicle.vehicle_id}.jpg'
            VehicleImages.objects.get_or_create(
                vehicle_id=vehicle.vehicle_id,
                defaults={'image_name': image_name}
            )
        
        self.stdout.write(f'Created {min(len(vehicles), 5)} vehicle images')

    def create_search_logs(self, minimal=False):
        """Create search log entries"""
        # Test user IDs (replace with your Auth0 test user IDs)
        test_users = [
            'auth0|test-user-001',
            'auth0|test-user-002', 
            'auth0|test-user-003',
            'google-oauth2|test-user-004',
            'auth0|test-user-005'
        ]
        
        states = ['NSW', 'VIC', 'QLD', 'SA', 'WA']
        makes = ['Toyota', 'Tesla', 'Mazda', 'Hyundai', 'BMW']
        models = ['Corolla', 'Model 3', 'CX-5', 'i30', 'X3']
        years = ['2022', '2023', '2024']
        engine_types = ['Petrol', 'Hybrid', 'Electric', 'Diesel']
        
        search_logs = []
        num_searches = 5 if minimal else 20
        
        for i in range(num_searches):
            # Create some anonymous searches and some user searches
            is_anonymous = i % 3 == 0  # Every 3rd search is anonymous
            
            search_data = {
                'uid': str(uuid.uuid4()),
                'save_money': random.choice([True, False]),
                'greener_car': random.choice([True, False]),
                'good_all_rounder': random.choice([True, False]),
                'budget': Decimal(str(random.randint(15000, 80000))),
                'state': random.choice(states),
                'have_car': random.choice([True, False]),
                'ip_address': f'192.168.1.{random.randint(1, 254)}',
                'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'created_at': timezone.now() - timedelta(days=random.randint(0, 30))
            }
            
            # Add car details if they have a car
            if search_data['have_car']:
                search_data.update({
                    'make': random.choice(makes),
                    'model': random.choice(models),
                    'year': random.choice(years),
                    'engine_type': random.choice(engine_types),
                    'vehicle_id': f'VEH{random.randint(1, 5):03d}'
                })
            
            search_log = CarSearchLog.objects.create(**search_data)
            search_logs.append(search_log)
        
        self.stdout.write(f'Created {len(search_logs)} search logs')
        return search_logs

    def create_garage_entries(self, search_logs, minimal=False):
        """Create garage entries for test users"""
        test_users = [
            {'user_id': 'auth0|test-user-001', 'email': 'john.doe@example.com'},
            {'user_id': 'auth0|test-user-002', 'email': 'jane.smith@example.com'},
            {'user_id': 'google-oauth2|test-user-003', 'email': 'mike.johnson@example.com'},
        ]
        
        num_entries = 3 if minimal else 10
        
        for i in range(num_entries):
            user = test_users[i % len(test_users)]
            search_log = search_logs[i % len(search_logs)]
            
            garage_data = {
                'user_id': user['user_id'],
                'user_email': user['email'],
                'save_money': search_log.save_money,
                'greener_car': search_log.greener_car,
                'good_all_rounder': search_log.good_all_rounder,
                'budget': search_log.budget,
                'state': search_log.state,
                'have_car': search_log.have_car,
                'make': search_log.make,
                'model': search_log.model,
                'year': search_log.year,
                'engine_type': search_log.engine_type,
                'vehicle_id': search_log.vehicle_id,
                'original_search_uid': search_log.uid,
                'is_current_car': i % 4 == 0,  # Every 4th car is marked as current
                'nickname': f"{search_log.make} {search_log.model}" if search_log.make else f"Car #{i+1}",
                'ip_address': search_log.ip_address,
                'user_agent': search_log.user_agent,
                'created_at': search_log.created_at + timedelta(hours=1)
            }
            
            MyGarage.objects.create(**garage_data)
        
        self.stdout.write(f'Created {num_entries} garage entries')

    def create_subscriptions(self, search_logs):
        """Create subscription records"""
        test_users = [
            {'user_id': 'auth0|test-user-001', 'email': 'john.doe@example.com'},
            {'user_id': 'auth0|test-user-002', 'email': 'jane.smith@example.com'},
            {'user_id': 'google-oauth2|test-user-003', 'email': 'mike.johnson@example.com'},
        ]
        
        plans = ['smart-choice', 'core-advantage', 'full-insight-pro']
        
        for i, user in enumerate(test_users):
            subscription_data = {
                'user_id': user['user_id'],
                'user_email': user['email'],
                'payment_uuid': str(uuid.uuid4()),
                'search_uid': search_logs[i].uid if i < len(search_logs) else None,
                'plan_name': plans[i % len(plans)],
                'subscription_status': 'active',
                'created_at': timezone.now() - timedelta(days=random.randint(1, 30))
            }
            
            UserSubscription.objects.create(**subscription_data)
        
        self.stdout.write(f'Created {len(test_users)} subscriptions')

    def get_statistics(self):
        """Print database statistics"""
        stats = {
            'States': States.objects.count(),
            'Car Makes': CarMakes.objects.count(),
            'Vehicles': Vehicles.objects.count(),
            'Car Details': CarDetails.objects.count(),
            'Vehicle Images': VehicleImages.objects.count(),
            'Search Logs': CarSearchLog.objects.count(),
            'Garage Entries': MyGarage.objects.count(),
            'Subscriptions': UserSubscription.objects.count(),
        }
        
        self.stdout.write('\n' + '='*50)
        self.stdout.write('DATABASE STATISTICS')
        self.stdout.write('='*50)
        for model, count in stats.items():
            self.stdout.write(f'{model}: {count}')
        self.stdout.write('='*50 + '\n')