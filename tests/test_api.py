import pytest
import json
from main import app

@pytest.fixture
def client():
    """Create a test client for the Flask app"""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


class TestAPIRoutes:
    """Test suite for Flask API routes"""
    
    def test_home_page(self, client):
        """Test home page loads"""
        response = client.get('/')
        assert response.status_code == 200, "Home page failed to load"
    
    def test_get_menu_api(self, client):
        """Test GET /api/menu endpoint"""
        response = client.get('/api/menu')
        assert response.status_code == 200, "Menu API failed"
        
        data = json.loads(response.data)
        assert isinstance(data, list), "Menu should return a list"
        assert len(data) > 0, "Menu should not be empty"
    
    def test_create_order_api(self, client):
        """Test POST /api/orders endpoint"""
        order_data = {
            "user_id": 1,
            "table_number": 5,
            "items": [
                {
                    "item_id": "BUFF001",
                    "name": "Buffet Special",
                    "quantity": 2,
                    "price": 25.99
                }
            ]
        }
        
        response = client.post(
            '/api/orders',
            data=json.dumps(order_data),
            content_type='application/json'
        )
        
        assert response.status_code == 201, "Order creation failed"
        data = json.loads(response.data)
        assert 'order_id' in data, "Response missing order_id"
    
    def test_get_user_orders(self, client):
        """Test GET /api/orders/<user_id> endpoint"""
        user_id = 1
        response = client.get(f'/api/orders/{user_id}')
        assert response.status_code == 200, "Failed to get user orders"
        
        data = json.loads(response.data)
        assert isinstance(data, list), "Orders should be a list"
    
    def test_update_order_status(self, client):
        """Test PUT /api/orders/<order_id> endpoint"""
        # First create an order
        order_data = {
            "user_id": 1,
            "table_number": 3,
            "items": [{"item_id": "BUFF001", "name": "Test", "quantity": 1, "price": 9.99}]
        }
        create_response = client.post(
            '/api/orders',
            data=json.dumps(order_data),
            content_type='application/json'
        )
        order_id = json.loads(create_response.data)['order_id']
        
        # Update the order
        update_data = {"status": "completed"}
        response = client.put(
            f'/api/orders/{order_id}',
            data=json.dumps(update_data),
            content_type='application/json'
        )
        
        assert response.status_code == 200, "Failed to update order"
        data = json.loads(response.data)
        assert data['status'] == 'updated', "Update status not confirmed"
    
    def test_invalid_order_creation(self, client):
        """Test creating order with missing data"""
        incomplete_data = {
            "table_number": 5
            # Missing user_id and items
        }
        
        response = client.post(
            '/api/orders',
            data=json.dumps(incomplete_data),
            content_type='application/json'
        )
        
        assert response.status_code == 400, "Should return 400 for bad request"
    
    def test_menu_category_filter(self, client):
        """Test filtering menu by category"""
        response = client.get('/api/menu?category=Buffet')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        for item in data:
            assert item['category'] == 'Buffet', "Wrong category returned"
