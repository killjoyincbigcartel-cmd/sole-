# WE Sole API

WE Sole is a sneaker wishlist API project. It is designed to let users register, log in, and keep track of sneakers they want to buy.

## Project goal

Build a small, secure REST API around one main resource: `wishlist_items`. Each wishlist item belongs to the user who created it, and users should only be able to view or change their own items.

## Planned features

- User registration and login
- Authentication for protected routes
- Create, list, view, update, and delete wishlist items
- Store details such as sneaker name, size, target price, notes, and priority
- Enforce ownership using the authenticated user's ID
- Return consistent HTTP status codes for errors and successful requests

## Main user story

> As a sneaker enthusiast, I want to save, view, update, and delete sneakers from my wishlist so I can keep track of the shoes I want to buy.

## API overview

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/auth/register` | Create an account |
| POST | `/auth/login` | Log in and receive an authentication token or session |
| GET | `/auth/profile` | View the current user's profile |
| PUT | `/auth/profile` | Update the current user's profile |
| GET | `/wishlist_items` | List the current user's wishlist |
| POST | `/wishlist_items` | Add a sneaker to the wishlist |
| GET | `/wishlist_items/{id}` | View one wishlist item |
| PUT | `/wishlist_items/{id}` | Update one wishlist item |
| DELETE | `/wishlist_items/{id}` | Remove one wishlist item |

See [API endpoints](docs/api-endpoints.md), [database design](docs/database-design.md), and [project scope](docs/project-scope.md) for more details.

## Security notes

- Passwords should be stored as secure hashes, never as plain text.
- Protected routes should require a valid authentication token or session.
- The server must get the item's owner ID from the authenticated user, not trust an owner ID supplied in the request body.
- Requests to another user's item should be denied without exposing private data.

## Project status

The API is built around the user and wishlist flows described in this repository. The project is now moving from design into runnable local development and test setup.

## Setup

Follow these steps to run the app locally:

1. Clone the repository:

   ```bash
   git clone <your-repo-url>
   cd sole--main
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

4. Copy the example environment file and fill in any local values:

   ```bash
   cp .env.example .env
   ```

5. Start the Flask app:

   ```bash
   flask run
   ```

   If your shell does not pick up the Flask app automatically, you can also run:

   ```bash
   export FLASK_APP=wsgi.py
   export FLASK_ENV=development
   flask run
   ```

   The app should be available at `http://127.0.0.1:5000` by default.

## Run with Docker Compose

Docker Compose starts the Flask web app and PostgreSQL together. The web service uses the same `wsgi:app` application factory as local runs.

1. Copy the Compose environment example and set local values:

   ```bash
   cp .env.compose.example .env
   ```

   Replace the placeholder `JWT_SECRET` and `POSTGRES_PASSWORD`. Generate URL-safe values with:

   ```bash
   python3 -c 'import secrets; print(secrets.token_urlsafe(48))'
   ```

   `.env` is git-ignored; do not commit real secrets.

2. Start PostgreSQL, build the image, apply migrations, and start the web app:

   ```bash
   docker compose --env-file .env up -d db
   docker compose --env-file .env build web
   docker compose --env-file .env run --rm web flask --app wsgi db upgrade
   docker compose --env-file .env up -d web
   ```

3. Verify both services and the health endpoint:

   ```bash
   docker compose --env-file .env ps
   curl -i http://127.0.0.1:8000/health
   docker compose --env-file .env logs web
   ```

   The health request should return `200 OK` with `{"status":"ok"}`. Stop the services with `docker compose --env-file .env down`; the named `postgres_data` volume keeps database contents. Use `down -v` only when you intend to delete that data.

The Docker image contains the app and dependencies; JWT secrets and database configuration are supplied at runtime through Compose and are not baked into image layers. Containers are replaceable instances, while the named Postgres volume persists data independently. JWT authentication is stateless: requests carry signed tokens that the app verifies with `JWT_SECRET`, so no server-side session store is needed. User and wishlist records still persist in PostgreSQL.

## Environment variables

Copy `.env.example` to `.env` before running the app.

The project currently uses the following environment variables:

```env
FLASK_APP=wsgi.py
FLASK_ENV=development
JWT_SECRET=your-super-secret-key
DATABASE_URL=sqlite:///dev.db
```

What each one is for:

- `FLASK_APP`: tells Flask which app entry point to load. In this project that is `wsgi.py`.
- `FLASK_ENV`: sets the runtime environment. Use `development` locally and switch to another environment when deploying.
- `JWT_SECRET`: secret key used to sign JSON Web Tokens for authentication.
- `DATABASE_URL`: database connection string. Local development can use SQLite (`sqlite:///dev.db`), while production may use PostgreSQL or another hosted database.

If you are using a real database in another environment, replace the local SQLite URL with your actual connection string.

## Database and migrations

This project uses Flask-Migrate with the Flask CLI, so database setup is handled through `flask db` commands.

When you are ready to initialize migrations for the project, use:

```bash
flask db init
flask db migrate -m "initial migration"
flask db upgrade
```

For ongoing schema work, the general pattern is:

```bash
flask db migrate -m "describe your change"
flask db upgrade
```

This keeps the app tied to the same migration workflow used by the Flask-SQLAlchemy and Flask-Migrate setup already in the project.

## Getting started

To get oriented quickly, review the project docs in the `docs/` folder:

- [docs/api-endpoints.md](docs/api-endpoints.md)
- [docs/database-design.md](docs/database-design.md)
- [docs/project-scope.md](docs/project-scope.md)

These documents explain the API contract and the planned data model before you start adding new routes or features.

