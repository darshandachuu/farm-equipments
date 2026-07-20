from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from app import db
from app.models.models import Equipment, Booking, Notification

api_bp = Blueprint('api', __name__, url_prefix='/api')


@api_bp.route('/equipment/check-availability/<int:equipment_id>')
@login_required
def check_availability(equipment_id):
    equip = Equipment.query.get_or_404(equipment_id)
    start = request.args.get('start_date')
    end = request.args.get('end_date')

    if not start or not end:
        return jsonify({'available': equip.is_available, 'message': 'Provide dates to check'}), 200

    from datetime import datetime
    try:
        start_date = datetime.strptime(start, '%Y-%m-%d').date()
        end_date = datetime.strptime(end, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'error': 'Invalid date format'}), 400

    conflict = Booking.query.filter(
        Booking.equipment_id == equipment_id,
        Booking.status.in_(['pending', 'approved', 'active']),
        Booking.start_date <= end_date,
        Booking.end_date >= start_date
    ).first()

    return jsonify({
        'available': conflict is None,
        'message': 'Available' if conflict is None else 'Already booked for selected dates'
    })


@api_bp.route('/notifications/unread-count')
@login_required
def unread_count():
    count = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
    return jsonify({'count': count})


@api_bp.route('/notifications/mark-read', methods=['POST'])
@login_required
def mark_read():
    Notification.query.filter_by(user_id=current_user.id, is_read=False).update({'is_read': True})
    db.session.commit()
    return jsonify({'success': True})
