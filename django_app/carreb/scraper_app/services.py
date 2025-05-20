import re

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
