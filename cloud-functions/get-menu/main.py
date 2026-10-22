import json
import os

import functions_framework
import pymongo

# MongoDB connection string
MONGODB_URI = os.environ.get('MONGODB_URI')

@functions_framework.http
def get_menu(request):
    """
    Cloud Function to retrieve menu items from MongoDB.
    Supports GET requests with optional category filtering.
    """
    # Handle CORS preflight
    if request.method == 'OPTIONS':
        headers = {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET',
            'Access-Control-Allow-Headers': 'Content-Type',
        }
        return ('', 204, headers)

    headers = {'Access-Control-Allow-Origin': '*'}

    try:
        # Connect to MongoDB
        client = pymongo.MongoClient(MONGODB_URI)
        db = client['buffetier']
        collection = db['menu']

        # Get query parameters
        category = request.args.get('category', None)
        available_only = request.args.get('available', 'false').lower() == 'true'

        # Build query filter
        query = {}
        if category:
            query['category'] = category
        if available_only:
            query['available'] = True

        # Fetch menu items
        menu_items = list(collection.find(query))

        # Convert ObjectId to string for JSON serialization
        for item in menu_items:
            item['_id'] = str(item['_id'])

        # Close connection
        client.close()

        # Return menu items
        return (json.dumps({
            'success': True,
            'count': len(menu_items),
            'menu': menu_items
        }), 200, headers)

    except pymongo.errors.ConnectionFailure as conn_error:
        return (json.dumps({'error': f'Database connection error: {str(conn_error)}'}), 500, headers)
    except Exception as e:
        return (json.dumps({'error': f'Server error: {str(e)}'}), 500, headers)
