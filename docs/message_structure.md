# Message Schema Requirements

This document provides a detailed reference for the data structures of the real-time events used to communicate between the client and the server via Socket.IO.

## Requirement Directory

| Requirement ID | Name                              | Description                                                                      |
|----------------|-----------------------------------|----------------------------------------------------------------------------------|
| `[MPR-1.1.1]`  | `get_cards`                       | Requests the user's complete list of tracked cards.                              |
| `[MPR-1.1.2]`  | `add_card`                        | Adds a new card to the user's tracked list.                                      |
| `[MPR-1.1.3]`  | `update_card`                     | Updates an existing tracked card's amount or specifications.                     |
| `[MPR-1.1.4]`  | `delete_card`                     | Removes a card from the user's tracked list.                                     |
| `[MPR-1.1.5]`  | `search_card_names`               | Requests a list of card names for autocomplete functionality.                    |
| `[MPR-1.1.6]`  | `get_card_availability`           | Triggers a check for the availability of all the user's tracked cards.           |
| `[MPR-1.1.7]`  | `get_card_printings`              | Requests all valid printings for a given card name.                              |
| `[MPR-1.1.8]`  | `update_stores`                   | Updates the user's list of preferred stores.                                     |
| `[MPR-1.1.9]`  | `stock_data_request`              | Requests aggregated stock details for a single card across all preferred stores. |
| `[MPR-1.1.10]` | `parse_card_list`                 | Submits a raw text list of cards to be parsed.                                   |
| `[MPR-1.1.11]` | `login_user_me`                   | Authenticates the current user session.                                          |
| `[MPR-1.2.1]`  | `cards_data`                      | Provides the client with the user's complete and updated list of tracked cards.  |
| `[MPR-1.2.2]`  | `card_name_search_results`        | Returns a list of card names for autocomplete functionality.                     |
| `[MPR-1.2.3]`  | `availability_check_started`      | Notifies the client that a background availability check has started.            |
| `[MPR-1.2.4]`  | `card_availability_data`          | Sends real-time stock information for a specific card from a store.              |
| `[MPR-1.2.5]`  | `card_printings_data`             | Provides the client with all valid printings for a specific card.                |
| `[MPR-1.2.6]`  | `user_stores_data`                | Provides the client with the user's list of preferred stores.                    |
| `[MPR-1.2.7]`  | `stock_data`                      | Provides aggregated stock details for a card.                                    |
| `[MPR-1.2.8]`  | `error`                           | Sends an error message to the client for display.                                |
| `[MPR-2.1.1]`  | `availability_request`            | Commands the Scheduler to enqueue a web scraping task.                           |
| `[MPR-2.1.2]`  | `queue_all_availability_checks`   | Commands the Scheduler to queue checks for all tracked cards.                    |
| `[MPR-2.2.1]`  | `availability_result`             | Reports the results of a web scraping task to the Backend API.                   |
| `[MPR-2.2.2]`  | `catalog_*_result`                | Reports the results of various catalog population tasks.                         |

---

## 1. Client-Server Communication (Socket.IO)

This section defines the payloads for events emitted between the Vue.js frontend and the Flask backend.

### 1.1. Client-to-Server Events

These are messages the client sends to the server.

#### `get_cards`

Requests the user's complete list of tracked cards.

* **Schema:**

    ```json
    {
      "user": {
        "username": "string"
      }
    }
    ```

#### `add_card`

Adds a new card to the user's tracked list.

* **Schema:**

    ```json
    {
      "command": "add",
      "update_data": {
        "card": {
          "name": "Card Name"
        },
        "amount": 1,
        "card_specs": [
          {
            "set_code": {
              "code": "M21"
            },
            "collector_number": "123",
            "finish": {
              "name": "foil"
            }
          }
        ]
      }
    }
    ```

#### `update_card`

Updates an existing tracked card's amount or specifications.

* **Schema:**

    ```json
    {
      "command": "update",
      "update_data": {
        "card": {
          "name": "Card Name"
        },
        "amount": 2,
        "card_specs": [
          {
            "set_code": {
              "code": "2X2"
            },
            "finish": {
              "name": "non-foil"
            }
          },
          {
            "finish": {
              "name": "etched"
            }
          }
        ]
      }
    }
    ```

#### `delete_card`

Removes a card from the user's tracked list.

* **Schema:**

    ```json
    {
      "command": "delete",
      "update_data": {
        "card": {
          "name": "Card Name"
        }
      }
    }
    ```

#### `search_card_names`

Requests a list of card names for autocomplete functionality.

* **Schema:**

    ```json
    {
      "query": "search term"
    }
    ```

#### `get_card_availability`

Triggers a check for the availability of all the user's tracked cards.

* **Schema:** `None`

#### `get_card_printings`

Requests all valid printings for a given card name.

* **Schema:**

    ```json
    {
        "card": {
            "name": "Card Name"
        }
    }
    ```

#### `update_stores`

Updates the user's list of preferred stores.

* **Schema:**

    ```json
    {
        "stores": [
            {
                "slug": "slug-1",
                "name": "Store One"
            },
            {
                "slug": "slug-2",
                "name": "Store Two"
            }
        ],
        "user": {
            "username": "string"
        }
    }
    ```

#### `stock_data_request`

Requests aggregated stock details for a single card across all preferred stores.

* **Schema:**

    ```json
    {
        "card_name": "Card Name"
    }
    ```

#### `parse_card_list`

Parses a raw text string representing a card list.

* **Schema:**

    ```json
    {
        "raw_list": "1x Card Name (SET) 123 *foil*"
    }
    ```

#### `login_user_me`

Authenticates the requesting client.

* **Schema:**

    ```json
    {
        "user": {
            "username": "string"
        },
        "password": "string"
    }
    ```

### 1.2. Server-to-Client Events

These are messages the server sends to the client.

#### `cards_data`

Provides the client with the user's complete and updated list of tracked cards. This is sent in response to `get_cards`, `add_card`, `update_card`, and `delete_card`.

* **Schema:**

    ```json
    {
        "cards": [
            {
                "card": {
                    "name": "string"
                },
                "amount": "integer",
                "card_specs": [
                    {
                        "set_code": {
                            "code": "string",
                            "name": "string"
                        },
                        "collector_number": "string",
                        "finish": {
                            "name": "string"
                        }
                    }
                ]
            }
        ]
    }
    ```

#### `card_name_search_results`

Returns a list of autocomplete suggestions in response to a `search_card_names` event.

* **Schema:**

    ```json
    {   
        "names": ["string"]
    }
    ```

#### `availability_check_started`

Notifies the client that a background availability check has started for a specific card at a specific store. This is useful for showing a "Searching..." or loading state in the UI.

* **Schema:**

    ```json
    {
        "store": "string (store-slug)",
        "card": "string (Card Name)"
    }
    ```

#### `card_availability_data`

Sends real-time stock information for a specific card from a specific store. This is the result of a completed background check.

* **Schema:**

    ```json
    {
      "card": {
        "card": {
            "name": "Card Name"
        },
        "amount": 1,
        "card_specs": null
      },
      "store": {
        "slug": "store-slug",
        "name": "Store Name"
      },
      "items": [
        {
          "price": "float",
          "stock": "integer",
          "condition": "string",
          "set": "string (set_code)",
          "collector_number": "string",
          "finish": "string",
          "url": "string (URL)"
        }
      ]
    }
    ```

#### `card_printings_data`

Provides the client with all valid printings for a specific card.

* **Schema:**

    ```json
    {
        "card_name": "string",
        "printings": [
            {
                "set_code": "string",
                "collector_number": "string",
                "finish": "string"
            }
        ]
    }
    ```

#### `user_stores_data`

Provides the client with the user's list of preferred stores.

* **Schema:**

    ```json
    {
        "stores": [
            {
                "id": "integer",
                "name": "string",
                "slug": "string",
                "homepage": "string",
                "search_url": "string",
                "fetch_strategy": "string"
            }
        ]
    }
    ```

#### `stock_data`

Provides aggregated stock details for a card in response to `stock_data_request`.

* **Schema:**

    ```json
    {
        "card_name": "string",
        "items": [
            {
              "store_name": "string",
              "price": "float",
              "stock": "integer",
              "condition": "string",
              "set": "string (set_code)",
              "collector_number": "string",
              "finish": "string",
              "url": "string (URL)"
            }
        ]
    }
    ```

#### `error`

Sends an error message to the client for display.

* **Schema:**

    ```json
    {
        "message": "string"
    }
    ```

## 2. Internal Backend Communication (Redis Pub/Sub)

This section defines the payloads for messages passed between backend services.

### 2.1. `scheduler-requests` Channel

Messages published by the Backend API to command the Scheduler.

#### `availability_request`

Commands the Scheduler to enqueue a web scraping task for a specific card at a specific store.

* **Schema:**

    ```json
    {
        "command": "availability_request",
        "payload": {
            "user": {
                "username": "string"
            },
            "store": {
                "slug": "string",
                "name": "string"
            },
            "card_data": {
                "card": {
                    "name": "string"
                },
                "amount": "integer",
                "card_specs": "array | null"
            }
        }
    }
    ```

#### `queue_all_availability_checks`

Commands the Scheduler to queue availability checks for all tracked cards for users.

* **Schema:** `None`

### 2.2. `worker-results` Channel

Messages published by an RQ Worker to report the results of a completed task.

#### `availability_result`

Reports the results of a web scraping task to the Backend API for caching and potential forwarding.

* **Schema:**

    ```json
    {
        "card": {
            "card": { "name": "string" },
            "amount": "integer",
            "card_specs": "array | null"
        },
        "store": {
            "slug": "string",
            "name": "string"
        },
        "items": [
            {
                "name": "string",
                "set_code": "string",
                "collector_number": "string",
                "finish": "string",
                "price": "float",
                "condition": "string",
                "quantity": "integer",
                "url": "string"
            }
        ]
    }
    ```

#### Catalog Tasks

Report results for catalog population functions like `catalog_card_names_result`, `catalog_set_data_result`, `catalog_printings_chunk_result`, and `catalog_finishes_chunk_result`.

* **Schema (e.g. `catalog_card_names_result`):**

    ```json
    {
        "names": ["string"]
    }
    ```
