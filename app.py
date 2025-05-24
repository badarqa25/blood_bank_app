from flask import Flask, render_template, request, redirect, url_for, jsonify
import mysql.connector
from mysql.connector import Error
import boto3
from datetime import datetime, timedelta
import os

app = Flask(__name__)

# Database configuration
db_config = {
    'host': os.getenv('DB_HOST', 'databasebloodbank.cszgm2s0y0br.us-east-1.rds.amazonaws.com'),
    'database': os.getenv('DB_NAME', 'bloodbank'),
    'user': os.getenv('DB_USER', 'admin'),
    'password': os.getenv('DB_PASSWORD', 'badarqa2500'),
    'ssl_disabled': True,
    'use_pure': True
}

def create_db_connection():
    try:
        connection = mysql.connector.connect(**db_config)
        print("Successfully connected to the database")
        return connection
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
        return None

def close_db_connection(connection, cursor=None):
    try:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()
    except Error as e:
        print(f"Error closing connection: {e}")

@app.route('/')
def home():
    try:
        return render_template('index.html')
    except Exception as e:
        print(f"Error rendering template: {e}")
        return "Error loading page", 500

# Donor Management
@app.route('/donors', methods=['GET'])
def list_donors():
    connection = create_db_connection()
    if not connection:
        return "Database connection error", 500
        
    cursor = None
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM Donors")
        donors = cursor.fetchall()
        return render_template('donors.html', donors=donors)
    except Error as e:
        print(f"Database query error: {e}")
        return "Database error", 500
    finally:
        close_db_connection(connection, cursor)

@app.route('/donor/add', methods=['GET', 'POST'])
def add_donor():
    if request.method == 'POST':
        data = request.form
        connection = create_db_connection()
        if not connection:
            return "Database connection error", 500
            
        cursor = None
        try:
            cursor = connection.cursor()
            query = """
            INSERT INTO Donors 
            (first_name, last_name, blood_type, date_of_birth, contact_number, email, address, health_info)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(query, (
                data['first_name'], data['last_name'], data['blood_type'], 
                data['date_of_birth'], data['contact_number'], data['email'], 
                data['address'], data['health_info']
            ))
            connection.commit()
            return redirect(url_for('list_donors'))
        except Error as e:
            print(f"Database error: {e}")
            return "Error saving donor", 500
        finally:
            close_db_connection(connection, cursor)
    
    return render_template('add_donor.html')

# Blood Inventory Management
@app.route('/inventory', methods=['GET'])
def list_inventory():
    connection = create_db_connection()
    if not connection:
        return "Database connection error", 500
        
    cursor = None
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("""
            SELECT b.*, d.first_name, d.last_name 
            FROM Blood_Inventory b
            LEFT JOIN Donors d ON b.donor_id = d.donor_id
            ORDER BY b.expiry_date
        """)
        inventory = cursor.fetchall()
        
        for item in inventory:
            if item['expiry_date']:
                days_left = (item['expiry_date'] - datetime.now().date()).days
                item['days_until_expiry'] = days_left if days_left > 0 else 0
        
        return render_template('inventory.html', inventory=inventory)
    except Error as e:
        print(f"Database error: {e}")
        return "Database error", 500
    finally:
        close_db_connection(connection, cursor)

@app.route('/inventory/add', methods=['GET', 'POST'])
def add_blood():
    if request.method == 'POST':
        data = request.form
        collection_date = datetime.strptime(data['collection_date'], '%Y-%m-%d').date()
        expiry_date = collection_date + timedelta(days=42)
        
        connection = create_db_connection()
        if not connection:
            return "Database connection error", 500
            
        cursor = None
        try:
            cursor = connection.cursor()
            query = """
            INSERT INTO Blood_Inventory 
            (donor_id, blood_type, collection_date, expiry_date, storage_location, status, test_results)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(query, (
                data['donor_id'], data['blood_type'], collection_date, 
                expiry_date, data['storage_location'], 'available', data['test_results']
            ))
            connection.commit()
            return redirect(url_for('list_inventory'))
        except Error as e:
            print(f"Database error: {e}")
            return "Error saving blood unit", 500
        finally:
            close_db_connection(connection, cursor)
    
    connection = create_db_connection()
    if not connection:
        return "Database connection error", 500
        
    cursor = None
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT donor_id, first_name, last_name FROM Donors")
        donors = cursor.fetchall()
        return render_template('add_blood.html', donors=donors)
    except Error as e:
        print(f"Database error: {e}")
        return "Database error", 500
    finally:
        close_db_connection(connection, cursor)

# Patient Management
@app.route('/patients', methods=['GET'])
def list_patients():
    connection = create_db_connection()
    if not connection:
        return "Database connection error", 500
        
    cursor = None
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM Patients")
        patients = cursor.fetchall()
        return render_template('patients.html', patients=patients)
    except Error as e:
        print(f"Database error: {e}")
        return "Database error", 500
    finally:
        close_db_connection(connection, cursor)

@app.route('/patient/add', methods=['GET', 'POST'])
def add_patient():
    if request.method == 'POST':
        data = request.form
        connection = create_db_connection()
        if not connection:
            return "Database connection error", 500
            
        cursor = None
        try:
            cursor = connection.cursor()
            query = """
            INSERT INTO Patients 
            (first_name, last_name, contact_number, email, hospital_details)
            VALUES (%s, %s, %s, %s, %s)
            """
            cursor.execute(query, (
                data['first_name'], data['last_name'], data['contact_number'],
                data.get('email'), data.get('hospital_details')
            ))
            connection.commit()
            return redirect(url_for('list_patients'))
        except Error as e:
            print(f"Database error: {e}")
            return "Error saving patient", 500
        finally:
            close_db_connection(connection, cursor)
    
    return render_template('add_patient.html')

# Request Management
@app.route('/requests', methods=['GET'])
def list_requests():
    connection = create_db_connection()
    if not connection:
        return "Database connection error", 500
        
    cursor = None
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("""
            SELECT r.*, p.first_name as patient_first_name, p.last_name as patient_last_name
            FROM Requests r
            JOIN Patients p ON r.patient_id = p.patient_id
            ORDER BY r.request_date DESC
        """)
        requests = cursor.fetchall()
        return render_template('requests.html', requests=requests)
    except Error as e:
        print(f"Database error: {e}")
        return "Database error", 500
    finally:
        close_db_connection(connection, cursor)

@app.route('/request/create', methods=['GET', 'POST'])
def create_request():
    if request.method == 'POST':
        data = request.form
        connection = create_db_connection()
        if not connection:
            return "Database connection error", 500
            
        cursor = None
        try:
            cursor = connection.cursor()
            query = """
            INSERT INTO Requests 
            (patient_id, blood_type_needed, quantity, hospital_details)
            VALUES (%s, %s, %s, %s)
            """
            cursor.execute(query, (
                data['patient_id'], data['blood_type_needed'], 
                data['quantity'], data.get('hospital_details')
            ))
            connection.commit()
            return redirect(url_for('list_requests'))
        except Error as e:
            print(f"Database error: {e}")
            return "Error creating request", 500
        finally:
            close_db_connection(connection, cursor)
    
    connection = create_db_connection()
    if not connection:
        return "Database connection error", 500
        
    cursor = None
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT patient_id, first_name, last_name FROM Patients")
        patients = cursor.fetchall()
        return render_template('create_request.html', patients=patients)
    except Error as e:
        print(f"Database error: {e}")
        return "Database error", 500
    finally:
        close_db_connection(connection, cursor)

@app.route('/request/fulfill/<int:request_id>', methods=['POST'])
def fulfill_request(request_id):
    blood_type = request.form.get('blood_type')
    quantity = int(request.form.get('quantity', 1))
    
    connection = create_db_connection()
    if not connection:
        return "Database connection error", 500
        
    cursor = None
    try:
        cursor = connection.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT blood_id FROM Blood_Inventory 
            WHERE blood_type = %s AND status = 'available' AND expiry_date > CURDATE()
            ORDER BY expiry_date
            LIMIT %s
        """, (blood_type, quantity))
        
        available_units = cursor.fetchall()
        
        if len(available_units) < quantity:
            return "Not enough blood units available", 400
        
        for unit in available_units:
            cursor.execute("""
                UPDATE Blood_Inventory 
                SET status = 'used' 
                WHERE blood_id = %s
            """, (unit['blood_id'],))
            
            cursor.execute("""
                INSERT INTO Transfusions 
                (request_id, blood_id, medical_personnel, notes)
                VALUES (%s, %s, %s, %s)
            """, (request_id, unit['blood_id'], 'System', 'Automated fulfillment'))
        
        cursor.execute("""
            UPDATE Requests 
            SET status = 'fulfilled' 
            WHERE request_id = %s
        """, (request_id,))
        
        connection.commit()
        return redirect(url_for('list_requests'))
    except Error as e:
        connection.rollback()
        print(f"Database error: {e}")
        return f"Error fulfilling request: {e}", 500
    finally:
        close_db_connection(connection, cursor)

# API Endpoints
@app.route('/api/blood-availability', methods=['GET'])
def blood_availability():
    blood_type = request.args.get('type')
    
    connection = create_db_connection()
    if not connection:
        return jsonify({"error": "Database connection failed"}), 500
        
    cursor = None
    try:
        cursor = connection.cursor(dictionary=True)
        
        if blood_type:
            query = """
                SELECT COUNT(*) as count 
                FROM Blood_Inventory 
                WHERE blood_type = %s AND status = 'available' AND expiry_date > CURDATE()
            """
            cursor.execute(query, (blood_type,))
        else:
            query = """
                SELECT blood_type, COUNT(*) as count 
                FROM Blood_Inventory 
                WHERE status = 'available' AND expiry_date > CURDATE()
                GROUP BY blood_type
            """
            cursor.execute(query)
        
        result = cursor.fetchall()
        return jsonify(result)
    except Error as e:
        print(f"Database error: {e}")
        return jsonify({"error": "Database query failed"}), 500
    finally:
        close_db_connection(connection, cursor)

@app.route('/api/recent-activity')
def recent_activity():
    connection = create_db_connection()
    if not connection:
        return jsonify({"error": "Database connection failed"}), 500
        
    cursor = None
    try:
        cursor = connection.cursor(dictionary=True)
        
        cursor.execute("SELECT COUNT(*) as total_patients FROM Patients")
        total_patients = cursor.fetchone()['total_patients']
        
        cursor.execute("SELECT COUNT(*) as pending_requests FROM Requests WHERE status = 'pending'")
        pending_requests = cursor.fetchone()['pending_requests']
        
        cursor.execute("""
            SELECT COUNT(*) as expiring_soon 
            FROM Blood_Inventory 
            WHERE expiry_date BETWEEN CURDATE() AND DATE_ADD(CURDATE(), INTERVAL 7 DAY)
            AND status = 'available'
        """)
        expiring_soon = cursor.fetchone()['expiring_soon']
        
        cursor.execute("""
            SELECT first_name, last_name, contact_number, created_at 
            FROM Patients 
            ORDER BY created_at DESC 
            LIMIT 5
        """)
        recent_patients = cursor.fetchall()
        
        cursor.execute("""
            SELECT r.blood_type_needed, r.status, p.first_name as patient_first_name, 
                   p.last_name as patient_last_name
            FROM Requests r
            JOIN Patients p ON r.patient_id = p.patient_id
            ORDER BY r.request_date DESC 
            LIMIT 5
        """)
        recent_requests = cursor.fetchall()
        
        return jsonify({
            "total_patients": total_patients,
            "pending_requests": pending_requests,
            "expiring_soon": expiring_soon,
            "recent_patients": recent_patients,
            "recent_requests": recent_requests
        })
    except Error as e:
        print(f"Database error: {e}")
        return jsonify({"error": "Database query failed"}), 500
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
