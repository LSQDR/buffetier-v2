import pytest
import requests
import os

# Get function URL from environment
PROCESS_ORDER_URL = os.environ.get('PROCESS_ORDER_FUNCTION_URL')

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
