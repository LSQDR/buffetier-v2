"""
Phase 5 Security Tests
Tests for input validation, RBAC enforcement, and session security.
"""

import pytest
from main import app
from database import mongo_db, neon_db
from utils.validation import (
    validate_password_strength,
    validate_email_address,
    validate_phone_number,
    sanitize_html_input,
    contains_sql_injection_patterns
)


class TestInputValidation:
    """Test input validation and sanitization"""
    
    def test_password_validation_rejects_weak_passwords(self):
        """Test that weak passwords are rejected"""
        
        # Too short
        valid, error = validate_password_strength("short")
        assert valid is False
        assert "8 characters" in error
        
        # No uppercase
        valid, error = validate_password_strength("password123!")
        assert valid is False
        assert "uppercase" in error
        
        # No lowercase
        valid, error = validate_password_strength("PASSWORD123!")
        assert valid is False
        assert "lowercase" in error
        
        # No digit
        valid, error = validate_password_strength("Password!")
        assert valid is False
        assert "digit" in error
        
        # No special character
        valid, error = validate_password_strength("Password123")
        assert valid is False
        assert "special character" in error
        
        # Valid strong password
        valid, error = validate_password_strength("SecurePass123!")
        assert valid is True
        assert error is None
    
    
    def test_email_validation_rejects_invalid_emails(self):
        """Test that invalid email formats are rejected"""
        
        # Invalid formats
        invalid_emails = [
            "notanemail",
            "@example.com",
            "user@",
            "user name@example.com",
            "user@.com",
            ""
        ]
        
        for email in invalid_emails:
            valid, result = validate_email_address(email)
            assert valid is False, f"Should reject invalid email: {email}"
        
        # Valid emails
        valid_emails = [
            "user@example.com",
            "test.user@example.co.uk",
            "user+tag@example.com"
        ]
        
        for email in valid_emails:
            valid, result = validate_email_address(email)
            assert valid is True, f"Should accept valid email: {email}"
    
    
    def test_phone_validation_rejects_invalid_formats(self):
        """Test that invalid phone numbers are rejected"""
        
        # Invalid formats
        invalid_phones = [
            "123",
            "abcdefghij",
            "1234567890123456",
            "+1234567890"
        ]
        
        for phone in invalid_phones:
            valid, result = validate_phone_number(phone)
            assert valid is False, f"Should reject invalid phone: {phone}"
        
        # Valid UK formats
        valid_phones = [
            "07700900123",
            "+447700900123",
            "01234567890",
            "02012345678"
        ]
        
        for phone in valid_phones:
            valid, result = validate_phone_number(phone)
            assert valid is True, f"Should accept valid phone: {phone}"
    
    
    def test_html_sanitization_prevents_xss(self):
        """Test that HTML is sanitized to prevent XSS attacks"""
        
        # Malicious inputs
        xss_attempts = [
            "<script>alert('XSS')</script>",
            "<img src=x onerror=alert('XSS')>",
            "<iframe src='evil.com'></iframe>",
            "<a href='javascript:alert(1)'>Click</a>"
        ]
        
        for malicious in xss_attempts:
            sanitized = sanitize_html_input(malicious)
            # Should not contain script tags or javascript
            assert "<script>" not in sanitized.lower()
            assert "javascript:" not in sanitized.lower()
            assert "<iframe" not in sanitized.lower()
    
    
    def test_sql_injection_detection(self):
        """Test that SQL injection patterns are detected"""
        
        # SQL injection attempts
        sql_injections = [
            "'; DROP TABLE users; --",
            "1' OR '1'='1",
            "admin'--",
            "1 UNION SELECT * FROM users",
            "'; DELETE FROM orders WHERE '1'='1"
        ]
        
        for injection in sql_injections:
            detected = contains_sql_injection_patterns(injection)
            assert detected is True, f"Should detect SQL injection: {injection}"
        
        # Normal inputs
        normal_inputs = [
            "John Doe",
            "test@example.com",
            "Regular comment here"
        ]
        
        for normal in normal_inputs:
            detected = contains_sql_injection_patterns(normal)
            assert detected is False, f"Should not flag normal input: {normal}"



class TestRBACEnforcement:
    """Test Role-Based Access Control"""
    
    def test_unauthorized_users_blocked_from_admin_routes(self):
        """Test that non-admin users cannot access admin routes"""
        
        with app.test_client() as client:
            # Try to access admin dashboard without login
            response = client.get('/admin', follow_redirects=False)
            assert response.status_code == 302  # Should redirect
            assert '/login' in response.location or response.location.endswith('login')
            
            # Try to access admin menu without login
            response = client.get('/admin/menu', follow_redirects=False)
            assert response.status_code == 302
            
            # Try to access admin reviews without login
            response = client.get('/admin/reviews', follow_redirects=False)
            assert response.status_code == 302
    
    
    def test_non_admin_users_cannot_access_admin_routes(self):
        """Test that regular users (non-admin) are blocked from admin pages"""
        
        with app.test_client() as client:
            with client.session_transaction() as sess:
                # Set session as regular user (not admin)
                sess['user_id'] = 999
                sess['user_name'] = 'Regular User'
                sess['is_admin'] = False
            
            # Try to access admin dashboard
            response = client.get('/admin', follow_redirects=False)
            assert response.status_code == 302  # Should redirect
            
            # Try to access admin menu
            response = client.get('/admin/menu', follow_redirects=False)
            assert response.status_code == 302
    
    
    def test_admin_users_can_access_admin_routes(self):
        """Test that admin users can access admin routes"""
        
        with app.test_client() as client:
            with client.session_transaction() as sess:
                # Set session as admin user
                sess['user_id'] = 1
                sess['user_name'] = 'Admin User'
                sess['is_admin'] = True
            
            # Admin dashboard
            response = client.get('/admin')
            assert response.status_code == 200
            
            # Admin menu
            response = client.get('/admin/menu')
            assert response.status_code == 200
            
            # Admin reviews
            response = client.get('/admin/reviews')
            assert response.status_code == 200



class TestSessionSecurity:
    """Test session security features"""
    
    def test_session_cleared_on_logout(self):
        """Test that session is completely cleared on logout"""
        
        with app.test_client() as client:
            # Login (simulate)
            with client.session_transaction() as sess:
                sess['user_id'] = 123
                sess['user_name'] = 'Test User'
                sess['is_admin'] = False
            
            # Logout
            response = client.get('/logout', follow_redirects=True)
            
            # Check session is cleared
            with client.session_transaction() as sess:
                assert 'user_id' not in sess
                assert 'user_name' not in sess
                assert 'is_admin' not in sess
    
    
    def test_protected_routes_require_authentication(self):
        """Test that protected routes redirect to login"""
        
        with app.test_client() as client:
            protected_routes = [
                '/dashboard',
                '/cart',
                '/admin',
                '/admin/menu',
                '/admin/reviews'
            ]
            
            for route in protected_routes:
                response = client.get(route, follow_redirects=False)
                assert response.status_code == 302, f"Route {route} should redirect"
                # Should redirect to login or index
                assert '/login' in response.location or '/' in response.location
