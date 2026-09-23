"""Importing the MongoDB module must not open a connection."""


def test_collections_stay_disconnected_until_used():
    from database.mongo_db import menu_collection, reviews_collection

    assert type(menu_collection).__name__ == "_LazyCollection"
    assert type(reviews_collection).__name__ == "_LazyCollection"
