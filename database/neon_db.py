import os
import psycopg2
import hashlib


def get_neon_connection():
    """Get connection to Neon Postgres"""
    return psycopg2.connect(
        os.environ.get('NEON_DB_URL'),
        sslmode='require'
    )

def get_user_by_email(email):
    """Fetch user by email"""
    conn = get_neon_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM users WHERE email = %s", (email,))
            user = cur.fetchone()
        return user
    finally:
        conn.close()

def create_user(email, name, phone):
    """Create a new user"""
    conn = get_neon_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO users (email, name, phone)
                VALUES (%s, %s, %s)
                RETURNING user_id
            """, (email, name, phone))
            user_id = cur.fetchone()[0]
            conn.commit()
            return user_id
    finally:
        conn.close()

def delete_user(user_id):
    """Delete a user"""
    conn = get_neon_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM users WHERE user_id = %s", (user_id,))
            conn.commit()
    finally:
        conn.close()

def create_order(user_id, table_number, total_price, order_items):
    """Create a new order"""
    conn = get_neon_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO orders (user_id, table_number, total_price, status)
                VALUES (%s, %s, %s, 'pending')
                RETURNING order_id
            """, (user_id, table_number, total_price))
            order_id = cur.fetchone()[0]
            
            for item in order_items:
                cur.execute("""
                    INSERT INTO order_items (order_id, menu_item_id, item_name, quantity, price)
                    VALUES (%s, %s, %s, %s, %s)
                """, (order_id, item['item_id'], item['name'], item['quantity'], item['price']))
            
            conn.commit()
            return order_id
    finally:
        conn.close()

def get_all_orders(user_id):
    """Get all orders for a user"""
    conn = get_neon_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT o.order_id, o.total_price, o.status, o.created_at
                FROM orders o
                WHERE o.user_id = %s
                ORDER BY o.created_at DESC
            """, (user_id,))
            orders = cur.fetchall()
        return orders
    finally:
        conn.close()

def delete_order(order_id):
    """Delete an order"""
    conn = get_neon_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM orders WHERE order_id = %s", (order_id,))
            conn.commit()
    finally:
        conn.close()

def update_order_status(order_id, status):
    """Update order status"""
    conn = get_neon_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE orders SET status = %s WHERE order_id = %s",
                (status, order_id)
            )
            conn.commit()
            return True
    finally:
        conn.close()

def hash_password(password):
    """Hash a password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def register_user(email, name, phone, password):
    """Register a new user with password"""
    conn = get_neon_connection()
    try:
        with conn.cursor() as cur:
            password_hash = hash_password(password)
            cur.execute("""
                INSERT INTO users (email, name, phone, password_hash)
                VALUES (%s, %s, %s, %s)
                RETURNING user_id
            """, (email, name, phone, password_hash))
            user_id = cur.fetchone()[0]
            conn.commit()
            return user_id
    except Exception as e:
        conn.rollback()
        return None
    finally:
        conn.close()

def authenticate_user(email, password):
    """Authenticate user by email and password"""
    conn = get_neon_connection()
    try:
        with conn.cursor() as cur:
            password_hash = hash_password(password)
            cur.execute("""
                SELECT user_id, email, name, phone
                FROM users
                WHERE email = %s AND password_hash = %s
            """, (email, password_hash))
            user = cur.fetchone()
            
            if user:
                return {
                    'user_id': user[0],
                    'email': user[1],
                    'name': user[2],
                    'phone': user[3]
                }
            return None
    finally:
        conn.close()

def get_user_by_id(user_id):
    """Get user details by ID"""
    conn = get_neon_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT user_id, email, name, phone, created_at
                FROM users
                WHERE user_id = %s
            """, (user_id,))
            user = cur.fetchone()
            
            if user:
                return {
                    'user_id': user[0],
                    'email': user[1],
                    'name': user[2],
                    'phone': user[3],
                    'created_at': str(user[4])
                }
            return None
    finally:
        conn.close()
