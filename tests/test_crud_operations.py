import pytest
import sys
import os


sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dotenv import load_dotenv
load_dotenv()

from database.neon_db import (
    get_neon_connection,
    create_order,
    get_all_orders,
    update_order_status,
    delete_order_with_items
)
from database.mongo_db import (
    get_mongo_connection,
    create_menu_item,
    get_all_menu_items,
    update_menu_item,
    delete_menu_item
)
from bson import ObjectId

# PostgreSQL CRUD Tests
def test_postgresql_create_order():
    """Test CREATE operation on orders"""
    order_items = [
        {'item_id': 'BUFF001', 'name': 'Test Item', 'quantity': 1, 'price': 10.00}
    ]
    order_id = create_order(user_id=1, table_number=99, total_price=10.00, order_items=order_items)
    assert order_id is not None
    assert isinstance(order_id, int)
    
    # Cleanup
    delete_order_with_items(order_id)

def test_postgresql_read_orders():
    """Test READ operation on orders"""
    orders = get_all_orders(user_id=1)
    assert isinstance(orders, list)

def test_postgresql_update_order():
    """Test UPDATE operation on orders"""
    # Create test order
    order_items = [
        {'item_id': 'BUFF001', 'name': 'Test Item', 'quantity': 1, 'price': 10.00}
    ]
    order_id = create_order(user_id=1, table_number=99, total_price=10.00, order_items=order_items)
    
    # Update status
    result = update_order_status(order_id, 'completed')
    assert result == True
    
    # Cleanup
    delete_order_with_items(order_id)

def test_postgresql_delete_order():
    """Test DELETE operation on orders"""
    # Create test order
    order_items = [
        {'item_id': 'BUFF001', 'name': 'Test Item', 'quantity': 1, 'price': 10.00}
    ]
    order_id = create_order(user_id=1, table_number=99, total_price=10.00, order_items=order_items)
    
    # Delete it
    delete_order_with_items(order_id)
    
    # Verify deletion - get_all_orders should not include it
    orders = get_all_orders(user_id=1)
    deleted_order = [o for o in orders if o[0] == order_id]
    assert len(deleted_order) == 0

# MongoDB CRUD Tests
def test_mongodb_create_menu_item():
    """Test CREATE operation on menu"""
    # First, clean up any existing test items from previous runs
    items = get_all_menu_items()
    for item in items:
        if item.get('item_id') == 'TEST_CREATE':
            delete_menu_item(item['_id'])
    
    # Now create the test item
    mongo_id = create_menu_item(
        item_id='TEST_CREATE',
        name='Test Item',
        category='Test',
        description='Test description',
        price=9.99,
        available=True
    )
    
    try:
        # Assertions
        assert mongo_id is not None
        assert isinstance(mongo_id, str)
        assert len(mongo_id) == 24  # MongoDB ObjectId is 24 characters
        
        # Verify it was created
        items = get_all_menu_items()
        created_items = [i for i in items if i.get('item_id') == 'TEST_CREATE']
        assert len(created_items) == 1
        assert created_items[0]['name'] == 'Test Item'
        
    finally:
        # Cleanup
        try:
            delete_menu_item(mongo_id)
        except:
            pass

def test_mongodb_read_menu_items():
    """Test READ operation on menu"""
    items = get_all_menu_items()
    assert isinstance(items, list)
    assert len(items) > 0

def test_mongodb_update_menu_item():
    """Test UPDATE operation on menu"""
    # Create test item
    item_id = create_menu_item(
        item_id='TEST_UPDATE',
        name='Original Name',
        category='Test',
        description='Test',
        price=10.00
    )
    
    # Update it
    result = update_menu_item(
        menu_id=item_id,
        item_id='TEST_UPDATE',
        name='Updated Name',
        category='Test',
        description='Updated description',
        price=15.00,
        available=True
    )
    assert result == True
    
    # Cleanup
    delete_menu_item(item_id)

def test_mongodb_delete_menu_item():
    """Test DELETE operation on menu"""
    # Create test item
    item_id = create_menu_item(
        item_id='TEST_DELETE',
        name='Delete Me',
        category='Test',
        description='Test',
        price=5.00
    )
    
    # Delete it
    result = delete_menu_item(item_id)
    assert result == True
    
    # Verify deletion
    items = get_all_menu_items()
    deleted_item = [i for i in items if i.get('_id') == item_id]
    assert len(deleted_item) == 0
