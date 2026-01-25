"""
Reviews Blueprint
Handles customer reviews - submission, display, and admin moderation.
"""

from flask import Blueprint, render_template, request, session, redirect, url_for, flash, jsonify
from database import mongo_db
from utils.auth import login_required, admin_required
from app.extensions import csrf

reviews_bp = Blueprint('reviews', __name__)


@reviews_bp.route('/reviews')
def reviews_page():
    """Public reviews page showing all reviews"""
    try:
        reviews = mongo_db.get_all_reviews()
        stats = mongo_db.get_review_stats()
        
        user_logged_in = 'user_id' in session
        
        return render_template('reviews/reviews.html', 
                             reviews=reviews, 
                             stats=stats,
                             user_logged_in=user_logged_in)
    except Exception as e:
        flash(f'Error loading reviews: {str(e)}', 'error')
        return redirect(url_for('main.index'))


@reviews_bp.route('/api/reviews', methods=['GET'])
def api_get_reviews():
    """API endpoint to get all reviews"""
    try:
        reviews = mongo_db.get_all_reviews()
        
        for review in reviews:
            review['_id'] = str(review['_id'])
            review['created_at'] = review['created_at'].isoformat() if review.get('created_at') else None
        
        return jsonify(reviews), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@reviews_bp.route('/api/reviews/submit', methods=['POST'])
@csrf.exempt
@login_required
def api_submit_review():
    """API endpoint to submit a new review (login required)"""
    try:
        data = request.get_json()
        
        rating = data.get('rating')
        comment = data.get('comment', '').strip()
        
        if not rating or rating not in [1, 2, 3, 4, 5]:
            return jsonify({'error': 'Invalid rating. Must be 1-5'}), 400
        
        if not comment or len(comment) < 10:
            return jsonify({'error': 'Comment must be at least 10 characters'}), 400
        
        if len(comment) > 500:
            return jsonify({'error': 'Comment must be less than 500 characters'}), 400
        
        user_id = session.get('user_id')
        user_name = session.get('user_name')
        
        review_id = mongo_db.create_review(user_id, user_name, rating, comment)
        
        if review_id:
            return jsonify({
                'success': True,
                'review_id': review_id,
                'message': 'Review submitted successfully!'
            }), 201
        else:
            return jsonify({'error': 'Failed to create review'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 400
