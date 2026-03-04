from flask import Flask, render_template, request, redirect, session
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "supersecretkey"

db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="ChandanHN@20",
    database="vehicle_rental"
)

cursor = db.cursor(dictionary=True, buffered=True)

# Home
@app.route('/')
def home():
    return redirect('/login')

# Register
@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = generate_password_hash(request.form['password'])

        cursor.execute(
            "INSERT INTO users (name,email,password) VALUES (%s,%s,%s)",
            (name,email,password)
        )
        db.commit()
        return redirect('/login')

    return render_template('register.html')

@app.route('/my_bookings')
def my_bookings():
    if 'user_id' not in session:
        return redirect('/login')

    cursor.execute("""
        SELECT bookings.*, vehicles.name 
        FROM bookings 
        JOIN vehicles ON bookings.vehicle_id = vehicles.id 
        WHERE bookings.user_id=%s
    """, (session['user_id'],))

    data = cursor.fetchall()
    return render_template("my_bookings.html", bookings=data)

@app.route('/cancel/<int:booking_id>')
def cancel(booking_id):
    if 'user_id' not in session:
        return redirect('/login')

    # Get vehicle id first
    cursor.execute("SELECT vehicle_id FROM bookings WHERE id=%s", (booking_id,))
    booking = cursor.fetchone()

    if booking:
        vehicle_id = booking['vehicle_id']

        # Delete booking
        cursor.execute("DELETE FROM bookings WHERE id=%s", (booking_id,))

        # Make vehicle available again
        cursor.execute("UPDATE vehicles SET available=TRUE WHERE id=%s", (vehicle_id,))

        db.commit()

    return redirect('/my_bookings')

# Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        cursor.execute("SELECT * FROM users WHERE email=%s", (email,))
        user = cursor.fetchone()

        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['role'] = user['role']
            return redirect('/dashboard')
        else:
            return "Invalid Credentials"

    return render_template("login.html")

# Dashboard
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect('/login')
    return render_template('dashboard.html')

# Vehicles
@app.route('/vehicles')
def vehicles():
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM vehicles")
    vehicles = cursor.fetchall()
    return render_template("vehicles.html", vehicles=vehicles)

# Book
@app.route('/book/<int:id>', methods=['GET','POST'])
def book(id):
    if 'user_id' not in session:
        return redirect('/login')

    cursor.execute("SELECT * FROM vehicles WHERE id=%s",(id,))
    vehicle = cursor.fetchone()

    if request.method == 'POST':
        days = int(request.form['days'])
        total = days * float(vehicle['price_per_day'])

        cursor.execute(
            "INSERT INTO bookings (user_id,vehicle_id,days,total_price) VALUES (%s,%s,%s,%s)",
            (session['user_id'], id, days, total)
        )

        cursor.execute("UPDATE vehicles SET available=FALSE WHERE id=%s",(id,))
        db.commit()

        return f"Booking Successful! Total: ₹{total}"

    return render_template('book.html', vehicle=vehicle)

# Logout
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

@app.route('/admin')
def admin():
    if 'user_id' not in session:
        return redirect('/login')

    if session.get('role') != 'admin':
        return "Access Denied"

    cursor.execute("SELECT * FROM vehicles")
    vehicles = cursor.fetchall()

    cursor.execute("""
        SELECT bookings.*, users.name AS user_name, vehicles.name AS vehicle_name
        FROM bookings
        JOIN users ON bookings.user_id = users.id
        JOIN vehicles ON bookings.vehicle_id = vehicles.id
    """)
    bookings = cursor.fetchall()

    return render_template("admin.html", vehicles=vehicles, bookings=bookings)

if __name__ == "__main__":
    app.run(debug=True)

