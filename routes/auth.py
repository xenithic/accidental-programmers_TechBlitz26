from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required, current_user
from models.user import User

auth_bp = Blueprint('auth', __name__)

def redirect_by_role(role):
    print(f"[DEBUG Login] Detected user role: {role}")
    if not role:
        return redirect(url_for('auth.login'))
        
    safe_role = str(role).strip().lower()
    
    if safe_role == 'patient':
        return redirect(url_for('patient_dashboard'))
    elif safe_role == 'doctor':
        return redirect(url_for('doctor_dashboard'))
    elif safe_role == 'receptionist':
        return redirect(url_for('receptionist_dashboard'))
    
    return redirect(url_for('auth.login'))

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect_by_role(current_user.role)
        
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.get_by_email(email)
        
        if user and user.check_password(password):
            login_user(user)
            return redirect_by_role(user.role)
            
        flash('Invalid email or password', 'danger')
        
    return render_template('login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    # Only patients register themselves
    if current_user.is_authenticated:
        return redirect_by_role(current_user.role)

    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        
        existing_user = User.get_by_email(email)
        if existing_user:
            flash('Email address already associated with an account.', 'warning')
            return redirect(url_for('auth.register'))
            
        User.create(name=name, email=email, password=password, role='patient')
        
        flash('Registration successful. You can now log in.', 'success')
        return redirect(url_for('auth.login'))
        
    return render_template('register.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))
