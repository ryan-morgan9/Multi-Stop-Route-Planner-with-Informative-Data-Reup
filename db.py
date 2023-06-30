import sqlite3

from werkzeug.security import generate_password_hash


# Ryan Morgan


# Create a DB with tables
def create_database():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()

    # Create the user table.
    c.execute("""CREATE TABLE user(
      user_id INTEGER PRIMARY KEY,
      email TEXT UNIQUE,
      password TEXT,
      address TEXT);
    """)

    # Create the routes table.
    c.execute("""CREATE TABLE routes(
      route_id INTEGER PRIMARY KEY,
      route TEXT,
      transport_mode TEXT,
      distance REAL,
      user_id INTEGER,
      CONSTRAINT fk_user
        FOREIGN KEY(user_id) 
        REFERENCES user(user_id)
        ON DELETE CASCADE);
    """)

    conn.commit()
    conn.close()


# Register a user to DB
def add_user(email, password):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    
    # Attempt to retrieve user from DB using email
    c.execute("SELECT * FROM user WHERE email = (?)", [email])
    validation = c.fetchone()
    # Check and validate for whether the account already exists
    if validation:
        print("Account already exists...")
        # add flash for html page
        conn.commit()
        conn.close()
        return False

    # Generate hashed password and insert user into DB
    hashed_password = generate_password_hash(password, "sha256")
    c.execute("INSERT into USER(email, password) VALUES (?, ?)", (email, hashed_password,))

    conn.commit()
    conn.close()
    return True


# Save a route for the user
def add_route(user_id, route, trans_mode, distance):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()

    print(user_id, route)

    # Insert new route into DB (routes DB table)
    c.execute("INSERT into routes(user_id, route, transport_mode, distance) VALUES (?, ?, ?, ?)", 
              (user_id, route, trans_mode, distance,))

    conn.commit()
    conn.close()


# Get all saved routes for a user
def get_route(user_id):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()

    # Get all routes saved by a user
    c.execute("SELECT * FROM routes WHERE user_id = (?)", [user_id])

    # Fetch the record from the database (if it exists)
    routes = c.fetchall()

    conn.close()
    # If there are routes then return them
    if routes:
        return routes
    return None


# Delete a selected route
def delete_route(route_id, user_id):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()

    #Delete the route selected by the user
    c.execute("DELETE FROM routes WHERE route_id = (?) AND user_id = (?)", [route_id, user_id])

    conn.commit()
    conn.close()


# Get custom starting location if there is one
def get_address(user_id):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()

    c.execute("SELECT address FROM user WHERE user_id = (?)", [user_id])

    # Fetch the record from the database (if it exists)
    address = c.fetchone()

    conn.close()

    # If there is an address then return it
    if address:
        return address

    return None


# Update custom starting location
def add_address(address, user_id):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()

    # Update address of a user
    c.execute("UPDATE user SET address = ? WHERE user_id = ?", (address, user_id))

    conn.commit()
    conn.close()
