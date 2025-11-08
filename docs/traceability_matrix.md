# Requirements Traceability Matrix

This document provides a mapping from the software requirements defined in `srd.md` to the specific implementation artifacts (code files, functions, etc.) within the project. This ensures that every requirement has a corresponding implementation and helps in assessing the impact of code changes.

## 1. User Management (Backend)

## 1. User Management

| Requirement ID | Requirement Description | Implementation Artifact(s) | Test Case(s) |
| :--- | :--- | :--- | :--- |
| **[1.1.1]** | Allow a new user to be created. | `LGS_Stock_Backend/managers/user_manager/user_manager.py` (`add_user`) | `LGS_Stock_Backend/tests/test_user_manager.py` (`test_add_new_user`) |
| **[1.1.2]** | Prevent creation of a user if the username already exists. | `LGS_Stock_Backend/managers/user_manager/user_manager.py` (`user_exists` check in `add_user`) | `LGS_Stock_Backend/tests/test_user_manager.py` (`test_add_existing_user_fails`) |
| **[1.1.3]** | Retrieve a user's complete data by their exact username. | `LGS_Stock_Backend/data/database/user_queries.py` (`get_user_by_username`) | `LGS_Stock_Backend/tests/test_database_queries.py` (`test_get_user_by_username`) |
| **[1.1.7]** | Provide a "display" version of a user's data (no password hash). | `LGS_Stock_Backend/managers/user_manager/user_manager.py` (`get_public_user_profile`) | `LGS_Stock_Backend/tests/test_user_manager.py` (`test_get_public_user_profile`) |
| **[1.2.1]** | Allow an existing user's username to be updated. | `LGS_Stock_Backend/managers/user_manager/user_manager.py` (`update_username`) | `LGS_Stock_Backend/tests/test_user_manager.py` (`test_update_username`) |
| **[1.2.3]** | Allow an existing user's password hash to be updated. | `LGS_Stock_Backend/data/database/user_queries.py` (`update_password`) | `LGS_Stock_Backend/tests/test_database_queries.py` (`test_update_password`) |
| **[1.2.6]** | Ensure all API requests are authenticated. | `LGS_Stock_Backend/managers/flask_manager/flask_manager.py` (Flask-Login setup)<br>`LGS_Stock_Backend/managers/socket_manager/socket_handlers.py` (Use of `current_user`) | `LGS_Stock_Backend/tests/test_authentication.py` (`test_unauthenticated_socket_denial`)<br>`frontend/tests/auth_flow.spec.js` (`test_redirect_on_unauthenticated_access`) |
| **[1.3.1]** | A user shall be able to add a store to their list of tracked preferences. | `LGS_Stock_Backend/data/database/user_queries.py` (`set_user_stores`) | `LGS_Stock_Backend/tests/test_user_preferences.py` (`test_add_user_store_preference`) |
| **[1.3.2]** | Prevent a user from adding the same store multiple times. | `LGS_Stock_Backend/data/database/user_queries.py` (`set_user_stores` logic) | `LGS_Stock_Backend/tests/test_user_preferences.py` (`test_add_duplicate_store_preference`) |
| **[1.3.3]** | A user shall be able to retrieve their list of tracked preferences. | `LGS_Stock_Backend/data/database/user_queries.py` (`get_user_stores`) | `LGS_Stock_Backend/tests/test_user_preferences.py` (`test_get_user_stores`) |
| **[1.3.7]** | A user shall be able to remove a store from their list of tracked preferences. | `LGS_Stock_Backend/data/database/user_queries.py` (`set_user_stores`) | `LGS_Stock_Backend/tests/test_user_preferences.py` (`test_remove_user_store_preference`) |
| **[1.4.1]** | Return `401 Unauthorized` for invalid login. | `LGS_Stock_Backend/routes/auth_routes.py` (`login` endpoint) | `LGS_Stock_Backend/tests/test_auth_routes.py` (`test_login_invalid_credentials`) |

## 2. Store Management

| Requirement ID | Requirement Description | Implementation Artifact(s) | Test Case(s) |
| :--- | :--- | :--- | :--- |
| **[2.1.1]** | Retrieve a specific store's metadata using its unique slug. | `LGS_Stock_Backend/managers/store_manager/store_manager.py` (`get_store`) | `LGS_Stock_Backend/tests/test_store_manager.py` (`test_get_store_by_slug`) |
| **[2.1.3]** | Retrieve a list of all available stores. | `LGS_Stock_Backend/managers/store_manager/stores/__init__.py` (`_load_stores_from_db`) | `LGS_Stock_Backend/tests/manager/test_store_manager.py` (`test_store_registry_loads_from_db`)<br>`frontend/tests/account_page.spec.js` (`test_display_all_stores`) |
| **[2.2.1]** | Provide a `CrystalCommerceStore` base class. | `LGS_Stock_Backend/managers/store_manager/stores/crystal_commerce_store.py` | `LGS_Stock_Backend/tests/store_scrappers/test_crystal_commerce_store.py` |
| **[2.2.2]** | Base class shall perform a product search. | `LGS_Stock_Backend/managers/store_manager/stores/crystal_commerce_store.py` (`_scrape_listings`) | `LGS_Stock_Backend/tests/store_scrappers/test_crystal_commerce_store.py` (`test_scrape_listings_success`) |
| **[2.2.3]** | Base class shall fetch an individual product page. | `LGS_Stock_Backend/managers/store_manager/stores/crystal_commerce_store.py` (`_get_product_page`) | `LGS_Stock_Backend/tests/store_scrappers/test_crystal_commerce_store.py` (`test_scrape_listings_success`) |
| **[2.2.4]** | Parse search result pages for product listings. | `LGS_Stock_Backend/managers/store_manager/stores/crystal_commerce_store.py` (`_get_product_listings`) | `LGS_Stock_Backend/tests/store_scrappers/test_crystal_commerce_store.py` (`test_scrape_listings_success`) |
| **[2.2.5]** | Parse in-stock variants for condition, price, etc. | `LGS_Stock_Backend/managers/store_manager/stores/crystal_commerce_store.py` (`_parse_variants`) | `LGS_Stock_Backend/tests/store_scrappers/test_crystal_commerce_store.py` (`test_scrape_listings_success`) |
| **[2.2.6]** | Parse product detail page for canonical info. | `LGS_Stock_Backend/managers/store_manager/stores/crystal_commerce_store.py` (`_parse_product_page_details`) | `LGS_Stock_Backend/tests/store_scrappers/test_crystal_commerce_store.py` (`test_scrape_listings_success`) |
| **[2.2.7]** | Scraper shall stop on non-matching results. | `LGS_Stock_Backend/managers/store_manager/stores/crystal_commerce_store.py` (`_scrape_listings`) | `LGS_Stock_Backend/tests/store_scrappers/test_crystal_commerce_store.py` (`test_scrape_listings_stops_on_non_matching_card`) |
| **[2.2.8]** | Scraper shall prevent duplicate listings. | `LGS_Stock_Backend/managers/store_manager/stores/crystal_commerce_store.py` (`_scrape_listings`) | `LGS_Stock_Backend/tests/store_scrappers/test_crystal_commerce_store.py` (`test_scrape_listings_deduplicates_results`) |
| **[2.2.9]** | Scraper shall handle network errors. | `LGS_Stock_Backend/managers/store_manager/stores/crystal_commerce_store.py` (`_get_product_page`, `_scrape_listings`) | `LGS_Stock_Backend/tests/store_scrappers/test_crystal_commerce_store.py` (`test_scrape_listings_search_network_failure`) |
| **[2.2.10]**| Scraper shall handle parsing errors. | `LGS_Stock_Backend/managers/store_manager/stores/crystal_commerce_store.py` (`_parse_variants`) | *(Implicitly covered by individual parsing tests)* |

## 3. Card Tracking Management

| Requirement ID | Requirement Description | Implementation Artifact(s) | Test Case(s) |
| :--- | :--- | :--- | :--- |
| **[3.1.1]** | A user shall be able to add a new card to their tracked list. | **Backend**: `LGS_Stock_Backend/managers/socket_manager/socket_handlers.py` (`handle_add_user_tracked_card`)<br>**Frontend**: `frontend/src/composables/useSocket.js` (`saveCard`) | `LGS_Stock_Backend/tests/test_socket_handlers.py` (`test_add_card_socket_event`)<br>`frontend/tests/add_card_modal.spec.js` (`test_add_new_card_submission`) |
| **[3.1.3]** | Prevent adding a duplicate card specification for the same user. | `LGS_Stock_Backend/data/database/user_queries.py` (`add_user_card` logic) | `LGS_Stock_Backend/tests/test_database_queries.py` (`test_add_duplicate_card_spec_fails`) |
| **[3.1.4]** | A user shall be able to remove a card from their tracked list. | **Backend**: `LGS_Stock_Backend/managers/socket_manager/socket_handlers.py` (`handle_delete_user_tracked_card`)<br>**Frontend**: `frontend/src/composables/useSocket.js` (`deleteCard`) | `LGS_Stock_Backend/tests/test_socket_handlers.py` (`test_delete_card_socket_event`)<br>`frontend/tests/dashboard.spec.js` (`test_delete_card_button`) |
| **[3.1.5]** | A user shall be able to update the amount and specifications of a card. | **Backend**: `LGS_Stock_Backend/managers/socket_manager/socket_handlers.py` (`handle_update_user_tracked_cards`)<br>**Frontend**: `frontend/src/composables/useSocket.js` (`updateCard`) | `LGS_Stock_Backend/tests/test_socket_handlers.py` (`test_update_card_socket_event`)<br>`frontend/tests/edit_card_modal.spec.js` (`test_update_card_submission`) |
| **[3.1.6]** | Provide a complete list of a user's tracked cards. | **Backend**: `LGS_Stock_Backend/managers/socket_manager/socket_handlers.py` (`handle_get_cards`)<br>**Frontend**: `frontend/src/composables/useSocket.js` (handler for `cards_data`) | `LGS_Stock_Backend/tests/test_socket_handlers.py` (`test_get_cards_socket_event`)<br>`frontend/tests/dashboard.spec.js` (`test_display_tracked_cards_table`) |
| **[3.2.3]** | If a specification is not valid, the system should alert the user. | `LGS_Stock_Backend/managers/socket_manager/socket_handlers.py` (error handling in `handle_add_user_tracked_card`) | `LGS_Stock_Backend/tests/test_socket_handlers.py` (`test_add_card_with_invalid_spec_emits_error`) |

## 4. Cataloging & Search

| Requirement ID | Requirement Description | Implementation Artifact(s) | Test Case(s) |
| :--- | :--- | :--- | :--- |
| **[4.1.2]** | Provide a search endpoint that returns a list of card names. | **Backend**: `LGS_Stock_Backend/managers/socket_manager/socket_handlers.py` (`handle_search_card_names`)<br>**Frontend**: `frontend/src/components/AddCardModal.vue` | `LGS_Stock_Backend/tests/test_socket_handlers.py` (`test_search_card_names_socket_event`)<br>`frontend/tests/add_card_modal.spec.js` (`test_card_name_autocomplete`) |
| **[4.1.6]** | Scheduled background task to update the card catalog. | `LGS_Stock_Backend/tasks/catalog_tasks.py` (`update_card_catalog`)<br>`LGS_Stock_Backend/tasks/scheduler_setup.py` | `LGS_Stock_Backend/tests/tasks/test_catalog_tasks.py` (`test_update_card_catalog_task`) |
| **[4.2.2]** | Scheduled background task to update the set catalog. | `LGS_Stock_Backend/tasks/catalog_tasks.py` (`update_set_catalog`)<br>`LGS_Stock_Backend/tasks/scheduler_setup.py` | `LGS_Stock_Backend/tests/tasks/test_catalog_tasks.py` (`test_update_set_catalog_task`) |
| **[4.3.4]** | Scheduled background task to populate the full card printing catalog. | `LGS_Stock_Backend/tasks/catalog_tasks.py` (`update_full_catalog`)<br>`LGS_Stock_Backend/tasks/scheduler_setup.py` | `LGS_Stock_Backend/tests/tasks/test_catalog_tasks.py` (`test_update_full_catalog_task`) |
| **[4.3.5]** | API endpoint to retrieve all valid printings for a card name. | `LGS_Stock_Backend/managers/socket_manager/socket_handlers.py` (`handle_get_card_printings`) | `LGS_Stock_Backend/tests/test_socket_handlers.py` (`test_get_card_printings_socket_event`)<br>`frontend/tests/add_card_modal.spec.js` (`test_printing_dropdowns_population`) |
| **[4.3.6]** | Validate that a user-provided specification is a valid printing. | `LGS_Stock_Backend/managers/user_manager/user_manager.py` (`add_user_card`) | `LGS_Stock_Backend/tests/test_user_manager.py` (`test_add_card_with_invalid_spec`) |
| **[4.3.9]** | Reject request with an invalid specification combination. | `LGS_Stock_Backend/managers/socket_manager/socket_handlers.py` (error handling in `handle_add_user_tracked_card`) | `LGS_Stock_Backend/tests/test_socket_handlers.py` (`test_add_card_with_invalid_spec_emits_error`) |

## 5. Availability Checking & Notifications

| Requirement ID | Requirement Description | Implementation Artifact(s) | Test Case(s) |
| :--- | :--- | :--- | :--- |
| **[5.1.1]** | Trigger an availability check for a user's tracked cards. | **Backend**: `LGS_Stock_Backend/managers/socket_manager/socket_handlers.py` (`handle_get_card_availability`)<br>**Frontend**: `frontend/src/composables/useSocket.js` (on connect) | `LGS_Stock_Backend/tests/test_socket_handlers.py` (`test_get_card_availability_triggers_check`)<br>`frontend/tests/dashboard.spec.js` (`test_initial_availability_fetch_on_connect`) |
| **[5.1.2]** | Availability checks shall be performed by background workers. | `LGS_Stock_Backend/worker_entrypoint.py`<br>`LGS_Stock_Backend/tasks/card_availability_tasks.py` | `LGS_Stock_Backend/tests/test_task_manager.py` (`test_queue_task_sends_to_scheduler`)<br>`LGS_Stock_Backend/tests/tasks/test_card_availability_tasks.py` (`test_update_availability_single_card`) |
| **[5.1.3]** | The system shall cache availability results. | `LGS_Stock_Backend/managers/availability_manager/availability_storage.py` | `LGS_Stock_Backend/tests/test_availability_storage.py` (`test_cache_availability_data`, `test_get_cached_availability_data`) |
| **[5.1.4]** | Notify the user in real-time via WebSockets when new data is found. | **Backend**: `LGS_Stock_Backend/managers/socket_manager/worker_listener.py`<br>**Frontend**: `frontend/src/composables/useSocket.js` (listens for `card_availability_data`) | `LGS_Stock_Backend/tests/test_worker_listener.py` (`test_worker_result_emits_to_client`)<br>`frontend/tests/dashboard.spec.js` (`test_realtime_availability_update`) |
| **[5.1.5]** | Real-time payload must include store, price, and printing details. | `LGS_Stock_Backend/tasks/card_availability_tasks.py` (`update_availability_single_card`)<br>`frontend/src/composables/useSocket.js` | `LGS_Stock_Backend/tests/tasks/test_card_availability_tasks.py` (`test_update_availability_single_card_payload`)<br>`frontend/tests/in_stock_modal.spec.js` (`test_display_detailed_items`) |
| **[5.1.6]** | Automatically trigger an availability check for a newly added card. | `LGS_Stock_Backend/managers/socket_manager/socket_handlers.py` (`handle_add_user_tracked_card`) | `LGS_Stock_Backend/tests/test_socket_handlers.py` (`test_add_card_triggers_availability_check`) |
| **[5.1.6.1]**| Client shall intelligently merge availability data (upsert logic). | `frontend/src/composables/useSocket.js` (logic within the `card_availability_data` event handler) | `frontend/tests/use_socket_composable.spec.js` (`test_availability_map_upsert_logic`) |
| **[5.1.7]** | Recheck card availability at regular intervals. | `LGS_Stock_Backend/tasks/scheduler_setup.py`<br>`LGS_Stock_Backend/tasks/card_availability_tasks.py` (`update_all_tracked_cards_availability`) | `LGS_Stock_Backend/tests/tasks/test_scheduler_setup.py` (`test_schedule_recurring_tasks`)<br>`LGS_Stock_Backend/tests/tasks/test_card_availability_tasks.py` (`test_update_all_tracked_cards_availability`) |
