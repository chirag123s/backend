# django_app/carreb/api/management/commands/verify_data.py
from django.core.management.base import BaseCommand
from django.db.models import Count
from api.models import (
    CarMakes, States, Vehicles, CarDetails, CarSearchLog, 
    MyGarage, UserSubscription, VehicleImages
)


class Command(BaseCommand):
    help = 'Verify seeded data and show sample records'

    def handle(self, *args, **options):
        self.stdout.write('Verifying seeded data...\n')
        
        # Check data counts
        self.verify_data_counts()
        
        # Show sample records
        self.show_sample_records()
        
        # Show test user data
        self.show_test_user_data()
        
        # Show search logs with UIDs
        self.show_search_logs()

    def verify_data_counts(self):
        """Verify data counts"""
        models = [
            (States, 'States'),
            (CarMakes, 'Car Makes'),
            (Vehicles, 'Vehicles'),
            (CarDetails, 'Car Details'),
            (VehicleImages, 'Vehicle Images'),
            (CarSearchLog, 'Search Logs'),
            (MyGarage, 'Garage Entries'),
            (UserSubscription, 'Subscriptions'),
        ]
        
        self.stdout.write('='*60)
        self.stdout.write('DATA COUNTS VERIFICATION')
        self.stdout.write('='*60)
        
        for model, name in models:
            count = model.objects.count()
            status = '✓' if count > 0 else '✗'
            self.stdout.write(f'{status} {name}: {count}')
        
        self.stdout.write('='*60 + '\n')

    def show_sample_records(self):
        """Show sample records from each table"""
        self.stdout.write('SAMPLE RECORDS')
        self.stdout.write('='*60)
        
        # Sample vehicles
        vehicles = Vehicles.objects.all()[:3]
        self.stdout.write('\nSample Vehicles:')
        for vehicle in vehicles:
            self.stdout.write(f'  • {vehicle.year} {vehicle.make_name} {vehicle.model} ({vehicle.vehicle_id})')
        
        # Sample car makes
        makes = CarMakes.objects.filter(popular=True)[:5]
        self.stdout.write('\nPopular Car Makes:')
        for make in makes:
            self.stdout.write(f'  • {make.name} (popular: {make.popular})')
        
        # Sample states
        states = States.objects.all()[:4]
        self.stdout.write('\nStates:')
        for state in states:
            self.stdout.write(f'  • {state.short_name}: {state.name}')

    def show_test_user_data(self):
        """Show test user garage and subscription data"""
        self.stdout.write('\n' + '='*60)
        self.stdout.write('TEST USER DATA')
        self.stdout.write('='*60)
        
        # Show garage entries by user
        garage_by_user = MyGarage.objects.values('user_email').annotate(count=Count('id'))
        self.stdout.write('\nGarage Entries by User:')
        for entry in garage_by_user:
            self.stdout.write(f'  • {entry["user_email"]}: {entry["count"]} cars')
        
        # Show subscriptions
        subscriptions = UserSubscription.objects.all()
        self.stdout.write('\nSubscriptions:')
        for sub in subscriptions:
            self.stdout.write(f'  • {sub.user_email}: {sub.plan_name} ({sub.subscription_status})')

    def show_search_logs(self):
        """Show search logs with UIDs for testing"""
        self.stdout.write('\n' + '='*60)
        self.stdout.write('SEARCH LOGS FOR TESTING')
        self.stdout.write('='*60)
        
        search_logs = CarSearchLog.objects.all()[:5]
        self.stdout.write('\nSample Search UIDs (use these for testing):')
        for log in search_logs:
            car_info = f"{log.make} {log.model} {log.year}" if log.make else "No car specified"
            self.stdout.write(f'  • UID: {log.uid}')
            self.stdout.write(f'    Car: {car_info}')
            self.stdout.write(f'    Budget: ${log.budget}, State: {log.state}')
            self.stdout.write(f'    URL: /smart-car-finder?sid={log.uid}')
            self.stdout.write('')


# Sample API testing script
# test_api_endpoints.py (standalone script)
"""
API Testing Script for CarReb

Run this script to test the seeded data with actual API calls.
Make sure your Django server is running on localhost:8001
"""

import requests
import json

API_BASE_URL = 'http://localhost:8001/api'

def test_api_endpoints():
    """Test API endpoints with seeded data"""
    
    print("="*60)
    print("TESTING CARREB API ENDPOINTS")
    print("="*60)
    
    # Test 1: Get states
    print("\n1. Testing States API:")
    try:
        response = requests.get(f'{API_BASE_URL}/states/')
        if response.status_code == 200:
            data = response.json()
            print(f"   ✓ Found {len(data.get('states', []))} states")
            print(f"   Sample: {data['states'][0] if data.get('states') else 'None'}")
        else:
            print(f"   ✗ Error: {response.status_code}")
    except Exception as e:
        print(f"   ✗ Connection error: {e}")
    
    # Test 2: Get car makes
    print("\n2. Testing Car Makes API:")
    try:
        response = requests.get(f'{API_BASE_URL}/car/makes/')
        if response.status_code == 200:
            data = response.json()
            print(f"   ✓ Found {len(data.get('popular', []))} popular makes")
            print(f"   ✓ Found {len(data.get('all', []))} total makes")
            if data.get('popular'):
                print(f"   Sample popular: {data['popular'][0]['name']}")
        else:
            print(f"   ✗ Error: {response.status_code}")
    except Exception as e:
        print(f"   ✗ Connection error: {e}")
    
    # Test 3: Test search by ID (you'll need to replace with actual UID)
    print("\n3. Testing Search by ID API:")
    print("   Note: Replace 'test-uid' with actual UID from seeded data")
    
    # Test 4: Test garage listing (you'll need actual user ID)
    print("\n4. Testing Garage API:")
    print("   Note: Replace 'test-user-id' with actual user ID")
    print(f"   URL: {API_BASE_URL}/garage/list/?user_id=auth0|test-user-001")
    
    print("\n" + "="*60)
    print("API TESTING COMPLETE")
    print("="*60)

if __name__ == '__main__':
    test_api_endpoints()


# Quick test queries for Django shell
DJANGO_SHELL_QUERIES = """
# Quick Test Queries for Django Shell
# Run: python manage.py shell
# Then copy and paste these queries:

from api.models import *

# 1. Check data counts
print("Data Counts:")
print(f"States: {States.objects.count()}")
print(f"Car Makes: {CarMakes.objects.count()}")
print(f"Vehicles: {Vehicles.objects.count()}")
print(f"Search Logs: {CarSearchLog.objects.count()}")
print(f"Garage Entries: {MyGarage.objects.count()}")

# 2. Get sample search UIDs for testing
print("\\nSample Search UIDs:")
for log in CarSearchLog.objects.all()[:3]:
    print(f"UID: {log.uid}")
    print(f"URL: /smart-car-finder?sid={log.uid}")

# 3. Check test users
print("\\nTest Users in Garage:")
for garage in MyGarage.objects.all()[:5]:
    print(f"User: {garage.user_email}")
    print(f"Car: {garage.make} {garage.model} {garage.year}")
    print(f"Current Car: {garage.is_current_car}")

# 4. Check vehicle data
print("\\nSample Vehicles:")
for vehicle in Vehicles.objects.all()[:3]:
    print(f"{vehicle.year} {vehicle.make_name} {vehicle.model}")
    print(f"Fuel Cost: ${vehicle.annual_cost}/year")
    print(f"CO2: {vehicle.annual_tailpipe_co2}g/km")

# 5. Test search flow simulation
test_search = CarSearchLog.objects.first()
if test_search:
    print(f"\\nTest Search Flow:")
    print(f"1. Search UID: {test_search.uid}")
    print(f"2. Frontend URL: /smart-car-finder?sid={test_search.uid}")
    print(f"3. Pricing URL: /pricing?sid={test_search.uid}")
"""