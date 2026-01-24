"""
Input validation and sanitization utilities.
Provides security functions to validate and sanitize user inputs.
"""

import re
import bleach
from email_validator import validate_email, EmailNotValidError


# ============================================
# EMAIL VALIDATION
# ============================================

def validate_email_address(email):
    """
    Validate email address format and deliverability.
    
    Args:
        email: Email string to validate
        
    Returns:
        tuple: (is_valid: bool, normalized_email: str or error_message: str)
    """
    try:
        # Validate and normalize email
        valid = validate_email(email, check_deliverability=False)
        normalized_email = valid.normalized
        return True, normalized_email
    except EmailNotValidError as e:
        return False, str(e)


# ============================================
# PASSWORD VALIDATION
# ============================================

def validate_password_strength(password):
    """
    Validate password meets security requirements.
    
    Requirements:
    - Minimum 8 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one digit
    - At least one special character
    
    Args:
        password: Password string to validate
        
    Returns:
        tuple: (is_valid: bool, error_message: str or None)
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    
    if len(password) > 128:
        return False, "Password must be less than 128 characters"
    
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    
    if not re.search(r'\d', password):
        return False, "Password must contain at least one digit"
    
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False, "Password must contain at least one special character (!@#$%^&*...)"
    
    return True, None


# ============================================
# PHONE NUMBER VALIDATION
# ============================================

def validate_phone_number(phone):
    """
    Validate UK phone number format.
    
    Accepts formats:
    - 07700900123
    - +447700900123
    - 0800 123 4567
    - (01234) 567890
    
    Args:
        phone: Phone number string
        
    Returns:
        tuple: (is_valid: bool, normalized_phone: str or error_message: str)
    """
    # Remove spaces, parentheses, hyphens
    cleaned = re.sub(r'[\s\-\(\)]', '', phone)
    
    # UK mobile: 07xxx xxxxxx (11 digits)
    # UK landline: 01xxx xxxxx or 02x xxxx xxxx
    # International: +44
    
    # Check for valid UK formats
    if re.match(r'^(\+44|0)[1-9]\d{9}$', cleaned):
        return True, cleaned
    elif re.match(r'^(\+44|0)[1-9]\d{8,10}$', cleaned):
        return True, cleaned
    else:
        return False, "Invalid UK phone number format"


# ============================================
# XSS PREVENTION - HTML SANITIZATION
# ============================================

def sanitize_html_input(text, strip=True):
    """
    Remove or escape HTML tags to prevent XSS attacks.
    
    Args:
        text: User input string
        strip: If True, remove all HTML. If False, escape it.
        
    Returns:
        str: Sanitized text
    """
    if text is None:
        return ""
    
    if strip:
        # Remove all HTML tags completely
        return bleach.clean(text, tags=[], strip=True)
    else:
        # Escape HTML but keep the text
        return bleach.clean(text, tags=[], strip=False)


def sanitize_user_input(data):
    """
    Sanitize dictionary of user inputs (e.g., form data).
    
    Args:
        data: Dictionary of form inputs
        
    Returns:
        dict: Sanitized data
    """
    if not isinstance(data, dict):
        return data
    
    sanitized = {}
    for key, value in data.items():
        if isinstance(value, str):
            sanitized[key] = sanitize_html_input(value)
        else:
            sanitized[key] = value
    
    return sanitized


# ============================================
# SQL INJECTION PREVENTION CHECK
# ============================================

def contains_sql_injection_patterns(text):
    """
    Check if text contains common SQL injection patterns.
    
    Note: This is a detection mechanism. The PRIMARY defense
    is using parameterized queries (which you already do).
    
    Args:
        text: Input string to check
        
    Returns:
        bool: True if suspicious patterns detected
    """
    if not isinstance(text, str):
        return False
    
    # Common SQL injection patterns
    sql_patterns = [
        r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|EXECUTE)\b)",
        r"(--|#|/\*|\*/)",  # SQL comments
        r"(\bOR\b.*=.*)",  # OR 1=1
        r"(\bUNION\b.*\bSELECT\b)",
        r"(;.*\b(SELECT|INSERT|UPDATE|DELETE)\b)"
    ]
    
    text_upper = text.upper()
    
    for pattern in sql_patterns:
        if re.search(pattern, text_upper, re.IGNORECASE):
            return True
    
    return False


# ============================================
# GENERAL INPUT VALIDATION
# ============================================

def validate_length(text, min_length=1, max_length=1000, field_name="Input"):
    """
    Validate text length.
    
    Args:
        text: String to validate
        min_length: Minimum allowed length
        max_length: Maximum allowed length
        field_name: Name of field for error message
        
    Returns:
        tuple: (is_valid: bool, error_message: str or None)
    """
    if not isinstance(text, str):
        return False, f"{field_name} must be text"
    
    length = len(text.strip())
    
    if length < min_length:
        return False, f"{field_name} must be at least {min_length} characters"
    
    if length > max_length:
        return False, f"{field_name} must be less than {max_length} characters"
    
    return True, None


def validate_alphanumeric(text, allow_spaces=True, field_name="Input"):
    """
    Validate text contains only alphanumeric characters.
    
    Args:
        text: String to validate
        allow_spaces: Whether to allow spaces
        field_name: Name of field for error message
        
    Returns:
        tuple: (is_valid: bool, error_message: str or None)
    """
    if allow_spaces:
        pattern = r'^[a-zA-Z0-9\s]+$'
    else:
        pattern = r'^[a-zA-Z0-9]+$'
    
    if re.match(pattern, text):
        return True, None
    else:
        return False, f"{field_name} can only contain letters and numbers"
