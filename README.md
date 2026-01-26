# Buffetier - Cloud-Based Restaurant Ordering System

A modern, full-stack restaurant ordering application built with Flask and deployed on Google Cloud Platform. Features real-time order management, menu administration, customer reviews, and secure payment processing.

[![Python](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.1.2-green.svg)](https://flask.palletsprojects.com/)
[![GCP](https://img.shields.io/badge/GCP-App%20Engine-orange.svg)](https://cloud.google.com/appengine)

##  Project Overview

Buffetier is a cloud-native restaurant ordering system that demonstrates enterprise-level architecture using:
- **Microservices**: Serverless Cloud Functions for scalable operations
- **Dual Databases**: PostgreSQL for transactional data, MongoDB for flexible content
- **Cloud Storage**: Image hosting for menu items
- **Security**: RBAC, CSRF protection, rate limiting, input validation
- **Email Notifications**: SendGrid integration for order confirmations

---

##  Table of Contents

- [Features](#-features)
- [Architecture](#-architecture)
- [Technology Stack](#-technology-stack)
- [Prerequisites](#-prerequisites)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [Database Setup](#-database-setup)
- [Deployment](#-deployment)
- [API Documentation](#-api-documentation)
- [Testing](#-testing)
- [Security Features](#-security-features)
- [Project Structure](#-project-structure)

---

##  Features

### Customer Features
-  **User Authentication** - Secure registration and login with password hashing
-  **Menu Browser** - View categorized menu items with images and descriptions
-  **Shopping Cart** - Add, update, remove items with real-time total calculation
-  **Order Tracking** - Monitor order status from pending to completed
-  **Reviews System** - Submit ratings (1-5 stars) and written reviews
-  **Email Notifications** - Order confirmations and status updates via SendGrid

### Admin Features
-  **Dashboard** - Real-time order statistics and revenue tracking
-  **Order Management** - Update order status, delete orders
-  **Menu CRUD** - Create, read, update, delete menu items with image uploads
-  **Review Moderation** - Delete inappropriate reviews
-  **Cloud Storage** - Upload optimized menu images to Google Cloud Storage

### Technical Features
-  **Serverless Functions** - 3 Cloud Functions for menu, orders, and status updates
-  **Security** - CSRF protection, rate limiting, XSS prevention, SQL injection protection
-  **Dual Database** - PostgreSQL for users/orders, MongoDB for menu/reviews
-  **Responsive UI** - Bootstrap 5 with custom styling
-  **Secret Management** - Credentials stored in Google Secret Manager
-  **Email Integration** - Professional HTML email templates

---

##  Architecture

### System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Client (Browser)                         │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              Google App Engine (Flask App)                  │
│  ┌─────────────┬──────────────┬──────────────┬───────────┐ │
│  │   Auth BP   │   Main BP    │  Orders BP   │ Admin BP  │ │
│  │   Reviews   │    API BP    │   Errors BP  │           │ │
│  └─────────────┴──────────────┴──────────────┴───────────┘ │
└────────┬────────────┬───────────────┬──────────────┬────────┘
         │            │               │              │
         ▼            ▼               ▼              ▼
┌──────────────┐ ┌─────────────┐ ┌──────────┐ ┌──────────────┐
│   Neon DB    │ │  MongoDB    │ │  Cloud   │ │   SendGrid   │
│ (PostgreSQL) │ │  Atlas      │ │ Storage  │ │    Email     │
│              │ │             │ │          │ │              │
│ • users      │ │ • menu      │ │ • images │ │ • order conf │
│ • orders     │ │ • reviews   │ │          │ │ • status upd │
│ • order_items│ │             │ │          │ │              │
└──────────────┘ └─────────────┘ └──────────┘ └──────────────┘
         ▲            ▲               ▲
         │            │               │
         └────────────┴───────────────┘
                     │
      ┌──────────────┴──────────────┐
      │  Google Cloud Functions     │
      │  • get-menu                 │
      │  • process-order            │
      │  • update-order             │
      └─────────────────────────────┘
```

### Request Flow Example: Place Order

1. **User submits order** → Cart page
2. **POST /checkout** → Orders Blueprint
3. **Create order** → Neon PostgreSQL orders + order_items tables
4. **Send email** → SendGrid API confirmation email
5. **Clear cart** → Session management
6. **Redirect** → User dashboard with success message

---

##  Technology Stack

### Backend
- **Framework**: Flask 3.1.2
- **Language**: Python 3.12
- **ORM/Database Drivers**: psycopg2-binary, pymongo
- **Authentication**: Flask-WTF (CSRF), custom decorators
- **Rate Limiting**: Flask-Limiter

### Databases
- **PostgreSQL**: Neon users, orders, order_items
- **MongoDB**: Atlas menu items, reviews

### Cloud Services
- **Hosting**: Google App Engine Python 3.12 runtime
- **Functions**: Cloud Functions 
- **Storage**: Cloud Storage 
- **Secrets**: Secret Manager 

### External Services
- **Email**: SendGrid API
- **Maps**: Google Maps API

### Security
- **CSRF Protection**: Flask-WTF
- **Rate Limiting**: Flask-Limiter 
- **Input Validation**: bleach, email-validator, custom validators
- **Password Hashing**: SHA-256
- **XSS Prevention**: HTML sanitization
- **SQL Injection**: Parameterized queries

### Frontend
- **UI Framework**: Bootstrap 5
- **Icons**: Bootstrap Icons
- **JavaScript**: Vanilla JS

---

##  Database Setup

### PostgreSQL Neon Schema

```sql
-- Users table
CREATE TABLE users (
    user_id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    phone VARCHAR(20),
    password_hash VARCHAR(255) NOT NULL,
    is_admin BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Orders table
CREATE TABLE orders (
    order_id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(user_id),
    table_number INTEGER DEFAULT 0,
    total_price DECIMAL(10,2) NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    special_instructions TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Order items table
CREATE TABLE order_items (
    item_id SERIAL PRIMARY KEY,
    order_id INTEGER REFERENCES orders(order_id) ON DELETE CASCADE,
    menu_item_id VARCHAR(50),
    item_name VARCHAR(100) NOT NULL,
    quantity INTEGER NOT NULL,
    price DECIMAL(10,2) NOT NULL
);
```

### MongoDB Collections

**Menu Collection Schema:**
```json
{
  "_id": ObjectId,
  "item_id": "string",
  "name": "string",
  "category": "string",
  "description": "string",
  "price": float,
  "available": boolean,
  "image_url": "string"
}
```

**Reviews Collection Schema:**
```json
{
  "_id": ObjectId,
  "user_id": integer,
  "user_name": "string",
  "rating": integer (1-5),
  "comment": "string",
  "created_at": datetime
}
```

##  API Documentation

See [API_DOCUMENTATION.md] for complete API reference including:
- All REST endpoints
- Request/response formats
- Authentication requirements
- Example requests with curl/Postman

Quick Reference:

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/api/menu` | GET | None | Get all menu items |
| `/api/orders` | POST | Required | Create new order |
| `/api/cart/add` | POST | Required | Add item to cart |
| `/api/reviews/submit` | POST | Required | Submit review |

---

##  Testing

### Test Categories

1. **Authentication Tests** 
   - User registration validation
   - Login/logout functionality
   - Session management

2. **Admin Tests** 
   - Admin authentication
   - Menu CRUD operations
   - Order management
   - Review moderation

3. **API Tests** 
   - Menu endpoints
   - Order creation
   - Cart operations

4. **Database Tests** 
   - Neon PostgreSQL operations
   - MongoDB operations
   - Connection handling

5. **Security Tests** 
   - Input validation
   - XSS prevention
   - SQL injection prevention
   - CSRF protection
   - Rate limiting

---

##  Security Features

### 1. Authentication & Authorization
- **Password Hashing**: SHA-256 encryption
- **Session Management**: 30-minute timeout, HTTP-only cookies
- **Role-Based Access Control (RBAC)**: Admin vs regular users
- **Decorators**: `@login_required`, `@admin_required`

### 2. Input Validation
- **Email**: RFC 5322 compliant validation
- **Password**: Min 8 chars, uppercase, lowercase, digit, special char
- **Phone**: UK format validation
- **HTML Sanitization**: Bleach library for XSS prevention

### 3. Attack Prevention
- **CSRF Protection**: Flask-WTF tokens on all forms
- **SQL Injection**: Parameterized queries
- **XSS Prevention**: HTML escaping and sanitization
- **Rate Limiting**: 5 requests/min on auth endpoints

### 4. Secure Configuration
- **Environment Variables**: Sensitive data in .env files
- **Secret Manager**: Production credentials in GCP Secret Manager
- **HTTPS Only**: Enforced via `secure: always` in app.yaml
- **Security Headers**: Content-Security-Policy, X-Frame-Options

### 5. Audit Logging
- Security events logged with timestamps, user IDs, IP addresses
- Tracks unauthorized access attempts and privilege escalation

---

##  Project Structure

```
buffetier/
├── app/
│   ├── __init__.py              # App factory
│   ├── extensions.py            # Flask extensions
│   ├── blueprints/              # Route blueprints
│   │   ├── main.py             # Home, menu, location
│   │   ├── auth.py             # Login, register, logout
│   │   ├── orders.py           # Cart, checkout, dashboard
│   │   ├── reviews.py          # Reviews system
│   │   ├── admin.py            # Admin panel
│   │   ├── api.py              # REST API endpoints
│   │   └── errors.py           # Error handlers
│   ├── models/
│   │   └── user.py             # User model with validation
│   ├── templates/              # Jinja2 templates
│   └── static/                 # CSS, JS, images
├── database/
│   ├── neon_db.py              # PostgreSQL operations
│   └── mongo_db.py             # MongoDB operations
├── utils/
│   ├── auth.py                 # Auth decorators
│   ├── validation.py           # Input validation
│   ├── secrets.py              # Secret Manager helper
│   ├── cloud_storage.py        # GCS image uploads
│   └── email.py                # SendGrid integration
├── cloud-functions/
│   ├── get-menu/               # Menu retrieval function
│   ├── process-order/          # Order creation function
│   └── update-order/           # Status update function
├── tests/                      # pytest test suite
├── config.py                   # Configuration classes
├── main.py                     # Application entry point
├── app.yaml                    # App Engine config
├── requirements.txt            # Python dependencies
└── .env                        # Environment variables
```

---
