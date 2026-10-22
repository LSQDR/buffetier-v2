"""
Orders Blueprint
Handles cart, checkout, and order management
"""

import json

from flask import Blueprint, flash, redirect, render_template, session, url_for

from database.neon_db import create_order, get_user_by_id, get_user_orders
from utils.auth import login_required
from utils.email import send_order_confirmation

orders_bp = Blueprint('orders', __name__)


@orders_bp.route('/cart')
@login_required
def cart():
    """Display shopping cart"""
    cart_items = session.get('cart', {})
    total = sum(item['price'] * item['quantity'] for item in cart_items.values())

    return render_template('orders/cart.html',
                         cart_items=list(cart_items.values()),
                         total=total)


@orders_bp.route('/checkout', methods=['POST'])
@login_required
def checkout():
    """Process order checkout"""
    user_id = session.get('user_id')
    cart = session.get('cart', {})

    if not cart:
        flash('Your cart is empty', 'error')
        return redirect(url_for('main.menu'))

    # Calculate total
    total = sum(item['price'] * item['quantity'] for item in cart.values())

    # Prepare items for database
    items_json = json.dumps([{
        'item_id': item['item_id'],
        'name': item['name'],
        'price': item['price'],
        'quantity': item['quantity']
    } for item in cart.values()])

    # Create order
    order_id = create_order(user_id, items_json, total)

    if order_id:
        # Get user info for email
        user = get_user_by_id(user_id)

        # Send confirmation email
        if user and user.get('email'):
            order_details = {
                'order_id': order_id,
                'total_amount': total,
                'items': list(cart.values()),
                'status': 'pending'
            }

            email_sent = send_order_confirmation(
                to_email=user['email'],
                user_name=user['name'],
                order_details=order_details
            )

            if email_sent:
                print(f" Confirmation email sent to {user['email']}")
            else:
                print(f" Email send failed for order #{order_id}")

        # Clear cart
        session['cart'] = {}
        flash(f'Order #{order_id} placed successfully! Check your email for confirmation.', 'success')
        return redirect(url_for('orders.dashboard'))
    else:
        flash('Order failed. Please try again.', 'error')
        return redirect(url_for('orders.cart'))


@orders_bp.route('/dashboard')
@login_required
def dashboard():
    """User order dashboard"""
    if 'user_id' not in session:
        flash('Please login to view your orders', 'error')
        return redirect(url_for('auth.login'))

    user_id = session['user_id']
    user = get_user_by_id(user_id)
    orders = get_user_orders(user_id)

    return render_template('orders/dashboard.html', user=user, orders=orders)
