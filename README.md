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

Planning and API design. Implementation details, setup instructions, and tests will be added as the API is built.
