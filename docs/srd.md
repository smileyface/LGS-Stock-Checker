# Testing Requirements

This document outlines the functional requirements of the LGS-Stock-Checker application, framed as testable scenarios. It serves as a Software Requirements Document (SRD) to guide development and ensure quality assurance.

## 1 User Management

These requirements define the expected behavior of user account creation, modification, and data retrieval.

### 1.1 Core User Operations

- **[1.1.1]** The system shall allow a new user to be created with a unique username and a password hash.
- **[1.1.2]** The system shall prevent the creation of a new user if the chosen username already exists.
- **[1.1.3]** The system shall be able to retrieve a user's complete data by their exact, case-sensitive username.
- **[1.1.4]** The system shall return no user data when queried with a non-existent username.
- **[1.1.5]** The system shall provide a method to retrieve all registered users.
- **[1.1.6]** The system shall return an empty list when retrieving all users if none exist.
- **[1.1.7]** The system shall provide a "display" version of a user's data that explicitly excludes the password hash.

### 1.2 User Data Modification

- **[1.2.1]** The system shall allow an existing user's username to be updated. After the update, the old username shall no longer be valid for lookups.
- **[1.2.2]** An attempt to update the username for a non-existent user shall not create a new user or raise an error.
- **[1.2.3]** The system shall allow an existing user's password hash to be updated.
- **[1.2.4]** An attempt to update the password for a non-existent user shall not create a new user or raise an error.
- **[1.2.5]** The system shall prevent one user from updating another user's username.
- **[1.2.6]** The system shall ensure all API requests are authenticated

### 1.3 User Store Preferences

- **[1.3.1]** A user shall be able to add a store to their list of tracked preferences.
- **[1.3.2]** The system shall prevent a user from adding the same store to their preferences multiple times.
- **[1.3.3]** A user shall be able to retrieve their list of tracked preferences.
- **[1.3.4]** The system shall return an empty list when retrieving preferences for a non-existent user.
- **[1.3.5]** A user shall be able to update their list of tracked preferences.
- **[1.3.6]** An attempt to add a non-existent store to a user's preferences shall be ignored.
- **[1.3.7]** A user shall be able to remove a store from their list of tracked preferences.

### 1.4 Invalid Input

- **[1.4.1]** The system shall return an error `401 Unauthorized` if there's an invalid password or username when logging in.
- **[1.4.2]** The system shall return an error `400 Bad Request` if a user enters an empty username when updating their username.
- **[1.4.3]** The system shall return an error `400 Bad Request` if a user enters an already existing username when updating their username.
- **[1.4.4]** The system shall return an error `400 Bad Request` if a user enters an empty password when updating their password.

## 2 Store Management

These requirements define how store information is managed and retrieved.

### 2.1 Core Store Operations

- **[2.1.1]** The system shall be able to retrieve a specific store's metadata using its unique slug.
- **[2.1.2]** The system shall return no data when queried with a non-existent store slug.
- **[2.1.3]** The system shall be able to retrieve a list of all available stores.
- **[2.1.4]** The system shall return an empty list when retrieving all stores if none exist.

### 2.2 Crystal Commerce Scraper Interface

These requirements define a standardized, reusable interface for scraping stores that use the Crystal Commerce platform.

- **[2.2.1]** The system shall provide a `CrystalCommerceStore` base class that inherits from the generic `Store` class to encapsulate common scraping logic.
- **[2.2.2]** The base class shall implement a method to perform a product search on a Crystal Commerce site using a card name.
- **[2.2.3]** The base class shall provide a method to fetch the HTML content of an individual product page given its URL.
- **[2.2.4]** The system shall parse search result pages to identify and iterate through all product listings (e.g., `<li>` elements with class `product`).
- **[2.2.5]** For each product listing, the system shall parse all "in-stock" variants to extract Condition, Price, Stock Quantity, and Finish.
- **[2.2.6]** The system shall parse the product detail page to extract canonical information: Card Name, Set Name, and Collector Number.
- **[2.2.7]** The scraper shall stop processing search results for a given card name as soon as it encounters a result that does not match the target card name to improve efficiency.
- **[2.2.8]** The scraper shall prevent duplicate listings from being returned for the same card variant (based on a unique combination of its attributes).
- **[2.2.9]** The scraper shall gracefully handle and log network errors (e.g., timeouts, HTTP errors), returning an empty list of results without crashing.
- **[2.2.10]** The scraper shall gracefully handle and log parsing errors for individual variants, skipping the malformed variant while continuing to process others.

## 3. Card Tracking Management

These requirements define how users manage the list of cards they want to track.

- **[3.1.1]** A user shall be able to add a new card to their tracked list, specifying an amount and optional specifications (set, finish, etc.).
- **[3.1.2]** A duplicate card shall be defined as a card with the same name and specifications.
- **[3.1.3]** The system shall prevent adding a duplicate card *specification* for the same user. Adding a card name that is already tracked will add new specifications to the existing entry.
- **[3.1.4]** A user shall be able to remove a card from their tracked list.
- **[3.1.5]** A user shall be able to update the amount and specifications of a card they are tracking.
- **[3.1.6]** The system shall provide a complete list of a user's tracked cards, including all associated specifications.

### 3.2 Card Specifications

- **[3.2.1]** The system shall maintain a list of valid specifications, including set codes, collector numbers,and finishes.
- **[3.2.2]** The system shall allow users to select from valid specifications when adding or editing a card.
- **[3.2.3]** If a specification is not valid, the system should alert the user

## 4. Cataloging & Search

### 4.1 Card Catalog

These requirements define the global card catalog used for searching and validation.

- **[4.1.0]** A duplicate card shall be defined as a card with the same name.
- **[4.1.1]** The system shall maintain a database table of unique card names (referred to as the "card catalog") to ensure data integrity and consistency across the application.
- **[4.1.2]** The system shall provide a search endpoint that returns a list of card names matching a partial query string.
- **[4.1.3]** The card name search shall be case-insensitive.
- **[4.1.4]** The system shall have a mechanism (e.g., a background task) to populate the global card catalog from an external source.
- **[4.1.5]** The card catalogue shall contain a list of every unique card in the game.
- **[4.1.6]** The system shall include a scheduled background task that periodically fetches a list of all known card names from an external source (e.g., Scryfall) and updates the card catalog.
- **[4.1.7]** The background task shall add any new card names to the catalog that are not already present.
- **[4.1.8]** The background task shall not remove any card names from the catalog, even if they are no longer present in the external source.
- **[4.1.9]** The system shall use the catalogue to validate all cards in the system.

### 4.2 Set Catalog

- **[4.2.1]** The system shall maintain a persistent catalog of unique card sets, storing at least the set code, name, and release date.
- **[4.2.2]** The system shall include a scheduled background task that periodically fetches a list of all known sets from an external source (e.g., Scryfall).
- **[4.2.3]** The system shall limit the execution frequency of the background task to at most once every 24 hours to comply with external API rate limits.
- **[4.2.4]** The background task shall update the catalog with the fetched data, adding new sets and updating details for existing sets.
- **[4.2.5]** The background task shall not remove any sets from the catalog.

### 4.3 Card Printing Catalog & Specification Validation

These requirements define the system for storing detailed card printing data and using it to validate user input.

- **[4.3.1]** The system shall maintain a detailed catalog of all individual card printings. Each printing must be associated with a card name, a set code, and a collector number.
- **[4.3.2]** The system shall maintain a catalog of all possible card finishes (e.g., "foil", "non-foil", "etched").
- **[4.3.3]** The system shall associate each card printing with its available finishes.
- **[4.3.4]** The system shall include a scheduled background task (e.g., `update_full_catalog`) to populate the card printing, finish, and association catalogs from an external source.
- **[4.3.5]** The system shall provide an API endpoint to retrieve all valid printings (i.e., all valid combinations of set, collector number, and finish) for a given card name. This will be used to populate dropdown menus in the UI.
- **[4.3.6]** When a user adds or updates a tracked card with specifications, the system must validate that the provided `set_code`, `collector_number`, and `finish` combination is a valid, existing printing for that card name according to the catalog.
- **[4.3.7]** When a user tracks a card without providing any specifications (set, collector number, or finish), it signifies that they are interested in any available printing of that card.
- **[4.3.8]** When a user provides a partial set of specifications (e.g., only a `set_code`), any omitted fields (e.g., `collector_number`, `finish`) shall be treated as wildcards, matching any valid value for that field.
- **[4.3.9]** If a user submits a request with an invalid specification combination, the system shall reject the request and return an informative error.

## 5. Availability Checking & Notifications

These requirements define the core functionality of checking for card availability at various stores.

- **[5.1.1]** The system shall be able to trigger an availability check for a user's tracked cards against their list of preferred stores.
- **[5.1.2]** Availability checks shall be performed by background workers to avoid blocking the main application and user interface.
- **[5.1.3]** The system shall cache availability results (e.g., in Redis) to minimize redundant web scraping and improve performance.
- **[5.1.4]** The system shall notify the user in real-time via WebSockets when new availability data is found for a card they are tracking.
- **[5.1.5]** The real-time availability data payload for a found item must include the store name, the price, and the specific printing details (set code, collector number, finish).
- **[5.1.6]** The system shall automatically trigger an availability check for a newly added card against the user's preferred stores.
- **[5.1.6.1]** When the client receives availability data, it shall intelligently merge the results: if an item already exists in the local state, its price should be updated; otherwise, the new item should be added. Items no longer present in the payload should be removed from the local state for that specific store.
- **[5.1.7]** The system shall recheck card availability at regular intervals.

---

*This document will be expanded as new features and tests are added.*
