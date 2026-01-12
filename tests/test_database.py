import pytest
import os
from database import neon_db, mongo_db

class TestNeonDatabase:
    """Test suite for Neon Postgres database"""
    
    def test_neon_connection(self):
        """Test that we can connect to Neon database"""
        conn = neon_db.get_neon_connection()
        assert conn is not None, "Failed to connect to Neon"
        conn.close()
    
    def test_create_user(self):
        """Test creating a new user"""
        # Test data
        test_email = "test@buffetier.com"
        test_name = "Test User"
        test_phone = "07700900123"
        
        # Create user
        user_id = neon_db.create_user(test_email, test_name, test_phone)
        assert user_id is not None, "User creation failed"
        
        # Verify user exists
        user = neon_db.get_user_by_email(test_email)
        assert user is not None, "User not found after creation"
        assert user[1] == test_email, "Email doesn't match"
        
        # Cleanup - delete test user
        neon_db.delete_user(user_id)
    
    def test_create_order(self):
        """Test creating a new order"""
        # First create a test user
        user_id = neon_db.create_user("ordertest@test.com", "Order Test", "07700900456")
        
        # Create order items
        order_items = [
            {
                'item_id': 'BUFF001',
                'name': 'Buffet Special',
                'quantity': 2,
                'price': 25.99
            }
        ]
        
        # Create order
        order_id = neon_db.create_order(user_id, 5, 51.98, order_items)
        assert order_id is not None, "Order creation failed"
        
        # Verify order exists
        orders = neon_db.get_all_orders(user_id)
        assert len(orders) > 0, "No orders found for user"
        
        # Cleanup
        neon_db.delete_order(order_id)
        neon_db.delete_user(user_id)
    
    def test_update_order_status(self):
        """Test updating order status"""
        # Create test user and order
        user_id = neon_db.create_user("status@test.com", "Status Test", "07700900789")
        order_id = neon_db.create_order(user_id, 3, 25.99, [])
        
        # Update status
        result = neon_db.update_order_status(order_id, 'completed')
        assert result is True, "Failed to update order status"
        
        # Cleanup
        neon_db.delete_order(order_id)
        neon_db.delete_user(user_id)


class TestMongoDatabase:
    """Test suite for MongoDB database"""
    
    def test_mongo_connection(self):
        """Test that we can connect to MongoDB"""
        client = mongo_db.get_mongo_client()
        assert client is not None, "Failed to connect to MongoDB"
        
        # Test database access
        db = client.buffetier
        assert db is not None, "Failed to access buffetier database"
        client.close()
    
    def test_get_menu_items(self):
        """Test fetching menu items"""
        items = mongo_db.get_all_menu_items()
        assert isinstance(items, list), "Menu items should be a list"
        assert len(items) > 0, "No menu items found"
        
        # Verify item structure
        first_item = items[0]
        assert 'item_id' in first_item, "Menu item missing item_id"
        assert 'name' in first_item, "Menu item missing name"
        assert 'price' in first_item, "Menu item missing price"
    
    def test_get_menu_by_category(self):
        """Test fetching menu items by category"""
        category = "Buffet"
        items = mongo_db.get_menu_by_category(category)
        assert isinstance(items, list), "Should return a list"
        
        # Verify all items are from correct category
        for item in items:
            assert item['category'] == category, f"Item has wrong category: {item['category']}"
    
    def test_add_and_delete_review(self):
        """Test adding and removing a review"""
        # Add review
        review_data = {
            "user_name": "Test User",
            "rating": 5,
            "comment": "Great food!"
        }
        
        review_id = mongo_db.add_review(
            review_data['user_name'],
            review_data['rating'],
            review_data['comment']
        )
        assert review_id is not None, "Failed to add review"
        
        # Verify review was added
        reviews = mongo_db.get_all_reviews()
        found = any(r.get('user_name') == 'Test User' for r in reviews)
        assert found, "Review not found after adding"
        
        # Cleanup - delete review
        mongo_db.delete_review(review_id)
    
    def test_menu_item_availability(self):
        """Test that only available items are returned"""
        items = mongo_db.get_all_menu_items()
        
        # All items should have available=True
        for item in items:
            assert item.get('available') == True, f"Item {item['name']} is not available"
