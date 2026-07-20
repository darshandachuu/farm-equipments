from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime
from app import db
from app.models.models import Booking, Payment, Equipment
from app.utils.helpers import generate_payment_number, create_notification, format_currency

payment_bp = Blueprint('payment', __name__)


@payment_bp.route('/payment/<int:booking_id>', methods=['GET', 'POST'])
@login_required
def make_payment(booking_id):
    booking = Booking.query.get_or_404(booking_id)

    if booking.farmer_id != current_user.id:
        flash('Unauthorized action.', 'danger')
        return redirect(url_for('farmer.my_bookings'))

    if booking.status != 'approved':
        flash('This booking is not ready for payment.', 'warning')
        return redirect(url_for('farmer.my_bookings'))

    if request.method == 'POST':
        payment_method = request.form.get('payment_method', 'cash')
        notes = request.form.get('notes', '').strip()

        payment = Payment(
            payment_number=generate_payment_number(),
            booking_id=booking.id,
            payer_id=current_user.id,
            payee_id=booking.equipment.owner.user.id,
            amount=booking.total_amount,
            payment_method=payment_method,
            payment_type='rental',
            status='completed',
            transaction_id=generate_payment_number(),
            notes=notes,
            paid_at=datetime.utcnow()
        )
        db.session.add(payment)

        booking.status = 'active'

        if booking.security_deposit > 0:
            deposit_payment = Payment(
                payment_number=generate_payment_number(),
                booking_id=booking.id,
                payer_id=current_user.id,
                payee_id=booking.equipment.owner.user.id,
                amount=booking.security_deposit,
                payment_method=payment_method,
                payment_type='deposit',
                status='completed',
                transaction_id=generate_payment_number(),
                notes='Security deposit',
                paid_at=datetime.utcnow()
            )
            db.session.add(deposit_payment)

        db.session.commit()

        create_notification(
            booking.equipment.owner.user.id,
            'Payment Received',
            f'Payment of {format_currency(booking.total_amount)} received for booking #{booking.booking_number}.',
            'success'
        )

        create_notification(
            current_user.id,
            'Payment Successful',
            f'Your payment of {format_currency(booking.total_amount)} for booking #{booking.booking_number} was successful.',
            'success'
        )

        flash('Payment successful! Your booking is now active.', 'success')
        return redirect(url_for('farmer.my_bookings'))

    return render_template('payment/make_payment.html', booking=booking, format_currency=format_currency)


@payment_bp.route('/payment/invoice/<int:payment_id>')
@login_required
def invoice(payment_id):
    payment = Payment.query.get_or_404(payment_id)
    if payment.payer_id != current_user.id and payment.payee_id != current_user.id:
        if not current_user.is_admin():
            flash('Unauthorized action.', 'danger')
            return redirect(url_for('farmer.dashboard'))

    return render_template('payment/invoice.html', payment=payment, format_currency=format_currency)
