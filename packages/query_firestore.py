# query pharmacies from firestore db
from geolib import geohash
from geopy.distance import geodesic
import yaml
import os


def load_yaml_file(filepath):
    with open(filepath, 'r') as file:
        data = yaml.safe_load(file)
    return data

# Use the function to load the configuration
config = load_yaml_file('config.yaml')

env = os.getenv("deployment_env")

FIREBASE_PHARMACIES_DB = config[env]["firebase"]["pharmacy_db"] 

# return pharmacies from db based on location
def find_nearby_pharmaices(db, lat, lon, radius, num_pharmacies):
  found_pharmacies = []

  search_size = [2, 4, 8, 16] # radius search progression in miles, note after 16 miles the places api is called

  # grow search until we find enough pharmacies to call
  for radius in search_size:

    # get geohashes to search
    geohash_precision, search_geohashes = get_min_search_buckets(lat=lat, lon=lon, miles_precision=radius)

    # get all pharmacies within geohash search
    unfiltered_pharmacies = db_geo_query(db=db, search_geohashes=search_geohashes, precision=geohash_precision)

    # filter geohash pharmacies by radius
    found_pharmacies = filter_pharms_by_radius(user_lat=lat, user_lon=lon, pharmacies=unfiltered_pharmacies, radius=radius)

    # check to see if we have found enough pharmacies 
    if len(found_pharmacies) >= num_pharmacies:
      return found_pharmacies[:num_pharmacies]

  # if not found MIN_RESULT_PHARMS pharmacies, return what we did find
  return found_pharmacies


# filters search bucket to be within
def filter_pharms_by_radius(user_lat, user_lon, pharmacies, radius):
  filtered_pharmacies = []

  # filter pharmacies by distance in miles from user
  for pharmacy in pharmacies:
    # append pharmacies within desired radius
    if geodesic((user_lat, user_lon), (pharmacy['location']['lat'], pharmacy['location']['lon'])).miles <= radius:
      filtered_pharmacies.append(pharmacy)

  return filtered_pharmacies

  
# returns pharmacies from db within specified search buckets
def db_geo_query(db, search_geohashes, precision):
    pharmacies = []
    for geohash in search_geohashes:
        try:
            # Make query to 'users' collection where 'geohash' field is equal to the specified value
            query_ref = db.collection(FIREBASE_PHARMACIES_DB).where(f'location.geohash_{str(precision)}', '==', geohash).where('pharm_code', '==', 'CVS')

            # Execute the query and get the resulting documents
            query_results = query_ref.get()

            # Extract data from documents
            results_list = [doc.to_dict() for doc in query_results]

            pharmacies.extend(results_list)

        except Exception as e:
            print(f"An error occurred: {e}")
            return None
        
    return pharmacies


# returns a list of geohashes to query given a location and precision in miles
def get_min_search_buckets(lat, lon, miles_precision):
    geohash_precision = 5 # default to smallest range

    # mapping between miles precision and geohash { miles, geohash_prcecision }
    miles_to_geohash_precision = [{3: 5}, {25: 4}, {100: 3}]
    for item in miles_to_geohash_precision:
            for key, value in item.items():
                if key >= miles_precision:
                    geohash_precision = value

    # geohash user location
    # user_location_geohash = geohash.encode(lat, lon, geohash_precision)

    # increase precision to find minimum geohash buckets needed to search area
    zoomed_geohash = geohash.encode(lat, lon, geohash_precision + 1)
    zoomed_neighbors = list(geohash.neighbours(zoomed_geohash))
    zoomed_neighbors.append(zoomed_geohash)

    # create list of unique search buckets 
    search_buckets = set()
    for string in zoomed_neighbors:
        bucket = string[:-1]
        if bucket: # check if bucket in list already
            search_buckets.add(bucket)

    return geohash_precision, list(search_buckets)