import re
import os
import requests
import time
import random

from django.conf import settings
#from django.http import JsonResponse
from rest_framework.response import Response
from duckduckgo_search import DDGS
from PIL import Image
from io import BytesIO
from django.utils.text import slugify


#Parse vehicle engine
def parse_vehicle_engine_spec(engine):

    engine_capacity = ''
    engine_cylinder = ''
    induction = ''
    engine_type = ''
    fuel_grade = ''
    
    if 'Electric Plug-in Electric/Petrol' in engine:
        # Match engine capacity (e.g. "0.6L", "2.0L", etc.)
        capacity_match = re.search(r'\b[\d.]+L\b', engine)
        engine_capacity = capacity_match.group() if capacity_match else ''

        # Find where engine capacity ends
        if engine_capacity:
            after_capacity = engine.split(engine_capacity, 1)[1].strip()
        else:
            after_capacity = engine.strip()

        # Match fuel type (ends with RON or RO — flexible)
        fuel_match = re.search(r'(.*?)(\b.*?RO[N]?\b)', after_capacity)
        if fuel_match:
            engine_type = fuel_match.group(1).strip()
            fuel_grade = fuel_match.group(2).strip()
        else:
            engine_type = after_capacity
            fuel_grade = ''

    elif 'cyl Plug-in Electric/Petrol' in engine:
        # Find engine capacity (e.g., "1.5L")
        capacity_match = re.search(r'\b[\d.]+L\b', engine)
        engine_capacity = capacity_match.group(0) if capacity_match else ''

        # Find engine cylinder (e.g., "4cyl")
        cyl_match = re.search(r'\b\d+cyl\b', engine)
        engine_cylinder = cyl_match.group(0) if cyl_match else ''

        # Find fuel type (e.g., "91RON")
        fuel_match = re.search(r'\b\S*RO[N]?\b', engine)
        fuel_grade = fuel_match.group(0) if fuel_match else ''

        # Everything in between = engine type
        engine_type = engine
        for val in [engine_capacity, engine_cylinder, fuel_grade]:
            if val:
                engine_type = engine_type.replace(val, '')
        engine_type = engine_type.strip()

    elif 'Turbo Petrol' in engine:
        tokens = engine.split()

        engine_capacity = next((t for t in tokens if t.endswith("L")), '')
        engine_cylinder = next((t for t in tokens if t.endswith("cyl")), '')
        induction = next((t for t in tokens if "Turbo" in t), '')
        fuel_grade = next((t for t in tokens if re.search(r'RO[N]?$', t)), '')

        # Remaining token after extracting above
        used_tokens = {engine_capacity, engine_cylinder, induction, fuel_grade}
        engine_type = next((t for t in tokens if t not in used_tokens), '')

    elif 'Petrol' in engine and 'Turbo' not in engine:
        engine_capacity = re.search(r'\b[\d.]+L\b', engine)
        engine_capacity = engine_capacity.group() if engine_capacity else ''

        engine_cylinder = re.search(r'\b\d+cyl\b', engine, re.IGNORECASE)
        engine_cylinder = engine_cylinder.group() if engine_cylinder else ''

        engine_type = re.search(r'\b(Petrol|Diesel|Hybrid|Electric)\b', engine, re.IGNORECASE)
        engine_type = engine_type.group() if engine_type else ''

        fuel_grade = re.search(r'\b\S*RO[N]?\b', engine, re.IGNORECASE)  # matches RON or similar
        fuel_grade = fuel_grade.group() if fuel_grade else ''

    elif 'Diesel' in engine and 'Turbo' not in engine:
        engine_capacity = re.search(r'\b[\d.]+L\b', engine)
        engine_capacity = engine_capacity.group() if engine_capacity else ''

        engine_cylinder = re.search(r'\b\d+cyl\b', engine, re.IGNORECASE)
        engine_cylinder = engine_cylinder.group() if engine_cylinder else ''

        engine_type = re.search(r'\b(Petrol|Diesel|Hybrid|Electric)\b', engine, re.IGNORECASE)
        engine_type = engine_type.group() if engine_type else ''

    elif 'Turbo Diesel' in engine:
        tokens = engine.split()

        engine_capacity = next((t for t in tokens if t.endswith("L")), '')
        engine_cylinder = next((t for t in tokens if t.endswith("cyl")), '')
        induction = next((t for t in tokens if "Turbo" in t), '')
        fuel_grade = ''

        # Remaining token after extracting above
        used_tokens = {engine_capacity, engine_cylinder, induction, fuel_grade}
        engine_type = next((t for t in tokens if t not in used_tokens), '')
        
    elif 'cyl Electric/Petrol' in engine:
        # Match engine capacity (ends with L)
        capacity_match = re.search(r'\b[\d.]+L\b', engine)
        engine_capacity = capacity_match.group(0) if capacity_match else None

        # Match cylinder (ends with cyl)
        cyl_match = re.search(r'\b\d+cyl\b', engine)
        engine_cylinder = cyl_match.group(0) if cyl_match else None

        # Match fuel type (ends with RON or RO)
        fuel_match = re.search(r'\b\S*RO[N]?\b', engine)
        fuel_grade = fuel_match.group(0) if fuel_match else None

        # Remove all matched parts to get engine type
        engine_type = re.sub(r'[\d.]+L|\d+cyl|\S*RO[N]?', '', engine).strip()
    
    elif 'Turbo Plug-in Electric/Petrol' in engine:
        parts = engine.split()
    
        engine_capacity = next((p for p in parts if p.endswith('L')), '')
        engine_cylinder = next((p for p in parts if p.endswith('cyl')), '')
        induction = ''
        fuel_grade = ''
        engine_type = ''

        # Induction: assume it's the word right after "cyl"
        try:
            cyl_index = parts.index(engine_cylinder)
            induction = parts[cyl_index + 1]
        except (ValueError, IndexError):
            induction = ''

        # Fuel type: last word ending in RON
        fuel_grade = next((p for p in reversed(parts) if p.endswith('RON')), '')

        # Engine type: all words between induction and fuel_type
        try:
            fuel_index = parts.index(fuel_grade)
            engine_type = ' '.join(parts[cyl_index + 2:fuel_index])
        except (ValueError, IndexError):
            engine_type = ''

    elif 'Turbo Electric/Petrol' in engine:
        parts = engine.split()

        engine_capacity = next((p for p in parts if p.endswith('L')), '')
        engine_cylinder = next((p for p in parts if p.endswith('cyl')), '')
        fuel_grade = next((p for p in reversed(parts) if p.endswith('RO') or p.endswith('RON')), '')

        # Remove matched parts to extract the rest
        remaining = [p for p in parts if p not in {engine_capacity, engine_cylinder, fuel_grade}]

        # Assume first remaining = induction, rest = engine type
        induction = remaining[0] if remaining else ''
        engine_type = ' '.join(remaining[1:]) if len(remaining) > 1 else ''

    elif 'Turbo Electric/Diesel' in engine:
        parts = engine.split()

        engine_capacity = next((p for p in parts if p.endswith('L')), None)
        engine_cylinder = next((p for p in parts if p.endswith('cyl')), None)
        fuel_grade = ''

        # Remove matched parts to extract the rest
        remaining = [p for p in parts if p not in {engine_capacity, engine_cylinder, fuel_grade}]

        # Assume first remaining = induction, rest = engine type
        induction = remaining[0] if remaining else None
        engine_type = ' '.join(remaining[1:]) if len(remaining) > 1 else None
    
    elif 'Turbo Plug-in Electric/Diesel' in engine:
        parts = engine.split()
    
        engine_capacity = next((p for p in parts if p.endswith('L')), '')
        engine_cylinder = next((p for p in parts if p.endswith('cyl')), '')
        induction = ''
        fuel_grade = ''
        engine_type = ''

        # Induction: assume it's the word right after "cyl"
        try:
            cyl_index = parts.index(engine_cylinder)
            induction = parts[cyl_index + 1]
        except (ValueError, IndexError):
            induction = ''

        # Fuel type: last word ending in RON
        fuel_grade = ''

        # Engine type: all words between induction and fuel_type
        try:
            fuel_index = parts.index(fuel_grade)
            engine_type = ' '.join(parts[cyl_index + 2:fuel_index])
        except (ValueError, IndexError):
            engine_type = ''


    elif 'Pure Electric' in engine:
        engine_type = 'Pure Electric'

    return {
        "engine_capacity": engine_capacity,
        "engine_cylinder": engine_cylinder,
        "induction": induction,
        "engine_type": engine_type,
        "fuel_grade": fuel_grade
    }


# Parse vehicle transmission
def parse_vehicle_transmission_spec(transmission):

     # Match the transmission speed (number before "spd" or "speed")
    speed_match = re.search(r'\b(\d+)\s*(spd|speed)', transmission, re.IGNORECASE)
    speed = int(speed_match.group(1)) if speed_match else None

    # Remove the speed part to get transmission type
    transmission_type = re.sub(r'\b\d+\s*(spd|speed)\b', '', transmission, flags=re.IGNORECASE).strip()

    return {
        "speed": speed,
        "type": transmission_type
    }

# Parse tailpipe
def parse_vehicle_tailpipe(tailpipe_value):
    s = tailpipe_value.strip()

    if s.upper() == 'N/A':
        return {'value': '', 'note': ''}

    # Extract value and optional note in brackets
    match = re.match(r'^(\S+)(?:\s*\[(.*?)\])?$', s)
    if not match:
        return {'value': '', 'note': ''}

    value = match.group(1)
    note = match.group(2) if match.group(2) else ''

    # If value is "N/A", still return empty
    if value.upper() == 'N/A' and note == '':
        return {'value': '', 'note': ''}

    return {'value': value, 'note': note}



def normalize_liter_string(s):
    match = re.match(r'^(\d+(?:\.\d+)?)(L)$', s.strip(), re.IGNORECASE)
    if not match:
        return s  # Return as-is if it doesn't match pattern

    value, unit = match.groups()
    if '.' not in value:
        value = f"{value}.0"

    return f"{value}{unit.upper()}"


def generate_vehicle_id(year, latest_number):
    next_number = latest_number + 1
    return f"CRB-{year}-{next_number:06d}"


#def download_duck_image(request):
def download_duck_image_v1(make, model, year):
    make = make.strip() #request.GET.get('make')
    model = model.strip() #request.GET.get('model')
    year = year.strip() #request.GET.get('year')

    if not all([make, model, year]):
        return Response({"error": "Missing make, model, or year"}, status=400)

    query = f"{year} {make} {model} car"
    slug_name = slugify(f"{make}-{model}-{year}")
    filename = f"{slug_name}.jpg"
    file_path = os.path.join(settings.SCRAPER_DL_PATH, filename)
    file_url = f"{settings.MEDIA_URL}{filename}"

    # ✅ 5. Check if image already exists
    if os.path.exists(file_path):
        return Response({
            "message": "Image already exists",
            "filename": filename,
            "url": file_url
        })

    try:
        with DDGS() as ddgs:
            results = list(ddgs.images(query, max_results=30))

        if not results:
            return Response({"error": "No image found"}, status=404)

        # ✅ 1. Prioritize images from official domains
        preferred_domains = ['toyota.com', 'ford.com', 'nissanusa.com', 'honda.com', 'chevrolet.com']
        image_info = None

        for r in results:
            domain = r.get("source") or ""
            img_url = r.get("image")
            width = r.get("width", 0)
            height = r.get("height", 0)

            # ✅ 2. Portrait filter
            if height < width and img_url:
                # Prioritize manufacturer domains
                if any(domain.endswith(d) for d in preferred_domains):
                    image_info = r
                    break
                elif not image_info:  # fallback to first matching public portrait
                    image_info = r

        if not image_info:
            return Response({"error": "No portrait image found"}, status=404)

        # Download the image
        img_url = image_info['image']
        response = requests.get(img_url, timeout=10)
        response.raise_for_status()

        # ✅ 3. Resize image to width 720px using Pillow
        image = Image.open(BytesIO(response.content))
        if image.width > 720:
            ratio = 720 / image.width
            new_size = (720, int(image.height * ratio))
            image = image.resize(new_size, Image.ANTIALIAS)

        # ✅ Save the image
        os.makedirs(settings.MEDIA_ROOT, exist_ok=True)
        image.save(file_path, format='JPEG', quality=85)

        return Response({
            "message": "Image downloaded and processed",
            "filename": filename,
            "url": file_url
        })

    except Exception as e:
        return Response({"error": str(e)}, status=500)
    

#def download_duck_image(request):
def download_duck_image(make, model, year):
    make = make.strip() #request.GET.get('make')
    model = model.strip() #request.GET.get('model')
    year = year.strip() #request.GET.get('year')

    if not all([make, model, year]):
        return {"error": "Missing make, model, or year"}

    query = f"{year} {make} {model} official manufacturer car"
    fallback_query = f"{year} {make} {model} car"

    # Create URL-safe filename
    filename_slug = slugify(f"{make}-{model}-{year}")
    filename = f"{filename_slug}.jpg"
    file_path = os.path.join(settings.SCRAPER_DL_PATH, filename)
    os.makedirs(settings.SCRAPER_DL_PATH, exist_ok=True)

    # Check if image already exists
    if os.path.exists(file_path):
        return Response({
            "message": "Image already exists",
            "filename": filename,
            "url": f"{settings.MEDIA_URL}{filename}"
        })

    # Image search
    def get_image_url(query):
        with DDGS() as ddgs:
            results = list(ddgs.images(query, max_results=10))
        
        user_agents = [
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/37.0.2062.94 Chrome/37.0.2062.94 Safari/537.36',
            'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/45.0.2454.85 Safari/537.36',
            'Mozilla/5.0 (Windows NT 6.1; WOW64; Trident/7.0; rv:11.0) like Gecko',
            'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:40.0) Gecko/20100101 Firefox/40.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_5) AppleWebKit/600.8.9 (KHTML, like Gecko) Version/8.0.8 Safari/600.8.9',
            'Mozilla/5.0 (iPad; CPU OS 8_4_1 like Mac OS X) AppleWebKit/600.1.4 (KHTML, like Gecko) Version/8.0 Mobile/12H321 Safari/600.1.4',
            'Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/45.0.2454.85 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/45.0.2454.85 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.135 Safari/537.36 Edge/12.10240',
            'Mozilla/5.0 (Windows NT 6.3; WOW64; rv:40.0) Gecko/20100101 Firefox/40.0',
            'Mozilla/5.0 (Windows NT 6.3; WOW64; Trident/7.0; rv:11.0) like Gecko',
            'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/45.0.2454.85 Safari/537.36',
            'Mozilla/5.0 (Windows NT 6.1; Trident/7.0; rv:11.0) like Gecko',
            'Mozilla/5.0 (Windows NT 10.0; WOW64; rv:40.0) Gecko/20100101 Firefox/40.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_4) AppleWebKit/600.7.12 (KHTML, like Gecko) Version/8.0.7 Safari/600.7.12',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/45.0.2454.85 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.10; rv:40.0) Gecko/20100101 Firefox/40.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_5) AppleWebKit/600.8.9 (KHTML, like Gecko) Version/7.1.8 Safari/537.85.17',
            'Mozilla/5.0 (iPad; CPU OS 8_4 like Mac OS X) AppleWebKit/600.1.4 (KHTML, like Gecko) Version/8.0 Mobile/12H143 Safari/600.1.4',
            'Mozilla/5.0 (iPad; CPU OS 8_3 like Mac OS X) AppleWebKit/600.1.4 (KHTML, like Gecko) Version/8.0 Mobile/12F69 Safari/600.1.4',
            'Mozilla/5.0 (Windows NT 6.1; rv:40.0) Gecko/20100101 Firefox/40.0',
            'Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.1; WOW64; Trident/6.0)',
            'Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; WOW64; Trident/5.0)',
            'Mozilla/5.0 (Windows NT 6.3; WOW64; Trident/7.0; Touch; rv:11.0) like Gecko',
            'Mozilla/5.0 (Windows NT 5.1; rv:40.0) Gecko/20100101 Firefox/40.0',
            'Mozilla/5.0 (Windows NT 5.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/45.0.2454.85 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_3) AppleWebKit/600.6.3 (KHTML, like Gecko) Version/8.0.6 Safari/600.6.3',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_3) AppleWebKit/600.5.17 (KHTML, like Gecko) Version/8.0.5 Safari/600.5.17',
            'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:38.0) Gecko/20100101 Firefox/38.0',
            'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/44.0.2403.157 Safari/537.36',
            'Mozilla/5.0 (iPhone; CPU iPhone OS 8_4_1 like Mac OS X) AppleWebKit/600.1.4 (KHTML, like Gecko) Version/8.0 Mobile/12H321 Safari/600.1.4',
            'Mozilla/5.0 (Windows NT 10.0; WOW64; Trident/7.0; rv:11.0) like Gecko',
            'Mozilla/5.0 (iPad; CPU OS 7_1_2 like Mac OS X) AppleWebKit/537.51.2 (KHTML, like Gecko) Version/7.0 Mobile/11D257 Safari/9537.53',
            'Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; Trident/5.0)',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/45.0.2454.85 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/45.0.2454.85 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.9; rv:40.0) Gecko/20100101 Firefox/40.0',
            'Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.1; Trident/6.0)',
            'Mozilla/5.0 (Windows NT 6.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/45.0.2454.85 Safari/537.36'
        ]
        for result in results:
            delay = random.choice([15, 30, 45, 60])
            print(f"Next in {delay}sec.")
            time.sleep(delay)

            print(f"{make}-{model}-{year} = {result['image']}")
            
            if 'image' in result:
                try:
                    #img_resp = requests.get(result['image'], timeout=10)
                    headers = {
                        "User-Agent": random.choice(user_agents),
                        "Accept-Language": "en-US,en;q=0.9",
                        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                        "Referer": "https://google.com"
                    }
                    img_resp = requests.get(result['image'], headers=headers)
                    img = Image.open(BytesIO(img_resp.content))
                    if img.width > img.height:  # landscape only
                        return img
                except Exception:
                    continue
        return None

    image = get_image_url(query) or get_image_url(fallback_query)
    if not image:
        return {"error": "No suitable image found"}

    # Resize to 720px width
    def resize_image(img):
        # ✅ Fix: Convert if incompatible mode
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")

        if img.width > 720:
            ratio = 720 / img.width
            new_height = int(img.height * ratio)
            img = img.resize((720, new_height), Image.LANCZOS)
        return img

    # Crop to 720x480 if image is not landscape
    def crop_to_720x480(img):
        img = img.convert('RGB')  # Ensure JPEG compatible
        if img.width < 720 or img.height < 480:
            # Resize up first if too small
            img = img.resize((720, 480), Image.LANCZOS)
        else:
            # Center crop
            left = (img.width - 720) / 2
            top = (img.height - 480) / 2
            img = img.crop((left, top, left + 720, top + 480))
        return img

    # Process image
    if image.width < image.height:
        image = crop_to_720x480(image)
    else:
        image = resize_image(image)

    # Save image
    image.save(file_path, "JPEG", quality=85)

    return {
        "message": "Image downloaded",
        "filename": filename,
        "url": f"{settings.MEDIA_URL}{filename}"
    }