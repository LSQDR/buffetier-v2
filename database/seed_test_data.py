"""Create the schema and seed data that the live_db tests expect.

Reads DATABASE_URL and MONGO_URI from the environment. Run it against a
throwaway database only: it resets the users, orders and menu.

    python -m database.seed_test_data
"""

import os
from pathlib import Path

import psycopg2
from pymongo import MongoClient

from database.neon_db import hash_password

SCHEMA = Path(__file__).with_name('schema.sql')

# The tests sign in as user 1 for admin routes and user 2 for customer routes.
USERS = [
    ('Admin User', 'admin@buffetier.test', 'Admin-Pass-1', True),
    ('Regular User', 'user@buffetier.test', 'User-Pass-1', False),
]

MENU = [
    {'item_id': 'BUFF001', 'name': 'Lunch Buffet', 'category': 'Buffet',
     'description': 'Unlimited hot and cold dishes from the buffet.', 'price': 14.99},
    {'item_id': 'MAIN001', 'name': 'Chicken Katsu Curry', 'category': 'Mains',
     'description': 'Panko chicken, katsu sauce and steamed rice.', 'price': 12.50},
    {'item_id': 'MAIN002', 'name': 'Beer Battered Haddock', 'category': 'Mains',
     'description': 'Haddock in beer batter with chips and peas.', 'price': 13.95},
    {'item_id': 'DES001', 'name': 'Sticky Toffee Pudding', 'category': 'Desserts',
     'description': 'Date sponge with toffee sauce and custard.', 'price': 6.50},
]


def seed_postgres(url):
    conn = psycopg2.connect(url)
    with conn, conn.cursor() as cur:
        cur.execute(SCHEMA.read_text())
        cur.execute('TRUNCATE order_items, orders, users RESTART IDENTITY CASCADE')
        for name, email, password, is_admin in USERS:
            cur.execute(
                'INSERT INTO users (name, email, password_hash, is_admin) VALUES (%s, %s, %s, %s)',
                (name, email, hash_password(password), is_admin),
            )
    conn.close()


def seed_mongo(uri):
    db = MongoClient(uri)['buffetier']
    db.menu.delete_many({})
    db.menu.insert_many([{**item, 'available': True, 'image_url': ''} for item in MENU])


if __name__ == '__main__':
    seed_postgres(os.environ['DATABASE_URL'])
    seed_mongo(os.environ['MONGO_URI'])
    print('Seeded PostgreSQL and MongoDB.')
