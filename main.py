from dotenv import load_dotenv
load_dotenv()

import os
from flask import Flask, render_template, jsonify, request, session, redirect, url_for, flash
from database import neon_db, mongo_db 
from datetime import datetime, timedelta
from utils.auth import login_required, admin_required
from database.neon_db import get_all_orders_admin, get_order_stats, update_order_status, delete_order_with_items
from database.mongo_db import get_all_menu_items, create_menu_item, update_menu_item, delete_menu_item, get_all_reviews, delete_review
from utils.cloud_storage import upload_menu_image, delete_menu_image
from utils.secrets import get_secret


# ============================================
# APPLICATION SETUP
# ============================================

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

menu_cache = {
    'items': None,
    'timestamp': None,
    'ttl': 300  # Cache for 5 minutes (300 seconds)
}


# ============================================
# PUBLIC WEB ROUTES
# ============================================

@app.route('/')
def index():
    """Render home page."""
    return render_template('index.html')


@app.route('/menu')
def menu_page():
    """
    Display restaurant menu page with caching.
    
    Fetches all menu items from MongoDB and caches them for 5 minutes
    to reduce connection latency.
    
    Returns:
        Rendered menu template with items
    """
    global menu_cache
    
    try:
        # Check if cache is valid
        now = datetime.now()
        cache_valid = (
            menu_cache['items'] is not None and 
            menu_cache['timestamp'] is not None and 
            (now - menu_cache['timestamp']).seconds < menu_cache['ttl']
        )
        
        if not cache_valid:
            # Fetch fresh data from MongoDB
            items = mongo_db.get_all_menu_items()
            menu_cache['items'] = items
            menu_cache['timestamp'] = now
        else:
            # Use cached data
            items = menu_cache['items']
        
        return render_template('menu.html', items=items)
    except Exception as e:
        flash(f'Error loading menu: {str(e)}', 'error')
        return redirect(url_for('index'))



# ============================================
# AUTHENTICATION ROUTES
# ============================================

@app.route('/register', methods=['GET', 'POST'])
def register():
    """
    Handle user registration.
    
    GET: Display registration form
    POST: Process registration and create user account
    
    Returns:
        Registration template or redirect to dashboard
    """
    if request.method == 'POST':
        email = request.form.get('email')
        name = request.form.get('name')
        phone = request.form.get('phone')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        # Validate input
        if not all([email, name, phone, password, confirm_password]):
            flash('All fields are required', 'error')
            return render_template('register.html')
        
        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return render_template('register.html')
        
        # Check if user already exists
        existing_user = neon_db.get_user_by_email(email)
        if existing_user:
            flash('Email already registered', 'error')
            return render_template('register.html')
        
        # Create new user
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
    """Handle user login"""
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        # Use authenticate_user from neon_db
        user = neon_db.authenticate_user(email, password)
        
        if user:
            # Set session variables
            session['user_id'] = user['user_id']
            session['user_name'] = user['name']
            session['is_admin'] = user.get('is_admin', False)  # Add admin status
            
            flash('Login successful!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid email or password', 'danger')
            return redirect(url_for('login'))
    
    # GET request - show login form
    return render_template('login.html')



@app.route('/logout')
def logout():
    """
    Log out user and clear session.
    
    Returns:
        Redirect to home page
    """
    session.clear()
    flash('You have been logged out', 'success')
    return redirect(url_for('index'))


# ============================================
# PROTECTED USER ROUTES
# ============================================

@app.route('/dashboard')
@login_required
def dashboard():
    """
    Display user dashboard with order history.
    
    Returns:
        Dashboard template with user info and orders
    """
    user_id = session.get('user_id')
    user = neon_db.get_user_by_id(user_id)
    orders = neon_db.get_all_orders(user_id)
    
    return render_template('dashboard.html', user=user, orders=orders)


@app.route('/cart')
@login_required
def cart():
    """
    Display shopping cart page.
    
    Returns:
        Cart template with items and total
    """
    cart_items = session.get('cart', [])
    total = sum(item['price'] * item['quantity'] for item in cart_items)
    return render_template('cart.html', cart_items=cart_items, total=total)


@app.route('/checkout', methods=['POST'])
@login_required
def checkout():
    """
    Process checkout and create order.
    
    Validates cart, creates order in database, and clears cart.
    
    Returns:
        Redirect to dashboard with success message or cart with error
    """
    cart_items = session.get('cart', [])
    
    if not cart_items:
        flash('Your cart is empty', 'error')
        return redirect(url_for('menu_page'))
    
    # Calculate total price
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
        table_number = 0  # Can be updated later with table selection
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
# API ROUTES - MENU
# ============================================

@app.route('/api/menu', methods=['GET'])
def api_get_menu():
    """
    API endpoint to get menu items.
    
    Query Parameters:
        category (optional): Filter by category
    
    Returns:
        JSON array of menu items
    """
    try:
        category = request.args.get('category')
        
        if category:
            items = mongo_db.get_menu_by_category(category)
        else:
            items = mongo_db.get_all_menu_items()
        
        return jsonify(items), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============================================
# API ROUTES - ORDERS
# ============================================

@app.route('/api/orders', methods=['POST'])
def api_create_order():
    """
    API endpoint to create a new order.
    
    Request Body:
        user_id: int
        table_number: int (optional)
        items: list of {item_id, name, price, quantity}
    
    Returns:
        JSON with order_id and total price
    """
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
            'order_id': order_id,
            'total': total_price
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@app.route('/api/orders/<int:user_id>', methods=['GET'])
def api_get_user_orders(user_id):
    """
    API endpoint to get all orders for a user.
    
    Args:
        user_id: User ID
    
    Returns:
        JSON array of orders
    """
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
    """
    API endpoint to update order status.
    
    Args:
        order_id: Order ID
    
    Request Body:
        status: New status string
    
    Returns:
        JSON confirmation
    """
    try:
        data = request.get_json()
        status = data.get('status')
        
        if not status:
            return jsonify({'error': 'Status required'}), 400
        
        neon_db.update_order_status(order_id, status)
        
        return jsonify({'status': 'updated', 'order_id': order_id}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============================================
# API ROUTES - SHOPPING CART
# ============================================

@app.route('/api/cart/add', methods=['POST'])
@login_required
def api_add_to_cart():
    """
    API endpoint to add item to shopping cart.
    
    Request Body:
        item_id: string
        name: string
        price: float
        quantity: int
    
    Returns:
        JSON with success status and cart count
    """
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
    """
    API endpoint to get cart item count.
    
    Returns:
        JSON with total item count
    """
    if 'cart' not in session:
        return jsonify({'count': 0}), 200
    
    total_items = sum(item['quantity'] for item in session['cart'])
    return jsonify({'count': total_items}), 200


@app.route('/api/cart/remove/<item_id>', methods=['DELETE'])
@login_required
def api_remove_from_cart(item_id):
    """
    API endpoint to remove item from cart.
    
    Args:
        item_id: Item ID to remove
    
    Returns:
        JSON with success status
    """
    if 'cart' in session:
        session['cart'] = [item for item in session['cart'] if item['item_id'] != item_id]
        session.modified = True
        return jsonify({'success': True}), 200
    return jsonify({'success': False}), 400


@app.route('/api/cart/update', methods=['PUT'])
@login_required
def api_update_cart():
    """
    API endpoint to update item quantity in cart.
    
    Request Body:
        item_id: string
        quantity: int
    
    Returns:
        JSON with success status
    """
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
    """
    API endpoint to clear the shopping cart.
    
    Returns:
        JSON with success status
    """
    session['cart'] = []
    session.modified = True
    return jsonify({'success': True}), 200


# ============================================
# ADMIN ROUTES
# ============================================

# Admin Dashboard
@app.route('/admin')
@admin_required
def admin_dashboard():
    """Admin dashboard showing all orders and stats"""
    orders = get_all_orders_admin()
    stats = get_order_stats()
    return render_template('admin/dashboard.html', orders=orders, stats=stats)

# Update Order Status
@app.route('/admin/order/<int:order_id>/update', methods=['POST'])
@admin_required
def update_order_status_route(order_id):
    """Update order status"""
    new_status = request.form.get('status')
    update_order_status(order_id, new_status)
    flash(f'Order #{order_id} updated to {new_status}', 'success')
    return redirect(url_for('admin_dashboard'))

# Delete Order
@app.route('/admin/order/<int:order_id>/delete', methods=['POST'])
@admin_required
def delete_order_route(order_id):
    """Delete an order and its items"""
    delete_order_with_items(order_id)
    flash(f'Order #{order_id} deleted', 'success')
    return redirect(url_for('admin_dashboard'))

# Menu Management Page
@app.route('/admin/menu')
@admin_required
def admin_menu():
    """Admin menu management page"""
    menu_items = get_all_menu_items()
    return render_template('admin/menu.html', menu_items=menu_items)

# Create Menu Item
@app.route('/admin/menu/create', methods=['POST'])
@admin_required
def create_menu_item_route():
    """Create new menu item"""
    create_menu_item(
        item_id=request.form.get('item_id'),
        name=request.form.get('name'),
        category=request.form.get('category'),
        description=request.form.get('description'),
        price=float(request.form.get('price')),
        available=request.form.get('available') == 'on',
        image_url=request.form.get('image_url', '')
    )
    flash(f'Menu item created', 'success')
    return redirect(url_for('admin_menu'))

# Update Menu Item
@app.route('/admin/menu/<item_id>/update', methods=['POST'])
@admin_required
def update_menu_item_route(item_id):
    """Update existing menu item"""
    update_menu_item(
        menu_id=item_id,
        item_id=request.form.get('item_id'),
        name=request.form.get('name'),
        category=request.form.get('category'),
        description=request.form.get('description'),
        price=float(request.form.get('price')),
        available=request.form.get('available') == 'on',
        image_url=request.form.get('image_url', '')
    )
    flash('Menu item updated', 'success')
    return redirect(url_for('admin_menu'))

# Delete Menu Item
@app.route('/admin/menu/<item_id>/delete', methods=['POST'])
@admin_required
def delete_menu_item_route(item_id):
    """Delete menu item"""
    delete_menu_item(item_id)
    flash('Menu item deleted', 'success')
    return redirect(url_for('admin_menu'))

# Reviews Management (Bonus)
@app.route('/admin/reviews')
@admin_required
def admin_reviews():
    """Admin reviews management page"""
    reviews = get_all_reviews()
    return render_template('admin/reviews.html', reviews=reviews)

# Delete Review
@app.route('/admin/review/<review_id>/delete', methods=['POST'])
@admin_required
def delete_review_route(review_id):
    """Delete a review"""
    delete_review(review_id)
    flash('Review deleted', 'success')
    return redirect(url_for('admin_reviews'))



# ============================================
# CLOUD STORAGE API ROUTES
# ============================================

@app.route('/api/upload-image', methods=['POST'])
@admin_required
def upload_image():
    """Upload menu item image to Cloud Storage"""
    try:
        if 'image' not in request.files:
            return jsonify({'error': 'No image file provided'}), 400
        
        file = request.files['image']
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Upload to Cloud Storage
        image_url = upload_menu_image(file)
        
        return jsonify({
            'success': True,
            'url': image_url
        }), 200
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': f'Upload failed: {str(e)}'}), 500


@app.route('/api/delete-image', methods=['POST'])
@admin_required
def delete_image():
    """Delete image from Cloud Storage"""
    try:
        data = request.get_json()
        image_url = data.get('image_url')
        
        if not image_url:
            return jsonify({'error': 'No image URL provided'}), 400
        
        success = delete_menu_image(image_url)
        
        if success:
            return jsonify({'success': True}), 200
        else:
            return jsonify({'error': 'Failed to delete image'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============================================
# ERROR HANDLERS
# ============================================

@app.errorhandler(404)
def not_found(e):
    """Handle 404 errors."""
    return render_template('404.html'), 404


@app.errorhandler(500)
def server_error(e):
    """Handle 500 errors."""
    return "Internal server error", 500


@app.route('/api/upload-test', methods=['POST'])
@admin_required
def upload_test():
    """Debug upload to see exact error"""
    try:
        print("=== UPLOAD DEBUG ===")
        print(f"Files in request: {request.files}")
        
        if 'image' not in request.files:
            return jsonify({'error': 'No image in request'}), 400
        
        file = request.files['image']
        print(f"File object: {file}")
        print(f"Filename: {file.filename}")
        print(f"Content type: {file.content_type}")
        
        # Try to read file
        content = file.read()
        print(f"File size: {len(content)} bytes")
        
        # Reset file pointer
        file.seek(0)
        
        # Now try upload
        from utils.cloud_storage import upload_menu_image
        url = upload_menu_image(file)
        
        return jsonify({'success': True, 'url': url}), 200
        
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"ERROR: {error_trace}")
        return jsonify({'error': str(e), 'trace': error_trace}), 500
        
# ============================================
# APPLICATION ENTRY POINT
# ============================================

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)
