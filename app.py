from geopy.distance import geodesic
from datetime import datetime
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import requests

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'

# Database connection function with row_factory for dictionary-like access
def get_db_connection():
    conn = sqlite3.connect('attendance.db')
    conn.row_factory = sqlite3.Row  # Enable row access by column name
    return conn

# Initialize the database with onsite and offsite attendance tables
def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS User (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            firstname TEXT NOT NULL,
            lastname TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            employee_id TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            employee_type TEXT NOT NULL  -- onsite or offsite
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            employee_id TEXT NOT NULL,
            checkin_time TEXT NOT NULL,
            checkout_time TEXT,
            latitude REAL,
            longitude REAL,
            FOREIGN KEY(user_id) REFERENCES User(id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS OffsiteAttendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            employee_id TEXT NOT NULL,
            checkin_time TEXT NOT NULL,
            checkout_time TEXT,
            location_name TEXT NOT NULL,
            latitude REAL,
            longitude REAL,
            FOREIGN KEY(user_id) REFERENCES User(id)
        )
    ''')

    conn.commit()
    conn.close()

# Initialize the database
init_db()

# Define the office location (onsite location)
OFFICE_LOCATION = (12.9580466, 80.2040221)  # Example Office location

# Reverse geocoding to get location from coordinates (OpenCage API)
@app.route('/reverse_geocode', methods=['POST'])
def reverse_geocode():
    latitude = request.json.get('latitude')
    longitude = request.json.get('longitude')

    if not latitude or not longitude:
        return jsonify({"status": "Error: Latitude and Longitude not provided."}), 400

    # OpenCage API key
    api_key = '6cb90a211140451c961cec7bfcdabd21'
    url = f'https://api.opencagedata.com/geocode/v1/json?q={latitude}+{longitude}&key={api_key}'

    response = requests.get(url)
    data = response.json()

    if response.status_code == 200 and data['results']:
        # Get the first suggestion from OpenCage
        location_name = data['results'][0]['formatted']
        return jsonify({"status": "success", "location_name": location_name}), 200
    else:
        return jsonify({"status": "Error: Could not retrieve location."}), 500

# Home route
@app.route('/')
def home():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM User WHERE email = ?', (email,))
        user = cursor.fetchone()
        conn.close()

        if user and user['password'] == password:
            session['user_id'] = user['id']
            # Redirect based on employee type
            if user['employee_type'] == 'onsite':
                return redirect(url_for('dashboard'))
            elif user['employee_type'] == 'offsite':
                return redirect(url_for('offsite_dashboard'))
        else:
            return "Invalid credentials"
    return render_template('login.html')

# Onsite dashboard route
@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM User WHERE id = ?', (user_id,))
    user = cursor.fetchone()
    conn.close()

    if request.method == 'POST':
        latitude = request.json.get('latitude')
        longitude = request.json.get('longitude')

        if not latitude or not longitude:
            return jsonify({"status": "Error: Latitude and Longitude not provided."}), 400

        latitude = float(latitude)
        longitude = float(longitude)

        user_location = (latitude, longitude)
        distance = geodesic(user_location, OFFICE_LOCATION).meters

        conn = get_db_connection()
        cursor = conn.cursor()

        if distance <= 200:
            # User is within 200 meters of the office, check-in logic
            cursor.execute('SELECT * FROM Attendance WHERE user_id = ? ORDER BY id DESC LIMIT 1', (user_id,))
            last_attendance = cursor.fetchone()

            if not last_attendance or last_attendance['checkout_time']:
                # New check-in
                cursor.execute('''
                    INSERT INTO Attendance (user_id, name, employee_id, checkin_time, latitude, longitude)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (user_id, f"{user['firstname']} {user['lastname']}", user['employee_id'], datetime.now(), latitude, longitude))
                conn.commit()
                conn.close()
                return jsonify({"status": "Checked in successfully!"}), 200
            else:
                conn.close()
                return jsonify({"status": "You are already checked in!"}), 200
        else:
            # User is outside office radius, check-out logic
            cursor.execute('SELECT * FROM Attendance WHERE user_id = ? ORDER BY id DESC LIMIT 1', (user_id,))
            last_attendance = cursor.fetchone()

            if last_attendance and not last_attendance['checkout_time']:
                # Update checkout time
                cursor.execute('''
                    UPDATE Attendance SET checkout_time = ? WHERE id = ?
                ''', (datetime.now(), last_attendance['id']))
                conn.commit()
                conn.close()
                return jsonify({"status": "Checked out successfully!"}), 200
            else:
                conn.close()
                return jsonify({"status": "You are not checked in!"}), 200

    return render_template('dashboard.html', user=user)

# Offsite dashboard route
@app.route('/offsite_dashboard', methods=['GET', 'POST'])
def offsite_dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM User WHERE id = ?', (user_id,))
    user = cursor.fetchone()
    conn.close()

    if request.method == 'POST':
        latitude = request.json.get('latitude')
        longitude = request.json.get('longitude')
        location_name = request.json.get('location_name', None)

        if not latitude or not longitude or not location_name:
            return jsonify({"status": "Error: Missing location data."}), 400

        latitude = float(latitude)
        longitude = float(longitude)

        conn = get_db_connection()
        cursor = conn.cursor()

        # Check if the user has already checked in and not checked out
        cursor.execute('SELECT * FROM OffsiteAttendance WHERE user_id = ? ORDER BY id DESC LIMIT 1', (user_id,))
        last_attendance = cursor.fetchone()

        if not last_attendance or last_attendance['checkout_time']:
            # New check-in for offsite worker
            cursor.execute('''
                INSERT INTO OffsiteAttendance (user_id, name, employee_id, checkin_time, location_name, latitude, longitude)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (user_id, f"{user['firstname']} {user['lastname']}", user['employee_id'], datetime.now(), location_name, latitude, longitude))
            conn.commit()
            conn.close()
            return jsonify({"status": "Checked in successfully for offsite work!"}), 200
        else:
            # If already checked in, we handle the check-out
            cursor.execute('''
                UPDATE OffsiteAttendance SET checkout_time = ? WHERE id = ?
            ''', (datetime.now(), last_attendance['id']))
            conn.commit()
            conn.close()
            return jsonify({"status": "Checked out successfully!"}), 200

    return render_template('offsite_dashboard.html', user=user)


# Calculate working hours
@app.route('/calculate_hours', methods=['GET'])
def calculate_hours():
    if 'user_id' not in session:
        return jsonify({"status": "Unauthorized"}), 401

    user_id = session['user_id']
    conn = get_db_connection()
    cursor = conn.cursor()

    # Fetch check-in and check-out times
    cursor.execute('''
        SELECT checkin_time, checkout_time FROM Attendance WHERE user_id = ? AND checkout_time IS NOT NULL
        UNION
        SELECT checkin_time, checkout_time FROM OffsiteAttendance WHERE user_id = ? AND checkout_time IS NOT NULL
    ''', (user_id, user_id))
    attendances = cursor.fetchall()
    conn.close()

    total_hours = 0
    for attendance in attendances:
        checkin_time_str = attendance['checkin_time']
        checkout_time_str = attendance['checkout_time']

        # Adjust to parse time with microseconds if present
        checkin_time = datetime.strptime(checkin_time_str, "%Y-%m-%d %H:%M:%S.%f")
        checkout_time = datetime.strptime(checkout_time_str, "%Y-%m-%d %H:%M:%S.%f")

        # Calculate total hours worked
        total_hours += (checkout_time - checkin_time).total_seconds() / 3600

    return jsonify({"total_hours": round(total_hours, 2)})


# Logout route
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)
