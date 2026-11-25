"""
Cart and order prices come from the menu, not from the browser.

Hermetic: the menu lookup and the order insert are replaced, so these
tests need neither MongoDB nor PostgreSQL.
"""

import json

import pytest

from database import mongo_db, neon_db
from main import app

MENU = {
    'TEST001': {'item_id': 'TEST001', 'name': 'Test Dish', 'price': 12.5, 'available': True},
}


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(mongo_db, 'get_available_menu_item', lambda item_id: MENU.get(item_id))
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    with app.test_client() as client:
        with client.session_transaction() as session:
            session['user_id'] = 1
            session['user_name'] = 'Test User'
        yield client


def post_json(client, url, body):
    return client.post(url, data=json.dumps(body), content_type='application/json')


def test_cart_uses_menu_price_not_request_price(client):
    response = post_json(client, '/api/cart/add', {'item_id': 'TEST001', 'name': 'Free', 'price': 0.01})

    assert response.status_code == 200
    with client.session_transaction() as session:
        line = session['cart']['TEST001']
    assert line['price'] == 12.5
    assert line['name'] == 'Test Dish'


def test_cart_adds_quantity_to_existing_line(client):
    post_json(client, '/api/cart/add', {'item_id': 'TEST001'})
    post_json(client, '/api/cart/add', {'item_id': 'TEST001', 'quantity': 2})

    with client.session_transaction() as session:
        assert session['cart']['TEST001']['quantity'] == 3


@pytest.mark.parametrize('body, status', [
    ({'item_id': 'NOPE001'}, 404),
    ({}, 400),
    ({'item_id': 'TEST001', 'quantity': 0}, 400),
    ({'item_id': 'TEST001', 'quantity': 'two'}, 400),
])
def test_cart_rejects_bad_lines(client, body, status):
    response = post_json(client, '/api/cart/add', body)

    assert response.status_code == status
    with client.session_transaction() as session:
        assert session.get('cart', {}) == {}


def test_cart_reports_unreachable_menu(client, monkeypatch):
    def unreachable(item_id):
        raise ConnectionError('menu down')

    monkeypatch.setattr(mongo_db, 'get_available_menu_item', unreachable)

    response = post_json(client, '/api/cart/add', {'item_id': 'TEST001'})

    assert response.status_code == 503


def test_order_total_uses_menu_prices(client, monkeypatch):
    saved = {}

    def fake_create_order(user_id, items, total_amount, table_number=None):
        saved['items'] = json.loads(items)
        saved['total'] = total_amount
        return 42

    monkeypatch.setattr(neon_db, 'create_order', fake_create_order)

    response = post_json(client, '/api/orders', {
        'user_id': 1,
        'items': [{'item_id': 'TEST001', 'name': 'Free', 'quantity': 2, 'price': 0.01}],
    })

    assert response.status_code == 201
    assert response.get_json()['total'] == 25.0
    assert saved['total'] == 25.0
    assert saved['items'][0]['price'] == 12.5


def test_order_with_unknown_item_is_rejected(client, monkeypatch):
    monkeypatch.setattr(neon_db, 'create_order', lambda **kwargs: pytest.fail('order should not be saved'))

    response = post_json(client, '/api/orders', {
        'user_id': 1,
        'items': [{'item_id': 'NOPE001', 'quantity': 1, 'price': 0.01}],
    })

    assert response.status_code == 400
