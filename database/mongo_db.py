from pymongo import MongoClient
from bson import ObjectId
import os
from datetime import datetime, timezone

# ============================================
# DATABASE SETUP
# ============================================


def get_mongo_client():
    """Get MongoDB client with credentials from Secret Manager"""
    try:
        from utils.secrets import get_secret
        mongo_uri = get_secret('mongodb-uri')
        print("✓ Using MongoDB URI from Secret Manager")
    except Exception as e:
        print(f"⚠ Secret Manager unavailable: {e}")
        print("  Falling back to environment variable")
        mongo_uri = os.getenv('MONGO_URI')
        if not mongo_uri:
            raise Exception("MongoDB URI not found")
    
    return MongoClient(mongo_uri)


# Connection is deferred until a collection is used. Importing this module
# must succeed when MONGO_URI is unset and Secret Manager is unreachable.
_client = None
_db = None


def _ensure_db():
    """Open the buffetier database on first use."""
    global _client, _db
    if _db is None:
        _client = get_mongo_client()
        _db = _client['buffetier']
        print("✓ MongoDB connected successfully")
    return _db


class _LazyCollection:
    """Stand-in for a pymongo collection that connects on first attribute use."""

    def __init__(self, name):
        self._name = name

    def _collection(self):
        return _ensure_db()[self._name]

    def __getattr__(self, item):
        return getattr(self._collection(), item)


menu_collection = _LazyCollection('menu')
reviews_collection = _LazyCollection('reviews')


# ============================================
# MENU ITEM OPERATIONS
# ============================================

def get_all_menu_items():
    """Retrieve all menu items from MongoDB"""
    try:
        items = list(menu_collection.find())
        print(f"✓ Retrieved {len(items)} menu items from MongoDB")
        return items
    except Exception as e:
        print(f"Error fetching menu items: {e}")
        return []


def get_menu_item_by_id(item_id):
    """Get a single menu item by MongoDB ObjectId"""
    try:
        return menu_collection.find_one({'_id': ObjectId(item_id)})
    except Exception as e:
        print(f"Error fetching menu item: {e}")
        return None


def create_menu_item(item_id, name, category, description, price, available=True, image_url=''):
    """Create a new menu item"""
    try:
        item_data = {
            'item_id': item_id,
            'name': name,
            'category': category,
            'description': description,
            'price': float(price),
            'available': available,
            'image_url': image_url
        }
        
        result = menu_collection.insert_one(item_data)
        print(f"✓ Created menu item: {name}")
        return str(result.inserted_id)
    except Exception as e:
        print(f"Error creating menu item: {e}")
        return None


def update_menu_item(menu_id, item_id, name, category, description, price, available=True, image_url=''):
    """Update an existing menu item"""
    try:
        updated_data = {
            'item_id': item_id,
            'name': name,
            'category': category,
            'description': description,
            'price': float(price),
            'available': available,
            'image_url': image_url
        }
        
        result = menu_collection.update_one(
            {'_id': ObjectId(menu_id)},
            {'$set': updated_data}
        )
        print(f"✓ Updated menu item: {name}")
        return result.modified_count > 0
    except Exception as e:
        print(f"Error updating menu item: {e}")
        return False


def delete_menu_item(item_id):
    """Delete a menu item by ID"""
    try:
        result = menu_collection.delete_one({'_id': ObjectId(item_id)})
        print(f"✓ Deleted menu item: {item_id}")
        return result.deleted_count > 0
    except Exception as e:
        print(f"Error deleting menu item: {e}")
        return False


# ============================================
# REVIEW OPERATIONS
# ============================================


def get_all_reviews():
    """Retrieve all reviews sorted by newest first"""
    try:
        reviews = list(reviews_collection.find().sort('created_at', -1))  # Sort descending
        print(f"✓ Retrieved {len(reviews)} reviews from MongoDB")
        return reviews
    except Exception as e:
        print(f"Error fetching reviews: {e}")
        return []


def get_reviews_by_user(user_id):
    """Get all reviews by a specific user"""
    try:
        reviews = list(reviews_collection.find({'user_id': user_id}).sort('created_at', -1))
        return reviews
    except Exception as e:
        print(f"Error fetching user reviews: {e}")
        return []


def create_review(user_id, user_name, rating, comment):
    """
    Create a new review.
    
    Schema:
    {
        'user_id': int,           # from Neon users table
        'user_name': str,         # denormalized for display
        'rating': int,            # 1-5 stars
        'comment': str,           # review text
        'created_at': datetime    # timestamp
    }
    """
    try:
        review_data = {
            'user_id': int(user_id),
            'user_name': user_name,
            'rating': int(rating),
            'comment': comment,
            'created_at': datetime.now(timezone.utc)
        }
        
        result = reviews_collection.insert_one(review_data)
        print(f"✓ Created review by {user_name} with rating {rating}")
        return str(result.inserted_id)
    except Exception as e:
        print(f"Error creating review: {e}")
        return None


def delete_review(review_id):
    """Delete a review by ID (admin only)"""
    try:
        result = reviews_collection.delete_one({'_id': ObjectId(review_id)})
        print(f"✓ Deleted review: {review_id}")
        return result.deleted_count > 0
    except Exception as e:
        print(f"Error deleting review: {e}")
        return False


def get_review_stats():
    """Get review statistics"""
    try:
        pipeline = [  # Aggregation pipeline
            {
                '$group': {
                    '_id': None,
                    'total_reviews': {'$sum': 1},
                    'average_rating': {'$avg': '$rating'},
                    'five_star': {
                        '$sum': {'$cond': [{'$eq': ['$rating', 5]}, 1, 0]}
                    },
                    'four_star': {
                        '$sum': {'$cond': [{'$eq': ['$rating', 4]}, 1, 0]}
                    },
                    'three_star': {
                        '$sum': {'$cond': [{'$eq': ['$rating', 3]}, 1, 0]}
                    },
                    'two_star': {
                        '$sum': {'$cond': [{'$eq': ['$rating', 2]}, 1, 0]}
                    },
                    'one_star': {
                        '$sum': {'$cond': [{'$eq': ['$rating', 1]}, 1, 0]}
                    }
                }
            }
        ]
        
        result = list(reviews_collection.aggregate(pipeline))
        
        if result:
            stats = result[0]
            stats['average_rating'] = round(stats['average_rating'], 1) if stats['average_rating'] else 0
            return stats
        else:
            return {
                'total_reviews': 0,
                'average_rating': 0,
                'five_star': 0,
                'four_star': 0,
                'three_star': 0,
                'two_star': 0,
                'one_star': 0
            }
    except Exception as e:
        print(f"Error fetching review stats: {e}")
        return None
