
from .models import CarDetails

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

