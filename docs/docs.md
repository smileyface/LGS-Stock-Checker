# LGS Stock Checker

## Architecture Overview

This project follows a client-server architecture to provide real-time stock availability updates for trading cards.

### Adding a New Card Flow

When a user adds a new card, the following sequence of operations occurs across the system components:

```mermaid
sequenceDiagram
    participant ClientBrowser as Client (Browser)
    participant FlaskApp as Flask App (Web Interface)
    participant SocketIOServer as Socket.IO Server
    participant Redis as Redis (Cache & Queue)
    participant RQWorker as RQ Worker (Backend Task)
    participant Database as Database
    participant ExternalStore as External Store (Scraper Target)

    ClientBrowser->>FlaskApp: Emits "add_card" {card, amount, specs}
    activate SocketIOServer
    activate FlaskApp

    FlaskApp->>Database: managers.database_manager.add_user_card(username, card_name, amount, specs)
    activate Database
    Database-->>FlaskApp: Card added/updated in user_tracked_cards and card_specifications tables
    deactivate Database

    activate FlaskApp

    FlaskApp->>Database: managers.database_manager.get_users_cards(username)
    activate Database
    Database-->>FlaskApp: Returns updated list of user's tracked cards
    deactivate Database

    FlaskApp->>SocketIOServer: Calls send_card_list(username) (via managers.socket_manager.socket_events.send_card_list)
    SocketIOServer-->>ClientBrowser: Emits "cards_data" {tracked_cards} (updates dashboard table)
    deactivate FlaskApp

    ClientBrowser->>SocketIOServer: Emits "get_card_availability" (triggered by "cards_data" reception in dashboard.js)
    Note over ClientBrowser, ExternalStore: See User Requests Card Update graph
```

### User Requests Card Update

```mermaid
sequenceDiagram
    participant Browser as Client (Browser)
    participant FlaskApp as Flask App (Socket.IO Server)
    participant Redis as Redis (Message Queue & Cache)
    participant RQWorker as RQ Worker (Background Tasks)
    participant Database as Database
    participant ExternalStore as External Store (Scraper Target)

    Note over Browser, FlaskApp: 1. Client requests availability update
    Browser->>FlaskApp: Emit "get_card_availability"
    activate FlaskApp

    Note over FlaskApp, Database: 2. Flask App fetches user's cards and stores
    FlaskApp->>Database: managers.database_manager.get_users_cards(username)
    activate Database
    Database-->>FlaskApp: User's tracked card objects
    deactivate Database
    FlaskApp->>Database: managers.database_manager.get_user_stores(username)
    activate Database
    Database-->>FlaskApp: User's selected store objects
    deactivate Database

    Note over FlaskApp, Redis: 3. Flask App queues individual tasks for each (card, store) pair
    loop For each (Card, Store) combination
        FlaskApp->>Redis: Enqueue Task "update_availability_single_card" {user, store_slug, card_data}
        activate Redis
        deactivate Redis
    end
    deactivate FlaskApp

    Note over Redis, RQWorker: 4. RQ Workers pick up queued tasks
    Redis->>RQWorker: Pick up Task "update_availability_single_card"
    activate RQWorker

    Note over RQWorker, Redis: 5. RQ Worker checks cache for specific (store, card) availability
    RQWorker->>Redis: card_cache_manager.get_store_card_availability(store_slug, card_name)
    activate Redis
    Redis-->>RQWorker: Cached Listings (if found, expires after 30 mins)
    deactivate Redis

    alt If no cached data or stale
        Note over RQWorker, ExternalStore: 6a. RQ Worker scrapes external store
        RQWorker->>ExternalStore: store_instance.check_availability(card_data)
        activate ExternalStore
        ExternalStore-->>RQWorker: Scraped Listings
        deactivate ExternalStore
        Note over RQWorker, Redis: 6b. RQ Worker caches newly scraped data
        RQWorker->>Redis: availability_manager.availability_storage.cache_store_card_availability(store_slug, card_name, listings)
        activate Redis
        Redis-->>RQWorker: Data Stored with TTL
        deactivate Redis
    else If cached data is available and fresh
        Note over RQWorker: 6c. Use cached data
        RQWorker->>Redis: availability_manager.availability_storage.get_availability_data(store, cardname)
        activate Redis
        Redis-->>RQWorker: Data Stored with TTL
        deactivate Redis
    end

    Note over RQWorker, FlaskApp: 7. RQ Worker emits real-time update for specific card/store
    RQWorker->>FlaskApp: Emit "card_availability_update" {username, card_name, store_slug, items}
    activate FlaskApp
    FlaskApp-->>Browser: Emit "card_availability_update" {username, card_name, store_slug, items}
    deactivate FlaskApp
    Note right of Browser: Updates Specific Card's Row in UI (e.g., from "checking..." to ✅ or ❌)

    deactivate RQWorker
```


### Messages Sent Between Components

| Message Name                          | Message Data                                      | Target         | Description                                                          |
|---------------------------------------|---------------------------------------------------|----------------|----------------------------------------------------------------------|
| `add_card`                            | `card`, `amount`, `specs`                         | FlaskApp       | Adds a new card to the user's tracked cards.                         |
| `cards_data`                          | `tracked_cards`                                   | ClientBrowser  | Updates the dashboard table with the latest list of tracked cards.   |
| `get_card_availability`               | `card_name`, `store_slug`                         | FlaskApp       | Requests availability data for a specific card in a store.           |
| `card_availability_update`            | `card_name`, `store_slug`, `items`                | ClientBrowser  | Updates the availability status of a specific card in the dashboard. |
| `delete_card`                         | `card`                                            | FlaskApp       | Deletes a card from the user's tracked cards.                        |
| `update_card`                         | `card`, `update_data`                             | FlaskApp       | Updates the amount of a tracked card.                                |
| `get_user_stores`                     | `username`                                        | FlaskApp       | Retrieves the user's selected stores.                                |
| `get_users_cards`                     | `username`                                        | FlaskApp       | Retrieves the user's tracked cards.                                  |
| `save_store_availability_single_item` | `username`, `store_slug`, `card_name`, `listings` | Redis          | Saves the availability data for a specific card in a store.          |
| `load_data`                           | `key`, `field`                                    | Redis          | Loads cached data from Redis.                                        |
| `connect`                             | `url`                                             | SocketIOServer | Establishes a WebSocket connection with the client.                  |

## Appendix
### Import graphs
```mermaid
graph TD
    subgraph Root
        R[run.py]
    end

    subgraph App
        A_APP[app]
        A_ROUTES[app.routes]
    end

    subgraph Configuration
        C_CONFIG[config]
    end

    subgraph Core Logic
        CO_CORE[core]
    end

    subgraph External Integrations
        E_EXTERNALS[externals]
    end

    subgraph Managers
        M_AVAIL_MGR[managers.availability_manager]
        M_CARD_MGR[managers.card_manager]
        M_DB_MGR[managers.database_manager]
        M_REDIS_MGR[managers.redis_manager]
        M_SOCKET_MGR[managers.socket_manager]
        M_STORE_MGR[managers.store_manager]
        M_STORE_STORES[managers.store_manager.stores]
        M_TASKS_MGR[managers.tasks_manager]
        M_USER_MGR[managers.user_manager]
    end

    subgraph Utility
        U_UTILITY[utility]
    end

    %% Root dependencies
    R --> A_APP
    R --> M_SOCKET_MGR
    R --> M_TASKS_MGR
    R --> U_UTILITY

    %% App dependencies
    A_APP --> A_ROUTES
    A_APP --> M_SOCKET_MGR

    A_ROUTES --> M_SOCKET_MGR
    A_ROUTES --> M_STORE_STORES
    A_ROUTES --> M_USER_MGR

    %% Core dependencies
    CO_CORE --> C_CONFIG
    CO_CORE --> U_UTILITY

    %% External Integrations dependencies
    E_EXTERNALS --> M_REDIS_MGR
    E_EXTERNALS --> U_UTILITY

    %% Managers - Inter-manager dependencies and external (core/utility/externals)
    M_AVAIL_MGR --> M_REDIS_MGR
    M_AVAIL_MGR --> M_DB_MGR
    M_AVAIL_MGR --> M_STORE_MGR
    M_AVAIL_MGR --> M_USER_MGR
    M_AVAIL_MGR --> U_UTILITY

%% (card_parser.py doesn't have direct imports, but if it used utility.logger, it would be here)
    M_CARD_MGR --> U_UTILITY 

    M_DB_MGR --> U_UTILITY

    M_REDIS_MGR --> U_UTILITY

    M_SOCKET_MGR --> M_REDIS_MGR
    M_SOCKET_MGR --> M_CARD_MGR
    M_SOCKET_MGR --> M_DB_MGR
    M_SOCKET_MGR --> E_EXTERNALS
    M_SOCKET_MGR --> M_AVAIL_MGR
    M_SOCKET_MGR --> M_USER_MGR
    M_SOCKET_MGR --> U_UTILITY

    M_STORE_MGR --> M_DB_MGR
    M_STORE_MGR --> M_REDIS_MGR
    M_STORE_MGR --> M_STORE_STORES
    M_STORE_MGR --> U_UTILITY

    M_STORE_STORES --> CO_CORE
    M_STORE_STORES --> M_DB_MGR
    M_STORE_STORES --> U_UTILITY

    M_TASKS_MGR --> M_REDIS_MGR
    M_TASKS_MGR --> M_STORE_MGR
    M_TASKS_MGR --> M_USER_MGR
    M_TASKS_MGR --> U_UTILITY

    M_USER_MGR --> M_DB_MGR
    M_USER_MGR --> U_UTILITY
```