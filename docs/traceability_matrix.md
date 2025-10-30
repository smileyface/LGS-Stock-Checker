# Requirements Traceability Matrix

This document provides a mapping from the software requirements defined in `srd.md` to the specific implementation artifacts (code files, functions, etc.) within the project. This ensures that every requirement has a corresponding implementation and helps in assessing the impact of code changes.

## 1. User Management (Backend)

## 1. User Management

| Requirement ID | Requirement Description | Implementation Artifact(s) | Test Case(s) |
| :--- | :--- | :--- | :--- |
| **[1.2.6]** | The system shall ensure all API requests are authenticated. | `LGS_Stock_Backend/managers/flask_manager/flask_manager.py` (Flask-Login setup)<br>`LGS_Stock_Backend/managers/socket_manager/socket_handlers.py` (Use of `@login_required`) | `LGS_Stock_Backend/tests/test_authentication.py` (`test_authenticated_api_access`, `test_unauthenticated_api_denial`)<br>`frontend/tests/auth_flow.spec.js` (`test_redirect_on_unauthenticated_access`) |
| **[1.3.1]** | A user shall be able to add a store to their list of tracked preferences. | `LGS_Stock_Backend/managers/user_manager/user_manager.py` (`add_user_store_preference`) | `LGS_Stock_Backend/tests/test_user_preferences.py` (`test_add_user_store_preference`) |
| **[1.3.7]** | A user shall be able to remove a store from their list of tracked preferences. | `LGS_Stock_Backend/managers/user_manager/user_manager.py` (`remove_user_store_preference`) | `LGS_Stock_Backend/tests/test_user_preferences.py` (`test_remove_user_store_preference`) |

## 2. Store Management

| Requirement ID | Requirement Description | Implementation Artifact(s) | Test Case(s) |
| :--- | :--- | :--- | :--- |
| **[2.1.1]** | Retrieve a specific store's metadata using its unique slug. | `LGS_Stock_Backend/managers/store_manager/store_manager.py` (`get_store_by_slug`) | `LGS_Stock_Backend/tests/test_store_manager.py` (`test_get_store_by_slug`) |
| **[2.1.3]** | Retrieve a list of all available stores. | `LGS_Stock_Backend/managers/store_manager/store_manager.py` (`get_all_stores`) | `LGS_Stock_Backend/tests/test_store_manager.py` (`test_get_all_stores`)<br>`frontend/tests/account_page.spec.js` (`test_display_all_stores`) |

## 3. Card Tracking Management

| Requirement ID | Requirement Description | Implementation Artifact(s) | Test Case(s) |
| :--- | :--- | :--- | :--- |
| **[3.1.1]** | A user shall be able to add a new card to their tracked list. | **Backend**: `LGS_Stock_Backend/managers/socket_manager/socket_handlers.py` (`on_add_card`)<br>**Frontend**: `frontend/src/views/Dashboard.vue`, `frontend/src/components/AddCardModal.vue`, `frontend/src/composables/useSocket.js` (`saveCard`) | `LGS_Stock_Backend/tests/test_socket_handlers.py` (`test_add_card_socket_event`)<br>`frontend/tests/add_card_modal.spec.js` (`test_add_new_card_submission`) |
| **[3.1.4]** | A user shall be able to remove a card from their tracked list. | **Backend**: `LGS_Stock_Backend/managers/socket_manager/socket_handlers.py` (`on_delete_card`)<br>**Frontend**: `frontend/src/views/Dashboard.vue` (`deleteCard`), `frontend/src/composables/useSocket.js` (`deleteCard`) | `LGS_Stock_Backend/tests/test_socket_handlers.py` (`test_delete_card_socket_event`)<br>`frontend/tests/dashboard.spec.js` (`test_delete_card_button`) |
| **[3.1.5]** | A user shall be able to update the amount and specifications of a card. | **Backend**: `LGS_Stock_Backend/managers/socket_manager/socket_handlers.py` (`on_update_card`)<br>**Frontend**: `frontend/src/views/Dashboard.vue`, `frontend/src/components/EditCardModal.vue`, `frontend/src/composables/useSocket.js` (`updateCard`) | `LGS_Stock_Backend/tests/test_socket_handlers.py` (`test_update_card_socket_event`)<br>`frontend/tests/edit_card_modal.spec.js` (`test_update_card_submission`) |
| **[3.1.6]** | Provide a complete list of a user's tracked cards. | **Backend**: `LGS_Stock_Backend/managers/socket_manager/socket_handlers.py` (`on_get_cards`)<br>**Frontend**: `frontend/src/composables/useSocket.js` (handler for `cards_data`) | `LGS_Stock_Backend/tests/test_socket_handlers.py` (`test_get_cards_socket_event`)<br>`frontend/tests/dashboard.spec.js` (`test_display_tracked_cards_table`) |

## 4. Cataloging & Search

| Requirement ID | Requirement Description | Implementation Artifact(s) | Test Case(s) |
| :--- | :--- | :--- | :--- |
| **[4.1.2]** | Provide a search endpoint that returns a list of card names. | **Backend**: `LGS_Stock_Backend/managers/socket_manager/socket_handlers.py` (`on_search_card_names`)<br>**Frontend**: `frontend/src/components/AddCardModal.vue` (emits `search_card_names`) | `LGS_Stock_Backend/tests/test_socket_handlers.py` (`test_search_card_names_socket_event`)<br>`frontend/tests/add_card_modal.spec.js` (`test_card_name_autocomplete`) |
| **[4.1.6]** | Scheduled background task to update the card catalog. | `LGS_Stock_Backend/tasks/catalog_tasks.py` (`update_card_catalog`)<br>`LGS_Stock_Backend/tasks/scheduler_setup.py` (`schedule_recurring_tasks`) | `LGS_Stock_Backend/tests/tasks/test_catalog_tasks.py` (`test_update_card_catalog_task`) |
| **[4.2.2]** | Scheduled background task to update the set catalog. | `LGS_Stock_Backend/tasks/catalog_tasks.py` (`update_set_catalog`)<br>`LGS_Stock_Backend/tasks/scheduler_setup.py` (`schedule_recurring_tasks`) | `LGS_Stock_Backend/tests/tasks/test_catalog_tasks.py` (`test_update_set_catalog_task`) |
| **[4.3.4]** | Scheduled background task to populate the full card printing catalog. | `LGS_Stock_Backend/tasks/catalog_tasks.py` (`update_full_catalog`)<br>`LGS_Stock_Backend/tasks/scheduler_setup.py` (`schedule_recurring_tasks`) | `LGS_Stock_Backend/tests/tasks/test_catalog_tasks.py` (`test_update_full_catalog_task`) |
| **[4.3.5]** | API endpoint to retrieve all valid printings for a card name. | `LGS_Stock_Backend/managers/socket_manager/socket_handlers.py` (`on_get_card_printings`) | `LGS_Stock_Backend/tests/test_socket_handlers.py` (`test_get_card_printings_socket_event`)<br>`frontend/tests/add_card_modal.spec.js` (`test_printing_dropdowns_population`) |
| **[4.3.6]** | Validate that a user-provided specification is a valid printing. | `LGS_Stock_Backend/managers/user_manager/user_manager.py` (`add_user_card`, `update_user_card`) | `LGS_Stock_Backend/tests/test_user_manager.py` (`test_add_card_with_invalid_spec`) |

## 5. Availability Checking & Notifications

| Requirement ID | Requirement Description | Implementation Artifact(s) | Test Case(s) |
| :--- | :--- | :--- | :--- |
| **[5.1.1]** | Trigger an availability check for a user's tracked cards. | **Backend**: `LGS_Stock_Backend/managers/socket_manager/socket_handlers.py` (`on_get_card_availability`)<br>**Frontend**: `frontend/src/composables/useSocket.js` (emits `get_card_availability` on connect) | `LGS_Stock_Backend/tests/test_socket_handlers.py` (`test_get_card_availability_triggers_check`)<br>`frontend/tests/dashboard.spec.js` (`test_initial_availability_fetch_on_connect`) |
| **[5.1.2]** | Availability checks shall be performed by background workers. | `LGS_Stock_Backend/worker_entrypoint.py`<br>`LGS_Stock_Backend/tasks/card_availability_tasks.py` | `LGS_Stock_Backend/tests/test_task_manager.py` (`test_queue_task_sends_to_scheduler`)<br>`LGS_Stock_Backend/tests/tasks/test_card_availability_tasks.py` (`test_update_availability_single_card_execution`) |
| **[5.1.3]** | The system shall cache availability results. | `LGS_Stock_Backend/managers/availability_manager/availability_storage.py` | `LGS_Stock_Backend/tests/test_availability_manager.py` (`test_cache_availability_data`, `test_get_cached_availability_data`) |
| **[5.1.4]** | Notify the user in real-time via WebSockets when new data is found. | **Backend**: `LGS_Stock_Backend/managers/socket_manager/worker_listener.py` (listens for worker results and emits to client)<br>**Frontend**: `frontend/src/composables/useSocket.js` (listens for `card_availability_data`) | `LGS_Stock_Backend/tests/test_worker_listener.py` (`test_worker_result_emits_to_client`)<br>`frontend/tests/dashboard.spec.js` (`test_realtime_availability_update`) |
| **[5.1.5]** | Real-time payload must include store, price, and printing details. | `LGS_Stock_Backend/tasks/card_availability_tasks.py` (constructs the payload)<br>`frontend/src/composables/useSocket.js` (consumes the payload) | `LGS_Stock_Backend/tests/tasks/test_card_availability_tasks.py` (`test_update_availability_single_card_payload`)<br>`frontend/tests/in_stock_modal.spec.js` (`test_display_detailed_items`) |
| **[5.1.6]** | Automatically trigger an availability check for a newly added card. | `LGS_Stock_Backend/managers/socket_manager/socket_handlers.py` (`on_add_card` calls `availability_manager.check_availability_for_user_cards`) | `LGS_Stock_Backend/tests/test_socket_handlers.py` (`test_add_card_triggers_availability_check`) |
| **[5.1.6.1]**| Client shall intelligently merge availability data (upsert logic). | `frontend/src/composables/useSocket.js` (logic within the `card_availability_data` event handler) | `frontend/tests/use_socket_composable.spec.js` (`test_availability_map_upsert_logic`) |
| **[5.1.7]** | Recheck card availability at regular intervals. | `LGS_Stock_Backend/tasks/scheduler_setup.py` (`schedule_recurring_tasks` schedules `update_all_tracked_cards_availability`)<br>`LGS_Stock_Backend/tasks/card_availability_tasks.py` (`update_all_tracked_cards_availability`) | `LGS_Stock_Backend/tests/tasks/test_scheduler_setup.py` (`test_schedule_recurring_tasks`)<br>`LGS_Stock_Backend/tests/tasks/test_card_availability_tasks.py` (`test_update_all_tracked_cards_availability_fan_out`) |
