import json
import os
from datetime import datetime

import functions_framework
import psycopg2

DATABASE_URL = os.environ.get('DATABASE_URL')

@functions_framework.http
def process_order(request):
    """
    Cloud Function to process restaurant orders.
    Inserts into both orders and order_items tables.
    """
    # Handle CORS preflight
    if request.method == 'OPTIONS':
        headers = {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'POST',
            'Access-Control-Allow-Headers': 'Content-Type',
        }
        return ('', 204, headers)

    headers = {'Access-Control-Allow-Origin': '*'}

    try:
        request_json = request.get_json(silent=True)

        if not request_json:
            return (json.dumps({'error': 'No data provided'}), 400, headers)

        # Extract order data
        user_id = request_json.get('user_id')
        items = request_json.get('items')  # List of items
        total_price = request_json.get('total_price')
        table_number = request_json.get('table_number', 0)
        special_instructions = request_json.get('special_instructions', '')

        # Validate required fields
        if not all([user_id, items, total_price]):
            return (json.dumps({'error': 'Missing required fields'}), 400, headers)

        if not isinstance(items, list) or len(items) == 0:
            return (json.dumps({'error': 'Items must be a non-empty list'}), 400, headers)

        # Connect to database
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()

        try:
            # Insert into orders table
            cur.execute(
                """
                INSERT INTO orders (user_id, table_number, total_price, status, special_instructions, created_at)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING order_id
                """,
                (user_id, table_number, total_price, 'pending', special_instructions, datetime.now())
            )

            order_id = cur.fetchone()[0]

            # Insert each item into order_items table
            for item in items:
                cur.execute(
                    """
                    INSERT INTO order_items (order_id, menu_item_id, item_name, quantity, price)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (
                        order_id,
                        item.get('menu_item_id', 'UNKNOWN'),
                        item.get('name', 'Unknown Item'),
                        item.get('quantity', 1),
                        item.get('price', 0.0)
                    )
                )

            # Commit transaction
            conn.commit()

            return (json.dumps({
                'success': True,
                'order_id': order_id,
                'message': 'Order processed successfully',
                'status': 'pending',
                'items_count': len(items)
            }), 201, headers)

        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cur.close()
            conn.close()

    except psycopg2.Error as db_error:
        return (json.dumps({'error': f'Database error: {str(db_error)}'}), 500, headers)
    except Exception as e:
        return (json.dumps({'error': f'Server error: {str(e)}'}), 500, headers)
