import json
import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dotenv import load_dotenv

load_dotenv()


from database.mongo_db import (  # noqa: E402
    create_menu_item,
    delete_menu_item,
    get_all_menu_items,
    update_menu_item,
)
from database.neon_db import (  # noqa: E402
    create_order,
    delete_order_with_items,
    get_user_orders,
    update_order_status,
)

pytestmark = pytest.mark.live_db


def test_postgresql_create_order():
    """Test CREATE operation on orders"""
    order_items = [
        {'item_id': 'BUFF001', 'name': 'Test Item', 'quantity': 1, 'price': 10.00}
    ]
    order_id = create_order(
        user_id=1,
        items=json.dumps(order_items),
        total_amount=10.00,
        table_number=99
    )
    assert order_id is not None
    assert isinstance(order_id, int)

    delete_order_with_items(order_id)


def test_postgresql_read_orders():
    """Test READ operation on orders"""
    orders = get_user_orders(user_id=1)
    assert isinstance(orders, list)


def test_postgresql_update_order():
    """Test UPDATE operation on orders"""
    order_items = [
        {'item_id': 'BUFF001', 'name': 'Test Item', 'quantity': 1, 'price': 10.00}
    ]
    order_id = create_order(
        user_id=1,
        items=json.dumps(order_items),
        total_amount=10.00,
        table_number=99
    )

    result = update_order_status(order_id, 'completed')
    assert result is True

    delete_order_with_items(order_id)


def test_postgresql_delete_order():
    """Test DELETE operation on orders"""
    order_items = [
        {'item_id': 'BUFF001', 'name': 'Test Item', 'quantity': 1, 'price': 10.00}
    ]
    order_id = create_order(
        user_id=1,
        items=json.dumps(order_items),
        total_amount=10.00,
        table_number=99
    )

    delete_order_with_items(order_id)

    orders = get_user_orders(user_id=1)
    deleted_order = [o for o in orders if o['order_id'] == order_id]
    assert len(deleted_order) == 0


def test_mongodb_create_menu_item():
    """Test CREATE operation on menu"""
    items = get_all_menu_items()
    for item in items:
        if item.get('item_id') == 'TEST_CREATE':
            delete_menu_item(str(item['_id']))

    mongo_id = create_menu_item(
        item_id='TEST_CREATE',
        name='Test Item',
        category='Test',
        description='Test description',
        price=9.99,
        available=True
    )

    try:
        assert mongo_id is not None
        assert isinstance(mongo_id, str)
        assert len(mongo_id) == 24

        items = get_all_menu_items()
        created_items = [i for i in items if i.get('item_id') == 'TEST_CREATE']
        assert len(created_items) == 1
        assert created_items[0]['name'] == 'Test Item'

    finally:
        try:
            delete_menu_item(mongo_id)
        except Exception:
            pass


def test_mongodb_read_menu_items():
    """Test READ operation on menu"""
    items = get_all_menu_items()
    assert isinstance(items, list)
    assert len(items) > 0


def test_mongodb_update_menu_item():
    """Test UPDATE operation on menu"""
    item_id = create_menu_item(
        item_id='TEST_UPDATE',
        name='Original Name',
        category='Test',
        description='Test',
        price=10.00
    )

    result = update_menu_item(
        menu_id=item_id,
        item_id='TEST_UPDATE',
        name='Updated Name',
        category='Test',
        description='Updated description',
        price=15.00,
        available=True
    )
    assert result is True

    delete_menu_item(item_id)


def test_mongodb_delete_menu_item():
    """Test DELETE operation on menu"""
    item_id = create_menu_item(
        item_id='TEST_DELETE',
        name='Delete Me',
        category='Test',
        description='Test',
        price=5.00
    )

    result = delete_menu_item(item_id)
    assert result is True

    items = get_all_menu_items()
    deleted_item = [i for i in items if str(i.get('_id')) == item_id]
    assert len(deleted_item) == 0
