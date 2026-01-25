"""
API Blueprint
RESTful API endpoints for menu, orders, and cart operations.
"""

from flask import Blueprint, jsonify, request, session
from database import neon_db, mongo_db
from utils.auth import login_required
from app.extensions import csrf
from utils.cloud_storage import upload_menu_image


api_bp = Blueprint('api', __name__)


# ============================================
# MENU API
# ============================================

@api_bp.route('/menu', methods=['GET'])
def get_menu():
    """API endpoint to get menu items"""
    try:
        category = request.args.get('category')
        
        if category:
            items = mongo_db.get_menu_by_category(category)
        else:
            items = mongo_db.get_all_menu_items()
        
        # Convert ObjectId to string for JSON serialization
        for item in items:
            item['_id'] = str(item['_id'])
        
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
        data = request.get_json()
        
        if not data.get('user_id') or not data.get('items'):
            return jsonify({'error': 'Missing user_id or items'}), 400
        
        user_id = data['user_id']
        table_number = data.get('table_number', 0)
        items = data['items']
        
        total_price = sum(item['price'] * item['quantity'] for item in items)
        order_id = neon_db.create_order(user_id, table_number, total_price, items)
        
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
        orders = neon_db.get_all_orders(user_id)
        
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


@api_bp.route('/orders/<int:order_id>', methods=['PUT'])
@login_required
def update_order(order_id):
    """API endpoint to update order status"""
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
# CART API
# ============================================

@api_bp.route('/cart/add', methods=['POST'])
@login_required
def add_to_cart():
    """API endpoint to add item to shopping cart"""
    data = request.get_json()
    
    if 'cart' not in session:
        session['cart'] = {}  
    
    cart = session['cart']
    item_id = str(data.get('item_id'))
    
    # Check if item already in cart
    if item_id in cart:
        cart[item_id]['quantity'] += 1
    else:
        cart[item_id] = {
            'item_id': item_id,
            'name': data.get('name'),
            'price': float(data.get('price')),
            'quantity': int(data.get('quantity', 1))
        }
    
    session['cart'] = cart
    session.modified = True
    
    return jsonify({'success': True, 'cart_count': len(cart)}), 200


@api_bp.route('/cart/count', methods=['GET'])
def cart_count():
    """API endpoint to get cart item count"""
    if 'cart' not in session:
        return jsonify({'count': 0}), 200
    
    total_items = sum(item['quantity'] for item in session['cart'].values())
    return jsonify({'count': total_items}), 200


@api_bp.route('/cart/remove/<item_id>', methods=['DELETE'])
@login_required
def remove_from_cart(item_id):
    """API endpoint to remove item from cart"""
    if 'cart' in session and item_id in session['cart']:
        del session['cart'][item_id]
        session.modified = True
        return jsonify({'success': True}), 200
    return jsonify({'success': False}), 400


@api_bp.route('/cart/update', methods=['PUT'])
@login_required
def update_cart():
    """API endpoint to update item quantity in cart"""
    data = request.get_json()
    item_id = str(data.get('item_id'))
    quantity = int(data.get('quantity'))
    
    if 'cart' in session and item_id in session['cart']:
        if quantity > 0:
            session['cart'][item_id]['quantity'] = quantity
        else:
            del session['cart'][item_id]
        session.modified = True
        return jsonify({'success': True}), 200
    
    return jsonify({'success': False}), 400


@api_bp.route('/cart/clear', methods=['POST'])
@login_required
def clear_cart():
    """API endpoint to clear the shopping cart"""
    session['cart'] = {}  
    session.modified = True
    return jsonify({'success': True}), 200


# ============================================
# IMAGE UPLOAD API
# ============================================

@api_bp.route('/upload-image', methods=['POST'])
def upload_image():
    """API endpoint to upload menu item image to Cloud Storage"""
    try:
        # Check if admin
        if not session.get('is_admin'):
            return jsonify({'success': False, 'error': 'Admin access required'}), 403
        
        if 'image' not in request.files:
            return jsonify({'success': False, 'error': 'No image file provided'}), 400
        
        file = request.files['image']
        
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'}), 400
        
        # Upload to Cloud Storage
        public_url = upload_menu_image(file)
        
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

