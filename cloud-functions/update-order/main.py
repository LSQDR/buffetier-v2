import functions_framework
import psycopg2
import os
import json

DATABASE_URL = os.environ.get('DATABASE_URL')

@functions_framework.http
def update_order(request):
    """
    Cloud Function to update order status.
    Accepts PUT/POST requests with order_id and new status.
    """
    # Handle CORS preflight
    if request.method == 'OPTIONS':
        headers = {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'PUT, POST',
            'Access-Control-Allow-Headers': 'Content-Type',
        }
        return ('', 204, headers)
    
    headers = {'Access-Control-Allow-Origin': '*'}
    
    try:
        request_json = request.get_json(silent=True)
        
        if not request_json:
            return (json.dumps({'error': 'No data provided'}), 400, headers)
        
        # Extract data
        order_id = request_json.get('order_id')
        new_status = request_json.get('status')
        
        # Validate required fields
        if not order_id or not new_status:
            return (json.dumps({'error': 'Missing order_id or status'}), 400, headers)
        
        # Validate status value
        valid_statuses = ['pending', 'preparing', 'ready', 'completed', 'cancelled']
        if new_status not in valid_statuses:
            return (json.dumps({
                'error': f'Invalid status. Must be one of: {", ".join(valid_statuses)}'
            }), 400, headers)
        
        # Connect to database
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        
        try:
            # Check if order exists
            cur.execute("SELECT order_id, status FROM orders WHERE order_id = %s", (order_id,))
            order = cur.fetchone()
            
            if not order:
                return (json.dumps({'error': f'Order {order_id} not found'}), 404, headers)
            
            old_status = order[1]
            
            # Update order status
            cur.execute(
                "UPDATE orders SET status = %s WHERE order_id = %s",
                (new_status, order_id)
            )
            
            conn.commit()
            
            return (json.dumps({
                'success': True,
                'order_id': order_id,
                'old_status': old_status,
                'new_status': new_status,
                'message': f'Order status updated from {old_status} to {new_status}'
            }), 200, headers)
            
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
