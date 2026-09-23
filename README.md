# Buffetier

Restaurant ordering app. A customer registers, browses the menu, checks out, and can leave a review. An admin account can update order status and edit the menu.

There is no public demo.

Checkout stores an order and can send a confirmation email. It does not take payment.

## Contents

- [Stack](#stack)
- [Installation](#installation)
- [Configuration](#configuration)
- [Database setup](#database-setup)
- [Run locally](#run-locally)
- [Tests](#tests)
- [Deployment](#deployment)
- [Security](#security)
- [Project structure](#project-structure)

## Stack

What the tree actually uses:

- Python, Flask 3.1.2, Jinja templates
- Bootstrap 5.3.2 and a few vanilla JavaScript files under `app/static/js/`
- PostgreSQL through `psycopg2` in `database/neon_db.py` (users, orders, order items)
- MongoDB through `pymongo` in `database/mongo_db.py` (database `buffetier`, collections `menu` and `reviews`)
- Flask-WTF for CSRF, Flask-Limiter for rate limits
- SendGrid in `utils/email.py`, called when Secret Manager has `sendgrid-api-key`
- Google Cloud Storage helper in `utils/cloud_storage.py` and Secret Manager helper in `utils/secrets.py`
- Cloud Function source under `cloud-functions/` for `get-menu`, `process-order`, and `update-order`. Those folders are source only.

## Installation

Python 3.12.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Configuration

Copy these into the environment, or into a `.env` file next to `main.py`. `python-dotenv` loads that file. `.env` is gitignored. Do not commit it.

| Variable | Used by | Required |
| --- | --- | --- |
| `SECRET_KEY` | Flask session signing. `ProductionConfig` raises if this is missing. Development reads it and does not invent a key. | Yes, to sign sessions |
| `DATABASE_URL` | Postgres URL for `database/neon_db.py` when Secret Manager is unavailable | Yes, for users and orders |
| `MONGO_URI` | MongoDB URL for `database/mongo_db.py` when Secret Manager is unavailable | Yes, for the menu and reviews |
| `FLASK_ENV` | `development` (default), `testing`, or `production` | No |
| `GOOGLE_CLOUD_PROJECT` | Project id for `utils/secrets.py` | Only if you use Secret Manager |
| `GCS_BUCKET_NAME` | Menu image bucket. Defaults to `buffetier-menu-images` | No |
| `MONGODB_URI` | `cloud-functions/get-menu` only. The Flask app does not read this name | Only that function |
| `PROCESS_ORDER_FUNCTION_URL`, `GET_MENU_FUNCTION_URL`, `UPDATE_ORDER_FUNCTION_URL` | `tests/test_cloud_functions.py`. Unset, those tests skip | No |

The Flask app tries Secret Manager first, then the environment:

- secret `neon-db-uri`, else `DATABASE_URL`
- secret `mongodb-uri`, else `MONGO_URI`
- secret `sendgrid-api-key` (no environment fallback; email is skipped if this fails)
- secret `maps-api-key` on the location page

`database/mongo_db.py` does not connect when it is imported. The first menu or review call opens MongoDB.

## Database setup

Postgres tables used by `database/neon_db.py`:

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

CREATE TABLE orders (
    order_id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(user_id),
    table_number INTEGER DEFAULT 0,
    total_price DECIMAL(10,2) NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    special_instructions TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE order_items (
    item_id SERIAL PRIMARY KEY,
    order_id INTEGER REFERENCES orders(order_id) ON DELETE CASCADE,
    menu_item_id VARCHAR(50),
    item_name VARCHAR(100) NOT NULL,
    quantity INTEGER NOT NULL,
    price DECIMAL(10,2) NOT NULL
);
```

`password_hash` holds a salted PBKDF2 string, about 120 characters, which fits `VARCHAR(255)`.

MongoDB database `buffetier`:

Menu documents: `item_id`, `name`, `category`, `description`, `price`, `available`, `image_url`.

Review documents: `user_id`, `user_name`, `rating` (1–5), `comment`, `created_at`.

## Run locally

```bash
export SECRET_KEY="choose-a-long-random-string"
export DATABASE_URL="postgresql://USER:PASSWORD@HOST/DB"
export MONGO_URI="mongodb+srv://USER:PASSWORD@HOST/buffetier"
export FLASK_ENV=development
python main.py
```

The process listens on `http://127.0.0.1:8080`. GET `/`, `/login`, and `/register` render without a database. Signing in, the menu, checkout, reviews, and admin screens need `DATABASE_URL` and `MONGO_URI`.

## Tests

```bash
pytest --collect-only
pytest -m "not live_db"
```

Collection and `pytest -m "not live_db"` need no `DATABASE_URL` and no `MONGO_URI`. If `SECRET_KEY` is unset, `tests/conftest.py` sets a throwaway value for the test process only. That is not a production key.

`live_db` marks tests that open Neon or MongoDB and write rows (`tests/test_database.py`, `tests/test_crud_operations.py`, `tests/test_reviews.py`, and the menu/order cases in the API, admin, and security files). Run them only against a database you are willing to change:

```bash
pytest -m live_db
```

`tests/test_cloud_functions.py` imports `requests` and skips unless the three function URL variables above are set. GitHub Actions (`.github/workflows/tests.yml`) installs `requirements.txt` and runs the hermetic suite on `main`.

## Deployment

Nothing in this repo is deployed. There is no public demo, no tracked `app.yaml`, and no screenshot. `.gitignore` ignores `app.yaml` and `.env`. Do not treat a Cloud Function folder or a Storage helper as a running service.

## Security

- Passwords: salted PBKDF2-HMAC-SHA256, 600,000 iterations, 16 random bytes of salt, stored as `pbkdf2_sha256$iterations$salt$hash`. A 64-character unsalted SHA-256 hex digest from older rows still verifies. Login does not rewrite that row.
- `/cart`, `/checkout`, and `/dashboard` use `@login_required`. Admin routes use `@admin_required`.
- CSRF tokens on forms (Flask-WTF). Auth routes are limited to 5 requests per minute.
- Session cookie is HTTP-only, `SameSite=Lax`, and `Secure` outside development. Lifetime is 30 minutes.
- SQL uses parameters. Registration checks email, password strength, UK phone numbers, and a short SQL-injection pattern list.

This tree does not set `Content-Security-Policy` or `X-Frame-Options`, and it does not enforce HTTPS in config. Those headers are not applied by an `app.yaml` here because that file is not in the tree.

## Project structure

```
app/                  Flask factory, blueprints, templates, static files
database/neon_db.py   Postgres users and orders
database/mongo_db.py  MongoDB menu and reviews
utils/                auth decorators, validation, secrets, storage, email
cloud-functions/      function source (get-menu, process-order, update-order)
tests/                pytest suite
config.py             development, testing, and production settings
main.py               entry point
requirements.txt
pytest.ini            live_db marker
.github/workflows/    hermetic pytest
```

Route notes are in [API_DOCUMENTATION.md](API_DOCUMENTATION.md). The production base URL in that file is not a live demo.
