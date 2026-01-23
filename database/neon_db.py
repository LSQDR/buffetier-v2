"""
PostgreSQL (Neon) database operations for users and orders.
Uses Secret Manager for secure credential storage.
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import os
import hashlib

def get_neon_connection():
    """
    Get Neon PostgreSQL connection with credentials from Secret Manager.
    Falls back to environment variable if Secret Manager unavailable.
    """
    try:
        from utils.secrets import get_secret
        db_url = get_secret('neon-db-uri')
        print("✓ Using Neon URI from Secret Manager")
    except Exception as e:
        print(f"⚠ Secret Manager unavailable: {e}")
        print("  Falling back to environment variable")
        db_url = os.getenv('DATABASE_URL')
        if not db_url:
            raise Exception("Neon URI not found in Secret Manager or environment variables")
    
    return psycopg2.connect(db_url, cursor_factory=RealDictCursor)


# ============================================
# USER OPERATIONS
# ============================================

def register_user(name, email, password, is_admin=False):
    """Register a new user"""
    try:
        conn = get_neon_connection()
        cur = conn.cursor()
        
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        
        cur.execute("""
            INSERT INTO users (name, email, password, is_admin)
            VALUES (%s, %s, %s, %s)
            RETURNING user_id
        """, (name, email, hashed_password, is_admin))
        
        user_id = cur.fetchone()['user_id']
        conn.commit()
        cur.close()
        conn.close()
        
        return user_id
        
    except psycopg2.IntegrityError:
        return None  # Email already exists
    except Exception as e:
        print(f"Error registering user: {e}")
        return None


def authenticate_user(email, password):
    """Authenticate user login"""
    try:
        conn = get_neon_connection()
        cur = conn.cursor()
        
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        
        cur.execute("""
            SELECT user_id, name, email, is_admin
            FROM users
            WHERE email = %s AND password = %s
        """, (email, hashed_password))
        
        user = cur.fetchone()
        cur.close()
        conn.close()
        
        return dict(user) if user else None
        
    except Exception as e:
        print(f"Error authenticating user: {e}")
        return None


def get_user_by_id(user_id):
    """Get user by ID"""
    try:
        conn = get_neon_connection()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT user_id, name, email, is_admin
            FROM users
            WHERE user_id = %s
        """, (user_id,))
        
        user = cur.fetchone()
        cur.close()
        conn.close()
        
        return dict(user) if user else None
        
    except Exception as e:
        print(f"Error fetching user: {e}")
        return None


# ============================================
# ORDER OPERATIONS
# ============================================

def create_order(user_id, items, total_amount):
    """Create a new order"""
    try:
        conn = get_neon_connection()
        cur = conn.cursor()
        
        cur.execute("""
            INSERT INTO orders (user_id, items, total_amount, status)
            VALUES (%s, %s, %s, 'pending')
            RETURNING order_id
        """, (user_id, items, total_amount))
        
        order_id = cur.fetchone()['order_id']
        conn.commit()
        cur.close()
        conn.close()
        
        return order_id
        
    except Exception as e:
        print(f"Error creating order: {e}")
        return None


def get_user_orders(user_id):
    """Get all orders for a user"""
    try:
        conn = get_neon_connection()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT order_id, items, total_amount, status, order_date
            FROM orders
            WHERE user_id = %s
            ORDER BY order_date DESC
        """, (user_id,))
        
        orders = cur.fetchall()
        cur.close()
        conn.close()
        
        return [dict(order) for order in orders]
        
    except Exception as e:
        print(f"Error fetching user orders: {e}")
        return []


def get_all_orders():
    """Get all orders (admin)"""
    try:
        conn = get_neon_connection()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT o.order_id, o.user_id, u.name as user_name, u.email,
                   o.items, o.total_amount, o.status, o.order_date
            FROM orders o
            JOIN users u ON o.user_id = u.user_id
            ORDER BY o.order_date DESC
        """)
        
        orders = cur.fetchall()
        cur.close()
        conn.close()
        
        return [dict(order) for order in orders]
        
    except Exception as e:
        print(f"Error fetching all orders: {e}")
        return []


def update_order_status(order_id, new_status):
    """Update order status"""
    try:
        conn = get_neon_connection()
        cur = conn.cursor()
        
        cur.execute("""
            UPDATE orders
            SET status = %s
            WHERE order_id = %s
        """, (new_status, order_id))
        
        conn.commit()
        affected_rows = cur.rowcount
        cur.close()
        conn.close()
        
        return affected_rows > 0
        
    except Exception as e:
        print(f"Error updating order status: {e}")
        return False


def get_order_by_id(order_id):
    """Get order by ID"""
    try:
        conn = get_neon_connection()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT order_id, user_id, items, total_amount, status, order_date
            FROM orders
            WHERE order_id = %s
        """, (order_id,))
        
        order = cur.fetchone()
        cur.close()
        conn.close()
        
        return dict(order) if order else None
        
    except Exception as e:
        print(f"Error fetching order: {e}")
        return None
