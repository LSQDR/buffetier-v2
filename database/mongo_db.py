
import os
from pymongo import MongoClient
from datetime import datetime
from bson import ObjectId


def get_mongo_connection():
    """
    Establish connection to MongoDB with optimized timeouts.
    
    Returns:
        MongoDB database instance
    """
    mongo_uri = os.environ.get('MONGO_URI')
    
    if not mongo_uri:
        raise ValueError("MONGO_URI environment variable not set!")
    
    client = MongoClient(
        mongo_uri,
        serverSelectionTimeoutMS=30000,  # 30 second timeout
        connectTimeoutMS=30000,
        socketTimeoutMS=30000
    )
    return client['buffetier']


def get_all_menu_items():
    """
    Fetch all available menu items.
    
    Returns:
        list: List of menu item dictionaries
    """
    db = get_mongo_connection()
    
    # Check both possible collection names
    if 'menu_items' in db.list_collection_names():
        items = list(db.menu_items.find())
    elif 'menu' in db.list_collection_names():
        items = list(db.menu.find({"available": True}))
    else:
        items = []
    
    # Convert ObjectId to string for JSON serialization
    for item in items:
        if '_id' in item:
            item['_id'] = str(item['_id'])
    
    return items


def get_menu_by_category(category):
    """
    Fetch menu items by category.
    
    Args:
        category (str): Category name
        
    Returns:
        list: List of menu items in that category
    """
    db = get_mongo_connection()
    
    # Check both possible collection names
    if 'menu_items' in db.list_collection_names():
        items = list(db.menu_items.find({"category": category}))
    elif 'menu' in db.list_collection_names():
        items = list(db.menu.find({"category": category, "available": True}))
    else:
        items = []
    
    # Convert ObjectId to string
    for item in items:
        if '_id' in item:
            item['_id'] = str(item['_id'])
    
    return items


def add_review(user_name, rating, comment):
    """
    Add a customer review.
    
    Args:
        user_name (str): Name of reviewer
        rating (int): Rating 1-5
        comment (str): Review comment
        
    Returns:
        str: Inserted review ID
    """
    db = get_mongo_connection()
    
    review = {
        "user_name": user_name,
        "rating": rating,
        "comment": comment,
        "created_at": datetime.now()
    }
    
    result = db.reviews.insert_one(review)
    return str(result.inserted_id)


def get_all_reviews():
    """
    Get all reviews.
    
    Returns:
        list: List of review dictionaries
    """
    db = get_mongo_connection()
    reviews = list(db.reviews.find())
    
    # Convert ObjectId and datetime to strings
    for review in reviews:
        if '_id' in review:
            review['_id'] = str(review['_id'])
        if 'created_at' in review:
            review['created_at'] = str(review['created_at'])
    
    return reviews


def delete_review(review_id):
    """
    Delete a review.
    
    Args:
        review_id (str): Review ID to delete
    """
    db = get_mongo_connection()
    db.reviews.delete_one({"_id": ObjectId(review_id)})

def create_menu_item(item_id, name, category, description, price, available=True, image_url=''):
    """
    Create a new menu item.
    
    Args:
        item_id (str): Unique item ID (e.g., 'BUFF001')
        name (str): Item name
        category (str): Category name
        description (str): Item description
        price (float): Item price
        available (bool): Whether item is available
        image_url (str): Image URL
        
    Returns:
        str: Inserted item ID
    """
    db = get_mongo_connection()
    
    new_item = {
        'item_id': item_id,
        'name': name,
        'category': category,
        'description': description,
        'price': price,
        'available': available,
        'image_url': image_url
    }
    
    result = db.menu.insert_one(new_item)
    return str(result.inserted_id)


def update_menu_item(menu_id, item_id, name, category, description, price, available, image_url=''):
    """
    Update an existing menu item.
    
    Args:
        menu_id (str): MongoDB _id of the item
        item_id (str): Item ID
        name (str): Item name
        category (str): Category name
        description (str): Item description
        price (float): Item price
        available (bool): Whether item is available
        image_url (str): Image URL
        
    Returns:
        bool: True if successful
    """
    db = get_mongo_connection()
    
    updated_item = {
        'item_id': item_id,
        'name': name,
        'category': category,
        'description': description,
        'price': price,
        'available': available,
        'image_url': image_url
    }
    
    result = db.menu.update_one(
        {'_id': ObjectId(menu_id)}, 
        {'$set': updated_item}
    )
    return result.modified_count > 0 or result.matched_count > 0



def delete_menu_item(menu_id):
    """
    Delete a menu item.
    
    Args:
        menu_id (str): MongoDB _id of the item to delete
        
    Returns:
        bool: True if successful
    """
    db = get_mongo_connection()
    result = db.menu.delete_one({'_id': ObjectId(menu_id)})
    return result.deleted_count > 0
