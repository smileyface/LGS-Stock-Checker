# Database Schema

This document outlines the structure of the database tables used in the LGS Stock Checker application.

## `users`

Stores user account information.

| Column        | Type    | Constraints              | Description                               |
|---------------|---------|--------------------------|-------------------------------------------|
| `id`          | Integer | Primary Key, Index       | Unique identifier for the user.           |
| `username`      | String  | Unique, Not Null         | The user's chosen username.               |
| `password_hash` | String  | Not Null                 | The user's hashed password.               |

## `stores`

Stores information about the local game stores.

| Column         | Type    | Constraints              | Description                               |
|----------------|---------|--------------------------|-------------------------------------------|
| `id`           | Integer | Primary Key, Index       | Unique identifier for the store.          |
| `name`         | String  | Unique, Not Null         | The full name of the store.               |
| `slug`         | String  | Unique, Not Null         | A short, URL-friendly identifier.         |
| `homepage`     | String  | Not Null                 | The store's main website URL.             |
| `search_url`   | String  | Not Null                 | The URL for the store's search page.      |
| `fetch_strategy` | String  | Not Null                 | The strategy used to scrape the store.    |

## `cards`

A lookup table containing unique card names. This ensures that card names are consistent across the application.

| Column | Type   | Constraints        | Description                       |
|--------|--------|--------------------|-----------------------------------|
| `name` | String | Primary Key, Index | The unique name of the Magic card. |

## `user_tracked_cards`

An association table that links users to the cards they are tracking.

| Column      | Type    | Constraints              | Description                               |
|-------------|---------|--------------------------|-------------------------------------------|
| `id`        | Integer | Primary Key, Autoincrement | Unique identifier for the tracked card entry. |
| `user_id`   | Integer | Foreign Key (users.id)   | The ID of the user tracking the card.     |
| `card_name` | String  | Foreign Key (cards.name) | The name of the card being tracked.       |
| `amount`    | Integer | Not Null                 | The quantity of the card the user wants.  |

## `card_specifications`

Stores specific criteria for a tracked card (e.g., set, finish).

| Column             | Type    | Constraints                           | Description                               |
|--------------------|---------|---------------------------------------|-------------------------------------------|
| `id`               | Integer | Primary Key, Autoincrement            | Unique identifier for the specification.  |
| `user_card_id`     | Integer | Foreign Key (user_tracked_cards.id)   | The ID of the tracked card entry this applies to. |
| `set_code`         | String  | Nullable                              | The 3-4 letter set code (e.g., "M21").    |
| `collector_number` | String  | Nullable                              | The card's collector number in the set.   |
| `finish`           | String  | Nullable                              | The card's finish (e.g., "foil", "etched"). |

## `user_store_preferences`

A many-to-many association table linking users to their selected stores.

| Column     | Type    | Constraints              | Description                               |
|------------|---------|--------------------------|-------------------------------------------|
| `user_id`  | Integer | Primary Key, Foreign Key (users.id) | The ID of the user.              |
| `store_id` | Integer | Primary Key, Foreign Key (stores.id) | The ID of the selected store.    |