import sqlite3
import time

from flask import Flask, render_template, url_for, redirect, request, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user, UserMixin
from werkzeug.security import check_password_hash

# imports from the other project files
import db
import algorithm
import api

# Ryan Morgan

# Create instance of flask app and login manager
app = Flask(__name__)
app.secret_key = 'NewKey'
login_manager = LoginManager(app)
login_manager.login_view = 'login'


# User class for login
class User(UserMixin):
    def __init__(self, user_id, email, password):
        self.id = user_id
        self.email = email
        self.password = password


# Loads in the user from DB (for login)
@login_manager.user_loader
def load_user(user_id):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()

    # Get user from DB
    c.execute("SELECT * FROM user WHERE user_ID = (?)", [user_id])

    # Fetch the record from the database (if it exists)
    user = c.fetchone()

    conn.close()

    # Validate if user exists
    if user is None:
        return None
    else:
        # return user account
        return User(int(user[0]), user[1], user[2])


# Index view - No functionality
@app.route("/index", methods=["GET", "POST"])
def index():
    return render_template('base.html',
                           auth=current_user.is_authenticated)


# --- User authentication views ---
# Login user
@app.route("/login", methods=["GET", "POST"])
def login():
    # Redirect if already logged in
    if current_user.is_authenticated:
        return redirect(url_for('routeinput'))

    if request.method == 'POST':
        # Get form inputs
        email = request.form.get('email')
        password = request.form.get('password')

        # Remember me checkbox
        remember = False
        if request.form.get('remember'):
            remember = True

        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        # Get user from DB
        c.execute("SELECT * FROM user where email = (?)", [email])
        fetch_user = c.fetchone()
        # Validate non-existent users
        if fetch_user is None:
            flash('User cannot be found.', "error")
            print("User cannot be found")
            return redirect(url_for('login'))
        else:
            user = list(fetch_user)
            user_db = load_user(user[0])

        # If details are correct then login
        if email == user_db.email and check_password_hash(user_db.password, password):
            login_user(user_db, remember=remember)
            flash('Logged in Successfully with ' +
                  user_db.email + '.', "success")
            return redirect(url_for('routeinput'))
        else:
            # Login rejected for incorrect details
            flash('Login Unsuccessful.', "error")
            print("Login unsuccessful")
            return redirect(url_for('login'))

    # Render login form
    return render_template('login.html',
                           title='Login')


# Logout user
@app.route("/logout")
def logout():
    logout_user()
    flash('Logged Out Successfully.', "success")
    return redirect(url_for('routeinput'))


# Make a new user account
@app.route("/register", methods=["GET", "POST"])
def register():
    # Redirect if already logged in
    if current_user.is_authenticated:
        return redirect(url_for('routeinput'))

    if request.method == 'POST':
        # Get form inputs
        email = request.form.get('email')
        password = request.form.get('password')

        # Attempt to create account
        if db.add_user(email, password):
            print("Account Made.")
            flash("Account Made.", "success")
            return redirect(url_for('login'))
        else:
            print("Account Couldn't Be Made.")
            flash("Account Couldn't Be Made.", "error")
            return redirect(url_for('routeinput'))

    # Show register page
    return render_template('register.html',
                           auth=current_user.is_authenticated)


# --- Route planning views ---
# Route input view
@app.route("/", methods=["GET", "POST"])
@app.route("/routeinput", methods=["GET", "POST"])
def routeinput():
    # Loads the template for inputting route planning details
    return render_template('routeinput.html',
                           auth=current_user.is_authenticated)


# Route output view
@app.route("/routeoutput", methods=["GET", "POST"])
def routeoutput():
    if request.method == 'POST':
        # get starting point for route
        start = request.form.get('start')
        # get stops to find a route for
        stops = request.form.getlist('stop')
        # get mode of transport
        trans_mode = request.form.get('transtype')
        print(start, stops, trans_mode)

        # if the user selected their saved address as a starting point
        if request.form.get('useAddress'):
            # if they're logged in, then get their saved address
            if current_user.is_authenticated:
                start = db.get_address(current_user.id)[0]
                # if there's no address retrieved, then send them back to form
                if start is None:
                    return redirect(url_for('routeinput'))
            # if user isn't logged in then send them back to form
            else:
                return redirect(url_for('routeinput'))

        # get list of locations and a list of location coordinates
        locations = [start]
        coordinates = [api.get_coords(start)]
        # for each location, append it to a list and its geolocation to another
        for stop in stops:
            locations.append(stop)
            new_coord = api.get_coords(stop)
            if not new_coord:
                flash('Cannot retrieve geocoordinate from service.', "error")
                return redirect(url_for('routeinput'))
            coordinates.append(new_coord)
            # API is limited to 1 request per second
            time.sleep(1.2)

        print("Lists:", locations, coordinates)

        # Validation for duplicate input locations
        if len(locations) != len(set(locations)):
            flash("There are duplicate input locations.", "error")
            return redirect(url_for('routeinput'))

        # get informative information for each location for it to be displayed
        stop_data = {}
        # get data for each location and save to a dictionary
        for stop in range(len(coordinates)):
            weather_info = api.weather_api(coordinates[stop])
            pollution_info = api.pollution_api(coordinates[stop])
            # if data cannot be retrieved then go back to input form
            if not weather_info or not pollution_info:
                flash('Cannot retrieve pollution or weather data from API.', "error")
                return redirect(url_for('routeinput'))

            stop_data[locations[stop]] = [weather_info, pollution_info, stop]

        # get list of reversed geolocations (lat-long to long-lat) for matrix api
        coord_preprocess = []
        for coord in coordinates:
            coord_preprocess.append([coord[1], coord[0]])

        # Get distance matrix
        distances = api.distance_matrix(coord_preprocess)
        if not distances:
            flash('Cannot retrieve distance matrix from API.', "error")
            return redirect(url_for('routeinput'))

        # index of starting point for use in algorithm
        start_index = locations.index(start)
        try:
            # calculate the shortest route from the starting point using distances
            route, route_distance = algorithm.bruteforce_tsp(distances, start_index)
            print("Shortest route:", route)
        except:
            flash("Couldn't calculate shortest route.", "error")
            return redirect(url_for('routeinput'))

        # If travel mode is transit then get transit data
        if trans_mode == 'transit':
            # Starts on seconds location
            for route_index in range(1, len(route)):
                # Between two locations
                transit_info = api.transit_api(
                    coordinates[route[route_index - 1]], coordinates[route[route_index]])
                if not transit_info:
                    # If data cannot be retrieved
                    flash('Cannot retrieve transit data from API.', "error")
                    return redirect(url_for('routeinput'))
                # Save to dictionary
                stop_data[locations[route[route_index - 1]]].append(transit_info)

        # Get lists which are ordered for the shortest route
        # Location names
        loc_path = []
        # Coordinates
        coord_path = []
        for point in route:
            loc_path.append(locations[point])
            coord_path.append(coordinates[point])

        # render html page while passing in the data for display
        return render_template('routeoutput.html',
                               auth=current_user.is_authenticated,
                               route=loc_path,
                               trans_mode=trans_mode,
                               route_distance=route_distance,
                               coordinates=coord_path,
                               stop_data=stop_data)

    return redirect(url_for('routeinput'))


# --- Account/data management views ---
# Save a calculate route
@app.route("/saveroute", methods=["GET", "POST"])
@login_required
def saveroute():
    if request.method == 'POST':
        # Get route details from form
        route = request.form.get('wholeroute')
        trans_mode = request.form.get('trans_mode')
        route_distance = request.form.get('route_distance')

        print(route, trans_mode, route_distance)

        # Attempt to add route to DB
        try:
            db.add_route(current_user.id, route, trans_mode, route_distance)
        except:
            flash('Cannot save route.', "error")
            return redirect(url_for('routeinput'))

        return redirect(url_for('account'))

    return redirect(url_for('account'))


# Account page for managing user data
@app.route("/account", methods=["GET", "POST"])
@login_required
def account():
    # Retrieve all saved routes and custom starting address for the user
    routes, address = db.get_route(
        current_user.id), db.get_address(current_user.id)
    print("Routes:", routes)

    if request.method == 'POST':
        # Get new custom starting location
        new_address = request.form.get('new_address')

        # Update custom starting location
        db.add_address(new_address, current_user.id)

        return redirect(url_for('account'))

    # Show account page with routes and custom starting location
    return render_template('account.html',
                           routes=routes,
                           address=address,
                           auth=current_user.is_authenticated)


# Load a saved route
@app.route("/loadroute", methods=["GET", "POST"])
@login_required
def loadroute():
    if request.method == 'POST':
        # Get saved route
        loaded_route = request.form.get('load_route')
        print(loaded_route)

        # Convert route form string to python list
        loaded_route = eval(loaded_route)

        # Get travel mode and route distance
        trans_mode = request.form.get('transtype')
        route_distance = request.form.get('route_distance')

        # Get a list of location coordinates
        coordinates = []
        # Get informative information for each location for it to be displayed
        stop_data = {}
        # get data for each location and save to the dictionary/coords list
        for stop in range(len(loaded_route)):
            # Retrieval of coordinates    
            new_coord = api.get_coords(loaded_route[stop])
            # if coords cannot be retrieved then go back to input form
            if not new_coord:
                flash('Cannot retrieve geocoordinate from service.', "error")
                return redirect(url_for('routeinput'))
            coordinates.append(new_coord)

            # Retrieval of weather/pollution data
            weather_info = api.weather_api(new_coord)
            pollution_info = api.pollution_api(new_coord)
            # If data cannot be retrieved then go back to input form
            if not weather_info or not pollution_info:
                flash('Cannot retrieve data from API.', "error")
                return redirect(url_for('routeinput'))

            # Add data to dictionary
            stop_data[loaded_route[stop]] = [
                weather_info, pollution_info, stop]

            # API is limited to 1 request per second
            time.sleep(1.2)

        # If transit mode for save route is transit, get public transit data
        if trans_mode == 'transit':
            # Start on second location in route
            for route_index in range(1, len(loaded_route)):
                # Retrieve transit route between two locations
                transit_info = api.transit_api(
                    coordinates[route_index - 1], coordinates[route_index])
                # If data cannot be retrieved then go back to input form
                if not transit_info:
                    flash('Cannot retrieve transit data from API.', "error")
                    return redirect(url_for('routeinput'))
                # Save data to dictionary
                stop_data[loaded_route[route_index - 1]].append(transit_info)

        # render html page while passing in the data for display
        return render_template('routeoutput.html',
                               auth=current_user.is_authenticated,
                               route=loaded_route,
                               route_distance=route_distance,
                               coordinates=coordinates,
                               stop_data=stop_data)

    return redirect(url_for('account'))


# Delete a saved route
@app.route("/deleteroute", methods=["GET", "POST"])
@login_required
def deleteroute():
    if request.method == 'POST':
        # Get selected route to delete
        route_id = request.form.get('delete_route')

        # Attempt to delete the saved route
        try:
            db.delete_route(route_id, current_user.id)
        except:
            flash('Cannot delete saved route.', "error")
            return redirect(url_for('account'))

        return redirect(url_for('account'))
    return redirect(url_for('account'))


# RUNS SERVER
if __name__ == '__main__':
    app.run(debug=True)
