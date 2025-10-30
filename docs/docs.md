# LGS Stock Checker

## Architecture Overview

This project follows a modern client-server architecture with a decoupled frontend and a backend API, supported by background workers for intensive tasks.

### Architecture Definitions

* **Frontend (Vue.js SPA)**: A Single Page Application that provides the user interface. It communicates with the backend via a RESTful API for standard requests (like login) and WebSockets for real-time, bidirectional events (like adding a card or receiving availability updates). It is responsible for all presentation logic.

* **Backend (Flask API)**: The central server that handles business logic, authentication, and orchestrates operations. It exposes REST endpoints for standard CRUD operations and manages WebSocket connections. When a user requests an action that requires a background job (like checking card availability), the backend's primary role is to queue that task and immediately return a response to the client. It does not perform the heavy lifting itself.

* **Scheduler**: A dedicated process responsible for all task management. It schedules recurring jobs (e.g., daily catalog updates) and listens for on-demand task requests from the Backend via a Redis Pub/Sub channel. It is the *only* component that enqueues jobs into the Task Queue.

* **Task Queue (Redis & RQ)**: A Redis-backed queue managed by the Python RQ (Redis Queue) library. The **Scheduler** places long-running or intensive jobs (like web scraping) onto the queue to be processed asynchronously. This ensures the API remains responsive.

* **Worker (RQ Worker)**: A separate process that listens to the Task Queue. It picks up jobs as they are added and executes them. This is where tasks like scraping external store websites or updating catalogs from an external API actually happen. After completing a job, the worker reports results back to the Backend via a Redis Pub/Sub channel.

* **Cache (Redis)**: A Redis instance used for caching temporary data, most notably the results of web scraping for card availability. This prevents the system from repeatedly scraping the same store for the same card, reducing external requests and improving response time.

### Backend System Layers

The backend application is structured into distinct layers to enforce a clear separation of concerns and a unidirectional data flow. This makes the system easier to test, maintain, and reason about.

*   **Data Flow Rule**: The core data flow for asynchronous tasks is: **Backend -> Scheduler -> Worker -> Backend**. The Backend API should never enqueue jobs directly or perform heavy lifting.

* **Handlers (Controller Layer)**: Located in `managers/socket_manager/socket_handlers.py`. This is the entry point for all client communication via WebSockets. Its responsibilities are to:
  * Receive incoming requests.
  * Validate the shape of the incoming data (using Pydantic).
  * Call the appropriate Manager to handle the business logic.
  * Emit results or status updates back to the client.

* **Managers (Service Layer)**: Located in the `managers/` directory (e.g., `availability_manager`, `user_manager`, `task_manager`). This layer contains the core business logic of the application. Its responsibilities are to:
  * Orchestrate complex operations.
  * Interact with the Data Layer to fetch or persist information.
  * Use the `task_manager` to publish commands for the **Scheduler** to queue background jobs.
  * **Data Flow Rule**: Managers should **never** import directly from the `tasks` or `handlers` layers.

* **Tasks (Worker Layer)**: Located in the `tasks/` directory. These are the functions that are executed asynchronously by the RQ Workers. Their responsibilities are to:
  * Perform long-running or I/O-bound operations (e.g., web scraping, calling external APIs).
  * Interact with the Data Layer and Managers as needed.
  * Use the worker-safe `socket_emit` module to send results back to the client.

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
   Backend-->>Client: 409 Conflict {error: "Username already exists"}
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
    participant Scheduler
    participant DB as Database
    participant Redis as Redis (Pub/Sub & Queue)

    Client->>Backend: Emits "add_card" {card, amount, specs}
    activate Backend
    Backend->>DB: user_manager.add_user_card(...)
    activate DB
    DB-->>Backend: Card added
    deactivate DB

    note over Backend, Scheduler: Requirement [5.1.6] - Backend publishes a command for the Scheduler
    loop For each preferred store
        Backend->>Redis: Publishes "queue_task" command for "update_availability_single_card"
    end
    Redis->>Scheduler: Receives command, enqueues task to RQ

    note over Backend: After publishing commands, send updated list to client
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
    
    Note over Backend, Redis: 2. Backend checks cache for each (card, store) pair
    loop For each (Card, Store) combination
        Backend->>Redis: availability_storage.get_availability_data(store_slug, card_name)
        activate Redis
        Redis-->>Backend: Cached Listings (if found)
        deactivate Redis
        
        alt Data is cached
            Note over Backend, Client: 3a. Backend immediately sends cached data to client
            Backend-->>Client: Emits "card_availability_data" {store, card, items}
        else Data is not cached
            Note over Backend, Client: 3b. Backend notifies client that a check has started
            Backend-->>Client: Emits "availability_check_started" {store, card}
            Note over Backend, Redis: 3c. Backend queues a task to fetch the data
            Backend->>Redis: Enqueue Task "update_availability_single_card" {user, store_slug, card_data}
            
        end
    end
    deactivate Backend
    
    Note over Redis, Worker: 4. Worker picks up the queued task
    Redis->>Worker: Pick up Task "update_availability_single_card"
    activate Worker
    
    Note over Worker, ExternalStore: 5. Worker scrapes the external store website
    Worker->>ExternalStore: store_instance.fetch_card_availability(card_data)
    activate ExternalStore
    ExternalStore-->>Worker: Scraped Listings
    deactivate ExternalStore
    
    Note over Worker, Backend: 6. Worker publishes result to a Redis Pub/Sub channel
    Worker->>Backend: Publishes "availability_result" to Redis Pub/Sub
    activate Backend
    Note over Backend: Backend (listening to Pub/Sub) processes the result
    Backend->>Redis: Caches the new data
    deactivate Backend
    
    Note over Worker, Client: 7. Worker also emits data directly to client for immediate UI update
    Backend-->>Client: Emits "card_availability_data" {username, card_name, store_slug, items}
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

#### Scheduled Card Availability Check

This diagram illustrates the scheduled background task for periodically re-checking all tracked cards, fulfilling requirement [5.1.7].

```mermaid
sequenceDiagram

participant Scheduler
participant Redis as Redis Queue
participant Worker as RQ Worker
participant DB as Database
Scheduler->>Redis: Enqueues "update_all_tracked_cards_availability" task
note over Redis, Worker: Worker polls the queue for jobs
Redis->>Worker: Delivers task
activate Worker
Worker->>DB: Get all users and their tracked cards
DB-->>Worker: List of (user, card, store) combinations
note over Worker: For each combination, the worker enqueues a specific "update_availability_single_card" task. This distributes the load and re-uses the existing logic shown in the "Checking Card Availability" diagram.
Worker->>Redis: Enqueue many "update_availability_single_card" tasks
deactivate Worker 
```

#### Background Card Catalog Update

This diagram illustrates the scheduled background task for populating the global card catalog from an external source, fulfilling requirements `[4.1.6]` and `[4.1.7]`.

```mermaid
sequenceDiagram

    participant Scheduler
    participant Redis as Redis Queue
    participant Worker as RQ Worker
    participant ExternalAPI as External Card API (e.g., Scryfall)
    participant DB as Database

    Scheduler->>Redis: Enqueues "update_card_catalog" task
    note over Redis, Worker: Worker polls the queue for jobs
    Redis->>Worker: Delivers "update_card_catalog" task
    activate Worker
    Worker->>ExternalAPI: Request for all card names
    activate ExternalAPI
    ExternalAPI-->>Worker: Returns list of all card names
    deactivate ExternalAPI
    loop For each card name in list
        Worker->>DB: Add card name to catalog
    end
    note right of DB: The database's unique constraint on the name column prevents duplicates.
    deactivate Worker
```

#### Background Set Catalog Update

This diagram illustrates the scheduled background task for populating the set catalog from an external source.

```mermaid
sequenceDiagram

participant Scheduler
participant Redis as Redis Queue
participant Worker as RQ Worker
participant ExternalAPI as External Set API (e.g., Scryfall)
participant DB as Database
Scheduler->>Redis: Enqueues "update_set_catalog" task
note over Redis, Worker: Worker polls the queue for jobs
Redis->>Worker: Delivers "update_set_catalog" task
activate Worker
Worker->>ExternalAPI: Request for all set data
activate ExternalAPI
ExternalAPI-->>Worker: Returns list of all set data
deactivate ExternalAPI
loop For each set in list
   Worker->>DB: Add set to catalog
end
note right of DB: The database's unique constraint on the code column prevents duplicates.
deactivate Worker
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

    note over Backend: Requirement [5.1.6] - Trigger availability check for the new card
    loop For each preferred store
        Backend->>Redis as Redis Queue: Enqueue "update_availability_single_card" task
    end

    Backend-->>Client: Emits "cards_data" {tracked_cards}
    deactivate Backend
    Note right of Client: Dashboard table updates automatically
```

### Messages Sent Between Components

The frontend and backend communicate via two primary methods: a RESTful API for standard requests and Socket.IO for real-time, bidirectional events.
