"""
Admin Blueprint
Admin dashboard, order management, menu CRUD, and review moderation.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
from database import neon_db, mongo_db
from utils.auth import admin_required
from utils.cloud_storage import upload_menu_image, delete_menu_image
from utils.email import send_order_status_update
from app.extensions import csrf

admin_bp = Blueprint('admin', __name__)


# ============================================
# ADMIN DASHBOARD
# ============================================

@admin_bp.route('/')
@admin_required
def admin_dashboard():
    """Admin dashboard showing all orders and stats"""
    orders = neon_db.get_all_orders_admin()
    stats = neon_db.get_order_stats()
    return render_template('admin/dashboard.html', orders=orders, stats=stats)


# ============================================
# ORDER MANAGEMENT
# ============================================

@admin_bp.route('/order/<int:order_id>/update', methods=['POST'])
@admin_required
def update_order_status_route(order_id):
    """Update order status and send email notification"""
    try:
        new_status = request.form.get('status')
        
        if neon_db.update_order_status(order_id, new_status):
            try:
                order = neon_db.get_order_by_id(order_id)
                if order:
                    user = neon_db.get_user_by_id(order['user_id'])
                    if user:
                        email_sent = send_order_status_update(
                            to_email=user['email'],
                            user_name=user['name'],
                            order_id=order_id,
                            new_status=new_status
                        )
                        
                        if email_sent:
                            flash(f'Order #{order_id} updated to {new_status} and email sent', 'success')
                        else:
                            flash(f'Order #{order_id} updated to {new_status} (email failed)', 'warning')
                    else:
                        flash(f'Order #{order_id} updated to {new_status}', 'success')
                else:
                    flash(f'Order #{order_id} updated to {new_status}', 'success')
                    
            except Exception as email_error:
                print(f"Email notification failed: {email_error}")
                flash(f'Order #{order_id} updated to {new_status}', 'success')
        else:
            flash(f'Failed to update order #{order_id}', 'error')
            
        return redirect(url_for('admin.admin_dashboard'))
        
    except Exception as e:
        flash(f'Error updating order: {str(e)}', 'error')
        return redirect(url_for('admin.admin_dashboard'))


@admin_bp.route('/order/<int:order_id>/delete', methods=['POST'])
@admin_required
def delete_order_route(order_id):
    """Delete an order and its items"""
    neon_db.delete_order_with_items(order_id)
    flash(f'Order #{order_id} deleted', 'success')
    return redirect(url_for('admin.admin_dashboard'))


# ============================================
# MENU MANAGEMENT
# ============================================

@admin_bp.route('/menu')
@admin_required
def admin_menu():
    """Admin menu management page"""
    menu_items = mongo_db.get_all_menu_items()
    return render_template('admin/menu.html', menu_items=menu_items)


@admin_bp.route('/menu/create', methods=['POST'])
@admin_required
def create_menu_item_route():
    """Create new menu item"""
    mongo_db.create_menu_item(
        item_id=request.form.get('item_id'),
        name=request.form.get('name'),
        category=request.form.get('category'),
        description=request.form.get('description'),
        price=float(request.form.get('price')),
        available=request.form.get('available') == 'on',
        image_url=request.form.get('image_url', '')
    )
    flash('Menu item created', 'success')
    return redirect(url_for('admin.admin_menu'))


@admin_bp.route('/menu/<item_id>/update', methods=['POST'])
@admin_required
def update_menu_item_route(item_id):
    """Update existing menu item"""
    mongo_db.update_menu_item(
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
    return redirect(url_for('admin.admin_menu'))


@admin_bp.route('/menu/<item_id>/delete', methods=['POST'])
@admin_required
def delete_menu_item_route(item_id):
    """Delete menu item"""
    mongo_db.delete_menu_item(item_id)
    flash('Menu item deleted', 'success')
    return redirect(url_for('admin.admin_menu'))


# ============================================
# REVIEW MANAGEMENT
# ============================================

@admin_bp.route('/reviews')
@admin_required
def admin_reviews():
    """Admin reviews management page"""
    reviews = mongo_db.get_all_reviews()
    stats = mongo_db.get_review_stats()
    return render_template('admin/reviews.html', reviews=reviews, stats=stats)


@admin_bp.route('/review/<review_id>/delete', methods=['POST'])
@admin_required
def delete_review_route(review_id):
    """Delete a review"""
    mongo_db.delete_review(review_id)
    flash('Review deleted', 'success')
    return redirect(url_for('admin.admin_reviews'))


# ============================================
# CLOUD STORAGE API
# ============================================

@admin_bp.route('/api/upload-image', methods=['POST'])
@admin_required
def upload_image():
    """Upload menu item image to Cloud Storage"""
    try:
        if 'image' not in request.files:
            return jsonify({'error': 'No image file provided'}), 400
        
        file = request.files['image']
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        image_url = upload_menu_image(file)
        
        return jsonify({
            'success': True,
            'url': image_url
        }), 200
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': f'Upload failed: {str(e)}'}), 500


@admin_bp.route('/api/delete-image', methods=['POST'])
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
