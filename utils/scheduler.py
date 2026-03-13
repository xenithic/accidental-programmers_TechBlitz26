from datetime import datetime, timedelta
from database import db
from models.doctor import Doctor

def generate_slots(working_hours_start, working_hours_end, slot_duration):
    """
    Generates available time slots between working hours given a slot duration.
    """
    slots = []
    try:
        start_dt = datetime.strptime(working_hours_start, '%H:%M')
        end_dt = datetime.strptime(working_hours_end, '%H:%M')
    except (ValueError, TypeError):
        return slots

    current_dt = start_dt
    while current_dt + timedelta(minutes=int(slot_duration)) <= end_dt:
        slots.append(current_dt.strftime('%H:%M'))
        current_dt += timedelta(minutes=int(slot_duration))
        
    return slots

def get_available_slots(doctor_id, date):
    """
    Retrieves available slots for a specific doctor on a specific date.
    """
    doctor = Doctor.get_by_id(doctor_id)
    if not doctor:
        return []
        
    all_slots = generate_slots(doctor.working_hours_start, doctor.working_hours_end, doctor.slot_duration)
    
    # Retrieve existing booked appointments for the doctor on that date
    booked_appointments = db.appointments.find({
        'doctor_id': str(doctor_id),
        'date': date,
        'status': {'$ne': 'cancelled'}
    })
    
    booked_times = [appt.get('time') for appt in booked_appointments]
    
    # Filter out slots that are already booked
    available_slots = [slot for slot in all_slots if slot not in booked_times]
    
    return available_slots

def is_slot_available(doctor_id, date, time):
    """
    Checks if a slot is completely available to prevent double booking.
    """
    appointment = db.appointments.find_one({
        'doctor_id': str(doctor_id),
        'date': date,
        'time': time,
        'status': {'$ne': 'cancelled'}
    })
    return appointment is None

def create_appointment(doctor_id, patient_id, date, time):
    """
    Safely creates an appointment checking for double bookings.
    """
    if not is_slot_available(doctor_id, date, time):
        return False, "This time slot is already booked."
        
    result = db.appointments.insert_one({
        'doctor_id': str(doctor_id),
        'patient_id': str(patient_id),
        'date': date,
        'time': time,
        'status': 'booked'
    })
    return True, str(result.inserted_id)
