import requests
from geolib import geohash
import uuid
import yaml
import os

def load_yaml_file(filepath):
    with open(filepath, 'r') as file:
        data = yaml.safe_load(file)
    return data

# Use the function to load the configuration
config = load_yaml_file('config.yaml')

env = os.getenv("deployment_env")

GGL_PLACES_API_KEY = config[env]["places"]["api_key"] 
FIREBASE_PHARMACIES_DB = config[env]["firebase"]["pharmacy_db"] 


def find_new_nearby_pharmacies(db, location, radius_in_miles=1):
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
        "key": GGL_PLACES_API_KEY,
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

            phone, address = get_place_details(GGL_PLACES_API_KEY, ggl_place_id)
            phone_formatted = format_phone_number(phone)
            pharm_code = get_pharmacy_code(name)

            new_pharmacies.append({
                "name": name,
                "phone": phone_formatted,
                "address": address,
                "ggl_place_id": ggl_place_id,
                "pharm_code": pharm_code,
                "pharmacy_uuid": str(uuid.uuid4()),
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

        # add new pharmacies to db
        add_pharmacies_to_db(db=db, new_pharmacies=new_pharmacies)

        return new_pharmacies

    except Exception as e:
        print(f"An error occurred collecting new pharmacies: {e}")
        return []
    
# adds new pharmacies to the database
def add_pharmacies_to_db(db, new_pharmacies):
    for pharmacy in new_pharmacies:
        try:
            pharmacies_ref = db.collection(FIREBASE_PHARMACIES_DB)
            query = pharmacies_ref.where('ggl_place_id', '==', pharmacy['ggl_place_id']).limit(1)
            
            docs = list(query.stream())
            
            # Check if the query returns any document
            if len(docs) > 0:
                # pharmacy exists in db
                continue
            else:
                # pharmacy does not exist in db — add new pharmacy
                new_doc_ref = pharmacies_ref.document(pharmacy["pharm_uuid"])
                new_doc_ref.set(pharmacy)
            
        except Exception as e:
            continue # if checking for a pharmacy/ adding it to db fails, continue to the next pharmacy
    
    
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
    eligible_pharm_codes = ["CVS", "WGR", "RTA", "WMT" ] # our corresponding pharmacy code
    name = name.lower()
    for i, pharm in enumerate(eligible_pharms):
        if pharm.lower() in name:
            return eligible_pharm_codes[i]

    # otherwise return none
    return None

# parse pharmacy name to get name
def parse_pharmacy_brand(name):
    eligible_pharms = ["CVS Pharmacy", "Sam's Club", "Walgreens", "Rite Aid"]
    # Convert the name to lowercase for case-insensitive comparison
    name = name.lower()
    for pharm in eligible_pharms:
        if pharm.lower() == name:
            return True

    return False
