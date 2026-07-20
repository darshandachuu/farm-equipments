import os
import secrets
import string
from datetime import datetime
from functools import wraps
from flask import flash, redirect, url_for, request, abort, current_app, render_template
from flask_login import current_user
from werkzeug.utils import secure_filename
from app import db
from app.models.models import Notification


def generate_booking_number():
    prefix = "FER"
    rand = ''.join(secrets.choices(string.ascii_uppercase + string.digits, k=8))
    return f"{prefix}-{rand}"


def generate_payment_number():
    prefix = "PAY"
    rand = ''.join(secrets.choices(string.ascii_uppercase + string.digits, k=8))
    return f"{prefix}-{rand}"


def allowed_file(filename, allowed_extensions={'png', 'jpg', 'jpeg', 'gif', 'webp'}):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions


def save_upload(file, folder, current_filename=None):
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        ext = filename.rsplit('.', 1)[1].lower()
        new_filename = f"{secrets.token_hex(8)}.{ext}"
        upload_path = os.path.join(current_app.config[folder], new_filename)
        os.makedirs(os.path.dirname(upload_path), exist_ok=True)
        file.save(upload_path)
        if current_filename and current_filename != 'default.png' and current_filename != 'default_equipment.png':
            old_path = os.path.join(current_app.config[folder], current_filename)
            if os.path.exists(old_path):
                os.remove(old_path)
        return new_filename
    return current_filename


def owner_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_owner():
            abort(403)
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin():
            abort(403)
        return f(*args, **kwargs)
    return decorated_function


def farmer_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_farmer():
            abort(403)
        return f(*args, **kwargs)
    return decorated_function


def create_notification(user_id, title, message, notif_type='info', link=None):
    notif = Notification(
        user_id=user_id,
        title=title,
        message=message,
        type=notif_type,
        link=link
    )
    db.session.add(notif)
    db.session.commit()
    return notif


def format_currency(amount):
    return f"\u20b9{amount:,.2f}"


def time_since(dt):
    now = datetime.utcnow()
    diff = now - dt
    if diff.days > 365:
        return f"{diff.days // 365} year(s) ago"
    if diff.days > 30:
        return f"{diff.days // 30} month(s) ago"
    if diff.days > 0:
        return f"{diff.days} day(s) ago"
    if diff.seconds > 3600:
        return f"{diff.seconds // 3600} hour(s) ago"
    if diff.seconds > 60:
        return f"{diff.seconds // 60} minute(s) ago"
    return "Just now"
