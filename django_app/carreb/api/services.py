from .models import CarDetails, Vehicles, CarPricing, CarBodyCost, FuelRetailPrice, ElectricityGridEmissions
import math

def ParseCarDetailsFromGG(file):
    """Reads a fixed-width data file starting from row 3 and stores the data in the database."""
    data_to_insert = []

    # Read and decode the file
    decoded_file = file.read().decode('utf-8').strip().split("\n")

    # Skip the first three rows
    data_rows = decoded_file[3:]

    for line in data_rows:
        data = CarDetails(
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
            year=line[232:236].strip(),
            month=line[28:32].strip(),
        )
        data_to_insert.append(data)

    # Bulk insert for better performance
    CarDetails.objects.bulk_create(data_to_insert)
    return {"message": f"{len(data_to_insert)} records successfully stored."}