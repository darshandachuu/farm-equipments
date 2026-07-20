from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app import db, login_manager


class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='farmer')  # farmer, owner, admin
    avatar = db.Column(db.String(256), default='default.png')
    is_active = db.Column(db.Boolean, default=True)
    is_blocked = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    farmer_profile = db.relationship('FarmerProfile', backref='user', uselist=False, lazy=True)
    owner_profile = db.relationship('OwnerProfile', backref='user', uselist=False, lazy=True)
    bookings_made = db.relationship('Booking', backref='farmer', lazy=True, foreign_keys='Booking.farmer_id')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def is_farmer(self):
        return self.role == 'farmer'

    def is_owner(self):
        return self.role == 'owner'

    def is_admin(self):
        return self.role == 'admin'

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))


class FarmerProfile(db.Model):
    __tablename__ = 'farmer_profiles'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    farm_name = db.Column(db.String(150))
    farm_location = db.Column(db.String(255))
    farm_size = db.Column(db.String(50))
    crop_types = db.Column(db.String(255))


class OwnerProfile(db.Model):
    __tablename__ = 'owner_profiles'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    business_name = db.Column(db.String(150))
    business_address = db.Column(db.String(255))
    business_type = db.Column(db.String(50))
    gst_number = db.Column(db.String(20))
    bank_account = db.Column(db.String(50))
    ifsc_code = db.Column(db.String(20))

    equipment = db.relationship('Equipment', backref='owner', lazy=True)


class Equipment(db.Model):
    __tablename__ = 'equipment'

    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.Integer, db.ForeignKey('owner_profiles.id'), nullable=False)
    name = db.Column(db.String(150), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text)
    brand = db.Column(db.String(100))
    model = db.Column(db.String(100))
    year = db.Column(db.Integer)
    condition = db.Column(db.String(20), default='Good')
    daily_rate = db.Column(db.Float, nullable=False)
    weekly_rate = db.Column(db.Float)
    monthly_rate = db.Column(db.Float)
    security_deposit = db.Column(db.Float, default=0)
    location = db.Column(db.String(255))
    image = db.Column(db.String(256), default='default_equipment.png')
    is_available = db.Column(db.Boolean, default=True)
    is_approved = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    bookings = db.relationship('Booking', backref='equipment', lazy=True)


class Booking(db.Model):
    __tablename__ = 'bookings'

    id = db.Column(db.Integer, primary_key=True)
    booking_number = db.Column(db.String(20), unique=True, nullable=False)
    farmer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    equipment_id = db.Column(db.Integer, db.ForeignKey('equipment.id'), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    rental_type = db.Column(db.String(20), default='daily')  # daily, weekly, monthly
    total_days = db.Column(db.Integer, nullable=False)
    total_amount = db.Column(db.Float, nullable=False)
    security_deposit = db.Column(db.Float, default=0)
    status = db.Column(db.String(20), default='pending')  # pending, approved, rejected, active, completed, cancelled
    pickup_location = db.Column(db.String(255))
    purpose = db.Column(db.Text)
    notes = db.Column(db.Text)
    owner_notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Payment(db.Model):
    __tablename__ = 'payments'

    id = db.Column(db.Integer, primary_key=True)
    payment_number = db.Column(db.String(20), unique=True, nullable=False)
    booking_id = db.Column(db.Integer, db.ForeignKey('bookings.id'), nullable=False)
    payer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    payee_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    payment_method = db.Column(db.String(30), default='cash')  # cash, upi, card, bank_transfer
    payment_type = db.Column(db.String(20), default='rental')  # rental, deposit, refund
    status = db.Column(db.String(20), default='pending')  # pending, completed, failed, refunded
    transaction_id = db.Column(db.String(100))
    notes = db.Column(db.Text)
    paid_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    booking = db.relationship('Booking', backref='payments')
    payer = db.relationship('User', foreign_keys=[payer_id])
    payee = db.relationship('User', foreign_keys=[payee_id])


class Notification(db.Model):
    __tablename__ = 'notifications'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    type = db.Column(db.String(30), default='info')  # info, success, warning, danger
    is_read = db.Column(db.Boolean, default=False)
    link = db.Column(db.String(256))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref='notifications')
