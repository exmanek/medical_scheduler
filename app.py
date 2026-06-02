import os
from datetime import datetime, timedelta, time
from flask import Flask, request, jsonify, render_template, session
from config import Config
from database import db, migrate
from models import User, Patient, Doctor, DoctorSchedule, Appointment
from auth import (
    hash_password, verify_password, login_user, logout_user, 
    get_current_user, login_required, role_required
)

app = Flask(__name__)
app.config.from_object(Config)

# Initialize database and migrations
db.init_app(app)
migrate.init_app(app, db)


# Helper function to parse datetime strings
def parse_datetime(dt_str):
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
        try:
            return datetime.strptime(dt_str, fmt)
        except ValueError:
            pass
    raise ValueError("Invalid datetime format. Please use YYYY-MM-DD HH:MM.")


# Error handler for 400 Bad Request (returns JSON instead of HTML)
@app.errorhandler(400)
def bad_request_error(e):
    return jsonify({"error": "Bad request", "message": str(e.description)}), 400


# Error handler for 404 Not Found
@app.errorhandler(404)
def not_found_error(e):
    return jsonify({"error": "Not found", "message": "The requested resource could not be found."}), 404


# Error handler for 500 Internal Server Error
@app.errorhandler(500)
def internal_server_error(e):
    db.session.rollback()
    return jsonify({"error": "Internal server error", "message": "An unexpected error occurred."}), 500


# --- Views ---

@app.route('/')
def index():
    """Serve the single-page application dashboard."""
    return render_template('index.html')


# --- REST API Endpoints ---

# 1. Auth Endpoints

@app.route('/register', methods=['POST'])
def register():
    """Register a new patient account."""
    if 'user_id' in session:
        return jsonify({"error": "Already logged in"}), 400

    data = request.get_json() or {}
    required_fields = ['email', 'password', 'first_name', 'last_name', 'pesel', 'phone']
    
    # Validation
    for field in required_fields:
        if not data.get(field):
            return jsonify({"error": f"Field '{field}' is required and cannot be empty"}), 400

    email = data['email'].strip().lower()
    password = data['password']
    first_name = data['first_name'].strip()
    last_name = data['last_name'].strip()
    pesel = data['pesel'].strip()
    phone = data['phone'].strip()

    if '@' not in email:
        return jsonify({"error": "Invalid email address"}), 400

    if len(pesel) != 11 or not pesel.isdigit():
        return jsonify({"error": "PESEL must be exactly 11 digits"}), 400

    # Check uniqueness
    if User.query.filter_by(email=email).first():
        return jsonify({"error": "Email is already registered"}), 400

    if Patient.query.filter_by(pesel=pesel).first():
        return jsonify({"error": "PESEL is already registered"}), 400

    try:
        # Create User with 'patient' role
        pw_hash = hash_password(password)
        new_user = User(email=email, password_hash=pw_hash, role='patient')
        db.session.add(new_user)
        db.session.flush()  # get user.id

        # Create Patient profile
        new_patient = Patient(
            user_id=new_user.id,
            first_name=first_name,
            last_name=last_name,
            pesel=pesel,
            phone=phone
        )
        db.session.add(new_patient)
        db.session.commit()

        # Automatically log in the user after registration
        login_user(new_user)
        
        return jsonify({
            "message": "Patient registered successfully",
            "user": new_user.to_dict(),
            "patient": new_patient.to_dict()
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Registration failed", "details": str(e)}), 500


@app.route('/login', methods=['POST'])
def login():
    """Authenticate and log in a user."""
    if 'user_id' in session:
        return jsonify({"message": "Already logged in", "user": get_current_user().to_dict()}), 200

    data = request.get_json() or {}
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    user = User.query.filter_by(email=email).first()
    if not user or not verify_password(user.password_hash, password):
        return jsonify({"error": "Invalid email or password"}), 401

    login_user(user)
    
    response_data = {
        "message": "Logged in successfully",
        "user": user.to_dict()
    }
    
    # Include profile details based on role
    if user.role == 'patient' and user.patient:
        response_data['profile'] = user.patient.to_dict()
    elif user.role == 'doctor' and user.doctor:
        response_data['profile'] = user.doctor.to_dict()
        
    return jsonify(response_data), 200


@app.route('/logout', methods=['POST'])
@login_required
def logout():
    """Log out the current user."""
    logout_user()
    return jsonify({"message": "Logged out successfully"}), 200


@app.route('/me', methods=['GET'])
def get_me():
    """Retrieve details of the current logged-in user session."""
    user = get_current_user()
    if not user:
        return jsonify({"logged_in": False}), 200
    
    response_data = {
        "logged_in": True,
        "user": user.to_dict()
    }
    
    if user.role == 'patient' and user.patient:
        response_data['profile'] = user.patient.to_dict()
    elif user.role == 'doctor' and user.doctor:
        response_data['profile'] = user.doctor.to_dict()
        
    return jsonify(response_data), 200


# 2. Doctors Endpoints

@app.route('/doctors', methods=['GET'])
@login_required
def get_doctors():
    """Get a list of all doctors along with their schedules."""
    doctors = Doctor.query.all()
    return jsonify([doc.to_dict() for doc in doctors]), 200


@app.route('/doctors/<int:doctor_id>', methods=['GET'])
@login_required
def get_doctor(doctor_id):
    """Get detailed information about a single doctor."""
    doctor = Doctor.query.get_or_404(doctor_id)
    return jsonify(doctor.to_dict()), 200


# Admin/Doctor: Manage Doctor Schedules
@app.route('/doctors/<int:doctor_id>/schedule', methods=['POST'])
@login_required
def set_doctor_schedule(doctor_id):
    """
    Overwrites the doctor's weekly work schedule.
    Access: Admin, or the Doctor themselves.
    Payload: A list of schedule entries, e.g.
    [
        {"day_of_week": 0, "start_time": "08:00", "end_time": "16:00"},
        {"day_of_week": 2, "start_time": "09:00", "end_time": "17:00"}
    ]
    """
    current_user = get_current_user()
    doctor = Doctor.query.get_or_404(doctor_id)
    
    # Authorization check: only admin or the specific doctor can edit schedules
    if current_user.role != 'admin' and (current_user.role != 'doctor' or current_user.doctor.id != doctor.id):
        return jsonify({"error": "Unauthorized to edit this doctor's schedule"}), 403

    data = request.get_json()
    if not isinstance(data, list):
        return jsonify({"error": "Payload must be a list of schedule objects"}), 400

    try:
        # Delete existing schedule entries
        DoctorSchedule.query.filter_by(doctor_id=doctor.id).delete()

        # Add new schedules
        for entry in data:
            day_of_week = entry.get('day_of_week')
            start_str = entry.get('start_time')
            end_str = entry.get('end_time')

            if day_of_week is None or not start_str or not end_str:
                db.session.rollback()
                return jsonify({"error": "Schedule entries must contain 'day_of_week', 'start_time' and 'end_time'"}), 400

            if not (0 <= int(day_of_week) <= 6):
                db.session.rollback()
                return jsonify({"error": "day_of_week must be between 0 (Monday) and 6 (Sunday)"}), 400

            # Parse times
            sh, sm = map(int, start_str.split(':'))
            eh, em = map(int, end_str.split(':'))
            start_t = time(sh, sm)
            end_t = time(eh, em)

            if start_t >= end_t:
                db.session.rollback()
                return jsonify({"error": "start_time must be earlier than end_time"}), 400

            schedule_item = DoctorSchedule(
                doctor_id=doctor.id,
                day_of_week=day_of_week,
                start_time=start_t,
                end_time=end_t
            )
            db.session.add(schedule_item)

        db.session.commit()
        return jsonify({"message": "Doctor schedule updated successfully", "schedule": [s.to_dict() for s in doctor.schedules]}), 200

    except ValueError:
        db.session.rollback()
        return jsonify({"error": "Invalid time format. Use HH:MM"}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Failed to save schedule", "details": str(e)}), 500


# Admin-Only: Add new Doctor
@app.route('/doctors', methods=['POST'])
@role_required('admin')
def create_doctor():
    """Create a new Doctor and their corresponding User account."""
    data = request.get_json() or {}
    required_fields = ['email', 'password', 'first_name', 'last_name', 'specialization', 'room']
    
    for field in required_fields:
        if not data.get(field):
            return jsonify({"error": f"Field '{field}' is required"}), 400

    email = data['email'].strip().lower()
    password = data['password']
    first_name = data['first_name'].strip()
    last_name = data['last_name'].strip()
    specialization = data['specialization'].strip()
    room = data['room'].strip()

    if User.query.filter_by(email=email).first():
        return jsonify({"error": "Email is already registered"}), 400

    try:
        # Create User with 'doctor' role
        pw_hash = hash_password(password)
        new_user = User(email=email, password_hash=pw_hash, role='doctor')
        db.session.add(new_user)
        db.session.flush()

        # Create Doctor profile
        new_doctor = Doctor(
            user_id=new_user.id,
            first_name=first_name,
            last_name=last_name,
            specialization=specialization,
            room=room
        )
        db.session.add(new_doctor)
        db.session.commit()

        return jsonify({
            "message": "Doctor created successfully",
            "doctor": new_doctor.to_dict()
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Failed to create doctor", "details": str(e)}), 500


# Admin-Only: Update Doctor details
@app.route('/doctors/<int:doctor_id>', methods=['PUT'])
@role_required('admin')
def update_doctor(doctor_id):
    """Update details of a Doctor and their User email if updated."""
    doctor = Doctor.query.get_or_404(doctor_id)
    data = request.get_json() or {}

    try:
        if 'email' in data:
            new_email = data['email'].strip().lower()
            if new_email != doctor.user.email:
                if User.query.filter_by(email=new_email).first():
                    return jsonify({"error": "Email is already in use by another user"}), 400
                doctor.user.email = new_email

        if 'password' in data and data['password']:
            doctor.user.password_hash = hash_password(data['password'])

        if 'first_name' in data:
            doctor.first_name = data['first_name'].strip()
        if 'last_name' in data:
            doctor.last_name = data['last_name'].strip()
        if 'specialization' in data:
            doctor.specialization = data['specialization'].strip()
        if 'room' in data:
            doctor.room = data['room'].strip()

        db.session.commit()
        return jsonify({
            "message": "Doctor updated successfully",
            "doctor": doctor.to_dict()
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Failed to update doctor", "details": str(e)}), 500


# Admin-Only: Delete Doctor
@app.route('/doctors/<int:doctor_id>', methods=['DELETE'])
@role_required('admin')
def delete_doctor(doctor_id):
    """Delete a Doctor profile and their corresponding User account."""
    doctor = Doctor.query.get_or_404(doctor_id)
    try:
        user = doctor.user
        db.session.delete(user)  # Cascades deletion to the doctor record
        db.session.commit()
        return jsonify({"message": "Doctor and associated user deleted successfully"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Failed to delete doctor", "details": str(e)}), 500


# 3. Appointments Endpoints

@app.route('/appointments', methods=['GET'])
@login_required
def get_appointments():
    """
    Get appointments relevant to the currently logged-in user.
    - Patients see only their own appointments.
    - Doctors see only their own appointments.
    - Admins see all appointments.
    """
    current_user = get_current_user()
    
    if current_user.role == 'admin':
        appointments = Appointment.query.order_by(Appointment.appointment_date.asc()).all()
    elif current_user.role == 'doctor':
        if not current_user.doctor:
            return jsonify([]), 200
        appointments = Appointment.query.filter_by(doctor_id=current_user.doctor.id)\
            .order_by(Appointment.appointment_date.asc()).all()
    elif current_user.role == 'patient':
        if not current_user.patient:
            return jsonify([]), 200
        appointments = Appointment.query.filter_by(patient_id=current_user.patient.id)\
            .order_by(Appointment.appointment_date.asc()).all()
    else:
        appointments = []
        
    return jsonify([appt.to_dict() for appt in appointments]), 200


@app.route('/appointments', methods=['POST'])
@role_required('patient')
def create_appointment():
    """
    Book a new appointment.
    Access: Patients only.
    Validation Rules:
    - Date cannot be in the past.
    - Doctor must work on the selected day of the week.
    - The appointment time must fall within the doctor's schedule start and end time.
    - The 30-minute slot must not be double booked (clash with existing non-cancelled appts).
    """
    patient = get_current_user().patient
    if not patient:
        return jsonify({"error": "Patient profile not found"}), 400

    data = request.get_json() or {}
    doctor_id = data.get('doctor_id')
    date_str = data.get('appointment_date')
    notes = data.get('notes', '').strip()

    if not doctor_id or not date_str:
        return jsonify({"error": "doctor_id and appointment_date are required"}), 400

    try:
        proposed_dt = parse_datetime(date_str)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    # Rule 1: Check if date is in the past
    now = datetime.utcnow()
    # Adding a tiny 1-minute buffer to avoid clock sync issues in API calls
    if proposed_dt <= now + timedelta(minutes=1):
        return jsonify({"error": "Cannot book appointments in the past"}), 400

    # Get Doctor details
    doctor = Doctor.query.get(doctor_id)
    if not doctor:
        return jsonify({"error": "Doctor not found"}), 404

    # Rule 2: Check if doctor works on that day
    day_of_week = proposed_dt.weekday()  # 0 = Monday, 6 = Sunday
    schedules = DoctorSchedule.query.filter_by(doctor_id=doctor_id, day_of_week=day_of_week).all()
    if not schedules:
        return jsonify({"error": "Doctor does not work on this day of the week"}), 400

    # Rule 3: Check if within schedule working hours
    proposed_time = proposed_dt.time()
    in_hours = False
    for sched in schedules:
        if sched.start_time <= proposed_time <= sched.end_time:
            in_hours = True
            break

    if not in_hours:
        sched_list = [f"{s.start_time.strftime('%H:%M')}-{s.end_time.strftime('%H:%M')}" for s in schedules]
        return jsonify({"error": f"Doctor is not available at the requested time. Working schedules: {', '.join(sched_list)}"}), 400

    # Rule 4: Check if term is already booked (30 minutes slot collision)
    # Check if there is an active appointment (status != 'cancelled') in the range [proposed_dt - 29m 59s, proposed_dt + 29m 59s]
    start_window = proposed_dt - timedelta(minutes=29, seconds=59)
    end_window = proposed_dt + timedelta(minutes=29, seconds=59)

    collision = Appointment.query.filter(
        Appointment.doctor_id == doctor_id,
        Appointment.status != 'cancelled',
        Appointment.appointment_date.between(start_window, end_window)
    ).first()

    if collision:
        return jsonify({"error": "The selected time slot is already booked. Please choose another time."}), 400

    try:
        new_appointment = Appointment(
            patient_id=patient.id,
            doctor_id=doctor_id,
            appointment_date=proposed_dt,
            status='pending',
            notes=notes
        )
        db.session.add(new_appointment)
        db.session.commit()

        return jsonify({
            "message": "Appointment created successfully",
            "appointment": new_appointment.to_dict()
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Failed to create appointment", "details": str(e)}), 500


@app.route('/appointments/<int:appt_id>', methods=['PUT'])
@login_required
def update_appointment(appt_id):
    """
    Update appointment details.
    - Patients: Can only set status to 'cancelled' (anulowanie wizyty) on their own appointments.
    - Doctors: Can accept ('accepted'), reject/cancel ('cancelled'), or complete ('completed') their own appointments, and update notes.
    - Admins: Can change any field (status, notes, date, etc.).
    """
    appt = Appointment.query.get_or_404(appt_id)
    current_user = get_current_user()
    data = request.get_json() or {}

    try:
        if current_user.role == 'patient':
            # Verify ownership
            if not current_user.patient or appt.patient_id != current_user.patient.id:
                return jsonify({"error": "Unauthorized to update this appointment"}), 403
            
            # Patients can only cancel
            new_status = data.get('status')
            if new_status and new_status != 'cancelled':
                return jsonify({"error": "Patients can only update appointment status to 'cancelled'"}), 400
            
            if new_status:
                appt.status = 'cancelled'
            if 'notes' in data:
                # Patients can append notes, but let's restrict or merge
                appt.notes = f"{appt.notes or ''}\n[Patient Update]: {data['notes']}".strip()

        elif current_user.role == 'doctor':
            # Verify ownership
            if not current_user.doctor or appt.doctor_id != current_user.doctor.id:
                return jsonify({"error": "Unauthorized to update this appointment"}), 403
            
            new_status = data.get('status')
            if new_status:
                if new_status not in ['accepted', 'cancelled', 'completed']:
                    return jsonify({"error": "Invalid status code for doctors"}), 400
                appt.status = new_status
            
            if 'notes' in data:
                appt.notes = data['notes']

        elif current_user.role == 'admin':
            # Admins have full access
            if 'status' in data:
                if data['status'] not in ['pending', 'accepted', 'cancelled', 'completed']:
                    return jsonify({"error": "Invalid status"}), 400
                appt.status = data['status']
            if 'notes' in data:
                appt.notes = data['notes']
            if 'appointment_date' in data:
                try:
                    proposed_dt = parse_datetime(data['appointment_date'])
                    appt.appointment_date = proposed_dt
                except ValueError as e:
                    return jsonify({"error": str(e)}), 400

        db.session.commit()
        return jsonify({
            "message": "Appointment updated successfully",
            "appointment": appt.to_dict()
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Failed to update appointment", "details": str(e)}), 500


@app.route('/appointments/<int:appt_id>', methods=['DELETE'])
@login_required
def delete_appointment(appt_id):
    """
    Cancel or physically delete an appointment.
    - Patients: Can delete (cancel) their own if status is pending.
    - Admins: Can delete any appointment.
    """
    appt = Appointment.query.get_or_404(appt_id)
    current_user = get_current_user()

    # Authorization
    if current_user.role == 'patient':
        if not current_user.patient or appt.patient_id != current_user.patient.id:
            return jsonify({"error": "Unauthorized to delete this appointment"}), 403
        
        # Patient deletes usually mean cancellation or only deletion of pending
        try:
            db.session.delete(appt)
            db.session.commit()
            return jsonify({"message": "Appointment deleted successfully"}), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": "Failed to delete appointment", "details": str(e)}), 500

    elif current_user.role == 'admin':
        try:
            db.session.delete(appt)
            db.session.commit()
            return jsonify({"message": "Appointment deleted successfully by administrator"}), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": "Failed to delete appointment", "details": str(e)}), 500

    else:
        return jsonify({"error": "Unauthorized. Only patient owners or administrators can delete records."}), 403


# 4. Admin Reports

@app.route('/users', methods=['GET'])
@role_required('admin')
def get_users():
    """
    Get a list of all users.
    Access: Admin only.
    """
    users = User.query.all()
    result = []
    for u in users:
        u_dict = u.to_dict()
        if u.role == 'patient' and u.patient:
            u_dict['profile'] = u.patient.to_dict()
        elif u.role == 'doctor' and u.doctor:
            u_dict['profile'] = u.doctor.to_dict()
        result.append(u_dict)
    return jsonify(result), 200


@app.route('/all-appointments', methods=['GET'])
@role_required('admin')
def get_all_appointments():
    """
    Get a list of all appointments.
    Access: Admin only.
    """
    appointments = Appointment.query.order_by(Appointment.appointment_date.asc()).all()
    return jsonify([appt.to_dict() for appt in appointments]), 200


if __name__ == '__main__':
    # Ensure templates and static folders exist
    os.makedirs(os.path.join(app.root_path, 'templates'), exist_ok=True)
    os.makedirs(os.path.join(app.root_path, 'static'), exist_ok=True)
    
    # Run the server
    # Set host to 0.0.0.0 for easier access in browser testing
    app.run(host='0.0.0.0', port=5001, debug=True)
