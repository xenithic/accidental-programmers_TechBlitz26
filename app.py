from flask import Flask, render_template, redirect, url_for
from flask_login import LoginManager, login_required, current_user

from config import Config
from models.user import User
from routes.auth import auth_bp
from routes.doctors import doctors_bp
from routes.appointments import appointments_bp

app = Flask(__name__)
app.config.from_object(Config)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message_category = 'info'
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.get_by_id(user_id)

# Register Blueprints
app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(doctors_bp, url_prefix='/doctors')
app.register_blueprint(appointments_bp, url_prefix='/appointments')

@app.route('/')
def index():
    if current_user.is_authenticated:
        safe_role = str(current_user.role).strip().lower() if current_user.role else ''
        if safe_role == 'patient':
            return redirect(url_for('patient_dashboard'))
        elif safe_role == 'doctor':
            return redirect(url_for('doctor_dashboard'))
        elif safe_role == 'receptionist':
            return redirect(url_for('receptionist_dashboard'))
    return redirect(url_for('auth.login'))

@app.route('/dashboard/patient')
@login_required
def patient_dashboard():
    if current_user.role != 'patient':
        return "Unauthorized", 403
    return render_template('patient_dashboard.html')

@app.route('/dashboard/doctor')
@login_required
def doctor_dashboard():
    if current_user.role != 'doctor':
        return "Unauthorized", 403
    return render_template('doctor_dashboard.html')

@app.route('/dashboard/receptionist')
@login_required
def receptionist_dashboard():
    if current_user.role != 'receptionist':
        return "Unauthorized", 403
    return render_template('receptionist_dashboard.html')

def init_staff_accounts():
    # Create default receptionist if not exists
    if not User.get_by_email('receptionist@clinic.com'):
        User.create(
            name='System Receptionist',
            email='receptionist@clinic.com',
            password='admin123',
            role='receptionist'
        )
        print("Initialized default receptionist account.")
        
    # Create default doctor if not exists
    if not User.get_by_email('doctor1@clinic.com'):
        User.create(
            name='System Doctor',
            email='doctor1@clinic.com',
            password='doctor123',
            role='doctor'
        )
        print("Initialized default doctor account.")

# Run the initialization step
init_staff_accounts()

if __name__ == '__main__':
    app.run(debug=True)
