
import pytest

from database import mongo_db

pytestmark = pytest.mark.live_db


class TestReviewSystem:
    """Test suite for Phase 4 - Review System"""

    def test_create_review(self):
        """Test creating a new review"""
        # Test data
        user_id = 999
        user_name = "Test Reviewer"
        rating = 5
        comment = "This is a test review for the restaurant. Great food and service!"

        # Create review
        review_id = mongo_db.create_review(user_id, user_name, rating, comment)

        assert review_id is not None, "Review creation failed"
        assert isinstance(review_id, str), "Review ID should be a string"

        # Verify review was added
        reviews = mongo_db.get_all_reviews()
        found = False
        for review in reviews:
            if str(review['_id']) == review_id:
                found = True
                assert review['user_id'] == user_id, "User ID mismatch"
                assert review['user_name'] == user_name, "User name mismatch"
                assert review['rating'] == rating, "Rating mismatch"
                assert review['comment'] == comment, "Comment mismatch"
                assert 'created_at' in review, "Missing created_at timestamp"
                break

        assert found, "Review not found in database after creation"

        # Cleanup
        mongo_db.delete_review(review_id)


    def test_get_all_reviews(self):
        """Test retrieving all reviews"""
        # Create test reviews
        review_ids = []
        for i in range(3):
            review_id = mongo_db.create_review(
                user_id=1000 + i,
                user_name=f"Test User {i}",
                rating=4 + (i % 2),  # Alternating 4 and 5 stars
                comment=f"Test review number {i} with sufficient length to pass validation."
            )
            review_ids.append(review_id)

        # Fetch all reviews
        reviews = mongo_db.get_all_reviews()

        assert isinstance(reviews, list), "Reviews should be returned as a list"
        assert len(reviews) >= 3, "Should have at least 3 reviews"

        # Verify structure of reviews
        for review in reviews[:3]:
            assert '_id' in review, "Review missing _id"
            assert 'user_id' in review, "Review missing user_id"
            assert 'user_name' in review, "Review missing user_name"
            assert 'rating' in review, "Review missing rating"
            assert 'comment' in review, "Review missing comment"
            assert 'created_at' in review, "Review missing created_at"

            # Validate rating range
            assert 1 <= review['rating'] <= 5, "Rating should be between 1 and 5"

        # Cleanup
        for review_id in review_ids:
            mongo_db.delete_review(review_id)


    def test_admin_delete_review(self):
        """Test admin can delete reviews"""
        # Create a test review
        review_id = mongo_db.create_review(
            user_id=888,
            user_name="Test User to Delete",
            rating=3,
            comment="This review will be deleted by admin for testing purposes."
        )

        assert review_id is not None, "Failed to create test review"

        # Verify review exists
        reviews = mongo_db.get_all_reviews()
        exists_before = any(str(r['_id']) == review_id for r in reviews)
        assert exists_before, "Review should exist before deletion"

        # Delete review (admin action)
        delete_success = mongo_db.delete_review(review_id)
        assert delete_success is True, "Delete operation should return True"

        # Verify review is deleted
        reviews_after = mongo_db.get_all_reviews()
        exists_after = any(str(r['_id']) == review_id for r in reviews_after)
        assert not exists_after, "Review should not exist after deletion"


    def test_review_stats(self):
        """Bonus test: Verify review statistics calculation"""
        # Create reviews with known ratings
        review_ids = []
        ratings = [5, 5, 4, 3, 2]

        for i, rating in enumerate(ratings):
            review_id = mongo_db.create_review(
                user_id=2000 + i,
                user_name=f"Stats Test User {i}",
                rating=rating,
                comment=f"Test review with {rating} stars for statistics testing."
            )
            review_ids.append(review_id)

        # Get stats
        stats = mongo_db.get_review_stats()

        assert stats is not None, "Stats should not be None"
        assert 'total_reviews' in stats, "Missing total_reviews"
        assert 'average_rating' in stats, "Missing average_rating"
        assert stats['total_reviews'] >= 5, "Should have at least 5 reviews"

        # Average should be (5+5+4+3+2)/5 = 3.8
        expected_avg = sum(ratings) / len(ratings)
        assert abs(stats['average_rating'] - expected_avg) < 0.5, "Average rating calculation issue"

        # Cleanup
        for review_id in review_ids:
            mongo_db.delete_review(review_id)
