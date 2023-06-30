from geopy.geocoders import Nominatim
import requests

# Ryan Morgan

# Retrieval of geocoordinates
def get_coords(place):
    # make Nominatim instance (geocoding service)
    getcoords = Nominatim(user_agent="routeplan")

    try:
        # Geocode the location
        location_info = getcoords.geocode(place)

        print(location_info.address, (location_info.latitude, location_info.longitude))
        
        # Extract the coordinates from the response
        coords = [location_info.latitude, location_info.longitude]
    except:
        # For when geocoordinates cannot be retrieved
        print("Geolocation cannot be retrieved.")
        coords = None

    return coords


# Get distances between locations in the form of a matrix
def distance_matrix(locations):
    # Define body of URL and add locations
    body = {"locations": locations,
            "metrics": ["distance"],
            "units": "mi"}

    # Define header - authorization heading contains API key for Openrouteservice
    headers = {
        'Accept': 'application/json, application/geo+json, application/gpx+xml, img/png; charset=utf-8',
        #API Key
        'Authorization': '',
        'Content-Type': 'application/json; charset=utf-8'
    }
    
    # Make post request
    call = requests.post(
        'https://api.openrouteservice.org/v2/matrix/driving-car', json=body, headers=headers)

    # If request is unsuccessful
    if call.status_code != 200:
        print("Cannot retrieve distance matrix from API.")
        return None

    # Convert to python dictionary and extract necessary data
    return call.json()['distances']


# Retrieval of weather data
def weather_api(coords):
    # API key needed to access Openweather service
    apikey = ""

    # Format URL for API request
    url = "https://api.openweathermap.org/data/2.5/weather?lat={}&lon={}&appid={}&units=metric".format(coords[0],
                                                                                                       coords[1],
                                                                                                       apikey)

    # Make request
    response = requests.request("GET", url)

    # If request unsuccessful
    if response.status_code != 200:
        print("Cannot get weather from API.")
        return None
    
    # Convert to python dictionary and extract necessary data
    response = response.json()
    print(response)
    return [response["weather"][0], response["main"]["temp"]]

        
# Retrieval of weather data
def pollution_api(coords):
    # API key needed to access Openweather service
    apikey = ""

    # Format URL for API request
    url = "http://api.openweathermap.org/data/2.5/air_pollution?lat={}&lon={}&appid={}".format(coords[0],
                                                                                               coords[1],
                                                                                               apikey)

    # Make request
    response = requests.request("GET", url)

    # If request unsuccessful
    if response.status_code != 200:
        print("Cannot get pollution from API.")
        return None
    
    # Convert to python dictionary and extract necessary data
    response = response.json()
    print(response)
    return response["list"]


# Retrieval of public transit route data
def transit_api(location_start, location_end):
    # API key needed to access HERE service
    apikey = ""

    # Format URL for API request
    url = "https://transit.router.hereapi.com/v8/routes?origin={},{}&destination={},{}&apiKey={}".format(
        location_start[0], location_start[1], location_end[0], location_end[1], apikey
    )

    # Make request
    response = requests.request("GET", url)

    # If request unsuccessful
    if response.status_code != 200:
        print("Cannot get transit data:", response.status_code, response.text)
        return None
    
    # Convert to python dictionary
    response = response.json()
    print(response)
    return response
