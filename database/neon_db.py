"""
PostgreSQL (Neon) database operations for users and orders.
Uses Secret Manager for secure credential storage.
"""

import hashlib
import hmac
import os

import psycopg2
from psycopg2.extras import RealDictCursor

# OWASP baseline for PBKDF2-HMAC-SHA256. Salt is 16 random bytes.
_PBKDF2_ITERATIONS = 600_000


def hash_password(password):
    """Return a salted PBKDF2-HMAC-SHA256 hash. Two calls differ."""
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt,
        _PBKDF2_ITERATIONS,
    )
    return f"pbkdf2_sha256${_PBKDF2_ITERATIONS}${salt.hex()}${digest.hex()}"


def verify_password(password, stored):
    """Check a password against a salted hash, or a legacy unsalted SHA-256 digest."""
    if not stored or not isinstance(stored, str):
        return False

    if stored.startswith('pbkdf2_sha256$'):
        try:
            _, iterations, salt_hex, digest_hex = stored.split('$', 3)
            actual = hashlib.pbkdf2_hmac(
                'sha256',
                password.encode('utf-8'),
                bytes.fromhex(salt_hex),
                int(iterations),
            )
            expected = bytes.fromhex(digest_hex)
        except (ValueError, TypeError):
            return False
        return hmac.compare_digest(actual, expected)

    # Rows written before the salted hash are 64 hex characters of SHA-256.
    if len(stored) == 64:
        try:
            bytes.fromhex(stored)
        except ValueError:
            return False
        legacy = hashlib.sha256(password.encode('utf-8')).hexdigest()
        return hmac.compare_digest(legacy, stored)

    return False


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
            raise Exception("Neon URI not found in Secret Manager or environment variables") from e

    return psycopg2.connect(db_url, cursor_factory=RealDictCursor)


# ============================================
# USER OPERATIONS
# ============================================

def register_user(name, email, password, phone='', is_admin=False):
    """Register a new user"""
    try:
        conn = get_neon_connection()
        cur = conn.cursor()

        hashed_password = hash_password(password)

        cur.execute("""
            INSERT INTO users (name, email, phone, password_hash, is_admin)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING user_id
        """, (name, email, phone, hashed_password, is_admin))

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

        cur.execute("""
            SELECT user_id, name, email, phone, is_admin, password_hash
            FROM users
            WHERE email = %s
        """, (email,))

        user = cur.fetchone()
        cur.close()
        conn.close()

        if not user or not verify_password(password, user['password_hash']):
            return None

        user = dict(user)
        user.pop('password_hash', None)
        return user

    except Exception as e:
        print(f"Error authenticating user: {e}")
        return None


def get_user_by_id(user_id):
    """Get user by ID"""
    try:
        conn = get_neon_connection()
        cur = conn.cursor()

        cur.execute("""
            SELECT user_id, name, email, phone, is_admin, created_at
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


def get_user_by_email(email):
    """Get user by email address"""
    try:
        conn = get_neon_connection()
        cur = conn.cursor()

        cur.execute("""
            SELECT user_id, name, email, phone, is_admin, created_at
            FROM users
            WHERE email = %s
        """, (email,))

        user = cur.fetchone()
        cur.close()
        conn.close()

        return dict(user) if user else None

    except Exception as e:
        print(f"Error fetching user by email: {e}")
        return None


# ============================================
# ORDER OPERATIONS
# ============================================

def create_order(user_id, items, total_amount, table_number=None):
    """Create a new order with items in separate table"""
    conn = None
    try:
        conn = get_neon_connection()
        cur = conn.cursor()

        # Insert order use total_price not total_amount
        cur.execute("""
            INSERT INTO orders (user_id, table_number, total_price, status)
            VALUES (%s, %s, %s, 'pending')
            RETURNING order_id
        """, (user_id, table_number, total_amount))

        order_id = cur.fetchone()['order_id']

        # Parse items JSON
        import json
        items_list = json.loads(items) if isinstance(items, str) else items

        # Insert each item into order_items table
        for item in items_list:
            cur.execute("""
                INSERT INTO order_items (order_id, menu_item_id, item_name, quantity, price)
                VALUES (%s, %s, %s, %s, %s)
            """, (
                order_id,
                item.get('item_id', 'N/A'),
                item['name'],
                item['quantity'],
                item['price']
            ))

        conn.commit()
        cur.close()
        conn.close()

        print(f"✓ Order {order_id} created with {len(items_list)} items")
        return order_id

    except Exception as e:
        print(f"✗ Error creating order: {e}")
        import traceback
        traceback.print_exc()
        if conn:
            conn.rollback()
            conn.close()
        return None



def get_user_orders(user_id):
    """Get all orders for a user"""
    try:
        conn = get_neon_connection()
        cur = conn.cursor()

        cur.execute("""
            SELECT order_id, user_id, table_number,
                   total_price as total_amount, status,
                   created_at as order_date
            FROM orders
            WHERE user_id = %s
            ORDER BY created_at DESC
        """, (user_id,))

        orders = cur.fetchall()
        cur.close()
        conn.close()

        return [dict(order) for order in orders]

    except Exception as e:
        print(f"Error fetching user orders: {e}")
        return []


def get_all_orders():
    """Get all orders with items (admin)"""
    try:
        conn = get_neon_connection()
        cur = conn.cursor()

        # Get orders with user info
        cur.execute("""
            SELECT o.order_id, o.user_id, u.name as user_name, u.email,
                   o.table_number, o.total_price as total_amount,
                   o.status, o.created_at as order_date
            FROM orders o
            JOIN users u ON o.user_id = u.user_id
            ORDER BY o.created_at DESC
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
    """Get order by ID with items"""
    try:
        conn = get_neon_connection()
        cur = conn.cursor()

        # Get order
        cur.execute("""
            SELECT order_id, user_id, table_number,
                   total_price as total_amount, status,
                   created_at as order_date
            FROM orders
            WHERE order_id = %s
        """, (order_id,))

        order = cur.fetchone()

        if order:
            order_dict = dict(order)

            # Get order items
            cur.execute("""
                SELECT menu_item_id, item_name, quantity, price
                FROM order_items
                WHERE order_id = %s
            """, (order_id,))

            items = cur.fetchall()
            order_dict['items'] = [dict(item) for item in items]
        else:
            order_dict = None

        cur.close()
        conn.close()

        return order_dict

    except Exception as e:
        print(f"Error fetching order: {e}")
        return None


def get_all_orders_admin():
    """Get all orders with stats (alias for get_all_orders)"""
    return get_all_orders()


def get_order_stats():
    """Get order statistics by status"""
    try:
        conn = get_neon_connection()
        cur = conn.cursor()

        cur.execute("""
            SELECT status, COUNT(*) as count, SUM(total_price) as total
            FROM orders
            GROUP BY status
        """)

        stats = cur.fetchall()
        cur.close()
        conn.close()

        # Convert to dict for easy template access
        stats_dict = {
            'total_orders': 0,
            'total_revenue': 0,
            'pending': 0,
            'confirmed': 0,
            'preparing': 0,
            'ready': 0,
            'completed': 0,
            'cancelled': 0
        }

        for stat in stats:
            status = stat['status']
            count = stat['count']
            total = stat['total'] or 0

            stats_dict[status] = count
            stats_dict['total_orders'] += count
            stats_dict['total_revenue'] += float(total)

        return stats_dict

    except Exception as e:
        print(f"Error fetching order stats: {e}")
        return {
            'total_orders': 0,
            'total_revenue': 0,
            'pending': 0,
            'confirmed': 0,
            'preparing': 0,
            'ready': 0,
            'completed': 0,
            'cancelled': 0
        }



def delete_order_with_items(order_id):
    """Delete an order (no items table in your schema, so just delete order)"""
    try:
        conn = get_neon_connection()
        cur = conn.cursor()

        cur.execute("""
            DELETE FROM orders
            WHERE order_id = %s
        """, (order_id,))

        conn.commit()
        affected_rows = cur.rowcount
        cur.close()
        conn.close()

        return affected_rows > 0

    except Exception as e:
        print(f"Error deleting order: {e}")
        return False
