# WE Sole API

WE Sole is a Flask REST API for managing a personal sneaker wishlist. Users can register, log in, view or update their profile, and create, view, update, and delete wishlist items.

Each wishlist item belongs to the user who created it. Protected endpoints use a JWT bearer token, and the API checks ownership before returning or changing an individual item.

## Project overview

- **Backend:** Python 3.12, Flask 3
- **Database:** PostgreSQL for Docker Compose and production; SQLite is available for simple local development
- **ORM and migrations:** Flask-SQLAlchemy, Flask-Migrate, and Alembic
- **Authentication:** JWT tokens and hashed passwords
- **Production server:** Gunicorn
- **Container setup:** Docker and Docker Compose

## Repository structure

```text
.
├── app/
│   ├── auth/              # Registration, login, profile, JWT protection
│   ├── health/            # Health-check endpoint
│   ├── wishlist/          # Wishlist routes
│   ├── config.py          # Development, testing, production settings
│   ├── extensions.py      # Shared SQLAlchemy and Flask-Migrate objects
│   └── __init__.py        # create_app() application factory
├── migrations/            # Committed Alembic database migrations
├── docs/                  # API, database, and project documentation
├── Dockerfile
├── docker-compose.yml
├── gunicorn.conf.py
├── requirements.txt
└── wsgi.py                # WSGI entry point used by Gunicorn
```

The application uses one `create_app()` factory. Both local Flask commands and the Docker/Gunicorn container load the app through `wsgi.py`; Docker does not use a separate application implementation.

## API endpoints

| Method | Endpoint | Purpose | Authentication |
|---|---|---|---|
| POST | `/auth/register` | Create an account | No |
| POST | `/auth/login` | Log in and receive a JWT | No |
| GET | `/auth/profile` | View the signed-in user's profile | Yes |
| PUT | `/auth/profile` | Update the signed-in user's profile | Yes |
| GET | `/wishlist_items` | List the signed-in user's wishlist | Yes |
| POST | `/wishlist_items` | Add a sneaker to the wishlist | Yes |
| GET | `/wishlist_items/{id}` | View one wishlist item | Yes |
| PUT | `/wishlist_items/{id}` | Update one wishlist item | Yes |
| DELETE | `/wishlist_items/{id}` | Delete one wishlist item | Yes |
| GET | `/health` | Check whether the API is responding | No |

See [API endpoints](docs/api-endpoints.md), [database design](docs/database-design.md), and [project scope](docs/project-scope.md) for more detail.

## Requirements

For local development:
- Python 3.12 or newer
- Git

For the container setup:
- Docker Desktop (or Docker Engine)
- Docker Compose v2

## Run locally with Python

1. Clone the repository and enter the project directory:

   ```bash
   git clone https://github.com/killjoyincbigcartel-cmd/sole-.git
   cd sole-
   ```

2. Create and activate a virtual environment:

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

   On Windows PowerShell, activate it with `.venv\\Scripts\\Activate.ps1`.

3. Install dependencies:

   ```bash
   python -m pip install --upgrade pip
   python -m pip install -r requirements.txt
   ```

4. Create your local environment file:

   ```bash
   cp .env.example .env
   ```

   Check that `.env` has `FLASK_CONFIG=development`, a development-only `JWT_SECRET`, and `DATABASE_URL=sqlite:///dev.db`. Never commit real secrets.

5. Apply the committed database migrations:

   ```bash
   flask --app wsgi db upgrade
   ```

6. Start the development server:

   ```bash
   flask --app wsgi run
   ```

   The API is available at `http://127.0.0.1:5000`.

## Run with Docker Compose

Docker Compose runs two services:

- **db:** PostgreSQL 17, with a readiness health check and a named persistent volume.
- **web:** The WE Sole Flask API, built from the repository's Dockerfile and served by Gunicorn.

The web service waits until PostgreSQL is healthy before it starts. Compose passes the database connection string and JWT secret to the web container as environment variables. The database password and JWT secret stay in your local environment file, not in the image or source code. This follows the Compose service dependency and health-check behavior described in the [Docker Compose documentation](https://docs.docker.com/compose/how-tos/startup-order/).

### 1. Create the Docker environment file

From the project root, copy the example:

```bash
cp .env.compose.example .env.docker
```

Open `.env.docker` and replace the example values for:

- `POSTGRES_DB`
- `POSTGRES_USER`
- `POSTGRES_PASSWORD`
- `JWT_SECRET`

You can generate a strong URL-safe JWT secret with:

```bash
python3 -c 'import secrets; print(secrets.token_urlsafe(48))'
```

Use a unique database password and JWT secret. Keep `.env.docker` private. It is listed in `.gitignore` and must not be committed.

### 2. Start PostgreSQL and wait for it to become healthy

```bash
docker compose --env-file .env.docker up -d db
docker compose --env-file .env.docker ps
```

Wait until the `db` service reports `healthy`. The health check uses PostgreSQL's `pg_isready` command.

### 3. Build the API image

```bash
docker compose --env-file .env.docker build web
```

The Dockerfile installs the packages in `requirements.txt`, copies the application into the image, and runs Gunicorn as a non-root application user.

### 4. Apply database migrations

Run the existing migrations inside a one-time web container:

```bash
docker compose --env-file .env.docker run --rm web flask --app wsgi db upgrade
```

This creates or updates the database tables. The migration files are already in `migrations/`, so a fresh database needs `db upgrade`; do not run `db init` again.

Migrations are an explicit setup step. They are not automatically run every time the web container starts.

### 5. Start the API

```bash
docker compose --env-file .env.docker up -d web
```

You can also build and start both services in one command:

```bash
docker compose --env-file .env.docker up --build -d
```

If you use the one-command option on a brand-new database, still run the migration command from step 4 before testing the API. The web service may start before the tables exist.

### 6. Verify the containers and API

Check service status:

```bash
docker compose --env-file .env.docker ps
```

Check the health endpoint:

```bash
curl -i http://127.0.0.1:8000/health
```

A successful response is `HTTP/1.1 200 OK` with:

```json
{"status":"ok"}
```

The API is available at `http://127.0.0.1:8000`.

### 7. Test registration, login, and wishlist routes

Register a test user:

```bash
curl -i -X POST http://127.0.0.1:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "local_tester",
    "email": "local_tester@example.com",
    "password": "TestPassword123!"
  }'
```

A new account returns `201 Created`. If you already registered that username or email, use a different one; duplicate accounts return `409 Conflict`.

Log in:

```bash
curl -i -X POST http://127.0.0.1:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "local_tester@example.com",
    "password": "TestPassword123!"
  }'
```

A successful login returns `200 OK` and a JSON `token`. Copy that token into your terminal without sharing it:

```bash
TOKEN='paste_the_token_value_here'
```

Create a wishlist item:

```bash
curl -i -X POST http://127.0.0.1:8000/wishlist_items \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "sneaker_name": "Air Jordan 4 Retro",
    "brand": "Jordan",
    "size": 10,
    "target_price": 220.00,
    "priority": 1,
    "notes": "Docker Compose test"
  }'
```

A successful create returns `201 Created`. Retrieve the signed-in user's wishlist:

```bash
curl -i http://127.0.0.1:8000/wishlist_items \
  -H "Authorization: Bearer $TOKEN"
```

A successful list request returns `200 OK` and an `items` array. The same bearer-token pattern is used for the protected profile and individual wishlist-item routes.

### 8. View logs and stop the stack

View the API logs:

```bash
docker compose --env-file .env.docker logs -f web
```

Stop the containers and network:

```bash
docker compose --env-file .env.docker down
```

The named `postgres_data` volume preserves PostgreSQL data when containers are stopped or removed. **Only** use the following command if you intentionally want to delete the database contents and start fresh:

```bash
docker compose --env-file .env.docker down -v
```

## Deploy on Render

The live API is deployed at:

- API base URL: https://we-sole-api.onrender.com
- Health check: https://we-sole-api.onrender.com/health

The Render deployment uses a separate PostgreSQL database service (`we-sole-db`) and a Docker web service (`we-sole-api`). The web service builds from this repository's Dockerfile and starts Gunicorn with `wsgi:app`.

Configure these environment variables on the Render web service:

| Variable | Value |
|---|---|
| `FLASK_CONFIG` | `production` |
| `DATABASE_URL` | The PostgreSQL connection URL supplied by the Render database |
| `JWT_SECRET` | A long, randomly generated secret |

Use the database's internal connection URL when the web service and database are in the same Render region. This project uses the `psycopg2` driver, so the SQLAlchemy URL scheme must be `postgresql+psycopg2://`. Do not put database credentials or JWT secrets in GitHub or in the Docker image.

Set the Render health-check path to `/health`. A request to `/` may return 404 because the API does not define a homepage route; that does not mean the health endpoint or API is down.

### Run migrations against the Render database

When deploying to a new or empty production database, apply the migrations once before using database-backed endpoints. One way is to run the migration from your local project environment using the Render database's **external** connection URL:

```bash
export DATABASE_URL='postgresql+psycopg2://<external-user>:<external-password>@<external-host>:<port>/<database>'
FLASK_CONFIG=production flask --app wsgi db upgrade
unset DATABASE_URL
```

Replace the placeholders locally with the external URL from Render. Never paste the real URL into README files, source control, screenshots, or chat. The local Python environment must have the project's requirements installed, including `psycopg2-binary`.

After migration, confirm the deployed service responds:

```bash
curl -i https://we-sole-api.onrender.com/health
```

Then repeat the registration, login, create-wishlist, and list-wishlist requests above, replacing `http://127.0.0.1:8000` with `https://we-sole-api.onrender.com`.

## Environment variables

| Variable | Used by | Purpose |
|---|---|---|
| `FLASK_CONFIG` | Local and production app | Selects `development`, `testing`, or `production` configuration |
| `JWT_SECRET` | API | Signs and verifies JWTs; required in production |
| `DATABASE_URL` | API | Database connection URL; SQLite locally or PostgreSQL in Docker/Render |
| `POSTGRES_DB` | Docker Compose database | Name of the PostgreSQL database |
| `POSTGRES_USER` | Docker Compose database | PostgreSQL username |
| `POSTGRES_PASSWORD` | Docker Compose database | PostgreSQL password |
| `HOST_PORT` | Docker Compose | Host port mapped to the API; defaults to `8000` |

The `.env.example` file is for local Python development. The `.env.compose.example` file is the template for Docker Compose. Copy the latter to `.env.docker` and pass it with `--env-file .env.docker` for Compose commands.

## Database migrations

This project uses Flask-Migrate and Alembic. The committed migration history creates the users table, adds the user role, and creates the wishlist items table.

For local development:

```bash
flask --app wsgi db upgrade
```

After changing a model, create a migration and apply it:

```bash
flask --app wsgi db migrate -m "describe your change"
flask --app wsgi db upgrade
```

For Docker Compose, run Flask commands through the web service/container with the same `--env-file .env.docker` option used to start the stack.

## Security

- Passwords are stored as password hashes, not plain text.
- Protected routes require a valid JWT sent as `Authorization: Bearer <token>`.
- The API derives the owner ID from the authenticated token; it does not trust a client-supplied owner ID.
- Users can only access their own wishlist items.
- Production startup requires `DATABASE_URL` and `JWT_SECRET`.
- Keep `.env`, `.env.docker`, database passwords, and JWT secrets out of source control.

## Troubleshooting

- **The API returns 500 after a new database is created:** check the web logs and confirm the database migrations have been applied.
- **The web container starts before PostgreSQL is ready:** check `docker compose ps`; the Compose web service is configured to wait for the database health check.
- **The database driver cannot be loaded:** install dependencies from `requirements.txt` and confirm the URL starts with `postgresql+psycopg2://`.
- **The API returns 404 at the root URL:** use `/health` to check service health; a root homepage is not part of this API.
- **A registration request returns 409:** the username or email is already registered; use a new test account.

## Project documentation

- [API endpoints](docs/api-endpoints.md)
- [Database design](docs/database-design.md)
- [Project scope](docs/project-scope.md)
