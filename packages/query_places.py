import requests

eligible_pharms = ["CVS"] #["CVS", "Sam's Club", "Walgreens", "Rite Aid" ]

def evaluate_pharmacy_name(obj):
    return obj["name"] in eligible_pharms

def format_phone_number(phone_number):
    """
    Format a phone number to remove spaces, dashes, and other separators to produce a continuous string.

    Args:
    - phone_number (str): The phone number in a standard format (e.g., +1 518-272-1355).

    Returns:
    - str: The formatted phone number (e.g., +15182721355).
    """
    # Remove spaces, hyphens, and other non-digit characters except the plus sign
    formatted_number = ''.join(char for char in phone_number if char.isdigit() or char == '+')
    return formatted_number

def get_place_details(api_key, place_id):
    """
    Fetch detailed information for a specific place using Google Places API's "Place Details" feature.

    Args:
    - api_key (str): Your Google API key.
    - place_id (str): The unique Place ID of the location.

    Returns:
    - dict: The JSON response containing detailed information about the place.
    """
    url = "https://maps.googleapis.com/maps/api/place/details/json"
    params = {
        'key': api_key,
        'place_id': place_id,
        'fields': 'formatted_address,international_phone_number'  # Customize fields as needed
    }

    response = requests.get(url, params=params)
    formatted = response.json()["result"]
    return formatted

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
        "radius": int(radius_in_miles * 1609.34),  # Convert miles to meters
        "keyword": "CVS Pharmacy"
    }

    response = requests.get(url, params=params)
    response_list = response.json()["results"]
    
    filtered = [item for item in response_list if evaluate_pharmacy_name(item)]
    
    # extract useful info
    pharm = filtered[0]
    res = []
    for pharm in filtered:
        name = pharm["name"]
        place_id = pharm["place_id"]
        details = get_place_details(api_key, place_id)
        phone = format_phone_number(details["international_phone_number"])
        address = details["formatted_address"]
        res.append({
            "name": name,
            "phone": phone,
            "address": address
        })
    return res