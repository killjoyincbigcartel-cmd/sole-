# WE Sole API — Project Scope

## Overview

WE Sole is a sneaker wishlist API. Users can keep a personal list of sneakers they are interested in buying and manage the details for each item.

## User story

As a sneaker enthusiast, I want to save, view, update, and delete sneakers from my wishlist so I can keep track of the shoes I want to buy.

## Main resource

The main resource is `wishlist_items`. Every item belongs to one registered user.

## Core requirements

1. Users can register and log in.
2. Users must authenticate before accessing their wishlist.
3. Users can create, read, update, and delete their own wishlist items.
4. A user cannot access or modify another user's items.
5. The API validates incoming data and returns appropriate HTTP status codes.
6. Passwords are stored as hashes, not plain text.

## Out of scope for the first version

- Buying sneakers directly through the API
- Processing payments
- Live sneaker inventory or resale-price integrations
- Social feeds and following other users
- Admin endpoints unless they become necessary later

## Project pitch

WE Sole is a small, focused REST API for managing a personal sneaker wishlist. It demonstrates authentication, CRUD operations, data validation, database relationships, and authorization based on resource ownership. The scope is intentionally limited so the API can be built, tested, and improved in stages.
