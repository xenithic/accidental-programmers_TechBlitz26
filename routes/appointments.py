from flask import Blueprint, jsonify, request, render_template, redirect, url_for
from flask_login import login_required, current_user
from utils.scheduler import get_available_slots, create_appointment
from models.doctor import Doctor
from database import db

appointments_bp = Blueprint('appointments', __name__)

@appointments_bp.route('/available-slots/<doctor_id>/<date>', methods=['GET'])
@login_required
def available_slots(doctor_id, date):
    """
    Returns the available slots for a specific doctor on a selected date.
    Output: JSON response matching {"available_slots": ["09:00", "09:30"]}
    """
    slots = get_available_slots(doctor_id, date)
    return jsonify({
        "available_slots": slots
    })

@appointments_bp.route('/book', methods=['GET', 'POST'])
@login_required
def book_appointment():
    # Doctors are not allowed to book appointments
    if current_user.role == 'doctor':
        if request.method == 'GET':
            return redirect(url_for('doctor_dashboard'))
        return jsonify({"error": "Doctors cannot book appointments."}), 403

    if request.method == 'GET':
        doctors = Doctor.get_all()
        return render_template('book_appointment.html', doctors=doctors)

    data = request.json
    if not data:
        return jsonify({"error": "No booking data provided."}), 400
        
    doctor_id = data.get('doctor_id')
    date = data.get('date')
    time = data.get('time')
    
    if not doctor_id or not date or not time:
        return jsonify({"error": "Missing required fields."}), 400
        
    success, message = create_appointment(
        doctor_id=doctor_id,
        patient_id=current_user.id,
        date=date,
        time=time
    )
    
    if not success:
        return jsonify({"error": message}), 409
        
    return jsonify({"message": "Appointment booked successfully", "appointment_id": message}), 201

from models.user import User

from bson.objectid import ObjectId

def serialize_appointment(appt):
    appt['appointment_id'] = str(appt['_id'])
    appt['_id'] = str(appt['_id'])
    
    # Enrich with doctor name
    doctor = Doctor.get_by_id(appt.get('doctor_id'))
    if doctor:
        appt['doctor_name'] = f"Dr. {doctor.name} ({doctor.specialization})"
    else:
        # Fallback to User collection if doctor_id represents a user_id
        doc_user = User.get_by_id(appt.get('doctor_id'))
        appt['doctor_name'] = f"Dr. {doc_user.name}" if doc_user else "Unknown Doctor"
        
    # Enrich with patient name
    patient = User.get_by_id(appt.get('patient_id'))
    appt['patient_name'] = patient.name if patient else "Unknown Patient"
    
    return appt

@appointments_bp.route('/my', methods=['GET'])
@login_required
def my_appointments():
    appointments = list(db.appointments.find({
        'patient_id': str(current_user.id),
        'status': {'$ne': 'cancelled'}
    }))
    return jsonify([serialize_appointment(a) for a in appointments]), 200

@appointments_bp.route('/doctor', methods=['GET'])
@login_required
def doctor_appointments():
    if current_user.role != 'doctor':
        return jsonify({'error': 'Unauthorized'}), 403
        
    doctor_obj = Doctor.get_by_email(current_user.email)
    
    # Check both the user DB id and the Doctor object ID to be safe against schema nuances.
    query_doctor_id = str(current_user.id)
    if doctor_obj:
        query_doctor_id = str(doctor_obj.id)
        
    appointments = list(db.appointments.find({
        '$or': [
            {'doctor_id': str(current_user.id)},
            {'doctor_id': query_doctor_id}
        ],
        'status': {'$ne': 'cancelled'}
    }))
    
    return jsonify([serialize_appointment(a) for a in appointments]), 200

@appointments_bp.route('/all', methods=['GET'])
@login_required
def all_appointments():
    if current_user.role != 'receptionist':
        return jsonify({'error': 'Unauthorized'}), 403
        
    appointments = list(db.appointments.find())
    return jsonify([serialize_appointment(a) for a in appointments]), 200

@appointments_bp.route('/cancel/<appointment_id>', methods=['POST'])
@login_required
def cancel_appointment(appointment_id):
    if current_user.role == 'doctor':
        return jsonify({"error": "Unauthorized"}), 403

    try:
        obj_id = ObjectId(appointment_id)
    except Exception:
        return jsonify({"error": "Invalid appointment ID"}), 400

    appointment = db.appointments.find_one({"_id": obj_id})
    if not appointment:
        return jsonify({"error": "Appointment not found"}), 404

    # Ensure patient can only cancel their own
    if current_user.role == 'patient' and appointment.get('patient_id') != str(current_user.id):
        return jsonify({"error": "Unauthorized"}), 403

    db.appointments.update_one({"_id": obj_id}, {"$set": {"status": "cancelled"}})
    return jsonify({"message": "Appointment cancelled successfully"}), 200

@appointments_bp.route('/reschedule/<appointment_id>', methods=['POST'])
@login_required
def reschedule_appointment(appointment_id):
    if current_user.role == 'doctor':
        return jsonify({"error": "Unauthorized"}), 403

    data = request.json
    if not data or not data.get('date') or not data.get('time'):
        return jsonify({"error": "Date and time are required"}), 400

    try:
        obj_id = ObjectId(appointment_id)
    except Exception:
        return jsonify({"error": "Invalid appointment ID"}), 400

    appointment = db.appointments.find_one({"_id": obj_id})
    if not appointment:
        return jsonify({"error": "Appointment not found"}), 404

    if current_user.role == 'patient' and appointment.get('patient_id') != str(current_user.id):
        return jsonify({"error": "Unauthorized"}), 403

    # Cancel old appointment
    db.appointments.update_one({"_id": obj_id}, {"$set": {"status": "cancelled"}})

    # Attempt to create new
    success, message = create_appointment(
        doctor_id=appointment.get('doctor_id'),
        patient_id=appointment.get('patient_id'),
        date=data.get('date'),
        time=data.get('time')
    )

    if not success:
        # Revert cancellation if new slot is blocked
        db.appointments.update_one({"_id": obj_id}, {"$set": {"status": appointment.get("status", "booked")}})
        return jsonify({"error": message}), 409

    return jsonify({"message": "Appointment rescheduled successfully", "appointment_id": message}), 200
