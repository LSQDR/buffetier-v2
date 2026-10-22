"""
User Model
Handles user-related database operations with enhanced validation
"""

from database.neon_db import authenticate_user, get_neon_connection, get_user_by_email, get_user_by_id, register_user
from utils.validation import (
    contains_sql_injection_patterns,
    sanitize_html_input,
    validate_email_address,
    validate_password_strength,
    validate_phone_number,
)


class User:
    """User model for database operations with security validation"""

    @staticmethod
    def validate_email(email):
        """
        Validate email using enhanced validation

        Args:
            email: Email address to validate

        Returns:
            tuple: (is_valid, normalized_email or error_message)
        """
        return validate_email_address(email)

    @staticmethod
    def validate_password(password):
        """
        Validate password strength with enhanced requirements
        - Minimum 8 characters
        - At least one uppercase letter
        - At least one lowercase letter
        - At least one digit
        - At least one special character

        Args:
            password: Password to validate

        Returns:
            tuple: (is_valid, error_message or None)
        """
        return validate_password_strength(password)

    @staticmethod
    def validate_phone(phone):
        """
        Validate UK phone number

        Args:
            phone: Phone number to validate

        Returns:
            tuple: (is_valid, normalized_phone or error_message)
        """
        if not phone:
            return True, ""
        return validate_phone_number(phone)

    @staticmethod
    def create(name, email, password, phone=None):
        """
        Create a new user with enhanced security validation

        Args:
            name: User's name
            email: User's email
            password: Plain text password
            phone: User's phone number (optional)

        Returns:
            tuple: (success, user_id or error_message)
        """
        # Sanitize inputs to prevent XSS attacks
        name = sanitize_html_input(name)
        email = sanitize_html_input(email)

        # Check for SQL injection patterns
        if contains_sql_injection_patterns(name):
            return False, "Invalid characters in name"
        if contains_sql_injection_patterns(email):
            return False, "Invalid characters in email"

        # Validate email with normalization
        is_valid, result = validate_email_address(email)
        if not is_valid:
            return False, result
        normalized_email = result

        # Validate password strength
        is_valid, error = validate_password_strength(password)
        if not is_valid:
            return False, error

        # Validate and sanitize phone if provided
        if phone:
            phone = sanitize_html_input(phone)
            is_valid, error_or_normalized = validate_phone_number(phone)
            if not is_valid:
                return False, error_or_normalized
            normalized_phone = error_or_normalized
        else:
            normalized_phone = ''

        # Check if user exists
        if get_user_by_email(normalized_email):
            return False, "Email already registered"

        # Create user with normalized data
        user_id = register_user(
            name=name,
            email=normalized_email,
            password=password,
            phone=normalized_phone,
            is_admin=False
        )

        if user_id:
            return True, user_id
        else:
            return False, "Registration failed. Please try again."

    @staticmethod
    def authenticate(email, password):
        """
        Authenticate user with sanitized input

        Args:
            email: User's email
            password: Plain text password

        Returns:
            dict or None: User data if authenticated, None otherwise
        """
        # Sanitize email input
        email = sanitize_html_input(email)
        return authenticate_user(email, password)

    @staticmethod
    def get_by_email(email):
        """
        Get user by email

        Args:
            email: User's email

        Returns:
            dict or None: User data if found, None otherwise
        """
        email = sanitize_html_input(email)
        return get_user_by_email(email)

    @staticmethod
    def get_by_id(user_id):
        """
        Get user by ID

        Args:
            user_id: User's ID

        Returns:
            dict or None: User data if found, None otherwise
        """
        return get_user_by_id(user_id)

    @staticmethod
    def update_profile(user_id, name=None, phone=None):
        """
        Update user profile with validation

        Args:
            user_id: User's ID
            name: New name (optional)
            phone: New phone (optional)

        Returns:
            tuple: (success, error_message or None)
        """
        # Sanitize inputs
        if name:
            name = sanitize_html_input(name)
            if contains_sql_injection_patterns(name):
                return False, "Invalid characters in name"

        if phone:
            phone = sanitize_html_input(phone)
            is_valid, error_or_normalized = validate_phone_number(phone)
            if not is_valid:
                return False, error_or_normalized
            phone = error_or_normalized

        conn = get_neon_connection()
        cur = conn.cursor()

        try:
            updates = []
            params = []

            if name:
                updates.append("name = %s")
                params.append(name)
            if phone is not None:
                updates.append("phone = %s")
                params.append(phone)

            if not updates:
                return True, None

            params.append(user_id)
            query = f"UPDATE users SET {', '.join(updates)} WHERE user_id = %s"

            cur.execute(query, params)
            conn.commit()
            cur.close()
            conn.close()
            return True, None
        except Exception as e:
            print(f"Error updating profile: {e}")
            if conn:
                conn.rollback()
                conn.close()
            return False, "Failed to update profile"
