# WE Sole API — Database Design

This is the initial database plan. Column names and types can be adjusted to match the database and framework used in implementation.

## users

| Column | Purpose |
|---|---|
| `id` | Primary key |
| `username` | Unique account username |
| `password_hash` | Secure password hash; never store the plain-text password |
| `created_at` | Account creation timestamp |
| `updated_at` | Last profile update timestamp, if needed |

## wishlist_items

| Column | Purpose |
|---|---|
| `id` | Primary key |
| `user_id` | Foreign key referencing `users.id` |
| `sneaker_name` | Name of the sneaker |
| `brand` | Sneaker brand, if known |
| `size` | Desired shoe size |
| `target_price` | Price the user hopes to pay, if provided |
| `priority` | Optional priority value |
| `notes` | User's notes about the sneaker |
| `created_at` | When the item was added |
| `updated_at` | When the item was last changed |

## Relationship

One user can have many wishlist items. Each wishlist item belongs to one user.

`users.id` → `wishlist_items.user_id`

## Data and access rules

- `users.username` should be unique.
- `wishlist_items.user_id` should reference a valid user.
- Validate user input before saving it.
- Only return wishlist items belonging to the authenticated user on normal wishlist routes.
- Set `user_id` from the authenticated identity on the server; do not trust a value supplied by the client.
- Keep password hashes out of API responses.
