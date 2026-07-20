from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from datetime import datetime, date
from app import db
from app.models.models import Equipment, Booking, Payment, FarmerProfile
from app.utils.helpers import farmer_required, generate_booking_number, create_notification, format_currency

farmer_bp = Blueprint('farmer', __name__)


@farmer_bp.route('/farmer/dashboard')
@login_required
@farmer_required
def dashboard():
    total_bookings = Booking.query.filter_by(farmer_id=current_user.id).count()
    active_bookings = Booking.query.filter_by(farmer_id=current_user.id, status='active').count()
    pending_bookings = Booking.query.filter_by(farmer_id=current_user.id, status='pending').count()
    total_spent = db.session.query(db.func.sum(Payment.amount)).filter(
        Payment.payer_id == current_user.id,
        Payment.status == 'completed'
    ).scalar() or 0

    recent_bookings = Booking.query.filter_by(farmer_id=current_user.id)\
        .order_by(Booking.created_at.desc()).limit(5).all()

    available_equipment = Equipment.query.filter_by(is_available=True, is_approved=True, is_active=True)\
        .order_by(Equipment.created_at.desc()).limit(6).all()

    return render_template('farmer/dashboard.html',
                           total_bookings=total_bookings,
                           active_bookings=active_bookings,
                           pending_bookings=pending_bookings,
                           total_spent=total_spent,
                           recent_bookings=recent_bookings,
                           available_equipment=available_equipment,
                           format_currency=format_currency)


@farmer_bp.route('/farmer/equipment')
@login_required
@farmer_required
def search_equipment():
    page = request.args.get('page', 1, type=int)
    category = request.args.get('category', '')
    search = request.args.get('search', '')
    location = request.args.get('location', '')
    min_price = request.args.get('min_price', 0, type=float)
    max_price = request.args.get('max_price', 0, type=float)
    sort = request.args.get('sort', 'newest')

    query = Equipment.query.filter_by(is_available=True, is_approved=True, is_active=True)

    if category:
        query = query.filter_by(category=category)
    if search:
        query = query.filter(
            db.or_(
                Equipment.name.ilike(f'%{search}%'),
                Equipment.brand.ilike(f'%{search}%'),
                Equipment.description.ilike(f'%{search}%')
            )
        )
    if location:
        query = query.filter(Equipment.location.ilike(f'%{location}%'))
    if min_price > 0:
        query = query.filter(Equipment.daily_rate >= min_price)
    if max_price > 0:
        query = query.filter(Equipment.daily_rate <= max_price)

    if sort == 'price_low':
        query = query.order_by(Equipment.daily_rate.asc())
    elif sort == 'price_high':
        query = query.order_by(Equipment.daily_rate.desc())
    else:
        query = query.order_by(Equipment.created_at.desc())

    equipment = query.paginate(page=page, per_page=12, error_out=False)
    categories = ['Tractor', 'Harvester', 'Rotavator', 'Cultivator', 'Seed Drill',
                   'Sprayer', 'Thresher', 'Plough', 'Other']

    return render_template('farmer/search_equipment.html',
                           equipment=equipment,
                           categories=categories,
                           selected_category=category,
                           search=search,
                           location=location,
                           min_price=min_price,
                           max_price=max_price,
                           sort=sort)


@farmer_bp.route('/farmer/equipment/<int:equipment_id>')
@login_required
@farmer_required
def view_equipment(equipment_id):
    equip = Equipment.query.get_or_404(equipment_id)
    if not equip.is_approved or not equip.is_active:
        flash('Equipment not found.', 'warning')
        return redirect(url_for('farmer.search_equipment'))

    owner_user = equip.owner.user
    related = Equipment.query.filter(
        Equipment.category == equip.category,
        Equipment.id != equip.id,
        Equipment.is_approved == True,
        Equipment.is_active == True
    ).limit(3).all()

    return render_template('farmer/view_equipment.html',
                           equipment=equip,
                           owner=owner_user,
                           related=related,
                           format_currency=format_currency)


@farmer_bp.route('/farmer/book/<int:equipment_id>', methods=['GET', 'POST'])
@login_required
@farmer_required
def book_equipment(equipment_id):
    equip = Equipment.query.get_or_404(equipment_id)
    if not equip.is_available or not equip.is_approved:
        flash('Equipment is not available for booking.', 'warning')
        return redirect(url_for('farmer.search_equipment'))

    if request.method == 'POST':
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')
        rental_type = request.form.get('rental_type', 'daily')
        pickup_location = request.form.get('pickup_location', '').strip()
        purpose = request.form.get('purpose', '').strip()
        notes = request.form.get('notes', '').strip()

        try:
            start = datetime.strptime(start_date, '%Y-%m-%d').date()
            end = datetime.strptime(end_date, '%Y-%m-%d').date()
        except (ValueError, TypeError):
            flash('Invalid date format.', 'danger')
            return render_template('farmer/book_equipment.html', equipment=equip, format_currency=format_currency)

        if start < date.today():
            flash('Start date cannot be in the past.', 'danger')
            return render_template('farmer/book_equipment.html', equipment=equip, format_currency=format_currency)
        if end < start:
            flash('End date must be after start date.', 'danger')
            return render_template('farmer/book_equipment.html', equipment=equip, format_currency=format_currency)

        total_days = (end - start).days
        if total_days == 0:
            total_days = 1

        if rental_type == 'weekly' and equip.weekly_rate:
            weeks = total_days // 7
            remaining = total_days % 7
            total_amount = (weeks * equip.weekly_rate) + (remaining * equip.daily_rate)
        elif rental_type == 'monthly' and equip.monthly_rate:
            months = total_days // 30
            remaining = total_days % 30
            total_amount = (months * equip.monthly_rate) + (remaining * equip.daily_rate)
        else:
            total_amount = total_days * equip.daily_rate

        booking = Booking(
            booking_number=generate_booking_number(),
            farmer_id=current_user.id,
            equipment_id=equip.id,
            start_date=start,
            end_date=end,
            rental_type=rental_type,
            total_days=total_days,
            total_amount=round(total_amount, 2),
            security_deposit=equip.security_deposit or 0,
            status='pending',
            pickup_location=pickup_location,
            purpose=purpose,
            notes=notes
        )
        db.session.add(booking)
        db.session.commit()

        owner_user = equip.owner.user
        create_notification(
            owner_user.id,
            'New Booking Request',
            f'You have a new booking request from {current_user.full_name} for {equip.name}.',
            'info',
            url_for('owner.view_booking', booking_id=booking.id)
        )

        flash(f'Booking request submitted! Booking #{booking.booking_number}', 'success')
        return redirect(url_for('farmer.my_bookings'))

    return render_template('farmer/book_equipment.html', equipment=equip, format_currency=format_currency, now_date=date.today().isoformat())


@farmer_bp.route('/farmer/bookings')
@login_required
@farmer_required
def my_bookings():
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status', '')

    query = Booking.query.filter_by(farmer_id=current_user.id)
    if status:
        query = query.filter_by(status=status)

    bookings = query.order_by(Booking.created_at.desc()).paginate(page=page, per_page=10, error_out=False)
    return render_template('farmer/my_bookings.html', bookings=bookings, current_status=status)


@farmer_bp.route('/farmer/cancel-booking/<int:booking_id>', methods=['POST'])
@login_required
@farmer_required
def cancel_booking(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    if booking.farmer_id != current_user.id:
        flash('Unauthorized action.', 'danger')
        return redirect(url_for('farmer.my_bookings'))

    if booking.status not in ('pending', 'approved'):
        flash('This booking cannot be cancelled.', 'warning')
        return redirect(url_for('farmer.my_bookings'))

    booking.status = 'cancelled'
    db.session.commit()

    equip = booking.equipment
    owner_user = equip.owner.user
    create_notification(
        owner_user.id,
        'Booking Cancelled',
        f'Booking #{booking.booking_number} for {equip.name} has been cancelled by the farmer.',
        'warning',
        url_for('owner.view_booking', booking_id=booking.id)
    )

    flash('Booking cancelled successfully.', 'info')
    return redirect(url_for('farmer.my_bookings'))


@farmer_bp.route('/farmer/payments')
@login_required
@farmer_required
def payment_history():
    page = request.args.get('page', 1, type=int)
    payments = Payment.query.filter_by(payer_id=current_user.id)\
        .order_by(Payment.created_at.desc()).paginate(page=page, per_page=10, error_out=False)
    return render_template('farmer/payment_history.html', payments=payments, format_currency=format_currency)
