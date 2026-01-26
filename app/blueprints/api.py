"""
API Blueprint
RESTful API endpoints for menu, orders, and cart operations.
"""

from flask import Blueprint, jsonify, request, session
from database import neon_db, mongo_db
from utils.auth import login_required
from app.extensions import csrf
from utils.cloud_storage import upload_menu_image
import json


api_bp = Blueprint('api', __name__)


# ============================================
# MENU API
# ============================================


@api_bp.route('/menu', methods=['GET'])
def get_menu():
    """API endpoint to get menu items"""
    try:
        category = request.args.get('category')  # Check for category filter
        
        if category:
            items = list(mongo_db.menu_collection.find({'category': category}))  # Filter by category
        else:
            items = mongo_db.get_all_menu_items()  # Get all items
        
        for item in items:
            item['_id'] = str(item['_id'])  # Convert MongoDB ObjectId to string
        
        return jsonify(items), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============================================
# ORDERS API
# ============================================


@api_bp.route('/orders', methods=['POST'])
@login_required
def create_order():
    """API endpoint to create a new order"""
    try:
        data = request.get_json()  # Parse JSON request body
        
        if not data.get('user_id') or not data.get('items'):  # Validate required fields
            return jsonify({'error': 'Missing user_id or items'}), 400
        
        user_id = data['user_id']
        table_number = data.get('table_number', 0)
        items = data['items']
        
        total_price = sum(item['price'] * item['quantity'] for item in items)  # Calculate total
        order_id = neon_db.create_order(  # Save order to database
            user_id=user_id,
            items=json.dumps(items),
            total_amount=total_price,
            table_number=table_number
        )
        
        return jsonify({
            'order_id': order_id,
            'total': total_price
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@api_bp.route('/orders/<int:user_id>', methods=['GET'])
@login_required
def get_user_orders(user_id):
    """API endpoint to get all orders for a user"""
    try:
        orders = neon_db.get_user_orders(user_id)  # Fetch user's orders
        
        orders_list = []
        for order in orders:
            orders_list.append({  # Format order data
                'order_id': order['order_id'],
                'total_price': float(order['total_amount']),
                'status': order['status'],
                'created_at': str(order['order_date'])
            })
        
        return jsonify(orders_list), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_bp.route('/orders/<int:order_id>', methods=['PUT'])
@login_required
def update_order(order_id):
    """API endpoint to update order status"""
    try:
        data = request.get_json()  # Parse JSON request body
        status = data.get('status')  # Get new status
        
        if not status:  # Validate status provided
            return jsonify({'error': 'Status required'}), 400
        
        neon_db.update_order_status(order_id, status)  # Update in database
        
        return jsonify({'status': 'updated', 'order_id': order_id}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============================================
# CART API
# ============================================


@api_bp.route('/cart/add', methods=['POST'])
@login_required
def add_to_cart():
    """API endpoint to add item to shopping cart"""
    data = request.get_json()  # Parse JSON request
    
    if 'cart' not in session:  # Initialize cart if needed
        session['cart'] = {}
    
    cart = session['cart']
    item_id = str(data.get('item_id'))
    
    if item_id in cart:
        cart[item_id]['quantity'] += 1  # Increment quantity if exists
    else:
        cart[item_id] = {  # Add new item
            'item_id': item_id,
            'name': data.get('name'),
            'price': float(data.get('price')),
            'quantity': int(data.get('quantity', 1))
        }
    
    session['cart'] = cart
    session.modified = True  # Mark session as modified
    
    return jsonify({'success': True, 'cart_count': len(cart)}), 200


@api_bp.route('/cart/count', methods=['GET'])
def cart_count():
    """API endpoint to get cart item count"""
    if 'cart' not in session:  # Return 0 if cart doesn't exist
        return jsonify({'count': 0}), 200
    
    total_items = sum(item['quantity'] for item in session['cart'].values())  # Sum all quantities
    return jsonify({'count': total_items}), 200


@api_bp.route('/cart/remove/<item_id>', methods=['DELETE'])
@login_required
def remove_from_cart(item_id):
    """API endpoint to remove item from cart"""
    if 'cart' in session and item_id in session['cart']:  # Check if item exists
        del session['cart'][item_id]  # Remove item
        session.modified = True  # Mark session as modified
        return jsonify({'success': True}), 200
    return jsonify({'success': False}), 400


@api_bp.route('/cart/update', methods=['PUT'])
@login_required
def update_cart():
    """API endpoint to update item quantity in cart"""
    data = request.get_json()  # Parse JSON request
    item_id = str(data.get('item_id'))
    quantity = int(data.get('quantity'))
    
    if 'cart' in session and item_id in session['cart']:  # Check if item exists in cart
        if quantity > 0:
            session['cart'][item_id]['quantity'] = quantity  # Update quantity
        else:
            del session['cart'][item_id]  # Delete if quantity is 0 or less
        session.modified = True  # Mark session as modified
        return jsonify({'success': True}), 200
    
    return jsonify({'success': False}), 400


@api_bp.route('/cart/clear', methods=['POST'])
@login_required
def clear_cart():
    """API endpoint to clear the shopping cart"""
    session['cart'] = {}  # Empty cart
    session.modified = True  # Mark session as modified
    return jsonify({'success': True}), 200


# ============================================
# IMAGE UPLOAD API
# ============================================


@api_bp.route('/upload-image', methods=['POST'])
def upload_image():
    """API endpoint to upload menu item image to Cloud Storage"""
    try:
        if not session.get('is_admin'):  # Verify admin access
            return jsonify({'success': False, 'error': 'Admin access required'}), 403
        
        if 'image' not in request.files:  # Validate file exists
            return jsonify({'success': False, 'error': 'No image file provided'}), 400
        
        file = request.files['image']
        
        if file.filename == '':  # Validate filename not empty
            return jsonify({'success': False, 'error': 'No file selected'}), 400
        
        public_url = upload_menu_image(file)  # Upload to cloud storage
        
        return jsonify({
            'success': True,
            'url': public_url,
            'message': 'Image uploaded successfully'
        }), 200
        
    except ValueError as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    except Exception as e:
        print(f"Upload error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': f'Upload failed: {str(e)}'}), 500
