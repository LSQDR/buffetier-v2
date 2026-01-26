# Database Schema Documentation

Complete database schema reference for Buffetier's dual-database architecture.

---

## Database Architecture Overview

Buffetier uses a **dual-database architecture** combining:

1. **PostgreSQL (Neon)** - Relational data requiring ACID transactions
2. **MongoDB (Atlas)** - Flexible, document-based data

### Why Dual Databases?

| Feature | PostgreSQL | MongoDB |
|---------|------------|---------|
| **Data Structure** | Fixed schema, normalized | Flexible schema, documents |
| **Use Case** | Financial transactions, user auth | Content management, reviews |
| **Relationships** | Foreign keys, joins | Embedded documents, refs |
| **Consistency** | ACID guarantees | Eventual consistency |

---

## PostgreSQL Tables

### users Table

```sql
CREATE TABLE users (
    user_id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    phone VARCHAR(20),
    password_hash VARCHAR(255) NOT NULL,
    is_admin BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### orders Table

```sql
CREATE TABLE orders (
    order_id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(user_id),
    table_number INTEGER DEFAULT 0,
    total_price DECIMAL(10,2) NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    special_instructions TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### order_items Table

```sql
CREATE TABLE order_items (
    item_id SERIAL PRIMARY KEY,
    order_id INTEGER REFERENCES orders(order_id) ON DELETE CASCADE,
    menu_item_id VARCHAR(50),
    item_name VARCHAR(100) NOT NULL,
    quantity INTEGER NOT NULL,
    price DECIMAL(10,2) NOT NULL
);
```

---

## MongoDB Collections

### menu Collection

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

### reviews Collection

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

---

**Schema Version:** 1.0
