from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from app import db
from app.models.models import User, Equipment, Booking, Payment
from app.utils.helpers import admin_required, format_currency

reports_bp = Blueprint('reports', __name__)


@reports_bp.route('/reports')
@login_required
@admin_required
def index():
    return render_template('reports/index.html', active_page='reports')


@reports_bp.route('/reports/equipment-usage')
@login_required
@admin_required
def equipment_usage():
    equipment_stats = db.session.query(
        Equipment.name,
        Equipment.category,
        db.func.count(Booking.id).label('booking_count'),
        db.func.sum(Booking.total_amount).label('total_revenue')
    ).outerjoin(Booking).group_by(Equipment.id).order_by(db.func.count(Booking.id).desc()).all()

    return render_template('reports/equipment_usage.html', stats=equipment_stats, active_page='reports', format_currency=format_currency)


@reports_bp.route('/reports/revenue')
@login_required
@admin_required
def revenue():
    total_revenue = db.session.query(db.func.sum(Payment.amount)).filter(
        Payment.status == 'completed'
    ).scalar() or 0

    monthly_data = db.session.query(
        db.func.strftime('%Y-%m', Payment.created_at).label('month'),
        db.func.sum(Payment.amount).label('revenue'),
        db.func.count(Payment.id).label('transactions')
    ).filter(
        Payment.status == 'completed'
    ).group_by(db.func.strftime('%Y-%m', Payment.created_at)).order_by(
        db.func.strftime('%Y-%m', Payment.created_at).desc()
    ).limit(12).all()

    return render_template('reports/revenue.html',
                           total_revenue=total_revenue,
                           monthly_data=monthly_data,
                           active_page='reports',
                           format_currency=format_currency)


@reports_bp.route('/reports/bookings')
@login_required
@admin_required
def bookings():
    status_counts = db.session.query(
        Booking.status,
        db.func.count(Booking.id)
    ).group_by(Booking.status).all()

    monthly_bookings = db.session.query(
        db.func.strftime('%Y-%m', Booking.created_at).label('month'),
        db.func.count(Booking.id).label('count')
    ).group_by(db.func.strftime('%Y-%m', Booking.created_at)).order_by(
        db.func.strftime('%Y-%m', Booking.created_at).desc()
    ).limit(12).all()

    category_stats = db.session.query(
        Equipment.category,
        db.func.count(Booking.id).label('count')
    ).join(Equipment).group_by(Equipment.category).all()

    return render_template('reports/bookings.html',
                           status_counts=status_counts,
                           monthly_bookings=monthly_bookings,
                           category_stats=category_stats,
                           active_page='reports')


@reports_bp.route('/reports/users')
@login_required
@admin_required
def users():
    total_users = User.query.count()
    total_farmers = User.query.filter_by(role='farmer').count()
    total_owners = User.query.filter_by(role='owner').count()

    monthly_registrations = db.session.query(
        db.func.strftime('%Y-%m', User.created_at).label('month'),
        db.func.count(User.id).label('count'),
        User.role
    ).group_by(db.func.strftime('%Y-%m', User.created_at), User.role).order_by(
        db.func.strftime('%Y-%m', User.created_at).desc()
    ).limit(24).all()

    return render_template('reports/users.html',
                           total_users=total_users,
                           total_farmers=total_farmers,
                           total_owners=total_owners,
                           monthly_registrations=monthly_registrations,
                           active_page='reports')
