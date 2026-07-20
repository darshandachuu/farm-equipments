from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from datetime import datetime
from app import db
from app.models.models import Equipment, Booking, Payment, OwnerProfile
from app.utils.helpers import owner_required, save_upload, create_notification, format_currency

owner_bp = Blueprint('owner', __name__)


@owner_bp.route('/owner/dashboard')
@login_required
@owner_required
def dashboard():
    if not current_user.owner_profile:
        flash('Please complete your profile first.', 'warning')
        return redirect(url_for('auth.profile'))

    total_equipment = Equipment.query.filter_by(owner_id=current_user.owner_profile.id).count()
    available_equipment = Equipment.query.filter_by(owner_id=current_user.owner_profile.id, is_available=True).count()
    total_bookings = Booking.query.join(Equipment).filter(Equipment.owner_id == current_user.owner_profile.id).count()
    pending_bookings = Booking.query.join(Equipment).filter(
        Equipment.owner_id == current_user.owner_profile.id, Booking.status == 'pending'
    ).count()

    total_earnings = db.session.query(db.func.sum(Payment.amount)).join(Booking).join(Equipment).filter(
        Equipment.owner_id == current_user.owner_profile.id,
        Payment.payee_id == current_user.id,
        Payment.status == 'completed'
    ).scalar() or 0

    recent_bookings = Booking.query.join(Equipment).filter(
        Equipment.owner_id == current_user.owner_profile.id
    ).order_by(Booking.created_at.desc()).limit(5).all()

    my_equipment = Equipment.query.filter_by(owner_id=current_user.owner_profile.id)\
        .order_by(Equipment.created_at.desc()).limit(5).all()

    return render_template('owner/dashboard.html',
                           total_equipment=total_equipment,
                           available_equipment=available_equipment,
                           total_bookings=total_bookings,
                           pending_bookings=pending_bookings,
                           total_earnings=total_earnings,
                           recent_bookings=recent_bookings,
                           my_equipment=my_equipment,
                           active_page='dashboard',
                           format_currency=format_currency)


@owner_bp.route('/owner/equipment')
@login_required
@owner_required
def my_equipment():
    if not current_user.owner_profile:
        flash('Please complete your profile first.', 'warning')
        return redirect(url_for('auth.profile'))

    page = request.args.get('page', 1, type=int)
    equipment = Equipment.query.filter_by(owner_id=current_user.owner_profile.id)\
        .order_by(Equipment.created_at.desc()).paginate(page=page, per_page=10, error_out=False)
    return render_template('owner/my_equipment.html', equipment=equipment, active_page='equipment')


@owner_bp.route('/owner/equipment/add', methods=['GET', 'POST'])
@login_required
@owner_required
def add_equipment():
    if not current_user.owner_profile:
        flash('Please complete your profile first.', 'warning')
        return redirect(url_for('auth.profile'))

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        category = request.form.get('category', '').strip()
        description = request.form.get('description', '').strip()
        brand = request.form.get('brand', '').strip()
        model = request.form.get('model', '').strip()
        year = request.form.get('year', type=int)
        condition = request.form.get('condition', 'Good')
        daily_rate = request.form.get('daily_rate', type=float)
        weekly_rate = request.form.get('weekly_rate', type=float)
        monthly_rate = request.form.get('monthly_rate', type=float)
        security_deposit = request.form.get('security_deposit', 0, type=float)
        location = request.form.get('location', '').strip()

        errors = []
        if not name:
            errors.append('Equipment name is required.')
        if not category:
            errors.append('Category is required.')
        if not daily_rate or daily_rate <= 0:
            errors.append('Daily rate must be greater than 0.')

        if errors:
            for e in errors:
                flash(e, 'danger')
            return render_template('owner/add_equipment.html')

        image_file = request.files.get('image')
        image_filename = 'default_equipment.png'
        if image_file and image_file.filename:
            image_filename = save_upload(image_file, 'UPLOAD_FOLDER_EQUIPMENT')

        equip = Equipment(
            owner_id=current_user.owner_profile.id,
            name=name,
            category=category,
            description=description,
            brand=brand,
            model=model,
            year=year,
            condition=condition,
            daily_rate=daily_rate,
            weekly_rate=weekly_rate,
            monthly_rate=monthly_rate,
            security_deposit=security_deposit,
            location=location,
            image=image_filename,
            is_approved=False
        )
        db.session.add(equip)
        db.session.commit()

        flash('Equipment added successfully! Waiting for admin approval.', 'success')
        return redirect(url_for('owner.my_equipment'))

    categories = ['Tractor', 'Harvester', 'Rotavator', 'Cultivator', 'Seed Drill',
                   'Sprayer', 'Thresher', 'Plough', 'Other']
    return render_template('owner/add_equipment.html', categories=categories, active_page='add_equipment')


@owner_bp.route('/owner/equipment/edit/<int:equipment_id>', methods=['GET', 'POST'])
@login_required
@owner_required
def edit_equipment(equipment_id):
    equip = Equipment.query.get_or_404(equipment_id)
    if equip.owner_id != current_user.owner_profile.id:
        flash('Unauthorized action.', 'danger')
        return redirect(url_for('owner.my_equipment'))

    if request.method == 'POST':
        equip.name = request.form.get('name', equip.name).strip()
        equip.category = request.form.get('category', equip.category).strip()
        equip.description = request.form.get('description', equip.description).strip()
        equip.brand = request.form.get('brand', equip.brand).strip()
        equip.model = request.form.get('model', equip.model).strip()
        equip.year = request.form.get('year', equip.year, type=int)
        equip.condition = request.form.get('condition', equip.condition)
        equip.daily_rate = request.form.get('daily_rate', equip.daily_rate, type=float)
        equip.weekly_rate = request.form.get('weekly_rate', equip.weekly_rate, type=float)
        equip.monthly_rate = request.form.get('monthly_rate', equip.monthly_rate, type=float)
        equip.security_deposit = request.form.get('security_deposit', equip.security_deposit, type=float)
        equip.location = request.form.get('location', equip.location).strip()

        image_file = request.files.get('image')
        if image_file and image_file.filename:
            equip.image = save_upload(image_file, 'UPLOAD_FOLDER_EQUIPMENT', equip.image)

        db.session.commit()
        flash('Equipment updated successfully!', 'success')
        return redirect(url_for('owner.my_equipment'))

    categories = ['Tractor', 'Harvester', 'Rotavator', 'Cultivator', 'Seed Drill',
                   'Sprayer', 'Thresher', 'Plough', 'Other']
    return render_template('owner/edit_equipment.html', equipment=equip, categories=categories, active_page='equipment')


@owner_bp.route('/owner/equipment/delete/<int:equipment_id>', methods=['POST'])
@login_required
@owner_required
def delete_equipment(equipment_id):
    equip = Equipment.query.get_or_404(equipment_id)
    if equip.owner_id != current_user.owner_profile.id:
        flash('Unauthorized action.', 'danger')
        return redirect(url_for('owner.my_equipment'))

    active_bookings = Booking.query.filter(
        Booking.equipment_id == equip.id,
        Booking.status.in_(['pending', 'approved', 'active'])
    ).count()

    if active_bookings > 0:
        flash('Cannot delete equipment with active bookings.', 'warning')
        return redirect(url_for('owner.my_equipment'))

    equip.is_active = False
    db.session.commit()
    flash('Equipment deleted successfully.', 'info')
    return redirect(url_for('owner.my_equipment'))


@owner_bp.route('/owner/equipment/toggle/<int:equipment_id>', methods=['POST'])
@login_required
@owner_required
def toggle_availability(equipment_id):
    equip = Equipment.query.get_or_404(equipment_id)
    if equip.owner_id != current_user.owner_profile.id:
        flash('Unauthorized action.', 'danger')
        return redirect(url_for('owner.my_equipment'))

    equip.is_available = not equip.is_available
    db.session.commit()
    status = 'available' if equip.is_available else 'unavailable'
    flash(f'Equipment marked as {status}.', 'success')
    return redirect(url_for('owner.my_equipment'))


@owner_bp.route('/owner/bookings')
@login_required
@owner_required
def bookings():
    if not current_user.owner_profile:
        flash('Please complete your profile first.', 'warning')
        return redirect(url_for('auth.profile'))

    page = request.args.get('page', 1, type=int)
    status = request.args.get('status', '')

    query = Booking.query.join(Equipment).filter(Equipment.owner_id == current_user.owner_profile.id)
    if status:
        query = query.filter(Booking.status == status)

    bookings = query.order_by(Booking.created_at.desc()).paginate(page=page, per_page=10, error_out=False)
    return render_template('owner/bookings.html', bookings=bookings, current_status=status, active_page='bookings')


@owner_bp.route('/owner/booking/<int:booking_id>')
@login_required
@owner_required
def view_booking(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    if booking.equipment.owner_id != current_user.owner_profile.id:
        flash('Unauthorized action.', 'danger')
        return redirect(url_for('owner.bookings'))
    return render_template('owner/view_booking.html', booking=booking, format_currency=format_currency, active_page='bookings')


@owner_bp.route('/owner/booking/approve/<int:booking_id>', methods=['POST'])
@login_required
@owner_required
def approve_booking(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    if booking.equipment.owner_id != current_user.owner_profile.id:
        flash('Unauthorized action.', 'danger')
        return redirect(url_for('owner.bookings'))

    if booking.status != 'pending':
        flash('This booking cannot be approved.', 'warning')
        return redirect(url_for('owner.view_booking', booking_id=booking.id))

    booking.status = 'approved'
    booking.equipment.is_available = False
    db.session.commit()

    create_notification(
        booking.farmer_id,
        'Booking Approved!',
        f'Your booking #{booking.booking_number} for {booking.equipment.name} has been approved. Please proceed with payment.',
        'success',
        url_for('farmer.my_bookings')
    )

    flash('Booking approved successfully!', 'success')
    return redirect(url_for('owner.view_booking', booking_id=booking.id))


@owner_bp.route('/owner/booking/reject/<int:booking_id>', methods=['POST'])
@login_required
@owner_required
def reject_booking(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    if booking.equipment.owner_id != current_user.owner_profile.id:
        flash('Unauthorized action.', 'danger')
        return redirect(url_for('owner.bookings'))

    if booking.status != 'pending':
        flash('This booking cannot be rejected.', 'warning')
        return redirect(url_for('owner.view_booking', booking_id=booking.id))

    booking.status = 'rejected'
    owner_notes = request.form.get('owner_notes', '').strip()
    booking.owner_notes = owner_notes
    db.session.commit()

    create_notification(
        booking.farmer_id,
        'Booking Rejected',
        f'Your booking #{booking.booking_number} for {booking.equipment.name} has been rejected.',
        'danger',
        url_for('farmer.my_bookings')
    )

    flash('Booking rejected.', 'info')
    return redirect(url_for('owner.view_booking', booking_id=booking.id))


@owner_bp.route('/owner/booking/complete/<int:booking_id>', methods=['POST'])
@login_required
@owner_required
def complete_booking(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    if booking.equipment.owner_id != current_user.owner_profile.id:
        flash('Unauthorized action.', 'danger')
        return redirect(url_for('owner.bookings'))

    if booking.status != 'active':
        flash('This booking cannot be completed.', 'warning')
        return redirect(url_for('owner.view_booking', booking_id=booking.id))

    booking.status = 'completed'
    booking.equipment.is_available = True
    db.session.commit()

    create_notification(
        booking.farmer_id,
        'Booking Completed',
        f'Your booking #{booking.booking_number} for {booking.equipment.name} has been marked as completed.',
        'success',
        url_for('farmer.my_bookings')
    )

    flash('Booking marked as completed!', 'success')
    return redirect(url_for('owner.view_booking', booking_id=booking.id))


@owner_bp.route('/owner/earnings')
@login_required
@owner_required
def earnings():
    if not current_user.owner_profile:
        flash('Please complete your profile first.', 'warning')
        return redirect(url_for('auth.profile'))

    payments = Payment.query.join(Booking).join(Equipment).filter(
        Equipment.owner_id == current_user.owner_profile.id,
        Payment.payee_id == current_user.id,
        Payment.status == 'completed'
    ).order_by(Payment.created_at.desc()).all()

    total_earnings = sum(p.amount for p in payments)

    monthly_earnings = db.session.query(
        db.func.strftime('%Y-%m', Payment.created_at),
        db.func.sum(Payment.amount)
    ).join(Booking).join(Equipment).filter(
        Equipment.owner_id == current_user.owner_profile.id,
        Payment.payee_id == current_user.id,
        Payment.status == 'completed'
    ).group_by(db.func.strftime('%Y-%m', Payment.created_at)).order_by(db.func.strftime('%Y-%m', Payment.created_at).desc()).limit(12).all()

    return render_template('owner/earnings.html',
                           payments=payments,
                           total_earnings=total_earnings,
                           monthly_earnings=monthly_earnings,
                           active_page='earnings',
                           format_currency=format_currency)
