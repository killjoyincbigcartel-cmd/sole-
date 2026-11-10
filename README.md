# WE Sole API

WE Sole is a sneaker wishlist REST API. Users can register, log in, manage their profile, and keep track of sneakers they want to buy.

## Project goal

The API is built around users and one main resource: `wishlist_items`. Each wishlist item belongs to the authenticated user who created it, and users should only be able to view or change their own items.

## Main user story

> As a sneaker enthusiast, I want to save, view, update, and delete sneakers from my wishlist so I can keep track of the shoes I want to buy.

## API overview

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/auth/register` | Create an account |
| POST | `/auth/login` | Log in and receive an authentication token |
| GET | `/auth/profile` | View the current user's profile |
| PUT | `/auth/profile` | Update the current user's profile |
| GET | `/wishlist_items` | List the current user's wishlist |
| POST | `/wishlist_items` | Add a sneaker to the wishlist |
| GET | `/wishlist_items/{id}` | View one wishlist item |
| PUT | `/wishlist_items/{id}` | Update one wishlist item |
| DELETE | `/wishlist_items/{id}` | Remove one wishlist item |
| GET | `/health` | Check that the API is responding |

See [API endpoints](docs/api-endpoints.md), [database design](docs/database-design.md), and [project scope](docs/project-scope.md) for more details.

## Security notes

- Passwords are stored as secure hashes, never as plain text.
- Protected routes require a valid authentication token.
- The server gets the item's owner ID from the authenticated user instead of trusting an owner ID supplied in the request body.
- Requests to another user's item are denied without exposing private data.
- Keep JWT secrets and database passwords out of source control.

## Requirements

- Python 3.12 or newer for local development
- Docker Desktop with Docker Compose for the container setup

## Run locally

1. Clone the repository and enter the project folder:

   ```bash
   git clone https://github.com/killjoyincbigcartel-cmd/sole-.git
   cd sole-
   ```

2. Create and activate a virtual environment:

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. Install dependencies:

   ```bash
   python -m pip install --upgrade pip
   python -m pip install -r requirements.txt
   ```

4. Copy the local environment example and set a development JWT secret:

   ```bash
   cp .env.example .env
   ```

   Make sure `.env` has the settings needed for local development. A SQLite development database can use `DATABASE_URL=sqlite:///dev.db`, and Flask uses `FLASK_CONFIG=development`. Do not commit real secrets.

5. Apply the existing database migrations:

   ```bash
   flask --app wsgi db upgrade
   ```

6. Start the Flask app:

   ```bash
   flask --app wsgi run
   ```

   The app should be available at `http://127.0.0.1:5000`.

## Run with Docker Compose

Docker Compose starts the Flask API and PostgreSQL database together. The web container runs Gunicorn with `wsgi:app`. The `wsgi.py` entry point calls the same `create_app()` application factory used for local development; there is no separate Docker-only factory or app code path.

### 1. Configure the Docker environment

Copy the Compose example to a separate file so it does not overwrite your local `.env`:

```bash
cp .env.compose.example .env.docker
```

Open `.env.docker` and set the values for:

- `POSTGRES_DB`
- `POSTGRES_USER`
- `POSTGRES_PASSWORD`
- `JWT_SECRET`

You can generate a URL-safe JWT secret with:

```bash
python3 -c 'import secrets; print(secrets.token_urlsafe(48))'
```

Use a strong, unique database password. The example values are for local development only. Keep `.env.docker` private and do not commit it.

### 2. Build and start PostgreSQL

```bash
docker compose --env-file .env.docker up -d db
docker compose --env-file .env.docker build web
```

The database has a health check. Compose waits for PostgreSQL to become healthy before starting the web service.

### 3. Apply database migrations

Run the migrations inside the web image:

```bash
docker compose --env-file .env.docker run --rm web flask --app wsgi db upgrade
```

The repository already contains migration files, so a fresh setup needs `db upgrade`; do not run `db init` again.

### 4. Start the API

```bash
docker compose --env-file .env.docker up -d web
```

To build and start both services in one command instead, use:

```bash
docker compose --env-file .env.docker up --build
```

If you use that foreground command, leave it running in one terminal and run the migration command from another terminal after PostgreSQL is healthy.

### 5. Verify the containers and API

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

View the web service logs:

```bash
docker compose --env-file .env.docker logs web
```

Stop the services:

```bash
docker compose --env-file .env.docker down
```

The named `postgres_data` volume keeps database contents when containers are stopped or removed. **Only** use `down -v` when you intentionally want to delete the saved PostgreSQL data and start with a fresh database.

### Docker Compose test results

The Compose setup was tested successfully with the commands above:

- Docker built the `sole--main-web` image.
- PostgreSQL 17 initialized and reported `database system is ready to accept connections`.
- The PostgreSQL container passed its health check.
- Gunicorn 23.0.0 started and booted two workers.
- Flask-Migrate applied all three existing migrations:
  - `Create WE Sole users table`
  - `Add role to users`
  - `create wishlist items`
- `GET /health` returned `200 OK` and `{"status":"ok"}`.

## Environment variables

For local development, copy `.env.example` to `.env`. The app uses:

| Variable | Purpose |
|---|---|
| `FLASK_CONFIG` | Selects the app configuration, such as `development` or `production`. |
| `JWT_SECRET` | Secret used to sign and verify JSON Web Tokens. |
| `DATABASE_URL` | Database connection string. Local development can use `sqlite:///dev.db`; Docker Compose supplies a PostgreSQL URL to the web container. |

For Docker Compose, `.env.docker` supplies `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, and `JWT_SECRET`. Compose uses those values to configure PostgreSQL and build the web container's `DATABASE_URL`. The database connection uses the `psycopg2` driver provided by the `psycopg2-binary` Python package.

Flask 3 uses `FLASK_CONFIG` in this project; `FLASK_ENV` is not used.

## Database migrations

The project uses Flask-Migrate and Alembic. To apply the committed migrations:

```bash
flask --app wsgi db upgrade
```

When you change a model, generate and apply a new migration:

```bash
flask --app wsgi db migrate -m "describe your change"
flask --app wsgi db upgrade
```

For Docker, run those commands through the Compose web service as shown in the Docker setup above.

## Project documentation

- [API endpoints](docs/api-endpoints.md)
- [Database design](docs/database-design.md)
- [Project scope](docs/project-scope.md)
