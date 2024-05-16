import requests
from geolib import geohash


def find_new_nearby_pharmacies(api_key, location, radius_in_miles=1):
    """
    Find nearby pharmacies using Google Places API, with radius specified in miles.

    Args:
    - api_key (str): Your Google API key.
    - location (str): The latitude/longitude around which to retrieve place information. Format: "lat,lng".
    - radius_in_miles (int or float): Distance in miles within which to search for pharmacies (default is 1 mile).

    Returns:
    - dict: The JSON response from the Google Places API.
    """

    url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
    params = {
        "key": api_key,
        "location": location,
        "rankby": "distance",
        # "keyword": "CVS Pharmacy|Rite Aid|Wallgreens|Wallmart",
        "keyword": "CVS Pharmacy"
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()  # Raise an HTTPError for bad responses (4xx and 5xx)

        # Parse the JSON response
        response_json = response.json()

        pharm_response_list = response_json["results"]        

        filtered_pharmacies = [pharmacy for pharmacy in pharm_response_list if parse_pharmacy_brand(pharmacy["name"])]

        new_pharmacies = []
        for pharm in filtered_pharmacies:

            name = pharm["name"]
            ggl_place_id = pharm["place_id"]
            lon = pharm["geometry"]["location"]["lng"]
            lat = pharm["geometry"]["location"]["lat"]

            phone, address = get_place_details(api_key, ggl_place_id)
            phone_formatted = format_phone_number(phone)
            pharm_code = get_pharmacy_code(name)

            new_pharmacies.append({
                "name": name,
                "phone": phone_formatted,
                "address": address,
                "ggl_place_id": ggl_place_id,
                "pharm_code": pharm_code,
                "location": {
                    "geohash_2": geohash.encode(lat, lon, 2),
                    "geohash_3": geohash.encode(lat, lon, 3),
                    "geohash_4": geohash.encode(lat, lon, 4),
                    "geohash_5": geohash.encode(lat, lon, 5),
                    "geohash_6": geohash.encode(lat, lon, 6),
                    "lat": lat,
                    "lon": lon
                }
            })

        return new_pharmacies

    except Exception as e:
        print(f"An error occurred collecting new pharmacies: {e}")
        return []
    
    
# formats phone number using coiuntry code and no spaces or special characters
def format_phone_number(phone_number):
    # Remove spaces, hyphens, and other non-digit characters except the plus sign
    formatted_number = ''.join(char for char in phone_number if char.isdigit() or char == '+')
    return formatted_number

# returns pharmacy details like address and phone number
def get_place_details(api_key, place_id):
    url = "https://maps.googleapis.com/maps/api/place/details/json"
    params = {
        'key': api_key,
        'place_id': place_id,
        'fields': 'formatted_address,international_phone_number'  # Customize fields as needed
    }

    response = requests.get(url, params=params)
    response_json = response.json()
    address = response_json["result"]["formatted_address"]
    phone = response_json["result"]["international_phone_number"]
    return phone, address

# given pharmacy name, return RxRadar pharmacy code
def get_pharmacy_code(name):
    eligible_pharms = ["CVS Pharmacy", "Walgreens", "Rite Aid", "Wallmart"] # pharmacy name
    eligible_pharm_codes = ["CVS", "SCB", "WGR", "RTA" ] # our corresponding pharmacy code
    name = name.lower()
    for i, pharm in enumerate(eligible_pharms):
        if pharm.lower() in name:
            return eligible_pharm_codes[i]

    # otherwise return none
    return None

# parse pharmacy name to get name
def parse_pharmacy_brand(name):
    eligible_pharms = ["CVS", "Sam's Club", "Walgreens", "Rite Aid"]
    # Convert the name to lowercase for case-insensitive comparison
    name = name.lower()
    for pharm in eligible_pharms:
        if pharm.lower() == name:
            return True

    return False
