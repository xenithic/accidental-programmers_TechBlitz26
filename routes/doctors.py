from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user
from models.doctor import Doctor
from models.user import User
from database import db
from bson.objectid import ObjectId
import functools

doctors_bp = Blueprint('doctors', __name__)

def receptionist_required(f):
    @functools.wraps(f)
    def wrap(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'receptionist':
            return "Unauthorized", 403
        return f(*args, **kwargs)
    return wrap

@doctors_bp.route('/', methods=['GET'])
@login_required
@receptionist_required
def list_doctors():
    doctors_list = Doctor.get_all()
    return render_template('manage_doctors.html', doctors=doctors_list)

@doctors_bp.route('/add', methods=['POST'])
@login_required
@receptionist_required
def add_doctor():
    name = request.form.get('name')
    email = request.form.get('email')
    password = request.form.get('password')
    specialization = request.form.get('specialization')
    working_hours_start = request.form.get('working_hours_start')
    working_hours_end = request.form.get('working_hours_end')
    slot_duration = request.form.get('slot_duration')
    
    if User.get_by_email(email):
        flash('Email already registered', 'danger')
        return redirect(url_for('doctors.list_doctors'))
        
    user_id = User.create(name=name, email=email, password=password, role='doctor')
    Doctor.create(
        user_id=user_id,
        name=name,
        email=email,
        specialization=specialization,
        working_hours_start=working_hours_start,
        working_hours_end=working_hours_end,
        slot_duration=slot_duration
    )
    flash('Doctor added successfully', 'success')
    return redirect(url_for('doctors.list_doctors'))

@doctors_bp.route('/<doctor_id>', methods=['PUT', 'DELETE'])
@login_required
@receptionist_required
def manage_doctor(doctor_id):
    doctor = Doctor.get_by_id(doctor_id)
    if not doctor:
        return jsonify({'error': 'Doctor not found'}), 404
        
    if request.method == 'DELETE':
        # Delete the corresponding user
        if doctor.user_id:
            db.users.delete_one({'_id': ObjectId(doctor.user_id)})
        Doctor.delete(doctor_id)
        return jsonify({'message': 'Doctor deleted'}), 200
        
    elif request.method == 'PUT':
        data = request.json
        if not data:
            return jsonify({'error': 'No data provided'}), 400
            
        update_data = {
            'name': data.get('name', doctor.name),
            'specialization': data.get('specialization', doctor.specialization),
            'working_hours_start': data.get('working_hours_start', doctor.working_hours_start),
            'working_hours_end': data.get('working_hours_end', doctor.working_hours_end),
            'slot_duration': int(data.get('slot_duration', doctor.slot_duration))
        }
        
        # Update user name if it changed
        if data.get('name') and doctor.user_id:
            db.users.update_one({'_id': ObjectId(doctor.user_id)}, {'$set': {'name': data['name']}})
            
        Doctor.update(doctor_id, update_data)
        return jsonify({'message': 'Doctor updated successfully'}), 200
