import sys
from datetime import datetime, time, timedelta
from app import app
from database import db
from models import User, Patient, Doctor, DoctorSchedule, Appointment
from auth import hash_password

def seed_database():
    print("Starting database seeding...")
    
    with app.app_context():
        # Clear existing data to avoid duplication if rerun
        print("Clearing existing database entries...")
        Appointment.query.delete()
        DoctorSchedule.query.delete()
        Patient.query.delete()
        Doctor.query.delete()
        User.query.delete()
        db.session.commit()

        # 1. Create Admin User
        admin_email = "admin@scheduler.com"
        print(f"Creating Admin User: {admin_email}...")
        admin_user = User(
            email=admin_email,
            password_hash=hash_password("admin123"),
            role="admin"
        )
        db.session.add(admin_user)

        # 2. Create Doctors
        doc1_email = "kowalski@scheduler.com"
        print(f"Creating Doctor User: {doc1_email}...")
        doc1_user = User(
            email=doc1_email,
            password_hash=hash_password("doctor123"),
            role="doctor"
        )
        db.session.add(doc1_user)
        db.session.flush()

        doc1_profile = Doctor(
            user_id=doc1_user.id,
            first_name="Jan",
            last_name="Kowalski",
            specialization="Kardiolog (Cardiologist)",
            room="101A"
        )
        db.session.add(doc1_profile)
        db.session.flush()

        doc2_email = "nowak@scheduler.com"
        print(f"Creating Doctor User: {doc2_email}...")
        doc2_user = User(
            email=doc2_email,
            password_hash=hash_password("doctor123"),
            role="doctor"
        )
        db.session.add(doc2_user)
        db.session.flush()

        doc2_profile = Doctor(
            user_id=doc2_user.id,
            first_name="Anna",
            last_name="Nowak",
            specialization="Pediatra (Pediatrician)",
            room="203B"
        )
        db.session.add(doc2_profile)
        db.session.flush()

        # 3. Create Doctor Schedules
        print("Creating doctor working schedules...")
        
        # Dr Kowalski: Mon (0), Wed (2), Fri (4) from 08:00 to 16:00
        schedules_kowalski = [
            DoctorSchedule(doctor_id=doc1_profile.id, day_of_week=0, start_time=time(8, 0), end_time=time(16, 0)),
            DoctorSchedule(doctor_id=doc1_profile.id, day_of_week=2, start_time=time(8, 0), end_time=time(16, 0)),
            DoctorSchedule(doctor_id=doc1_profile.id, day_of_week=4, start_time=time(8, 0), end_time=time(14, 0))
        ]
        
        # Dr Nowak: Tue (1), Thu (3) from 09:00 to 17:00
        schedules_nowak = [
            DoctorSchedule(doctor_id=doc2_profile.id, day_of_week=1, start_time=time(9, 0), end_time=time(17, 0)),
            DoctorSchedule(doctor_id=doc2_profile.id, day_of_week=3, start_time=time(9, 0), end_time=time(17, 0))
        ]

        for s in schedules_kowalski + schedules_nowak:
            db.session.add(s)

        # 4. Create Patients
        patient1_email = "pacjent@scheduler.com"
        print(f"Creating Patient User: {patient1_email}...")
        patient1_user = User(
            email=patient1_email,
            password_hash=hash_password("pacjent123"),
            role="patient"
        )
        db.session.add(patient1_user)
        db.session.flush()

        patient1_profile = Patient(
            user_id=patient1_user.id,
            first_name="Piotr",
            last_name="Zielinski",
            pesel="91081512345",
            phone="+48 600 700 800"
        )
        db.session.add(patient1_profile)
        db.session.flush()

        # 5. Create Appointments
        print("Creating sample appointments...")
        
        # Helper to find a future date on a specific day of week
        def get_future_date_for_weekday(weekday_num, hour, minute):
            today = datetime.utcnow()
            days_ahead = weekday_num - today.weekday()
            if days_ahead <= 0: # Target day already passed this week
                days_ahead += 7
            future_date = today + timedelta(days=days_ahead)
            return datetime(future_date.year, future_date.month, future_date.day, hour, minute)

        # Helper to find a past date on a specific day of week
        def get_past_date_for_weekday(weekday_num, hour, minute):
            today = datetime.utcnow()
            days_behind = today.weekday() - weekday_num
            if days_behind <= 0:
                days_behind += 7
            past_date = today - timedelta(days=days_behind)
            return datetime(past_date.year, past_date.month, past_date.day, hour, minute)

        # Sample Appointment 1: Past appointment, completed
        appt_completed = Appointment(
            patient_id=patient1_profile.id,
            doctor_id=doc1_profile.id,
            appointment_date=get_past_date_for_weekday(0, 10, 0),  # Last Monday
            status="completed",
            notes="Wizyta kontrolna zakończona. Przepisano witaminy."
        )
        
        # Sample Appointment 2: Future appointment, accepted
        appt_accepted = Appointment(
            patient_id=patient1_profile.id,
            doctor_id=doc1_profile.id,
            appointment_date=get_future_date_for_weekday(2, 9, 30),  # Next Wednesday
            status="accepted",
            notes="Konsultacja kardiologiczna. Proszę przynieść ostatnie EKG."
        )

        # Sample Appointment 3: Future appointment, pending
        appt_pending = Appointment(
            patient_id=patient1_profile.id,
            doctor_id=doc2_profile.id,
            appointment_date=get_future_date_for_weekday(3, 11, 0),  # Next Thursday
            status="pending",
            notes="Wizyta z dzieckiem (bilans)."
        )

        db.session.add(appt_completed)
        db.session.add(appt_accepted)
        db.session.add(appt_pending)
        
        db.session.commit()
        print("Database seeded successfully!")
        
        # Summary
        print(f"\nCreated accounts:")
        print(f"Admin:    {admin_email} / admin123")
        print(f"Doctor 1: {doc1_email} / doctor123")
        print(f"Doctor 2: {doc2_email} / doctor123")
        print(f"Patient:  {patient1_email} / pacjent123")

if __name__ == "__main__":
    seed_database()
