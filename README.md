# Buffetier

Restaurant ordering app. A customer registers, browses the menu, checks out, and can leave a review. An admin account can update order status and edit the menu.

Built for a university cloud module. It ran on Google Cloud for that module and has since been taken down, so there is no live demo. The screenshots below come from a local run with seed data.

![Menu page](docs/screenshots/home.png)

Checkout stores an order and can send a confirmation email. It does not take payment.

## Contents

- [Stack](#stack)
- [Installation](#installation)
- [Configuration](#configuration)
- [Database setup](#database-setup)
- [Run locally](#run-locally)
- [Tests](#tests)
- [Screenshots](#screenshots)
- [Deployment](#deployment)
- [Security](#security)
- [Project structure](#project-structure)

## Stack

What the tree actually uses:

- Python, Flask 3.1.2, Jinja templates
- Bootstrap 5.3.2 and a few vanilla JavaScript files under `app/static/js/`
- PostgreSQL through `psycopg2` in `database/neon_db.py` for users, orders, and order items
- MongoDB through `pymongo` in `database/mongo_db.py`, database `buffetier`, for the `menu` and `reviews` collections
- Flask-WTF for CSRF, Flask-Limiter for rate limits
- SendGrid in `utils/email.py`, called when Secret Manager has `sendgrid-api-key`
- Google Cloud Storage helper in `utils/cloud_storage.py` and Secret Manager helper in `utils/secrets.py`
- Cloud Function source under `cloud-functions/` for `get-menu`, `process-order`, and `update-order`. Those folders are source only.
- pytest for tests, Ruff for linting, GitHub Actions for CI, and Docker Compose for local databases

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
| `FLASK_ENV` | `development`, `testing`, or `production`. Defaults to `development` | No |
| `GOOGLE_CLOUD_PROJECT` | Project id for `utils/secrets.py` | Only if you use Secret Manager |
| `GCS_BUCKET_NAME` | Menu image bucket. Defaults to `buffetier-menu-images` | No |
| `MONGODB_URI` | `cloud-functions/get-menu` only. The Flask app does not read this name | Only that function |
| `PROCESS_ORDER_FUNCTION_URL`, `GET_MENU_FUNCTION_URL`, `UPDATE_ORDER_FUNCTION_URL` | `tests/test_cloud_functions.py`. Unset, those tests skip | No |

The Flask app tries Secret Manager first, then the environment:

- secret `neon-db-uri`, else `DATABASE_URL`
- secret `mongodb-uri`, else `MONGO_URI`
- secret `sendgrid-api-key`, with no environment fallback. Email is skipped if this fails
- secret `maps-api-key` on the location page

`database/mongo_db.py` does not connect when it is imported. The first menu or review call opens MongoDB.

## Database setup

The Postgres tables used by `database/neon_db.py` are in [database/schema.sql](database/schema.sql): `users`, `orders`, and `order_items`. The file is safe to run more than once.


`password_hash` holds a salted PBKDF2 string, about 120 characters, which fits `VARCHAR(255)`.

MongoDB database `buffetier`:

Menu documents: `item_id`, `name`, `category`, `description`, `price`, `available`, `image_url`.

Review documents: `user_id`, `user_name`, `rating` from 1 to 5, `comment`, `created_at`.

### Local databases and seed data

```bash
docker compose up -d
export DATABASE_URL=postgresql://postgres:postgres@localhost:5432/buffetier
export MONGO_URI=mongodb://localhost:27017
python -m database.seed_test_data
```

The seed script creates the schema, empties the tables, and loads two accounts and four menu items. It is for local work and CI only.

| Account | Email | Password |
| --- | --- | --- |
| Admin | `admin@buffetier.test` | `Admin-Pass-1` |
| Customer | `user@buffetier.test` | `User-Pass-1` |

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

### Without a database

```bash
pytest -m "not live_db"
```

This needs no `DATABASE_URL` and no `MONGO_URI`. If `SECRET_KEY` is unset, `tests/conftest.py` sets a throwaway value for the test process only.

### The whole suite

`live_db` marks the tests that read and write PostgreSQL or MongoDB. Run them against the Docker Compose databases from [Local databases and seed data](#local-databases-and-seed-data), never against a database you want to keep, because the seed script empties the tables:

```bash
python -m database.seed_test_data
pytest
```

`tests/test_cloud_functions.py` skips unless `PROCESS_ORDER_FUNCTION_URL`, `GET_MENU_FUNCTION_URL`, and `UPDATE_ORDER_FUNCTION_URL` are set. The deployed functions were taken down with the rest of the module's Google Cloud project, so those tests skip.

### Lint

```bash
pip install ruff==0.17.1
ruff check .
```

### CI

`.github/workflows/tests.yml` runs two jobs on every push to `main` and every pull request:

- **Hermetic:** Ruff, then the suite with no database.
- **Full:** starts PostgreSQL 16 and MongoDB 7 as service containers, seeds them, and runs the whole suite.

## Screenshots

From a local run with the seed data.

| Menu | Cart |
| --- | --- |
| ![Menu](docs/screenshots/home.png) | ![Cart](docs/screenshots/cart.png) |

| Order placed | Admin dashboard |
| --- | --- |
| ![Order placed](docs/screenshots/order-placed.png) | ![Admin dashboard](docs/screenshots/admin-dashboard.png) |

## Deployment

The app ran on Google Cloud for a university module, using Secret Manager for credentials, Cloud Storage for menu images, and Cloud Functions for the menu and order endpoints. That deployment has been taken down, and its `app.yaml` was never tracked; `.gitignore` ignores `app.yaml` and `.env`. `ProductionConfig` and the Secret Manager lookups above are what that deployment used.

## Security

- Passwords: salted PBKDF2-HMAC-SHA256, 600,000 iterations, 16 random bytes of salt, stored as `pbkdf2_sha256$iterations$salt$hash`. A 64-character unsalted SHA-256 hex digest from older rows still verifies. Login does not rewrite that row.
- `/cart`, `/checkout`, and `/dashboard` use `@login_required`. Admin routes use `@admin_required`.
- CSRF tokens on forms through Flask-WTF. Auth routes are limited to 5 requests per minute.
- Session cookie is HTTP-only, `SameSite=Lax`, and `Secure` outside development. Lifetime is 30 minutes.
- SQL uses parameters. Registration checks email, password strength, UK phone numbers, and a short SQL-injection pattern list.

- Every response carries `Content-Security-Policy`, `X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff`, and `Referrer-Policy: strict-origin-when-cross-origin`. `tests/test_security_headers.py` checks them.

The policy allows `'unsafe-inline'` for scripts and styles, because the templates still use inline `onclick` handlers and inline styles. Moving those into the static JavaScript files would let the policy drop it. HTTPS is not enforced in config; that was left to the hosting platform.

## Project structure

```
app/                  Flask factory, blueprints, templates, static files
database/neon_db.py   Postgres users and orders
database/mongo_db.py  MongoDB menu and reviews
database/schema.sql   Postgres schema
database/seed_test_data.py  local and CI seed data
utils/                auth decorators, validation, secrets, storage, email
cloud-functions/      function source for get-menu, process-order, update-order
tests/                pytest suite
config.py             development, testing, and production settings
main.py               entry point
requirements.txt
pytest.ini            live_db marker
pyproject.toml        Ruff settings
docker-compose.yml    local PostgreSQL and MongoDB
docs/screenshots/     screenshots from a local run
.github/workflows/    lint, hermetic tests, full tests
```

Route notes are in [API_DOCUMENTATION.md](API_DOCUMENTATION.md). The production base URL in that file is not a live demo.
