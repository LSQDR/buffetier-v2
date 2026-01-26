# Buffetier API Documentation

Complete REST API reference for the Buffetier restaurant ordering system.

## Base URL

**Local Development:**
```
http://localhost:8080
```

**Production:**
```
https://sys-dev-485117.ew.r.appspot.com/
```

---

## Authentication

Most endpoints require user authentication. Authentication is session-based using Flask sessions.

### Authentication Flow
1. User logs in via `/login` (POST)
2. Session cookie is set with `user_id` and `is_admin`
3. Session persists for 30 minutes
4. Protected endpoints check for `user_id` in session

### Authorization Levels
- **Public**: No authentication required
- **User**: Requires login (`@login_required`)
- **Admin**: Requires admin privileges (`@admin_required`)

---

## Error Responses

All API endpoints return consistent error responses:

```json
{
  "error": "Error message description",
  "success": false
}
```

### HTTP Status Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 201 | Created |
| 400 | Bad Request |
| 401 | Unauthorized |
| 403 | Forbidden |
| 404 | Not Found |
| 429 | Too Many Requests |
| 500 | Internal Server Error |

---

## API Endpoints

### Authentication Endpoints

#### Register New User

**POST** `/register`

Register a new customer account.

**Auth Required:** No  
**Rate Limit:** 5 requests/minute

**Request Body:**
```json
{
  "name": "John Doe",
  "email": "john@example.com",
  "password": "SecurePass123!",
  "phone": "07700900123"
}
```

**Validation Rules:**
- **Name**: 1-100 characters, no HTML
- **Email**: Valid RFC 5322 format, unique
- **Password**: Min 8 chars, uppercase, lowercase, digit, special char
- **Phone**: UK format (optional)

**Success Response:**
```
Redirects to: /login
Flash message: "Registration successful! Please login."
```

**Error Response:**
```html
Renders: auth/register.html with error message
Possible errors:
- "Email already registered"
- "Password must contain at least one uppercase letter"
- "Invalid email format"
```

**cURL Example:**
```bash
curl -X POST http://localhost:8080/register \
  -d "name=John Doe" \
  -d "email=john@example.com" \
  -d "password=SecurePass123!" \
  -d "phone=07700900123"
```

---

#### Login

**POST** `/login`

Authenticate user and create session.

**Auth Required:** No  
**Rate Limit:** 5 requests/minute

**Request Body:**
```json
{
  "email": "john@example.com",
  "password": "SecurePass123!"
}
```

**Success Response:**
```
Redirects to: /menu
Session created with:
- user_id
- user_name
- is_admin
Flash message: "Welcome back, John!"
```

**Error Response:**
```html
Renders: auth/login.html
Flash message: "Invalid email or password"
```

**cURL Example:**
```bash
curl -X POST http://localhost:8080/login \
  -c cookies.txt \
  -d "email=john@example.com" \
  -d "password=SecurePass123!"
```

---

#### Logout

**GET** `/logout`

Clear user session.

**Auth Required:** No

**Success Response:**
```
Redirects to: /
Session cleared
Flash message: "Goodbye, John!"
```

**cURL Example:**
```bash
curl -X GET http://localhost:8080/logout \
  -b cookies.txt
```

---

### Menu Endpoints

#### Get All Menu Items

**GET** `/api/menu`

Retrieve all menu items from MongoDB.

**Auth Required:** No  
**Query Parameters:**
- `category` (optional): Filter by category (e.g., "Starters", "Mains", "Desserts")

**Success Response (200):**
```json
[
  {
    "_id": "507f1f77bcf86cd799439011",
    "item_id": "STARTER_001",
    "name": "Spring Rolls",
    "category": "Starters",
    "description": "Crispy vegetable spring rolls served with sweet chili sauce",
    "price": 5.99,
    "available": true,
    "image_url": "https://storage.googleapis.com/buffetier-menu-images/spring-rolls.jpg"
  },
  {
    "_id": "507f1f77bcf86cd799439012",
    "name": "Pad Thai",
    "category": "Mains",
    "description": "Thai stir-fried noodles with prawns, peanuts and lime",
    "price": 12.99,
    "available": true,
    "image_url": "https://storage.googleapis.com/buffetier-menu-images/pad-thai.jpg"
  }
]
```

**cURL Example:**
```bash
# Get all menu items
curl http://localhost:8080/api/menu

# Filter by category
curl http://localhost:8080/api/menu?category=Starters
```

---

### Cart Endpoints

#### Add Item to Cart

**POST** `/api/cart/add`

Add item to shopping cart.

**Auth Required:** Yes (`@login_required`)  
**Content-Type:** `application/json`

**Request Body:**
```json
{
  "item_id": "STARTER_001",
  "name": "Spring Rolls",
  "price": 5.99,
  "quantity": 2
}
```

**Success Response:**
```json
{
  "success": true,
  "cart_count": 3
}
```

**cURL Example:**
```bash
curl -X POST http://localhost:8080/api/cart/add \
  -b cookies.txt \
  -H "Content-Type: application/json" \
  -d '{
    "item_id": "STARTER_001",
    "name": "Spring Rolls",
    "price": 5.99,
    "quantity": 2
  }'
```

---

#### Get Cart Item Count

**GET** `/api/cart/count`

Get total number of items in cart.

**Auth Required:** No

**Success Response:**
```json
{
  "count": 5
}
```

**cURL Example:**
```bash
curl http://localhost:8080/api/cart/count -b cookies.txt
```

---

#### Update Cart Item Quantity

**PUT** `/api/cart/update`

Update quantity of item in cart.

**Auth Required:** Yes  
**Content-Type:** `application/json`

**Request Body:**
```json
{
  "item_id": "STARTER_001",
  "quantity": 3
}
```

**Success Response:**
```json
{
  "success": true
}
```

**Special Behavior:**
- If `quantity = 0`, item is removed from cart
- If `quantity < 0`, returns error

**cURL Example:**
```bash
curl -X PUT http://localhost:8080/api/cart/update \
  -b cookies.txt \
  -H "Content-Type: application/json" \
  -d '{"item_id": "STARTER_001", "quantity": 3}'
```

---

#### Remove Item from Cart

**DELETE** `/api/cart/remove/<item_id>`

Remove item completely from cart.

**Auth Required:** Yes

**Success Response:**
```json
{
  "success": true
}
```

**cURL Example:**
```bash
curl -X DELETE http://localhost:8080/api/cart/remove/STARTER_001 \
  -b cookies.txt
```

---

#### Clear Cart

**POST** `/api/cart/clear`

Remove all items from cart.

**Auth Required:** Yes

**Success Response:**
```json
{
  "success": true
}
```

**cURL Example:**
```bash
curl -X POST http://localhost:8080/api/cart/clear \
  -b cookies.txt
```

---

### Order Endpoints

#### Create Order

**POST** `/api/orders`

Create a new order from cart items.

**Auth Required:** Yes  
**Content-Type:** `application/json`

**Request Body:**
```json
{
  "user_id": 123,
  "table_number": 5,
  "items": [
    {
      "item_id": "STARTER_001",
      "name": "Spring Rolls",
      "price": 5.99,
      "quantity": 2
    },
    {
      "item_id": "MAIN_003",
      "name": "Pad Thai",
      "price": 12.99,
      "quantity": 1
    }
  ]
}
```

**Success Response:**
```json
{
  "order_id": 42,
  "total": 24.97
}
```

**Error Response:**
```json
{
  "error": "Missing user_id or items"
}
```

**Side Effects:**
- Order stored in `orders` table
- Items stored in `order_items` table
- Email confirmation sent to user (if configured)

**cURL Example:**
```bash
curl -X POST http://localhost:8080/api/orders \
  -b cookies.txt \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 123,
    "table_number": 5,
    "items": [
      {"item_id": "STARTER_001", "name": "Spring Rolls", "price": 5.99, "quantity": 2}
    ]
  }'
```

---

#### Get User Orders

**GET** `/api/orders/<user_id>`

Get all orders for a specific user.

**Auth Required:** Yes 

**Success Response:**
```json
[
  {
    "order_id": 42,
    "total_price": 24.97,
    "status": "preparing",
    "created_at": "2026-01-26 13:45:00"
  },
  {
    "order_id": 41,
    "total_price": 18.99,
    "status": "completed",
    "created_at": "2026-01-25 19:30:00"
  }
]
```

**cURL Example:**
```bash
curl http://localhost:8080/api/orders/123 -b cookies.txt
```

---

#### Update Order Status

**PUT** `/api/orders/<order_id>`

Update order status.

**Auth Required:** Yes  
**Content-Type:** `application/json`

**Request Body:**
```json
{
  "status": "ready"
}
```

**Valid Status Values:**
- `pending`
- `confirmed`
- `preparing`
- `ready`
- `completed`
- `cancelled`

**Success Response:**
```json
{
  "status": "updated",
  "order_id": 42
}
```

**cURL Example:**
```bash
curl -X PUT http://localhost:8080/api/orders/42 \
  -b cookies.txt \
  -H "Content-Type: application/json" \
  -d '{"status": "ready"}'
```

---

### Review Endpoints

#### Get All Reviews

**GET** `/api/reviews`

Get all customer reviews.

**Auth Required:** No

**Success Response:**
```json
[
  {
    "_id": "65abc123def456789",
    "user_id": 123,
    "user_name": "John Doe",
    "rating": 5,
    "comment": "Excellent food and service! Highly recommend the Pad Thai.",
    "created_at": "2026-01-26T13:45:00Z"
  },
  {
    "_id": "65abc123def456790",
    "user_id": 124,
    "user_name": "Jane Smith",
    "rating": 4,
    "comment": "Great atmosphere, good food. Would visit again.",
    "created_at": "2026-01-25T18:20:00Z"
  }
]
```

**cURL Example:**
```bash
curl http://localhost:8080/api/reviews
```

---

#### Submit Review

**POST** `/api/reviews/submit`

Submit a new review (authenticated users only).

**Auth Required:** Yes  
**Content-Type:** `application/json`  
**CSRF:** Exempt

**Request Body:**
```json
{
  "rating": 5,
  "comment": "Excellent food and service! Highly recommend the Pad Thai."
}
```

**Validation Rules:**
- **rating**: Integer 1-5 (required)
- **comment**: 10-500 characters (required)

**Success Response:**
```json
{
  "success": true,
  "review_id": "65abc123def456789",
  "message": "Review submitted successfully!"
}
```

**Error Response:**
```json
{
  "error": "Invalid rating. Must be 1-5"
}
```

**Possible Errors:**
- "Invalid rating. Must be 1-5"
- "Comment must be at least 10 characters"
- "Comment must be less than 500 characters"

**cURL Example:**
```bash
curl -X POST http://localhost:8080/api/reviews/submit \
  -b cookies.txt \
  -H "Content-Type: application/json" \
  -d '{
    "rating": 5,
    "comment": "Excellent food and service!"
  }'
```

---

### Admin Endpoints

All admin endpoints require `@admin_required` decorator.

#### Update Order Status

**POST** `/admin/order/<order_id>/update`

Update order status and send email notification.

**Auth Required:** Admin  
**Content-Type:** `application/x-www-form-urlencoded`

**Request Body:**
```
status=preparing
```

**Success Response:**
```
Redirects to: /admin
Flash message: "Order #42 updated to preparing and email sent"
```

**Side Effects:**
- Order status updated in database
- Email notification sent to customer via SendGrid

**cURL Example:**
```bash
curl -X POST http://localhost:8080/admin/order/42/update \
  -b admin-cookies.txt \
  -d "status=preparing"
```

---

#### Delete Order 

**POST** `/admin/order/<order_id>/delete`

Delete an order and all its items.

**Auth Required:** Admin

**Success Response:**
```
Redirects to: /admin
Flash message: "Order #42 deleted"
```

**Side Effects:**
- Order deleted from `orders` table
- Related records cascade deleted from `order_items` table

**cURL Example:**
```bash
curl -X POST http://localhost:8080/admin/order/42/delete \
  -b admin-cookies.txt
```

---

#### Create Menu Item

**POST** `/admin/menu/create`

Create a new menu item.

**Auth Required:** Admin  
**Content-Type:** `application/x-www-form-urlencoded`

**Request Body:**
```
item_id=DESSERT_005
name=Chocolate Lava Cake
category=Desserts
description=Warm chocolate cake with molten center
price=6.99
available=on
image_url=https://storage.googleapis.com/buffetier-menu-images/lava-cake.jpg
```

**Success Response :**
```
Redirects to: /admin/menu
Flash message: "Menu item created"
```

**cURL Example:**
```bash
curl -X POST http://localhost:8080/admin/menu/create \
  -b admin-cookies.txt \
  -d "item_id=DESSERT_005" \
  -d "name=Chocolate Lava Cake" \
  -d "category=Desserts" \
  -d "description=Warm chocolate cake" \
  -d "price=6.99" \
  -d "available=on" \
  -d "image_url=https://..."
```

---

#### Update Menu Item 

**POST** `/admin/menu/<item_id>/update`

Update existing menu item.

**Auth Required:** Admin

**Request Body:** Same as Create Menu Item

**Success Response:**
```
Redirects to: /admin/menu
Flash message: "Menu item updated"
```

---

#### Delete Menu Item 

**POST** `/admin/menu/<item_id>/delete`

Delete a menu item.

**Auth Required:** Admin

**Success Response:**
```
Redirects to: /admin/menu
Flash message: "Menu item deleted"
```

**cURL Example:**
```bash
curl -X POST http://localhost:8080/admin/menu/507f1f77bcf86cd799439011/delete \
  -b admin-cookies.txt
```

---

#### Delete Review 

**POST** `/admin/review/<review_id>/delete`

Delete a customer review (moderation).

**Auth Required:** Admin

**Success Response (302 Redirect):**
```
Redirects to: /admin/reviews
Flash message: "Review deleted"
```

**cURL Example:**
```bash
curl -X POST http://localhost:8080/admin/review/65abc123def456789/delete \
  -b admin-cookies.txt
```

---

#### Upload Menu Image 

**POST** `/admin/api/upload-image`

Upload menu item image to Google Cloud Storage.

**Auth Required:** Admin  
**Content-Type:** `multipart/form-data`

**Request Body:**
```
image: <binary file data>
```

**File Requirements:**
- **Formats**: PNG, JPG, JPEG, WebP
- **Max Size**: Automatically resized to 1024x1024
- **Optimization**: Converted to JPEG, 85% quality

**Success Response:**
```json
{
  "success": true,
  "url": "https://storage.googleapis.com/buffetier-menu-images/menu-items/20260126_134500_spring-rolls.jpg"
}
```

**Error Response:**
```json
{
  "error": "Invalid file type. Use PNG, JPG, JPEG, or WebP"
}
```

**cURL Example:**
```bash
curl -X POST http://localhost:8080/admin/api/upload-image \
  -b admin-cookies.txt \
  -F "image=@spring-rolls.jpg"
```

---

## Cloud Functions API

### Get Menu 

**GET** `https://REGION-PROJECT_ID.cloudfunctions.net/get-menu`

Retrieve menu items directly from MongoDB via Cloud Function.

**Query Parameters:**
- `category` optional: Filter by category
- `available` optional: "true" to show only available items

**Success Response:**
```json
{
  "success": true,
  "count": 12,
  "menu": [
    {
      "_id": "507f1f77bcf86cd799439011",
      "name": "Spring Rolls",
      "category": "Starters",
      "price": 5.99,
      "available": true
    }
  ]
}
```

**cURL Example:**
```bash
curl https://europe-west2-your-project.cloudfunctions.net/get-menu?category=Starters
```

---

### Process Order 
**POST** `https://REGION-PROJECT_ID.cloudfunctions.net/process-order`

Create order directly via Cloud Function (bypasses main app).

**Request Body:**
```json
{
  "user_id": 123,
  "table_number": 5,
  "total_price": 24.97,
  "special_instructions": "No peanuts please",
  "items": [
    {
      "menu_item_id": "STARTER_001",
      "name": "Spring Rolls",
      "quantity": 2,
      "price": 5.99
    }
  ]
}
```

**Success Response:**
```json
{
  "success": true,
  "order_id": 42,
  "message": "Order processed successfully",
  "status": "pending",
  "items_count": 2
}
```

---

### Update Order Status

**PUT/POST** `https://REGION-PROJECT_ID.cloudfunctions.net/update-order`

Update order status directly via Cloud Function.

**Request Body:**
```json
{
  "order_id": 42,
  "status": "preparing"
}
```

**Success Response:**
```json
{
  "success": true,
  "order_id": 42,
  "old_status": "pending",
  "new_status": "preparing",
  "message": "Order status updated from pending to preparing"
}
```

---

## Postman Collection

Import this collection to test all endpoints:

```json
{
  "info": {
    "name": "Buffetier API",
    "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
  },
  "item": [
    {
      "name": "Auth",
      "item": [
        {
          "name": "Register",
          "request": {
            "method": "POST",
            "url": "{{base_url}}/register",
            "body": {
              "mode": "urlencoded",
              "urlencoded": [
                {"key": "name", "value": "Test User"},
                {"key": "email", "value": "test@example.com"},
                {"key": "password", "value": "SecurePass123!"},
                {"key": "phone", "value": "07700900123"}
              ]
            }
          }
        }
      ]
    }
  ]
}
```

---

## Rate Limiting

| Endpoint | Limit |
|----------|-------|
| `/register` | 5 requests/minute |
| `/login` | 5 requests/minute |
| All others  | 200 requests/day, 50 requests/hour |

**Rate Limit Headers:**
```
X-RateLimit-Limit: 5
X-RateLimit-Remaining: 4
X-RateLimit-Reset: 1706280360
```

---

## Webhooks 

Currently not implemented, but architecture supports:
- Order status change webhooks
- Payment confirmation webhooks
- Inventory low-stock alerts

---

**Last Updated:** January 26, 2026  
**API Version:** 1.0  
