from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from app.models.models import User, FarmerProfile, OwnerProfile
from app.utils.helpers import create_notification

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/')
def index():
    if current_user.is_authenticated:
        return redirect_based_on_role(current_user)
    return redirect(url_for('auth.login'))


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect_based_on_role(current_user)

    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        email = request.form.get('email', '').strip().lower()
        phone = request.form.get('phone', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        role = request.form.get('role', 'farmer')

        errors = []
        if not full_name or len(full_name) < 2:
            errors.append('Full name must be at least 2 characters.')
        if not email or '@' not in email:
            errors.append('Valid email is required.')
        if not phone or len(phone) < 10:
            errors.append('Valid phone number is required.')
        if len(password) < 6:
            errors.append('Password must be at least 6 characters.')
        if password != confirm_password:
            errors.append('Passwords do not match.')
        if role not in ('farmer', 'owner'):
            errors.append('Invalid role selected.')
        if User.query.filter_by(email=email).first():
            errors.append('Email already registered.')

        if errors:
            for e in errors:
                flash(e, 'danger')
            return render_template('auth/register.html')

        user = User(
            email=email,
            full_name=full_name,
            phone=phone,
            role=role
        )
        user.set_password(password)
        db.session.add(user)
        db.session.flush()

        if role == 'farmer':
            profile = FarmerProfile(user_id=user.id)
            db.session.add(profile)
        elif role == 'owner':
            profile = OwnerProfile(user_id=user.id)
            db.session.add(profile)

        db.session.commit()
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/register.html')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect_based_on_role(current_user)

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        remember = request.form.get('remember', False)

        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password):
            if user.is_blocked:
                flash('Your account has been blocked. Contact administrator.', 'danger')
                return render_template('auth/login.html')
            if not user.is_active:
                flash('Your account is inactive. Contact administrator.', 'danger')
                return render_template('auth/login.html')

            login_user(user, remember=bool(remember))
            flash(f'Welcome back, {user.full_name}!', 'success')
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            return redirect_based_on_role(user)
        else:
            flash('Invalid email or password.', 'danger')

    return render_template('auth/login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))


@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        user = User.query.filter_by(email=email).first()
        if user:
            flash('If the email exists, a password reset link has been sent.', 'info')
        else:
            flash('If the email exists, a password reset link has been sent.', 'info')
        return redirect(url_for('auth.login'))
    return render_template('auth/forgot_password.html')


@auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        current_user.full_name = request.form.get('full_name', current_user.full_name).strip()
        current_user.phone = request.form.get('phone', current_user.phone).strip()

        if current_user.is_farmer() and current_user.farmer_profile:
            current_user.farmer_profile.farm_name = request.form.get('farm_name', current_user.farmer_profile.farm_name)
            current_user.farmer_profile.farm_location = request.form.get('farm_location', current_user.farmer_profile.farm_location)
            current_user.farmer_profile.farm_size = request.form.get('farm_size', current_user.farmer_profile.farm_size)
            current_user.farmer_profile.crop_types = request.form.get('crop_types', current_user.farmer_profile.crop_types)

        if current_user.is_owner() and current_user.owner_profile:
            current_user.owner_profile.business_name = request.form.get('business_name', current_user.owner_profile.business_name)
            current_user.owner_profile.business_address = request.form.get('business_address', current_user.owner_profile.business_address)
            current_user.owner_profile.business_type = request.form.get('business_type', current_user.owner_profile.business_type)
            current_user.owner_profile.gst_number = request.form.get('gst_number', current_user.owner_profile.gst_number)

        new_password = request.form.get('new_password', '')
        if new_password and len(new_password) >= 6:
            current_user.set_password(new_password)

        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('auth.profile'))

    return render_template('auth/profile.html')


def redirect_based_on_role(user):
    if user.is_admin():
        return redirect(url_for('admin.dashboard'))
    elif user.is_owner():
        return redirect(url_for('owner.dashboard'))
    else:
        return redirect(url_for('farmer.dashboard'))
