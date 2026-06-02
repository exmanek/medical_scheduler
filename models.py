from datetime import datetime
from database import db

class User(db.Model):
    """User accounts table."""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'patient', 'doctor', 'admin'
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # 1:1 relationship back-references
    patient = db.relationship('Patient', back_populates='user', uselist=False, cascade="all, delete-orphan")
    doctor = db.relationship('Doctor', back_populates='user', uselist=False, cascade="all, delete-orphan")

    def to_dict(self):
        """Serialize user object."""
        return {
            'id': self.id,
            'email': self.email,
            'role': self.role,
            'created_at': self.created_at.isoformat()
        }


class Patient(db.Model):
    """Patients details table."""
    __tablename__ = 'patients'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), unique=True, nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    pesel = db.Column(db.String(11), unique=True, nullable=False, index=True)
    phone = db.Column(db.String(20), nullable=False)

    # Relationships
    user = db.relationship('User', back_populates='patient')
    appointments = db.relationship('Appointment', back_populates='patient', cascade="all, delete-orphan")

    def to_dict(self):
        """Serialize patient object."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'email': self.user.email if self.user else None,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'pesel': self.pesel,
            'phone': self.phone
        }


class Doctor(db.Model):
    """Doctors details table."""
    __tablename__ = 'doctors'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), unique=True, nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    specialization = db.Column(db.String(100), nullable=False)
    room = db.Column(db.String(20), nullable=False)

    # Relationships
    user = db.relationship('User', back_populates='doctor')
    schedules = db.relationship('DoctorSchedule', back_populates='doctor', cascade="all, delete-orphan")
    appointments = db.relationship('Appointment', back_populates='doctor', cascade="all, delete-orphan")

    def to_dict(self):
        """Serialize doctor object."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'email': self.user.email if self.user else None,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'specialization': self.specialization,
            'room': self.room,
            'schedules': [s.to_dict() for s in self.schedules]
        }


class DoctorSchedule(db.Model):
    """Doctor working hours table."""
    __tablename__ = 'doctor_schedules'

    id = db.Column(db.Integer, primary_key=True)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.id', ondelete='CASCADE'), nullable=False)
    day_of_week = db.Column(db.Integer, nullable=False)  # 0 = Monday, ..., 6 = Sunday
    start_time = db.Column(db.Time, nullable=False)      # time object (HH:MM:SS)
    end_time = db.Column(db.Time, nullable=False)        # time object (HH:MM:SS)

    # Relationships
    doctor = db.relationship('Doctor', back_populates='schedules')

    def to_dict(self):
        """Serialize doctor schedule object."""
        return {
            'id': self.id,
            'doctor_id': self.doctor_id,
            'day_of_week': self.day_of_week,
            'start_time': self.start_time.strftime("%H:%M") if self.start_time else None,
            'end_time': self.end_time.strftime("%H:%M") if self.end_time else None
        }


class Appointment(db.Model):
    """Appointments scheduling table."""
    __tablename__ = 'appointments'

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id', ondelete='CASCADE'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.id', ondelete='CASCADE'), nullable=False)
    appointment_date = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(20), default='pending', nullable=False)  # 'pending', 'accepted', 'cancelled', 'completed'
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    patient = db.relationship('Patient', back_populates='appointments')
    doctor = db.relationship('Doctor', back_populates='appointments')

    def to_dict(self):
        """Serialize appointment object."""
        return {
            'id': self.id,
            'patient_id': self.patient_id,
            'patient_name': f"{self.patient.first_name} {self.patient.last_name}" if self.patient else "Unknown Patient",
            'patient_phone': self.patient.phone if self.patient else "",
            'doctor_id': self.doctor_id,
            'doctor_name': f"Dr {self.doctor.first_name} {self.doctor.last_name}" if self.doctor else "Unknown Doctor",
            'doctor_specialization': self.doctor.specialization if self.doctor else "",
            'appointment_date': self.appointment_date.isoformat(),
            'status': self.status,
            'notes': self.notes,
            'created_at': self.created_at.isoformat()
        }
