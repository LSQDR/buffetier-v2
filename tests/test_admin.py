import os
import sys

import pytest

from main import app

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dotenv import load_dotenv

load_dotenv()


@pytest.fixture
def client():
    """Create test client"""
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    with app.test_client() as client:
        yield client


@pytest.fixture
def admin_session(client):
    """Login as admin user"""
    with client.session_transaction() as session:
        session['user_id'] = 1
        session['user_name'] = 'Admin User'
        session['is_admin'] = True
    return client


@pytest.fixture
def regular_session(client):
    """Login as regular user"""
    with client.session_transaction() as session:
        session['user_id'] = 2
        session['user_name'] = 'Regular User'
        session['is_admin'] = False
    return client


def test_admin_dashboard_requires_login(client):
    """Test that admin dashboard requires login"""
    response = client.get('/admin/', follow_redirects=False)
    assert response.status_code in [302, 308]


def test_admin_dashboard_requires_admin(regular_session):
    """Test that non-admin users cannot access admin dashboard"""
    response = regular_session.get('/admin/', follow_redirects=False)
    assert response.status_code in [302, 308]


@pytest.mark.live_db
def test_admin_dashboard_accessible_by_admin(admin_session):
    """Test that admin users can access dashboard"""
    response = admin_session.get('/admin/')
    assert response.status_code == 200


def test_admin_menu_requires_admin(regular_session):
    """Test that non-admin users cannot access menu management"""
    response = regular_session.get('/admin/menu', follow_redirects=False)
    assert response.status_code in [302, 308]


@pytest.mark.live_db
def test_admin_menu_accessible_by_admin(admin_session):
    """Test that admin users can access menu management"""
    response = admin_session.get('/admin/menu')
    assert response.status_code == 200


def test_update_order_status_requires_admin(regular_session):
    """Test that only admins can update order status"""
    response = regular_session.post('/admin/order/1/update',
                                   data={'status': 'completed'},
                                   follow_redirects=False)
    assert response.status_code in [302, 308]


@pytest.mark.live_db
def test_update_order_status_by_admin(admin_session):
    """Test updating order status as admin"""
    response = admin_session.post('/admin/order/1/update',
                                 data={'status': 'preparing'},
                                 follow_redirects=True)
    assert response.status_code == 200


def test_create_menu_item_requires_admin(regular_session):
    """Test that only admins can create menu items"""
    response = regular_session.post('/admin/menu/create',
                                   data={'item_id': 'TEST001'},
                                   follow_redirects=False)
    assert response.status_code in [302, 308]
