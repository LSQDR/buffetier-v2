import os
from pymongo import MongoClient
from datetime import datetime

def get_mongo_client():
    """Get MongoDB client"""
    return MongoClient(os.environ.get('MONGO_URI'))

def get_all_menu_items():
    """Fetch all available menu items"""
    client = get_mongo_client()
    db = client.buffetier
    items = list(db.menu.find({"available": True}, {"_id": 0}))
    client.close()
    return items

def get_menu_by_category(category):
    """Fetch menu items by category"""
    client = get_mongo_client()
    db = client.buffetier
    items = list(db.menu.find(
        {"category": category, "available": True},
        {"_id": 0}
    ))
    client.close()
    return items

def add_review(user_name, rating, comment):
    """Add a customer review"""
    client = get_mongo_client()
    db = client.buffetier
    
    review = {
        "user_name": user_name,
        "rating": rating,
        "comment": comment,
        "created_at": datetime.now()
    }
    
    result = db.reviews.insert_one(review)
    client.close()
    return result.inserted_id

def get_all_reviews():
    """Get all reviews"""
    client = get_mongo_client()
    db = client.buffetier
    reviews = list(db.reviews.find({}, {"_id": 0}))
    client.close()
    return reviews

def delete_review(review_id):
    """Delete a review"""
    from bson import ObjectId
    client = get_mongo_client()
    db = client.buffetier
    db.reviews.delete_one({"_id": ObjectId(review_id)})
    client.close()
