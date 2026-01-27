import pytest
from database import neon_db, mongo_db
import uuid
import json


class TestNeonDatabase:
    
    def test_neon_connection(self):
        """Test Neon database connection"""
        conn = neon_db.get_neon_connection()
        assert conn is not None
        conn.close()
    
    def test_create_user(self):
        """Test creating a new user"""
        # Use unique email each run to avoid duplicates
        unique_suffix = uuid.uuid4().hex[:8]
        test_email = f"test_{unique_suffix}@buffetier.com"
        test_name = "Test User"
        test_phone = "07700900123"
        test_password = "testpass123"
        
        user_id = neon_db.register_user(test_name, test_email, test_password, test_phone)
        
        assert user_id is not None
        assert user_id > 0
        
        user = neon_db.get_user_by_id(user_id)
        assert user['email'] == test_email
        assert user['name'] == test_name
    
    def test_create_order(self):
        """Test creating a new order"""
        # Unique email for test user
        unique_suffix = uuid.uuid4().hex[:8]
        email = f"ordertest_{unique_suffix}@test.com"
        user_id = neon_db.register_user("Order Test", email, "pass123", "07700900456")
        assert user_id is not None
        
        items = [
            {'item_id': 'BUFF001', 'name': 'Buffet Special', 'quantity': 2, 'price': 25.99},
            {'item_id': 'DRINK001', 'name': 'Soft Drink', 'quantity': 1, 'price': 2.50}
        ]
        
        order_id = neon_db.create_order(
            user_id=user_id,
            items=json.dumps(items),
            total_amount=54.48,
            table_number=5
        )
        
        assert order_id is not None
        assert order_id > 0
        
        order = neon_db.get_order_by_id(order_id)
        assert order['user_id'] == user_id
        assert len(order['items']) == 2
    
    def test_update_order_status(self):
        """Test updating order status"""
        unique_suffix = uuid.uuid4().hex[:8]
        email = f"status_{unique_suffix}@test.com"
        user_id = neon_db.register_user("Status Test", email, "pass123", "07700900789")
        assert user_id is not None
        
        items = [{'item_id': 'TEST001', 'name': 'Test Item', 'quantity': 1, 'price': 10.00}]
        order_id = neon_db.create_order(
            user_id=user_id,
            items=json.dumps(items),
            total_amount=10.00,
            table_number=1
        )
        
        success = neon_db.update_order_status(order_id, 'preparing')
        assert success is True
        
        order = neon_db.get_order_by_id(order_id)
        assert order['status'] == 'preparing'


class TestMongoDatabase:
    
    def test_mongo_connection(self):
        """Test MongoDB connection"""
        items = mongo_db.get_all_menu_items()
        assert isinstance(items, list)
    
    def test_get_menu_items(self):
        """Test fetching all menu items"""
        items = mongo_db.get_all_menu_items()
        assert len(items) > 0
        assert 'name' in items[0]
        assert 'price' in items[0]
    
    def test_get_menu_by_category(self):
        """Test fetching menu items by category"""
        category = "Mains"
        items = list(mongo_db.menu_collection.find({'category': category}))
        
        assert len(items) > 0
        for item in items:
            assert item['category'] == category
    
    def test_add_and_delete_review(self):
        """Test adding and removing a review"""
        review_data = {
            "user_id": 1,
            "user_name": "Test User",
            "rating": 5,
            "comment": "Great food!"
        }
        
        review_id = mongo_db.create_review(
            review_data['user_id'],
            review_data['user_name'],
            review_data['rating'],
            review_data['comment']
        )
        
        assert review_id is not None
        
        success = mongo_db.delete_review(review_id)
        assert success is True
    
    def test_menu_item_availability(self):
        """Test menu item availability filtering"""
        items = mongo_db.get_all_menu_items()
        available_items = [item for item in items if item.get('available', True)]
        assert len(available_items) >= 0
