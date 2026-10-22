"""
Reviews Blueprint
Handles customer reviews - submission, display, and admin moderation.
"""

from flask import Blueprint, flash, jsonify, redirect, render_template, request, session, url_for

from app.extensions import csrf
from database import mongo_db
from utils.auth import login_required

reviews_bp = Blueprint('reviews', __name__)


@reviews_bp.route('/reviews')
def reviews_page():
    """Public reviews page showing all reviews"""
    try:
        reviews = mongo_db.get_all_reviews()  # Fetch all reviews
        stats = mongo_db.get_review_stats()  # Get review statistics

        user_logged_in = 'user_id' in session  # Check if user is authenticated

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
        reviews = mongo_db.get_all_reviews()  # Fetch all reviews

        for review in reviews:
            review['_id'] = str(review['_id'])  # Convert MongoDB ObjectId to string
            # Convert timestamp to ISO format
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
        data = request.get_json()  # Parse JSON request body

        rating = data.get('rating')  # Get rating value
        comment = data.get('comment', '').strip()  # Get comment and remove whitespace

        if not rating or rating not in [1, 2, 3, 4, 5]:  # Validate rating range
            return jsonify({'error': 'Invalid rating. Must be 1-5'}), 400

        if not comment or len(comment) < 10:  # Validate minimum length
            return jsonify({'error': 'Comment must be at least 10 characters'}), 400

        if len(comment) > 500:  # Validate maximum length
            return jsonify({'error': 'Comment must be less than 500 characters'}), 400

        user_id = session.get('user_id')  # Get logged-in user ID
        user_name = session.get('user_name')  # Get user's name

        review_id = mongo_db.create_review(user_id, user_name, rating, comment)  # Save review to database

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
