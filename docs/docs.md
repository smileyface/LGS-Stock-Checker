# LGS Stock Checker

## Architecture Overview

This project follows a modern client-server architecture with a decoupled frontend and a backend API, supported by background workers for intensive tasks.

### Sequence Diagrams 

#### User Registration Flow
This diagram shows the sequence for adding a new user.

```mermaid  
sequenceDiagram

participant Client as Frontend (Vue.js)
participant Backend as Backend API (Flask)
participant DB as Database
Client->>Backend: POST /api/register {username, password}
activate Backend
alt Username is available
   Backend->>DB: add_user(username, hash(password))
   activate DB
   DB-->>Backend: New user created
   deactivate DB
   Backend-->>Client: 201 Created {message: "User created"}
else Username already exists
   Backend-->>Client: 400 Bad Request {error: "Username taken"}
end
deactivate Backend
```

#### User Authentication Flow

This diagram shows the sequence for a user logging in and the frontend being populated with their data.

```mermaid
sequenceDiagram
    participant Client as Frontend (Vue.js)
    participant Backend as Backend API (Flask)
    participant DB as Database

    Client->>Backend: POST /api/login {username, password}
    activate Backend
    Backend->>DB: user_manager.authenticate_user(...)
    activate DB
    DB-->>Backend: Returns User ORM object
    deactivate DB
    Backend->>Backend: Flask-Login creates session
    Backend-->>Client: 200 OK {message: "Login successful"}
    deactivate Backend

    Note over Client: On successful login, redirect to Dashboard
    Client->>Client: authStore.checkAuthStatus()
    Client->>Backend: GET /api/user_data
    activate Backend
    Backend->>DB: Fetches current_user data
    activate DB
    DB-->>Backend: User data with stores
    deactivate DB
    Backend-->>Client: 200 OK {username, stores, ...}
    deactivate Backend
    Note over Client: Populates user state in authStore
```

#### Adding a New Tracked Card

When a user adds a new card, the following sequence of operations occurs across the system components:

```mermaid
sequenceDiagram
    participant Client as Frontend (Vue.js)
    participant Backend as Backend API (Flask)
    participant DB as Database

    Client->>Backend: Emits "add_card" {card, amount, specs}
    activate Backend
    Backend->>DB: user_manager.add_user_card(...)
    activate DB
    DB-->>Backend: Card added/updated
    deactivate DB

    Note over Backend: After DB operation, send updated list
    Backend->>DB: user_manager.load_card_list(username)
    activate DB
    DB-->>Backend: Returns updated list of tracked cards
    deactivate DB

    Backend-->>Client: Emits "cards_data" {tracked_cards}
    deactivate Backend
    Note right of Client: Dashboard table updates automatically
```

#### Checking Card Availability
When a check availability has been triggered.

```mermaid
sequenceDiagram
    participant Client as Frontend (Vue.js)
    participant Backend as Backend API (Flask)
    participant Redis as Redis (Queue & Cache)
    participant Worker as RQ Worker
    participant DB as Database
    participant ExternalStore as External Store

    Note over Client, Backend: 1. Client requests availability update
    Client->>Backend: Emit "get_card_availability"
    activate Backend

    Note over Backend, DB: 2. Backend fetches user's cards and stores
    Backend->>DB: user_manager.load_card_list(username)
    activate DB
    DB-->>Backend: User's tracked card objects
    deactivate DB
    Backend->>DB: user_manager.get_selected_stores(username)
    activate DB
    DB-->>Backend: User's selected store objects
    deactivate DB

    Note over Backend, Redis: 3. Backend queues tasks for each (card, store) pair not in cache
    loop For each (Card, Store) combination
        Backend->>Redis: Enqueue Task "update_availability_single_card" {user, store_slug, card_data}
        activate Redis
        deactivate Redis
    end
    deactivate Backend

    Note over Redis, Worker: 4. Worker picks up queued tasks
    Redis->>Worker: Pick up Task "update_availability_single_card"
    activate Worker
    Note over Worker, Redis: 5. Worker checks cache for specific (store, card) availability
    Worker->>Redis: availability_storage.get_availability_data(store_slug, card_name)
    activate Redis
    Redis-->>Worker: Cached Listings (if found)
    deactivate Redis

    alt If no cached data or stale
        Note over Worker, ExternalStore: 6a. Worker scrapes external store
        Worker->>ExternalStore: store_instance.fetch_card_availability(card_data)
        activate ExternalStore
        ExternalStore-->>Worker: Scraped Listings
        deactivate ExternalStore
        Note over Worker, Redis: 6b. Worker caches newly scraped data
        Worker->>Redis: availability_storage.cache_availability_data(...)
        activate Redis
        Redis-->>Worker: Data Stored with TTL
        deactivate Redis
    end
    Note over Worker, Backend: 7. RQ Worker emits real-time update for specific card/store
    Worker->>Backend: Publishes "card_availability_data" to Redis Pub/Sub
    activate Backend
    Backend-->>Client: Emits "card_availability_data" {username, card_name, store_slug, items}
    deactivate Backend
    Note right of Client: Updates Specific Card's Row in UI

    deactivate Worker
```

#### Updating a Tracked Card
```mermaid
sequenceDiagram
participant Client as Frontend (Vue.js)
participant Backend as Backend API (Flask)
participant DB as Database
Client->>Backend: Emits "update_card" {card, update_data}
activate Backend
Backend->>DB: user_manager.update_user_card(...)
activate DB
DB-->>Backend: Card updated
deactivate DB
Note over Backend: After DB operation, send updated list
Backend->>DB: user_manager.load_card_list(username)
activate DB
DB-->>Backend: Returns updated list of tracked cards
deactivate DB
Backend-->>Client: Emits "cards_data" {tracked_cards}
deactivate Backend
Note right of Client: Dashboard table updates automatically
```

#### Card Search Flow
```mermaid
sequenceDiagram
    participant Client as Frontend (Vue.js)
    participant Backend as Backend API (Flask)

    Client->>Backend: User types in search box
    activate Client
    Client->>Backend: Emits "search_card_names" { query: "search term" }
    deactivate Client
    activate Backend
    Backend->>Backend: Processes search query
    Backend->>Backend: Queries card catalog
    Backend-->>Client: Emits "card_name_search_results" { card_names: [...] }
    deactivate Backend
    activate Client
    Client->>Client: Updates autocomplete suggestions
    deactivate Client

```

#### Delete a Tracked Card
```mermaid
sequenceDiagram
    participant Client as Frontend (Vue.js)
    participant Backend as Backend API (Flask)
    participant DB as Database

    Client->>Backend: Emits "delete_card" { card: "card_name" }
    activate Backend
    Backend->>DB: user_manager.delete_user_card(...)
    activate DB
    DB-->>Backend: Card deleted
    deactivate DB

    Note over Backend: After DB operation, send updated list
    Backend->>DB: user_manager.load_card_list(username)
    activate DB
    DB-->>Backend: Returns updated list of tracked cards
    deactivate DB

    Backend-->>Client: Emits "cards_data" {tracked_cards}
    deactivate Backend
    Note right of Client: Dashboard table updates automatically
```

### Messages Sent Between Components
The frontend and backend communicate via two primary methods: a RESTful API for standard requests and Socket.IO for real-time, bidirectional events. 

#### REST API Endpoints

| Method | Endpoint | Description | 
|--------|---------------------------------|------------------------------------------------------| 
| POST | /api/login | Authenticates a user and creates a session. | 
| POST | /api/logout | Logs out the current user. | 
| GET | /api/user_data | Retrieves the logged-in user's profile data. | 
| GET | /api/stores | Returns a list of all available store slugs. | 
| POST | /api/account/update_username | Updates the logged-in user's username. | 
| POST | /api/account/update_password | Updates the logged-in user's password. | 
| POST | /api/account/update_stores | Updates the logged-in user's preferred stores. |

#### Socket.IO Events 
| Event Name | Direction | Data Payload | Description | 
|------------------------------|-------------------|---------------------------------------------|--------------------------------------------------------------------------| 
| connect | Client -> Server | - | Establishes a WebSocket connection. | 
| get_cards | Client -> Server | - | Requests the user's full list of tracked cards. | 
| cards_data | Server -> Client | { "tracked_cards": [...] } | Sends the full list of tracked cards to the client. | 
| add_card | Client -> Server | { "card", "amount", "card_specs" } | Adds a new card to the user's tracked list. | 
| update_card | Client -> Server | { "card", "update_data": {...} } | Updates the amount or specifications of a tracked card. | 
| delete_card | Client -> Server | { "card": "..." } | Deletes a card from the user's tracked list. | 
| search_card_names | Client -> Server | { "query": "..." } | Requests a list of card names matching a partial search query. | 
| card_name_search_results | Server -> Client | { "card_names": [...] } | Returns a list of autocomplete suggestions for the card search. | 
| get_card_availability | Client -> Server | - | Triggers background tasks to check for card availability. | 
| availability_check_started | Server -> Client | { "store", "card" } | Notifies the UI that a check has begun for a specific item. | 
| card_availability_data | Server -> Client | { "store", "card", "items": [...] } | Sends real-time availability results for a specific card and store. |