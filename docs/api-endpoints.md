# WE Sole API — Endpoint Plan

This is the planned endpoint contract. The exact response body and authentication mechanism can be finalized during implementation.

| Path | Method | Purpose | Success status | 400 — Bad Request | 401 — Unauthorized | 403 — Forbidden | 404 — Not Found | Access |
|---|---|---|---|---|---|---|---|---|
| `/auth/register` | POST | Register a user | 201 Created | Required fields missing or invalid | — | — | — | Public |
| `/auth/login` | POST | Log in and receive a token/session | 200 OK | Username or password missing | Credentials invalid | — | — | Public |
| `/auth/admin` | GET | Example admin-only protected resource | 200 OK | — | Missing or invalid authentication | User lacks admin role | — | Admin |
| `/auth/me` | GET | View the authenticated user's profile | 200 OK | — | Missing, invalid, or expired token | — | User account no longer exists | Logged-in |
| `/auth/me` | PATCH | Update the authenticated user's editable profile fields | 200 OK | No editable fields or invalid field values | Missing, invalid, or expired token | — | User account no longer exists | Logged-in |
| `/auth/profile` | GET | View current user's profile | 200 OK | — | Missing or invalid authentication | — | User account no longer exists | Logged-in |
| `/auth/profile` | PUT | Legacy alias for updating current user's editable profile fields | 200 OK | Profile fields missing or invalid | Missing or invalid authentication | — | User account no longer exists | Logged-in |
| `/wishlist_items` | GET | Paginated list of the authenticated user's wishlist (`page`, `per_page`; max 50) | 200 OK | Invalid `per_page` | Missing or invalid authentication | — | — (empty or past-end page returns 200) | Logged-in |
| `/wishlist_items` | POST | Add a sneaker to the authenticated user's wishlist | 201 Created | Required fields missing, invalid values, or client-supplied owner ID | Missing or invalid authentication | — | — | Logged-in |
| `/wishlist_items/{id}` | GET | Read an owned wishlist item by ID | 200 OK | Invalid ID format | Missing or invalid authentication | User does not own item | Item does not exist (JSON 404) | Logged-in |
| `/wishlist_items/{id}` | PATCH | Update an owned wishlist item | 200 OK | Invalid update fields | Missing or invalid authentication | User does not own item | Item does not exist (JSON 404) | Logged-in |
| `/wishlist_items/{id}` | DELETE | Delete an owned wishlist item | 204 No Content | Invalid ID format | Missing or invalid authentication | User does not own item | Item does not exist (JSON 404) | Logged-in |

## Authorization rule

The authenticated user's ID determines ownership. Wishlist creation rejects `user_id` and `owner_id` in the request body; the server assigns the owner from the verified token. Wishlist listing filters by that authenticated user ID.

Item-by-ID endpoints require the authenticated user's ID to match the item's `user_id`. A missing item returns JSON `404`; an existing item owned by someone else returns JSON `403`.

Wishlist list responses include `items`, `page`, `per_page`, `total`, and `pages`. Results are filtered by the authenticated user and ordered by item ID ascending before database-side pagination.

## Status-code notes

- Use `400` for missing or invalid input.
- Use `401` when authentication is missing or invalid.
- Use `403` when an authenticated user is not allowed to perform an action.
- Use `404` when the requested resource does not exist. The implementation may also return `404` for another user's resource to avoid revealing whether it exists; choose one policy and apply it consistently.
- Use `204` for a successful deletion when returning no response body.
