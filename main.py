import functions_framework
from firebase_admin import credentials, firestore, auth, initialize_app
from packages import query_places
from packages import query_firestore
import json

GGL_PLACES_API_KEY = "AIzaSyAkezSitJD1m7Y1ZLz_5yhllL-K5aux1us"


# Initialize Firebase Admin SDK with the service account key
cred = credentials.Certificate("firebase_creds.json")  # Update with your service account key file 
initialize_app(cred)
db = firestore.client() # set firestore client

@functions_framework.http
def main(request):
    LOCATION = "42.72889973797719, -73.67718872162821"  # Example location (Los Angeles, CA)

    NUM_PHARMS_TO_RETURN = 3


    # Get the JSON data from the request
    request_data = request.get_json(silent=True)

    user_lat = request_data['lat']
    user_lon = request_data['lon']
    search_radius = request_data['search_radius']

    search_radius = 6

    #1. query firestore and return pharmacies to search
    pharmacies = query_firestore.find_nearby_pharmaices(db=db, lat=user_lat, lot=user_lon, radius=search_radius, num_pharmacies=NUM_PHARMS_TO_RETURN)
    shortened_pharmacies = pharmacies[:NUM_PHARMS_TO_RETURN] # limit number of pharmacies to return

    return shortened_pharmacies


    #2. if we dont, then query places for a certain radius, add this data to the database return this data 
    # pharmacies = query_places.find_new_nearby_pharmacies(GGL_PLACES_API_KEY, LOCATION, RADIUS_IN_MILES)
    
    # NOTE WE DONT UPLOAD NEW PLACES YET
    # upload_pharmacy_data(pharmacies)


