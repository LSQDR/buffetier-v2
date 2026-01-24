"""
Main Blueprint
Handles home page, menu display, and general public routes.
"""

from flask import Blueprint, render_template, redirect, url_for, flash, session
from database import mongo_db
from utils.secrets import get_secret
from datetime import datetime

# Create blueprint
main_bp = Blueprint('main', __name__)

# Menu cache
menu_cache = {
    'items': None,
    'timestamp': None,
    'ttl': 300  # 5 minutes
}


@main_bp.route('/')
def index():
    """Render home page"""
    return render_template('index.html')


@main_bp.route('/menu')
def menu():
    """
    Display restaurant menu page with caching.
    
    Fetches all menu items from MongoDB and caches them for 5 minutes
    to reduce connection latency.
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
            items = mongo_db.get_all_menu_items()
            menu_cache['items'] = items
            menu_cache['timestamp'] = now
        else:
            items = menu_cache['items']
        
        return render_template('menu/menu.html', items=items)
    except Exception as e:
        flash(f'Error loading menu: {str(e)}', 'error')
        return redirect(url_for('main.index'))


@main_bp.route('/location')
def location():
    """Location page with Google Maps"""
    try:
        maps_api_key = get_secret('maps-api-key')
        return render_template('location.html', maps_api_key=maps_api_key)
    except Exception as e:
        print(f"Error loading location page: {str(e)}")
        flash('Unable to load map', 'error')
        return redirect(url_for('main.index'))
