from dotenv import load_dotenv
load_dotenv()

import os
from flask import Flask, render_template, jsonify, request, session, redirect, url_for, flash
from database import neon_db, mongo_db
from functools import wraps



app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

# ============================================
# AUTHENTICATION DECORATOR
# ============================================

def login_required(f):
    """Decorator to require login for routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login to access this page', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


# ============================================
# WEB ROUTES (HTML Pages)
# ============================================

@app.route('/')
def home():
    """Home page"""
    return render_template('index.html')

@app.route('/menu')
def menu_page():
    """Menu display page"""
    try:
        items = mongo_db.get_all_menu_items()
        return render_template('menu.html', items=items)
    except Exception as e:
        return f"Error loading menu: {str(e)}", 500

@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration"""
    if request.method == 'POST':
        email = request.form.get('email')
        name = request.form.get('name')
        phone = request.form.get('phone')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        # Validation
        if not all([email, name, phone, password, confirm_password]):
            flash('All fields are required', 'error')
            return render_template('register.html')
        
        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return render_template('register.html')
        
        # Check if user exists
        existing_user = neon_db.get_user_by_email(email)
        if existing_user:
            flash('Email already registered', 'error')
            return render_template('register.html')
        
        # Create user
        user_id = neon_db.register_user(email, name, phone, password)
        
        if user_id:
            session['user_id'] = user_id
            session['user_name'] = name
            flash('Registration successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Registration failed. Please try again.', 'error')
            return render_template('register.html')
    
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        if not email or not password:
            flash('Email and password are required', 'error')
            return render_template('login.html')
        
        user = neon_db.authenticate_user(email, password)
        
        if user:
            session['user_id'] = user['user_id']
            session['user_name'] = user['name']
            flash(f'Welcome back, {user["name"]}!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password', 'error')
            return render_template('login.html')
    
    return render_template('login.html')


@app.route('/logout')
def logout():
    """User logout"""
    session.clear()
    flash('You have been logged out', 'success')
    return redirect(url_for('home'))


@app.route('/dashboard')
@login_required
def dashboard():
    """User dashboard"""
    user_id = session.get('user_id')
    user = neon_db.get_user_by_id(user_id)
    orders = neon_db.get_all_orders(user_id)
    
    return render_template('dashboard.html', user=user, orders=orders)

@app.route('/cart')
@login_required
def cart():
    """Shopping cart page"""
    cart_items = session.get('cart', [])
    total = sum(item['price'] * item['quantity'] for item in cart_items)
    return render_template('cart.html', cart_items=cart_items, total=total)

@app.route('/checkout', methods=['POST'])
@login_required
def checkout():
    """Process checkout and create order"""
    cart_items = session.get('cart', [])
    
    if not cart_items:
        flash('Your cart is empty', 'error')
        return redirect(url_for('menu_page'))
    
    # Calculate total
    total_price = sum(item['price'] * item['quantity'] for item in cart_items)
    
    # Prepare items for database
    items = []
    for item in cart_items:
        items.append({
            'item_id': item['item_id'],
            'name': item['name'],
            'price': item['price'],
            'quantity': item['quantity']
        })
    
    # Create order in database
    try:
        user_id = session.get('user_id')
        table_number = 0  # Can be updated later
        order_id = neon_db.create_order(user_id, table_number, total_price, items)
        
        # Clear cart after successful order
        session['cart'] = []
        session.modified = True
        
        flash(f'Order #{order_id} placed successfully! Total: £{total_price:.2f}', 'success')
        return redirect(url_for('dashboard'))
        
    except Exception as e:
        flash(f'Error placing order: {str(e)}', 'error')
        return redirect(url_for('cart'))


# ============================================
# API ROUTES (JSON Responses)
# ============================================

@app.route('/api/menu', methods=['GET'])
def api_get_menu():
    """API: Get all menu items or filter by category"""
    try:
        category = request.args.get('category')
        
        if category:
            items = mongo_db.get_menu_by_category(category)
        else:
            items = mongo_db.get_all_menu_items()
        
        return jsonify(items), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/orders', methods=['POST'])
def api_create_order():
    """API: Create a new order"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data.get('user_id') or not data.get('items'):
            return jsonify({'error': 'Missing user_id or items'}), 400
        
        user_id = data['user_id']
        table_number = data.get('table_number', 0)
        items = data['items']
        
        # Calculate total price
        total_price = sum(item['price'] * item['quantity'] for item in items)
        
        # Create order in database
        order_id = neon_db.create_order(user_id, table_number, total_price, items)
        
        return jsonify({
            'success': True,
            'order_id': order_id,
            'total_price': total_price
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/orders/<int:user_id>', methods=['GET'])
def api_get_user_orders(user_id):
    """API: Get all orders for a user"""
    try:
        orders = neon_db.get_all_orders(user_id)
        
        # Format as JSON
        orders_list = []
        for order in orders:
            orders_list.append({
                'order_id': order[0],
                'total_price': float(order[1]),
                'status': order[2],
                'created_at': str(order[3])
            })
        
        return jsonify(orders_list), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/orders/<int:order_id>', methods=['PUT'])
def api_update_order(order_id):
    """API: Update order status"""
    try:
        data = request.get_json()
        status = data.get('status')
        
        if not status:
            return jsonify({'error': 'Status required'}), 400
        
        neon_db.update_order_status(order_id, status)
        
        return jsonify({'status': 'updated', 'order_id': order_id}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/cart/add', methods=['POST'])
@login_required
def api_add_to_cart():
    """Add item to shopping cart"""
    data = request.get_json()
    
    # Initialize cart in session if it doesn't exist
    if 'cart' not in session:
        session['cart'] = []
    
    cart = session['cart']
    item_id = str(data.get('item_id'))
    
    # Check if item already in cart
    found = False
    for item in cart:
        if item['item_id'] == item_id:
            item['quantity'] += 1
            found = True
            break
    
    # Add new item if not found
    if not found:
        cart.append({
            'item_id': item_id,
            'name': data.get('name'),
            'price': float(data.get('price')),
            'quantity': int(data.get('quantity', 1))
        })
    
    session['cart'] = cart
    session.modified = True
    
    return jsonify({'success': True, 'cart_count': len(cart)}), 200


@app.route('/api/cart/count', methods=['GET'])
def api_cart_count():
    """Get cart item count"""
    if 'cart' not in session:
        return jsonify({'count': 0}), 200
    
    total_items = sum(item['quantity'] for item in session['cart'])
    return jsonify({'count': total_items}), 200


@app.route('/api/cart/remove/<item_id>', methods=['DELETE'])
@login_required
def api_remove_from_cart(item_id):
    """Remove item from cart"""
    if 'cart' in session:
        session['cart'] = [item for item in session['cart'] if item['item_id'] != item_id]
        session.modified = True
        return jsonify({'success': True}), 200
    return jsonify({'success': False}), 400


@app.route('/api/cart/update', methods=['PUT'])
@login_required
def api_update_cart():
    """Update item quantity in cart"""
    data = request.get_json()
    item_id = str(data.get('item_id'))
    quantity = int(data.get('quantity'))
    
    if 'cart' in session:
        for item in session['cart']:
            if item['item_id'] == item_id:
                if quantity > 0:
                    item['quantity'] = quantity
                else:
                    session['cart'].remove(item)
                break
        session.modified = True
        return jsonify({'success': True}), 200
    
    return jsonify({'success': False}), 400


@app.route('/api/cart/clear', methods=['POST'])
@login_required
def api_clear_cart():
    """Clear the shopping cart"""
    session['cart'] = []
    session.modified = True
    return jsonify({'success': True}), 200

# ============================================
# ERROR HANDLERS
# ============================================

@app.errorhandler(404)
def not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def server_error(e):
    return "Internal server error", 500

# ============================================
# RUN APP
# ============================================

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)
