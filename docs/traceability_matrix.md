# Requirements Traceability Matrix

This document provides a mapping from the software requirements defined in `srd.md` to the specific implementation artifacts (code files, functions, etc.) within the project. This ensures that every requirement has a corresponding implementation and helps in assessing the impact of code changes.

## 1. User Management (Backend)

## 1. User Management

| Requirement ID | Requirement Description | Implementation Artifact(s) | Test Case(s) |
| :--- | :--- | :--- | :--- |
| **[1.1.1]** | Allow a new user to be created. | `backend/managers/user_manager/user_manager.py` (`add_user`) | `backend/tests/test_user_manager.py` (`test_add_new_user`) |
| **[1.1.2]** | Prevent creation of a user if the username already exists. | `backend/managers/user_manager/user_manager.py` (`user_exists` check in `add_user`) | `backend/tests/test_user_manager.py` (`test_add_existing_user_fails`) |
| **[1.1.3]** | Retrieve a user's complete data by their exact username. | `backend/data/database/user_queries.py` (`get_user_by_username`) | `backend/tests/test_database_queries.py` (`test_get_user_by_username`) |
| **[1.1.7]** | Provide a "display" version of a user's data (no password hash). | `backend/managers/user_manager/user_manager.py` (`get_public_user_profile`) | `backend/tests/test_user_manager.py` (`test_get_public_user_profile`) |
| **[1.2.1]** | Allow an existing user's username to be updated. | `backend/managers/user_manager/user_manager.py` (`update_username`) | `backend/tests/test_user_manager.py` (`test_update_username`) |
| **[1.2.3]** | Allow an existing user's password hash to be updated. | `backend/data/database/user_queries.py` (`update_password`) | `backend/tests/test_database_queries.py` (`test_update_password`) |
| **[1.2.6]** | Ensure all API requests are authenticated. | `backend/managers/flask_manager/flask_manager.py` (Flask-Login setup)<br>`backend/managers/socket_manager/socket_handlers.py` (Use of `current_user`) | `backend/tests/test_authentication.py` (`test_unauthenticated_socket_denial`)<br>`frontend/tests/auth_flow.spec.js` (`test_redirect_on_unauthenticated_access`) |
| **[1.3.1]** | A user shall be able to add a store to their list of tracked preferences. | `backend/data/database/user_queries.py` (`set_user_stores`) | `backend/tests/test_user_preferences.py` (`test_add_user_store_preference`) |
| **[1.3.2]** | Prevent a user from adding the same store multiple times. | `backend/data/database/user_queries.py` (`set_user_stores` logic) | `backend/tests/test_user_preferences.py` (`test_add_duplicate_store_preference`) |
| **[1.3.3]** | A user shall be able to retrieve their list of tracked preferences. | `backend/data/database/user_queries.py` (`get_user_stores`) | `backend/tests/test_user_preferences.py` (`test_get_user_stores`) |
| **[1.3.7]** | A user shall be able to remove a store from their list of tracked preferences. | `backend/data/database/user_queries.py` (`set_user_stores`) | `backend/tests/test_user_preferences.py` (`test_remove_user_store_preference`) |
| **[1.4.1]** | Return `401 Unauthorized` for invalid login. | `backend/routes/auth_routes.py` (`login` endpoint) | `backend/tests/test_auth_routes.py` (`test_login_invalid_credentials`) |

## 2. Store Management

| Requirement ID | Requirement Description | Implementation Artifact(s) | Test Case(s) |
| :--- | :--- | :--- | :--- |
| **[2.1.1]** | Retrieve a specific store's metadata using its unique slug. | `backend/managers/store_manager/store_manager.py` (`get_store`) | `backend/tests/test_store_manager.py` (`test_get_store_by_slug`) |
| **[2.1.3]** | Retrieve a list of all available stores. | `backend/managers/store_manager/stores/__init__.py` (`_load_stores_from_db`) | `backend/tests/manager/test_store_manager.py` (`test_store_registry_loads_from_db`)<br>`frontend/tests/account_page.spec.js` (`test_display_all_stores`) |
| **[2.2.1]** | Provide a `CrystalCommerceStore` base class. | `backend/managers/store_manager/stores/crystal_commerce_store.py` | `backend/tests/store_scrappers/test_crystal_commerce_store.py` |
| **[2.2.2]** | Base class shall perform a product search. | `backend/managers/store_manager/stores/crystal_commerce_store.py` (`_scrape_listings`) | `backend/tests/store_scrappers/test_crystal_commerce_store.py` (`test_scrape_listings_success`) |
| **[2.2.3]** | Base class shall fetch an individual product page. | `backend/managers/store_manager/stores/crystal_commerce_store.py` (`_get_product_page`) | `backend/tests/store_scrappers/test_crystal_commerce_store.py` (`test_scrape_listings_success`) |
| **[2.2.4]** | Parse search result pages for product listings. | `backend/managers/store_manager/stores/crystal_commerce_store.py` (`_get_product_listings`) | `backend/tests/store_scrappers/test_crystal_commerce_store.py` (`test_scrape_listings_success`) |
| **[2.2.5]** | Parse in-stock variants for condition, price, etc. | `backend/managers/store_manager/stores/crystal_commerce_store.py` (`_parse_variants`) | `backend/tests/store_scrappers/test_crystal_commerce_store.py` (`test_scrape_listings_success`) |
| **[2.2.6]** | Parse product detail page for canonical info. | `backend/managers/store_manager/stores/crystal_commerce_store.py` (`_parse_product_page_details`) | `backend/tests/store_scrappers/test_crystal_commerce_store.py` (`test_scrape_listings_success`) |
| **[2.2.7]** | Scraper shall stop on non-matching results. | `backend/managers/store_manager/stores/crystal_commerce_store.py` (`_scrape_listings`) | `backend/tests/store_scrappers/test_crystal_commerce_store.py` (`test_scrape_listings_stops_on_non_matching_card`) |
| **[2.2.8]** | Scraper shall prevent duplicate listings. | `backend/managers/store_manager/stores/crystal_commerce_store.py` (`_scrape_listings`) | `backend/tests/store_scrappers/test_crystal_commerce_store.py` (`test_scrape_listings_deduplicates_results`) |
| **[2.2.9]** | Scraper shall handle network errors. | `backend/managers/store_manager/stores/crystal_commerce_store.py` (`_get_product_page`, `_scrape_listings`) | `backend/tests/store_scrappers/test_crystal_commerce_store.py` (`test_scrape_listings_search_network_failure`) |
| **[2.2.10]**| Scraper shall handle parsing errors. | `backend/managers/store_manager/stores/crystal_commerce_store.py` (`_parse_variants`) | *(Implicitly covered by individual parsing tests)* |

## 3. Card Tracking Management

| Requirement ID | Requirement Description | Implementation Artifact(s) | Test Case(s) |
| :--- | :--- | :--- | :--- |
| **[3.1.1]** | A user shall be able to add a new card to their tracked list. | **Backend**: `backend/managers/socket_manager/socket_handlers.py` (`handle_add_user_tracked_card`)<br>**Frontend**: `frontend/src/composables/useSocket.js` (`saveCard`) | `backend/tests/test_socket_handlers.py` (`test_add_card_socket_event`)<br>`frontend/tests/add_card_modal.spec.js` (`test_add_new_card_submission`) |
| **[3.1.3]** | Prevent adding a duplicate card specification for the same user. | `backend/data/database/user_queries.py` (`add_user_card` logic) | `backend/tests/test_database_queries.py` (`test_add_duplicate_card_spec_fails`) |
| **[3.1.4]** | A user shall be able to remove a card from their tracked list. | **Backend**: `backend/managers/socket_manager/socket_handlers.py` (`handle_delete_user_tracked_card`)<br>**Frontend**: `frontend/src/composables/useSocket.js` (`deleteCard`) | `backend/tests/test_socket_handlers.py` (`test_delete_card_socket_event`)<br>`frontend/tests/dashboard.spec.js` (`test_delete_card_button`) |
| **[3.1.5]** | A user shall be able to update the amount and specifications of a card. | **Backend**: `backend/managers/socket_manager/socket_handlers.py` (`handle_update_user_tracked_cards`)<br>**Frontend**: `frontend/src/composables/useSocket.js` (`updateCard`) | `backend/tests/test_socket_handlers.py` (`test_update_card_socket_event`)<br>`frontend/tests/edit_card_modal.spec.js` (`test_update_card_submission`) |
| **[3.1.6]** | Provide a complete list of a user's tracked cards. | **Backend**: `backend/managers/socket_manager/socket_handlers.py` (`handle_get_cards`)<br>**Frontend**: `frontend/src/composables/useSocket.js` (handler for `cards_data`) | `backend/tests/test_socket_handlers.py` (`test_get_cards_socket_event`)<br>`frontend/tests/dashboard.spec.js` (`test_display_tracked_cards_table`) |
| **[3.2.3]** | If a specification is not valid, the system should alert the user. | `backend/managers/socket_manager/socket_handlers.py` (error handling in `handle_add_user_tracked_card`) | `backend/tests/test_socket_handlers.py` (`test_add_card_with_invalid_spec_emits_error`) |

## 4. Cataloging & Search

| Requirement ID | Requirement Description | Implementation Artifact(s) | Test Case(s) |
| :--- | :--- | :--- | :--- |
| **[4.1.2]** | Provide a search endpoint that returns a list of card names. | **Backend**: `backend/managers/socket_manager/socket_handlers.py` (`handle_search_card_names`)<br>**Frontend**: `frontend/src/components/AddCardModal.vue` | `backend/tests/test_socket_handlers.py` (`test_search_card_names_socket_event`)<br>`frontend/tests/add_card_modal.spec.js` (`test_card_name_autocomplete`) |
| **[4.1.6]** | Scheduled background task to update the card catalog. | `backend/tasks/catalog_tasks.py` (`update_card_catalog`)<br>`backend/tasks/scheduler_setup.py` | `backend/tests/tasks/test_catalog_tasks.py` (`test_update_card_catalog_task`) |
| **[4.2.2]** | Scheduled background task to update the set catalog. | `backend/tasks/catalog_tasks.py` (`update_set_catalog`)<br>`backend/tasks/scheduler_setup.py` | `backend/tests/tasks/test_catalog_tasks.py` (`test_update_set_catalog_task`) |
| **[4.3.4]** | Scheduled background task to populate the full card printing catalog. | `backend/tasks/catalog_tasks.py` (`update_full_catalog`)<br>`backend/tasks/scheduler_setup.py` | `backend/tests/tasks/test_catalog_tasks.py` (`test_update_full_catalog_task`) |
| **[4.3.5]** | API endpoint to retrieve all valid printings for a card name. | `backend/managers/socket_manager/socket_handlers.py` (`handle_get_card_printings`) | `backend/tests/test_socket_handlers.py` (`test_get_card_printings_socket_event`)<br>`frontend/tests/add_card_modal.spec.js` (`test_printing_dropdowns_population`) |
| **[4.3.6]** | Validate that a user-provided specification is a valid printing. | `backend/managers/user_manager/user_manager.py` (`add_user_card`) | `backend/tests/test_user_manager.py` (`test_add_card_with_invalid_spec`) |
| **[4.3.9]** | Reject request with an invalid specification combination. | `backend/managers/socket_manager/socket_handlers.py` (error handling in `handle_add_user_tracked_card`) | `backend/tests/test_socket_handlers.py` (`test_add_card_with_invalid_spec_emits_error`) |

## 5. Availability Checking & Notifications

| Requirement ID | Requirement Description | Implementation Artifact(s) | Test Case(s) |
| :--- | :--- | :--- | :--- |
| **[5.1.1]** | Trigger an availability check for a user's tracked cards. | **Backend**: `backend/managers/socket_manager/socket_handlers.py` (`handle_get_card_availability`)<br>**Frontend**: `frontend/src/composables/useSocket.js` (on connect) | `backend/tests/test_socket_handlers.py` (`test_get_card_availability_triggers_check`)<br>`frontend/tests/dashboard.spec.js` (`test_initial_availability_fetch_on_connect`) |
| **[5.1.2]** | Availability checks shall be performed by background workers. | `backend/worker_entrypoint.py`<br>`backend/tasks/card_availability_tasks.py` | `backend/tests/test_task_manager.py` (`test_queue_task_sends_to_scheduler`)<br>`backend/tests/tasks/test_card_availability_tasks.py` (`test_update_availability_single_card`) |
| **[5.1.3]** | The system shall cache availability results. | `backend/managers/availability_manager/availability_storage.py` | `backend/tests/test_availability_storage.py` (`test_cache_availability_data`, `test_get_cached_availability_data`) |
| **[5.1.4]** | Notify the user in real-time via WebSockets when new data is found. | **Backend**: `backend/managers/socket_manager/worker_listener.py`<br>**Frontend**: `frontend/src/composables/useSocket.js` (listens for `card_availability_data`) | `backend/tests/test_worker_listener.py` (`test_worker_result_emits_to_client`)<br>`frontend/tests/dashboard.spec.js` (`test_realtime_availability_update`) |
| **[5.1.5]** | Real-time payload must include store, price, and printing details. | `backend/tasks/card_availability_tasks.py` (`update_availability_single_card`)<br>`frontend/src/composables/useSocket.js` | `backend/tests/tasks/test_card_availability_tasks.py` (`test_update_availability_single_card_payload`)<br>`frontend/tests/in_stock_modal.spec.js` (`test_display_detailed_items`) |
| **[5.1.6]** | Automatically trigger an availability check for a newly added card. | `backend/managers/socket_manager/socket_handlers.py` (`handle_add_user_tracked_card`) | `backend/tests/test_socket_handlers.py` (`test_add_card_triggers_availability_check`) |
| **[5.1.6.1]**| Client shall intelligently merge availability data (upsert logic). | `frontend/src/composables/useSocket.js` (logic within the `card_availability_data` event handler) | `frontend/tests/use_socket_composable.spec.js` (`test_availability_map_upsert_logic`) |
| **[5.1.7]** | Recheck card availability at regular intervals. | `backend/tasks/scheduler_setup.py`<br>`backend/tasks/card_availability_tasks.py` (`update_all_tracked_cards_availability`) | `backend/tests/tasks/test_scheduler_setup.py` (`test_schedule_recurring_tasks`)<br>`backend/tests/tasks/test_card_availability_tasks.py` (`test_update_all_tracked_cards_availability`) |
