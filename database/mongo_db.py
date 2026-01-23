from pymongo import MongoClient
from bson import ObjectId
import os

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

# Initialize
try:
    client = get_mongo_client()
    db = client['buffetier']
    menu_collection = db['menu']
    reviews_collection = db['reviews']
    print("✓ MongoDB connected successfully")
except Exception as e:
    print(f"✗ MongoDB connection failed: {e}")
    raise


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
    """Retrieve all reviews"""
    try:
        reviews = list(reviews_collection.find())
        return reviews
    except Exception as e:
        print(f"Error fetching reviews: {e}")
        return []


def create_review(review_data):
    """Create a new review"""
    try:
        result = reviews_collection.insert_one(review_data)
        return str(result.inserted_id)
    except Exception as e:
        print(f"Error creating review: {e}")
        return None


def delete_review(review_id):
    """Delete a review by ID"""
    try:
        result = reviews_collection.delete_one({'_id': ObjectId(review_id)})
        return result.deleted_count > 0
    except Exception as e:
        print(f"Error deleting review: {e}")
        return False
