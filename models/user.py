from flask_login import UserMixin
from database import db
from werkzeug.security import generate_password_hash, check_password_hash
from bson.objectid import ObjectId

class User(UserMixin):
    def __init__(self, user_data):
        self.id = str(user_data.get('_id'))
        self.name = user_data.get('name')
        self.email = user_data.get('email')
        self.password_hash = user_data.get('password_hash')
        self.role = user_data.get('role')

    @staticmethod
    def get_by_id(user_id):
        try:
            user_data = db.users.find_one({'_id': ObjectId(user_id)})
            if user_data:
                return User(user_data)
        except Exception:
            pass
        return None

    @staticmethod
    def get_by_email(email):
        user_data = db.users.find_one({'email': email})
        if user_data:
            return User(user_data)
        return None

    @staticmethod
    def create(name, email, password, role='patient'):
        password_hash = generate_password_hash(password)
        result = db.users.insert_one({
            'name': name,
            'email': email,
            'password_hash': password_hash,
            'role': role
        })
        return str(result.inserted_id)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
