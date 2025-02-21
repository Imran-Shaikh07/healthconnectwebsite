from flask import Flask, render_template, request, redirect, url_for, jsonify, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os
from werkzeug.utils import secure_filename

# Allowed file extensions
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
# Set default SQLite database for development
database_url = os.getenv('DATABASE_URL', 'sqlite:///healthcare.db')
if database_url.startswith('postgres://'):
    database_url = database_url.replace('postgres://', 'postgresql://')
app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'

db = SQLAlchemy(app)

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Models
class Customer(db.Model):
    __tablename__ = 'customer'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    phone = db.Column(db.String(15))
    address = db.Column(db.Text)
    gender = db.Column(db.String(10))
    dob = db.Column(db.Date)
    blood_group = db.Column(db.String(5))
    photo_url = db.Column(db.String(200))
    emergency_contact = db.Column(db.String(15))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    bookings = db.relationship('Booking', backref='customer', lazy=True)
    notifications = db.relationship('Notification', backref='customer', lazy=True)

class Technician(db.Model):
    __tablename__ = 'technician'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    phone = db.Column(db.String(15))
    address = db.Column(db.Text)
    department = db.Column(db.String(50))
    specialist = db.Column(db.String(50))
    workplace = db.Column(db.String(100))
    locations = db.Column(db.Text)  # Comma-separated list of locations
    blood_group = db.Column(db.String(5))
    gender = db.Column(db.String(10))
    dob = db.Column(db.Date)
    biography = db.Column(db.Text)
    photo_url = db.Column(db.String(200))
    status = db.Column(db.String(20), default='available')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    assignments = db.relationship('Booking', backref='technician', lazy=True)
    notifications = db.relationship('Notification', backref='technician', lazy=True)

class Booking(db.Model):
    __tablename__ = 'booking'
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    technician_id = db.Column(db.Integer, db.ForeignKey('technician.id'))
    test_type = db.Column(db.String(50), nullable=False)
    date_time = db.Column(db.DateTime, nullable=False)
    location = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(20), default='pending')
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)

class Notification(db.Model):
    __tablename__ = 'notification'
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'))
    technician_id = db.Column(db.Integer, db.ForeignKey('technician.id'))
    message = db.Column(db.Text, nullable=False)
    type = db.Column(db.String(20), nullable=False)  # 'booking', 'status', 'profile'
    read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# Helper function for file uploads
def save_file(file):
    if file:
        try:
            # For local development
            if os.getenv('ENVIRONMENT') == 'development':
                filename = secure_filename(file.filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                return f'/static/uploads/{filename}'
            # For production with Cloudinary
            else:
                import cloudinary
                import cloudinary.uploader
                cloudinary.config(
                    cloud_name = os.getenv('CLOUDINARY_CLOUD_NAME'),
                    api_key = os.getenv('CLOUDINARY_API_KEY'),
                    api_secret = os.getenv('CLOUDINARY_API_SECRET')
                )
                result = cloudinary.uploader.upload(file)
                return result['secure_url']
        except Exception as e:
            print(f"Upload error: {e}")
    return None

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/customer-register', methods=['GET', 'POST'])
def customer_register():
    if request.method == 'POST':
        try:
            # Get form data with default values for optional fields
            name = request.form.get('name')
            email = request.form.get('email')
            password = request.form.get('password')
            phone = request.form.get('phone', '')
            gender = request.form.get('gender', '')
            dob_str = request.form.get('dob')
            blood_group = request.form.get('blood_group', '')
            address = request.form.get('address', '')
            emergency_contact = request.form.get('emergency_contact', '')
            photo = request.files.get('photo')

            # Validate required fields
            if not all([name, email, password]):
                return render_template('customer-register.html', 
                                    error='Name, email, and password are required')

            # Check if email already exists
            if Customer.query.filter_by(email=email).first():
                return render_template('customer-register.html', 
                                    error='Email already registered')

            # Convert date string to date object if provided
            dob = None
            if dob_str:
                try:
                    dob = datetime.strptime(dob_str, '%Y-%m-%d').date()
                except ValueError:
                    return render_template('customer-register.html', 
                                        error='Invalid date format')

            # Handle photo upload
            photo_url = None
            if photo:
                photo_url = save_file(photo)

            # Create new customer
            customer = Customer(
                name=name,
                email=email,
                password=generate_password_hash(password),
                phone=phone,
                gender=gender,
                dob=dob,
                blood_group=blood_group,
                address=address,
                emergency_contact=emergency_contact,
                photo_url=photo_url
            )

            db.session.add(customer)
            db.session.commit()

            # Redirect to login page
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('customer_login'))

        except Exception as e:
            db.session.rollback()
            return render_template('customer-register.html', 
                                error=f'Registration failed: {str(e)}')

    # GET request - show registration form
    return render_template('customer-register.html')

@app.route('/customer-login', methods=['GET', 'POST'])
def customer_login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        customer = Customer.query.filter_by(email=email).first()
        
        if customer and check_password_hash(customer.password, password):
            session['user_id'] = customer.id
            session['user_type'] = 'customer'
            return redirect(url_for('customer_dashboard'))
        
        return render_template('customer-login.html', error='Invalid email or password')
    
    return render_template('customer-login.html')

@app.route('/customer-dashboard')
def customer_dashboard():
    if 'user_id' not in session or session['user_type'] != 'customer':
        return redirect(url_for('customer_login'))
    
    customer = Customer.query.get_or_404(session['user_id'])
    
    # Sample data for testing (remove in production)
    if not Booking.query.filter_by(customer_id=customer.id).first():
        sample_bookings = [
            Booking(
                customer_id=customer.id,
                test_type='Blood Test',
                date_time=datetime.now().replace(day=datetime.now().day + 2),
                location='Mumbai',
                status='pending'
            ),
            Booking(
                customer_id=customer.id,
                test_type='X-Ray',
                date_time=datetime.now().replace(day=datetime.now().day + 3),
                location='Delhi',
                status='accepted',
                technician_id=1  # Assuming technician with ID 1 exists
            ),
            Booking(
                customer_id=customer.id,
                test_type='MRI Scan',
                date_time=datetime.now().replace(day=datetime.now().day - 5),
                location='Bangalore',
                status='completed',
                technician_id=2  # Assuming technician with ID 2 exists
            ),
            Booking(
                customer_id=customer.id,
                test_type='ECG',
                date_time=datetime.now().replace(day=datetime.now().day - 2),
                location='Chennai',
                status='completed',
                technician_id=1
            ),
            Booking(
                customer_id=customer.id,
                test_type='CT Scan',
                date_time=datetime.now().replace(day=datetime.now().day - 1),
                location='Hyderabad',
                status='cancelled'
            ),
            Booking(
                customer_id=customer.id,
                test_type='Ultrasound',
                date_time=datetime.now().replace(day=datetime.now().day - 3),
                location='Pune',
                status='cancelled'
            )
        ]
        db.session.bulk_save_objects(sample_bookings)
        db.session.commit()
    
    # Get bookings by status
    upcoming_bookings = Booking.query.filter_by(
        customer_id=customer.id
    ).filter(
        Booking.status.in_(['pending', 'accepted'])
    ).order_by(Booking.date_time.desc()).all()
    
    completed_bookings = Booking.query.filter_by(
        customer_id=customer.id,
        status='completed'
    ).order_by(Booking.date_time.desc()).all()
    
    cancelled_bookings = Booking.query.filter_by(
        customer_id=customer.id,
        status='cancelled'
    ).order_by(Booking.date_time.desc()).all()
    
    return render_template('customer-dashboard.html',
                         customer=customer,
                         upcoming_bookings=upcoming_bookings,
                         completed_bookings=completed_bookings,
                         cancelled_bookings=cancelled_bookings)

@app.route('/update-customer-profile', methods=['POST'])
def update_customer_profile():
    if 'user_id' not in session or session['user_type'] != 'customer':
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        data = request.json
        customer = Customer.query.get_or_404(session['user_id'])
        
        customer.phone = data.get('mobile', customer.phone)
        customer.blood_group = data.get('blood_group', customer.blood_group)
        customer.address = data.get('address', customer.address)
        customer.dob = datetime.strptime(data.get('dob'), '%Y-%m-%d').date() if data.get('dob') else customer.dob
        customer.gender = data.get('gender', customer.gender)
        customer.emergency_contact = data.get('emergency_contact', customer.emergency_contact)
        
        db.session.commit()
        return jsonify({'message': 'Profile updated successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/technician-login', methods=['GET', 'POST'])
def technician_login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        technician = Technician.query.filter_by(email=email).first()
        
        if technician and check_password_hash(technician.password, password):
            session['user_id'] = technician.id
            session['user_type'] = 'technician'
            return redirect(url_for('technician_dashboard'))
        
        return render_template('technician-login.html', error='Invalid email or password')
    
    return render_template('technician-login.html')

@app.route('/technician-dashboard')
def technician_dashboard():
    if 'user_id' not in session or session['user_type'] != 'technician':
        flash('Please login first', 'error')
        return redirect(url_for('technician_login'))
    
    technician = Technician.query.get_or_404(session['user_id'])
    
    # Create sample bookings for testing if none exist
    if not Booking.query.filter_by(technician_id=technician.id).first():
        sample_bookings = [
            Booking(
                customer_id=1,  # Assuming customer with ID 1 exists
                technician_id=technician.id,
                test_type='Blood Test',
                date_time=datetime.now().replace(day=datetime.now().day + 1),
                location='Mumbai',
                status='pending'
            ),
            Booking(
                customer_id=1,
                technician_id=technician.id,
                test_type='X-Ray',
                date_time=datetime.now().replace(day=datetime.now().day + 2),
                location='Delhi',
                status='accepted'
            )
        ]
        db.session.bulk_save_objects(sample_bookings)
        db.session.commit()
    
    # Get bookings by status
    pending_bookings = Booking.query.filter_by(
        technician_id=technician.id,
        status='pending'
    ).order_by(Booking.created_at.desc()).all()
    
    accepted_bookings = Booking.query.filter_by(
        technician_id=technician.id,
        status='accepted'
    ).order_by(Booking.created_at.desc()).all()
    
    rejected_bookings = Booking.query.filter_by(
        technician_id=technician.id,
        status='rejected'
    ).order_by(Booking.created_at.desc()).all()
    
    # Add flash messages for debugging
    if not any([pending_bookings, accepted_bookings, rejected_bookings]):
        flash('No bookings found', 'info')
    
    return render_template('technician-dashboard.html',
                         technician=technician,
                         pending_bookings=pending_bookings,
                         accepted_bookings=accepted_bookings,
                         rejected_bookings=rejected_bookings)

@app.route('/book-test', methods=['POST'])
def book_test():
    if 'user_id' not in session or session['user_type'] != 'customer':
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        data = request.json
        booking = Booking(
            customer_id=session['user_id'],
            test_type=data['test_type'],
            date_time=datetime.strptime(data['date_time'], '%Y-%m-%dT%H:%M'),
            location=data['location']
        )
        
        db.session.add(booking)
        db.session.commit()
        
        return jsonify({'message': 'Booking successful'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/cancel-booking/<int:booking_id>', methods=['POST'])
def cancel_booking(booking_id):
    if 'user_id' not in session or session['user_type'] != 'customer':
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        booking = Booking.query.get_or_404(booking_id)
        if booking.customer_id != session['user_id']:
            return jsonify({'error': 'Unauthorized'}), 401
        
        booking.status = 'cancelled'
        db.session.commit()
        
        return jsonify({'message': 'Booking cancelled successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/technician-register', methods=['GET', 'POST'])
def technician_register():
    if request.method == 'POST':
        try:
            # Check if email already exists
            if Technician.query.filter_by(email=request.form['email']).first():
                return render_template('technician-register.html', 
                    error='Email already registered')

            # Get form data
            name = request.form['name']
            email = request.form['email']
            password = request.form['password']
            phone = request.form['phone']
            address = request.form['address']
            department = request.form['department']
            specialist = request.form['specialist']
            workplace = request.form['workplace']
            blood_group = request.form['blood_group']
            gender = request.form['gender']
            
            # Handle date conversion
            try:
                dob = datetime.strptime(request.form['dob'], '%Y-%m-%d').date()
            except ValueError:
                return render_template('technician-register.html', 
                    error='Invalid date format')

            locations = request.form['locations']
            biography = request.form.get('biography', '')
            
            # Handle photo upload
            photo = request.files.get('photo')
            photo_url = None
            if photo:
                if photo.filename == '':
                    photo_url = None
                elif not allowed_file(photo.filename):
                    return render_template('technician-register.html', 
                        error='Invalid file type. Please upload an image file (png, jpg, jpeg, gif)')
                else:
                    photo_url = save_file(photo)
            
            # Create new technician
            technician = Technician(
                name=name,
                email=email,
                password=generate_password_hash(password),
                phone=phone,
                address=address,
                department=department,
                specialist=specialist,
                workplace=workplace,
                blood_group=blood_group,
                gender=gender,
                dob=dob,
                locations=locations,
                biography=biography,
                photo_url=photo_url
            )
            
            db.session.add(technician)
            db.session.commit()
            
            # Log in the technician after successful registration
            session['user_id'] = technician.id
            session['user_type'] = 'technician'
            
            flash('Registration successful!', 'success')
            return redirect(url_for('technician_dashboard'))
            
        except Exception as e:
            db.session.rollback()
            # Log the error for debugging
            print(f"Error during registration: {str(e)}")
            # Return more specific error message
            error_msg = str(e)
            if 'unique constraint' in error_msg.lower():
                error_msg = 'Email already registered'
            elif 'not null constraint' in error_msg.lower():
                error_msg = 'Please fill in all required fields'
            else:
                error_msg = 'Registration failed. Please check all fields and try again.'
            
            return render_template('technician-register.html', 
                error=error_msg)
      
    return render_template('technician-register.html')

@app.route('/handle-booking/<action>/<int:booking_id>', methods=['POST'])
def handle_booking(action, booking_id):
    if 'user_id' not in session or session['user_type'] != 'technician':
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        booking = Booking.query.get_or_404(booking_id)
        
        if action == 'accept':
            booking.status = 'accepted'
            message = 'Booking accepted successfully'
        elif action == 'reject':
            booking.status = 'rejected'
            message = 'Booking rejected successfully'
        elif action == 'complete':
            booking.status = 'completed'
            message = 'Booking marked as completed'
        else:
            return jsonify({'error': 'Invalid action'}), 400
        
        db.session.commit()
        return jsonify({'message': message})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/get-customer-details/<int:customer_id>')
def get_customer_details(customer_id):
    if 'user_id' not in session or session['user_type'] != 'technician':
        return jsonify({'error': 'Unauthorized'}), 401
    
    customer = Customer.query.get_or_404(customer_id)
    return jsonify({
        'name': customer.name,
        'email': customer.email,
        'phone': customer.phone,
        'gender': customer.gender,
        'blood_group': customer.blood_group,
        'address': customer.address
    })

@app.route('/services')
def services():
    return render_template('services.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        # Handle contact form submission
        name = request.form.get('name')
        email = request.form.get('email')
        subject = request.form.get('subject')
        message = request.form.get('message')
        
        # Here you would typically send an email or save to database
        flash('Thank you for your message. We will get back to you soon!', 'success')
        return redirect(url_for('contact'))
        
    return render_template('contact.html')

def init_db():
    with app.app_context():
        # Drop all tables
        db.drop_all()
        # Create all tables
        db.create_all()
        print("Database initialized successfully!")

if __name__ == '__main__':
    app.run() 