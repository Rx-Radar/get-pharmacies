import functions_framework
from firebase_admin import credentials, firestore, auth, initialize_app
from flask import jsonify, request
from packages import query_places
from packages import query_firestore
import json
import yaml
import os


def load_yaml_file(filepath):
    with open(filepath, 'r') as file:
        data = yaml.safe_load(file)
    return data

# Use the function to load the configuration
config = load_yaml_file('config.yaml')

env = os.getenv("deployment_env")

## ----- no current imports from env ------ ##

# Initialize Firebase Admin SDK with the service account key
cred = credentials.Certificate("firebase_creds.json")  # Update with your service account key file  
initialize_app(cred)
db = firestore.client() # set firestore client

@functions_framework.http
def main(request):

    """
    Example request body
    {
        "lat": 42.3397,
        "lon": -71.091720,
        "num_pharmacies": 2
    }

    or below for testing purposes returns owen and simon phone

    {
        "lat": 0.00,
        "lon": 0.00,
        "num_pharmacies": 2
    }
    """

    # Get the JSON data from the request
    request_data = request.get_json(silent=True)

    # validate request body
    success, out = validate_request(request_data=request_data)
    if not success:
        return out

    user_lat = request_data['lat']
    user_lon = request_data['lon']
    num_pharmacies = request_data['num_pharmacies']

    search_radius = 6 # NOT CURRENTLY IN USE

    # query firestore and return pharmacies to search
    pharmacies = query_firestore.find_nearby_pharmaices(db=db, lat=user_lat, lon=user_lon, radius=search_radius, num_pharmacies=num_pharmacies)
    if len(pharmacies) >= num_pharmacies:
        return pharmacies

    # query new ones from google places API if we have less than the target amount
    ggl_formated_location = f'{user_lat}, {user_lon}'
    new_pharmacies = query_places.find_new_nearby_pharmacies(db=db, location=ggl_formated_location)

    # if after places search, we found more pharmacies from db query
    if len(pharmacies) > len(new_pharmacies):
        return pharmacies

    return new_pharmacies[:num_pharmacies] # return the first num_pharmacies found from places
        

# validate request body data
def validate_request(request_data):
    # Check if request_data is None or empty
    if not request_data:
        return False, (jsonify({'error': 'Request body empty'}), 400)
    
    # Check if 'lat', 'lon', and 'num_pharmacies' keys exist
    if 'lat' not in request_data or 'lon' not in request_data or 'num_pharmacies' not in request_data:
        return False, (jsonify({'error': 'Request must include \'lat\' and \'lon\' and \'num_pharmacies\'fields'}), 400)
    
    # Check if 'lat' and 'lon' are non-empty numbers
    if not isinstance(request_data['lat'], (int, float)) or not isinstance(request_data['lon'], (int, float)):
        return False, (jsonify({'error': '\'lat\' and \'lon\' must be non empty numbers'}), 400)
    
    # Check if 'num_pharmacies' is a non-empty number
    if not isinstance(request_data['num_pharmacies'], (int, float)) or request_data['num_pharmacies'] <= 0:
        return False, (jsonify({'error': 'num_pharmacies must be a non empty number'}), 400)
    
    return True, None
