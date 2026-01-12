import os
from flask import Flask, render_template, jsonify, request
from database import neon_db, mongo_db

app = Flask(__name__)

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
