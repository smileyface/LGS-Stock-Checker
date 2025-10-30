# Requirements Traceability Matrix

This document provides a mapping from the software requirements defined in `srd.md` to the specific implementation artifacts (code files, functions, etc.) within the project. This ensures that every requirement has a corresponding implementation and helps in assessing the impact of code changes.

## 1. User Management

| Requirement ID | Requirement Description | Implementation Artifact(s) |
| :--- | :--- | :--- |
| **[1.2.6]** | The system shall ensure all API requests are authenticated. | `LGS_Stock_Backend/managers/flask_manager/flask_manager.py` (Flask-Login setup)<br>`LGS_Stock_Backend/managers/socket_manager/socket_handlers.py` (Use of `@login_required`) |
| **[1.3.1]** | A user shall be able to add a store to their list of tracked preferences. | `LGS_Stock_Backend/managers/user_manager/user_manager.py` (`add_user_store_preference`) |
| **[1.3.7]** | A user shall be able to remove a store from their list of tracked preferences. | `LGS_Stock_Backend/managers/user_manager/user_manager.py` (`remove_user_store_preference`) |

## 2. Store Management

| Requirement ID | Requirement Description | Implementation Artifact(s) |
| :--- | :--- | :--- |
| **[2.1.1]** | Retrieve a specific store's metadata using its unique slug. | `LGS_Stock_Backend/managers/store_manager/store_manager.py` (`get_store_by_slug`) |
| **[2.1.3]** | Retrieve a list of all available stores. | `LGS_Stock_Backend/managers/store_manager/store_manager.py` (`get_all_stores`) |

## 3. Card Tracking Management

| Requirement ID | Requirement Description | Implementation Artifact(s) |
| :--- | :--- | :--- |
| **[3.1.1]** | A user shall be able to add a new card to their tracked list. | **Backend**: `LGS_Stock_Backend/managers/socket_manager/socket_handlers.py` (`on_add_card`)<br>**Frontend**: `frontend/src/views/Dashboard.vue`, `frontend/src/components/AddCardModal.vue`, `frontend/src/composables/useSocket.js` (`saveCard`) |
| **[3.1.4]** | A user shall be able to remove a card from their tracked list. | **Backend**: `LGS_Stock_Backend/managers/socket_manager/socket_handlers.py` (`on_delete_card`)<br>**Frontend**: `frontend/src/views/Dashboard.vue` (`deleteCard`), `frontend/src/composables/useSocket.js` (`deleteCard`) |
| **[3.1.5]** | A user shall be able to update the amount and specifications of a card. | **Backend**: `LGS_Stock_Backend/managers/socket_manager/socket_handlers.py` (`on_update_card`)<br>**Frontend**: `frontend/src/views/Dashboard.vue`, `frontend/src/components/EditCardModal.vue`, `frontend/src/composables/useSocket.js` (`updateCard`) |
| **[3.1.6]** | Provide a complete list of a user's tracked cards. | **Backend**: `LGS_Stock_Backend/managers/socket_manager/socket_handlers.py` (`on_get_cards`)<br>**Frontend**: `frontend/src/composables/useSocket.js` (handler for `cards_data`) |

## 4. Cataloging & Search

| Requirement ID | Requirement Description | Implementation Artifact(s) |
| :--- | :--- | :--- |
| **[4.1.2]** | Provide a search endpoint that returns a list of card names. | **Backend**: `LGS_Stock_Backend/managers/socket_manager/socket_handlers.py` (`on_search_card_names`)<br>**Frontend**: `frontend/src/components/AddCardModal.vue` (emits `search_card_names`) |
| **[4.1.6]** | Scheduled background task to update the card catalog. | `LGS_Stock_Backend/tasks/catalog_tasks.py` (`update_card_catalog`)<br>`LGS_Stock_Backend/tasks/scheduler_setup.py` (`schedule_recurring_tasks`) |
| **[4.2.2]** | Scheduled background task to update the set catalog. | `LGS_Stock_Backend/tasks/catalog_tasks.py` (`update_set_catalog`)<br>`LGS_Stock_Backend/tasks/scheduler_setup.py` (`schedule_recurring_tasks`) |
| **[4.3.4]** | Scheduled background task to populate the full card printing catalog. | `LGS_Stock_Backend/tasks/catalog_tasks.py` (`update_full_catalog`)<br>`LGS_Stock_Backend/tasks/scheduler_setup.py` (`schedule_recurring_tasks`) |
| **[4.3.5]** | API endpoint to retrieve all valid printings for a card name. | `LGS_Stock_Backend/managers/socket_manager/socket_handlers.py` (`on_get_card_printings`) |
| **[4.3.6]** | Validate that a user-provided specification is a valid printing. | `LGS_Stock_Backend/managers/user_manager/user_manager.py` (`add_user_card`, `update_user_card`) |

## 5. Availability Checking & Notifications

| Requirement ID | Requirement Description | Implementation Artifact(s) |
| :--- | :--- | :--- |
| **[5.1.1]** | Trigger an availability check for a user's tracked cards. | **Backend**: `LGS_Stock_Backend/managers/socket_manager/socket_handlers.py` (`on_get_card_availability`)<br>**Frontend**: `frontend/src/composables/useSocket.js` (emits `get_card_availability` on connect) |
| **[5.1.2]** | Availability checks shall be performed by background workers. | `LGS_Stock_Backend/worker_entrypoint.py`<br>`LGS_Stock_Backend/tasks/card_availability_tasks.py` |
| **[5.1.3]** | The system shall cache availability results. | `LGS_Stock_Backend/managers/availability_manager/availability_storage.py` |
| **[5.1.4]** | Notify the user in real-time via WebSockets when new data is found. | **Backend**: `LGS_Stock_Backend/managers/socket_manager/worker_listener.py` (listens for worker results and emits to client)<br>**Frontend**: `frontend/src/composables/useSocket.js` (listens for `card_availability_data`) |
| **[5.1.5]** | Real-time payload must include store, price, and printing details. | `LGS_Stock_Backend/tasks/card_availability_tasks.py` (constructs the payload)<br>`frontend/src/composables/useSocket.js` (consumes the payload) |
| **[5.1.6]** | Automatically trigger an availability check for a newly added card. | `LGS_Stock_Backend/managers/socket_manager/socket_handlers.py` (`on_add_card` calls `availability_manager.check_availability_for_user_cards`) |
| **[5.1.6.1]**| Client shall intelligently merge availability data (upsert logic). | `frontend/src/composables/useSocket.js` (logic within the `card_availability_data` event handler) |
| **[5.1.7]** | Recheck card availability at regular intervals. | `LGS_Stock_Backend/tasks/scheduler_setup.py` (`schedule_recurring_tasks` schedules `update_all_tracked_cards_availability`)<br>`LGS_Stock_Backend/tasks/card_availability_tasks.py` (`update_all_tracked_cards_availability`) |
