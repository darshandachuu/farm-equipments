from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from app import db
from app.models.models import User, Equipment, Booking, Payment, FarmerProfile, OwnerProfile, Notification
from app.utils.helpers import admin_required, create_notification, format_currency

admin_bp = Blueprint('admin', __name__)


@admin_bp.route('/admin/dashboard')
@login_required
@admin_required
def dashboard():
    total_users = User.query.count()
    total_farmers = User.query.filter_by(role='farmer').count()
    total_owners = User.query.filter_by(role='owner').count()
    total_equipment = Equipment.query.count()
    pending_approval = Equipment.query.filter_by(is_approved=False, is_active=True).count()
    total_bookings = Booking.query.count()
    active_bookings = Booking.query.filter_by(status='active').count()
    pending_bookings = Booking.query.filter_by(status='pending').count()

    total_revenue = db.session.query(db.func.sum(Payment.amount)).filter(
        Payment.status == 'completed'
    ).scalar() or 0

    recent_bookings = Booking.query.order_by(Booking.created_at.desc()).limit(10).all()
    recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()
    pending_equipments = Equipment.query.filter_by(is_approved=False, is_active=True).limit(5).all()

    today = datetime.utcnow().date()
    week_ago = today - timedelta(days=7)
    new_users_this_week = User.query.filter(User.created_at >= datetime.combine(week_ago, datetime.min.time())).count()
    bookings_this_week = Booking.query.filter(Booking.created_at >= datetime.combine(week_ago, datetime.min.time())).count()

    return render_template('admin/dashboard.html',
                           total_users=total_users,
                           total_farmers=total_farmers,
                           total_owners=total_owners,
                           total_equipment=total_equipment,
                           pending_approval=pending_approval,
                           total_bookings=total_bookings,
                           active_bookings=active_bookings,
                           pending_bookings=pending_bookings,
                           total_revenue=total_revenue,
                           recent_bookings=recent_bookings,
                           recent_users=recent_users,
                           pending_equipments=pending_equipments,
                           new_users_this_week=new_users_this_week,
                           bookings_this_week=bookings_this_week,
                           active_page='dashboard',
                           format_currency=format_currency)


@admin_bp.route('/admin/users')
@login_required
@admin_required
def manage_users():
    page = request.args.get('page', 1, type=int)
    role = request.args.get('role', '')
    search = request.args.get('search', '')

    query = User.query
    if role:
        query = query.filter_by(role=role)
    if search:
        query = query.filter(
            db.or_(
                User.full_name.ilike(f'%{search}%'),
                User.email.ilike(f'%{search}%')
            )
        )

    users = query.order_by(User.created_at.desc()).paginate(page=page, per_page=15, error_out=False)
    return render_template('admin/manage_users.html', users=users, current_role=role, search=search, active_page='users')


@admin_bp.route('/admin/user/toggle/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def toggle_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash('You cannot block your own account.', 'warning')
        return redirect(url_for('admin.manage_users'))

    user.is_blocked = not user.is_blocked
    db.session.commit()

    status = 'blocked' if user.is_blocked else 'unblocked'
    flash(f'User {user.full_name} has been {status}.', 'info')
    return redirect(url_for('admin.manage_users'))


@admin_bp.route('/admin/user/delete/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash('You cannot delete your own account.', 'warning')
        return redirect(url_for('admin.manage_users'))

    user.is_active = False
    user.is_blocked = True
    db.session.commit()
    flash(f'User {user.full_name} has been deactivated.', 'info')
    return redirect(url_for('admin.manage_users'))


@admin_bp.route('/admin/equipment')
@login_required
@admin_required
def manage_equipment():
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status', '')
    search = request.args.get('search', '')

    query = Equipment.query
    if status == 'pending':
        query = query.filter_by(is_approved=False, is_active=True)
    elif status == 'approved':
        query = query.filter_by(is_approved=True)
    elif status == 'inactive':
        query = query.filter_by(is_active=False)
    if search:
        query = query.filter(
            db.or_(
                Equipment.name.ilike(f'%{search}%'),
                Equipment.category.ilike(f'%{search}%')
            )
        )

    equipment = query.order_by(Equipment.created_at.desc()).paginate(page=page, per_page=15, error_out=False)
    return render_template('admin/manage_equipment.html', equipment=equipment, current_status=status, search=search, active_page='equipment')


@admin_bp.route('/admin/equipment/approve/<int:equipment_id>', methods=['POST'])
@login_required
@admin_required
def approve_equipment(equipment_id):
    equip = Equipment.query.get_or_404(equipment_id)
    equip.is_approved = True
    db.session.commit()

    create_notification(
        equip.owner.user.id,
        'Equipment Approved',
        f'Your equipment "{equip.name}" has been approved and is now visible to farmers.',
        'success'
    )

    flash(f'Equipment "{equip.name}" approved successfully.', 'success')
    return redirect(url_for('admin.manage_equipment'))


@admin_bp.route('/admin/equipment/reject/<int:equipment_id>', methods=['POST'])
@login_required
@admin_required
def reject_equipment(equipment_id):
    equip = Equipment.query.get_or_404(equipment_id)
    equip.is_active = False
    db.session.commit()

    create_notification(
        equip.owner.user.id,
        'Equipment Rejected',
        f'Your equipment "{equip.name}" has been rejected. Please contact support for details.',
        'danger'
    )

    flash(f'Equipment "{equip.name}" has been rejected.', 'info')
    return redirect(url_for('admin.manage_equipment'))


@admin_bp.route('/admin/bookings')
@login_required
@admin_required
def manage_bookings():
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status', '')

    query = Booking.query
    if status:
        query = query.filter_by(status=status)

    bookings = query.order_by(Booking.created_at.desc()).paginate(page=page, per_page=15, error_out=False)
    return render_template('admin/manage_bookings.html', bookings=bookings, current_status=status, active_page='bookings')


@admin_bp.route('/admin/payments')
@login_required
@admin_required
def manage_payments():
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status', '')

    query = Payment.query
    if status:
        query = query.filter_by(status=status)

    payments = query.order_by(Payment.created_at.desc()).paginate(page=page, per_page=15, error_out=False)

    total_completed = db.session.query(db.func.sum(Payment.amount)).filter(
        Payment.status == 'completed'
    ).scalar() or 0
    total_pending = db.session.query(db.func.sum(Payment.amount)).filter(
        Payment.status == 'pending'
    ).scalar() or 0

    return render_template('admin/manage_payments.html',
                           payments=payments,
                           total_completed=total_completed,
                           total_pending=total_pending,
                           current_status=status,
                           active_page='payments',
                           format_currency=format_currency)


@admin_bp.route('/admin/notifications')
@login_required
@admin_required
def notifications():
    notifs = Notification.query.filter_by(user_id=current_user.id)\
        .order_by(Notification.created_at.desc()).limit(50).all()
    return render_template('admin/notifications.html', notifications=notifs, active_page='notifications')


@admin_bp.route('/admin/notifications/mark-read', methods=['POST'])
@login_required
@admin_required
def mark_notifications_read():
    Notification.query.filter_by(user_id=current_user.id, is_read=False).update({'is_read': True})
    db.session.commit()
    flash('All notifications marked as read.', 'info')
    return redirect(url_for('admin.notifications'))
