from database import db
from bson.objectid import ObjectId

class Doctor:
    def __init__(self, doctor_data):
        self.id = str(doctor_data.get('_id'))
        self.user_id = doctor_data.get('user_id')
        self.name = doctor_data.get('name')
        self.email = doctor_data.get('email')
        self.specialization = doctor_data.get('specialization')
        self.working_hours_start = doctor_data.get('working_hours_start')
        self.working_hours_end = doctor_data.get('working_hours_end')
        self.slot_duration = doctor_data.get('slot_duration')

    @staticmethod
    def get_all():
        doctors_data = db.doctors.find()
        return [Doctor(doc) for doc in doctors_data]

    @staticmethod
    def get_by_id(doctor_id):
        try:
            doc_data = db.doctors.find_one({'_id': ObjectId(doctor_id)})
            if doc_data:
                return Doctor(doc_data)
        except Exception:
            pass
        return None

    @staticmethod
    def get_by_email(email):
        doc_data = db.doctors.find_one({'email': email})
        if doc_data:
            return Doctor(doc_data)
        return None

    @staticmethod
    def create(user_id, name, email, specialization, working_hours_start, working_hours_end, slot_duration):
        result = db.doctors.insert_one({
            'user_id': str(user_id),
            'name': name,
            'email': email,
            'specialization': specialization,
            'working_hours_start': working_hours_start,
            'working_hours_end': working_hours_end,
            'slot_duration': int(slot_duration)
        })
        return str(result.inserted_id)

    @staticmethod
    def update(doctor_id, update_data):
        db.doctors.update_one(
            {'_id': ObjectId(doctor_id)},
            {'$set': update_data}
        )

    @staticmethod
    def delete(doctor_id):
        db.doctors.delete_one({'_id': ObjectId(doctor_id)})
