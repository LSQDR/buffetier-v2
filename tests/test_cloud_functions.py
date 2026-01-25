import pytest
import requests
import os
from dotenv import load_dotenv


load_dotenv()

# Get function URL from environment
PROCESS_ORDER_URL = os.environ.get('PROCESS_ORDER_FUNCTION_URL')
GET_MENU_URL = os.environ.get('GET_MENU_FUNCTION_URL')
UPDATE_ORDER_URL = os.environ.get('UPDATE_ORDER_FUNCTION_URL')

@pytest.mark.skipif(not PROCESS_ORDER_URL, reason="Function URL not set")
def test_process_order_function():
    """Test that process order function creates order successfully"""
    response = requests.post(PROCESS_ORDER_URL, json={
        'user_id': 1,
        'table_number': 5,
        'total_price': 28.48,
        'items': [
            {'menu_item_id': 'BUFF001', 'name': 'Buffet Special', 'quantity': 2, 'price': 25.99},
            {'menu_item_id': 'DRINK001', 'name': 'Soft Drink', 'quantity': 1, 'price': 2.50}
        ]
    })
    
    assert response.status_code == 201
    data = response.json()
    assert data['success'] == True
    assert 'order_id' in data
    assert data['items_count'] == 2

@pytest.mark.skipif(not PROCESS_ORDER_URL, reason="Function URL not set")
def test_process_order_missing_data():
    """Test that function rejects incomplete data"""
    response = requests.post(PROCESS_ORDER_URL, json={
        'user_id': 1
        # Missing items and total_price
    })
    
    assert response.status_code == 400
    data = response.json()
    assert 'error' in data

@pytest.mark.skipif(not PROCESS_ORDER_URL, reason="Function URL not set")
def test_process_order_empty_items():
    """Test that function rejects empty items list"""
    response = requests.post(PROCESS_ORDER_URL, json={
        'user_id': 1,
        'total_price': 10.00,
        'items': []  # Empty list
    })
    
    assert response.status_code == 400
    data = response.json()
    assert 'error' in data


GET_MENU_URL = os.environ.get('GET_MENU_FUNCTION_URL')

@pytest.mark.skipif(not GET_MENU_URL, reason="Function URL not set")
def test_get_menu_function():
    """Test that get menu function returns menu items"""
    response = requests.get(GET_MENU_URL)
    
    assert response.status_code == 200
    data = response.json()
    assert data['success'] == True
    assert 'menu' in data
    assert 'count' in data
    assert len(data['menu']) > 0

@pytest.mark.skipif(not GET_MENU_URL, reason="Function URL not set")
def test_get_menu_by_category():
    """Test filtering menu by category"""
    response = requests.get(f"{GET_MENU_URL}?category=Buffet")
    
    assert response.status_code == 200
    data = response.json()
    assert data['success'] == True
    # All returned items should be in Buffet category
    for item in data['menu']:
        assert item['category'] == 'Buffet'

@pytest.mark.skipif(not GET_MENU_URL, reason="Function URL not set")
def test_get_menu_available_only():
    """Test filtering for available items only"""
    response = requests.get(f"{GET_MENU_URL}?available=true")
    
    assert response.status_code == 200
    data = response.json()
    assert data['success'] == True
    # All returned items should be available
    for item in data['menu']:
        assert item['available'] == True


UPDATE_ORDER_URL = os.environ.get('UPDATE_ORDER_FUNCTION_URL')

@pytest.mark.skipif(not UPDATE_ORDER_URL, reason="Function URL not set")
def test_update_order_function():
    """Test updating order status"""
    response = requests.post(UPDATE_ORDER_URL, json={
        'order_id': 1,
        'status': 'completed'
    })
    
    assert response.status_code == 200
    data = response.json()
    assert data['success'] == True
    assert data['new_status'] == 'completed'

@pytest.mark.skipif(not UPDATE_ORDER_URL, reason="Function URL not set")
def test_update_order_invalid_status():
    """Test that invalid status is rejected"""
    response = requests.post(UPDATE_ORDER_URL, json={
        'order_id': 1,
        'status': 'invalid'
    })
    
    assert response.status_code == 400
    data = response.json()
    assert 'error' in data

@pytest.mark.skipif(not UPDATE_ORDER_URL, reason="Function URL not set")
def test_update_order_not_found():
    """Test updating non-existent order"""
    response = requests.post(UPDATE_ORDER_URL, json={
        'order_id': 99999,
        'status': 'completed'
    })
    
    assert response.status_code == 404
    data = response.json()
    assert 'error' in data