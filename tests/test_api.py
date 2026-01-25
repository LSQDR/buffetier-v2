import pytest
import json
from main import app


@pytest.fixture
def client():
    """Create a test client for the Flask app"""
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    with app.test_client() as client:
        yield client


@pytest.fixture
def authenticated_client(client):
    """Create authenticated test client"""
    with client.session_transaction() as session:
        session['user_id'] = 1
        session['user_name'] = 'Test User'
        session['is_admin'] = False
    return client


class TestAPIRoutes:
    """Test suite for Flask API routes"""
    
    def test_home_page(self, client):
        """Test home page loads"""
        response = client.get('/')
        assert response.status_code == 200
    
    def test_get_menu_api(self, client):
        """Test GET /api/menu endpoint"""
        response = client.get('/api/menu')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert isinstance(data, list)
        assert len(data) > 0
    
    def test_create_order_api(self, authenticated_client):
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
        
        response = authenticated_client.post(
            '/api/orders',
            data=json.dumps(order_data),
            content_type='application/json'
        )
        
        assert response.status_code == 201
        data = json.loads(response.data)
        assert 'order_id' in data
    
    def test_get_user_orders(self, authenticated_client):
        """Test GET /api/orders/<user_id> endpoint"""
        user_id = 1
        response = authenticated_client.get(f'/api/orders/{user_id}')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert isinstance(data, list)
    
    def test_update_order_status(self, authenticated_client):
        """Test PUT /api/orders/<order_id> endpoint"""
        order_data = {
            "user_id": 1,
            "table_number": 3,
            "items": [{"item_id": "BUFF001", "name": "Test", "quantity": 1, "price": 9.99}]
        }
        create_response = authenticated_client.post(
            '/api/orders',
            data=json.dumps(order_data),
            content_type='application/json'
        )
        
        if create_response.status_code != 201:
            pytest.skip("Order creation failed, cannot test update")
        
        order_id = json.loads(create_response.data)['order_id']
        
        update_data = {"status": "completed"}
        response = authenticated_client.put(
            f'/api/orders/{order_id}',
            data=json.dumps(update_data),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'updated'
    
    def test_invalid_order_creation(self, authenticated_client):
        """Test creating order with missing data"""
        incomplete_data = {
            "table_number": 5
        }
        
        response = authenticated_client.post(
            '/api/orders',
            data=json.dumps(incomplete_data),
            content_type='application/json'
        )
        
        assert response.status_code == 400
    
    def test_menu_category_filter(self, client):
        """Test filtering menu by category"""
        response = client.get('/api/menu?category=Buffet')
        
        assert response.status_code == 200
        
        data = json.loads(response.data)
        if len(data) > 0:
            for item in data:
                assert item['category'] == 'Buffet'
