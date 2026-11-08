# WE Sole API — Endpoint Plan

This is the planned endpoint contract. The exact response body and authentication mechanism can be finalized during implementation.

| Path | Method | Purpose | Success status | 400 — Bad Request | 401 — Unauthorized | 403 — Forbidden | 404 — Not Found | Access |
|---|---|---|---|---|---|---|---|---|
| `/auth/register` | POST | Register a user | 201 Created | Required fields missing or invalid | — | — | — | Public |
| `/auth/login` | POST | Log in and receive a token/session | 200 OK | Username or password missing | Credentials invalid | — | — | Public |
| `/auth/profile` | GET | View current user's profile | 200 OK | — | Missing or invalid authentication | — | User account no longer exists | Logged-in |
| `/auth/profile` | PUT | Update current user's profile | 200 OK | Profile fields missing or invalid | Missing or invalid authentication | — | User account no longer exists | Logged-in |
| `/wishlist_items` | GET | List current user's wishlist | 200 OK | — | Missing or invalid authentication | — | — (empty list returns 200) | Logged-in |
| `/wishlist_items` | POST | Add a sneaker to the wishlist | 201 Created | Required fields missing or invalid | Missing or invalid authentication | — | — | Logged-in |
| `/wishlist_items/{id}` | GET | View one owned wishlist item | 200 OK | Invalid ID format | Missing or invalid authentication | Access to another user's item is denied | Item does not exist | Logged-in |
| `/wishlist_items/{id}` | PUT | Update an owned wishlist item | 200 OK | Invalid ID or update fields | Missing or invalid authentication | Updating another user's item is denied | Item does not exist | Logged-in |
| `/wishlist_items/{id}` | DELETE | Delete an owned wishlist item | 204 No Content | Invalid ID format | Missing or invalid authentication | Deleting another user's item is denied | Item does not exist | Logged-in |

## Authorization rule

The authenticated user's ID determines ownership. Do not accept an `owner_id` from the request body as proof of ownership.

## Status-code notes

- Use `400` for missing or invalid input.
- Use `401` when authentication is missing or invalid.
- Use `403` when an authenticated user is not allowed to perform an action.
- Use `404` when the requested resource does not exist. The implementation may also return `404` for another user's resource to avoid revealing whether it exists; choose one policy and apply it consistently.
- Use `204` for a successful deletion when returning no response body.
