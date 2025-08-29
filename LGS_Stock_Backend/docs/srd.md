# Testing Requirements

This document outlines the functional requirements of the LGS-Stock-Checker application, framed as testable scenarios. It serves as a Software Requirements Document (SRD) to guide development and ensure quality assurance.

## 1. User Management

These requirements define the expected behavior of user account creation, modification, and data retrieval.

### 1.1. Core User Operations

-   **[T-US-01]** The system shall allow a new user to be created with a unique username and a password hash.
-   **[T-US-02]** The system shall prevent the creation of a new user if the chosen username already exists.
-   **[T-US-03]** The system shall be able to retrieve a user's complete data by their exact, case-sensitive username.
-   **[T-US-04]** The system shall return no user data when queried with a non-existent username.
-   **[T-US-05]** The system shall provide a method to retrieve all registered users.
-   **[T-US-06]** The system shall return an empty list when retrieving all users if none exist.
-   **[T-US-07]** The system shall provide a "display" version of a user's data that explicitly excludes the password hash.

### 1.2. User Data Modification

-   **[T-US-08]** The system shall allow an existing user's username to be updated. After the update, the old username shall no longer be valid for lookups.
-   **[T-US-09]** An attempt to update the username for a non-existent user shall not create a new user or raise an error.
-   **[T-US-10]** The system shall allow an existing user's password hash to be updated.
-   **[T-US-11]** An attempt to update the password for a non-existent user shall not create a new user or raise an error.

### 1.3. User Store Preferences

-   **[T-US-12]** A user shall be able to add a store to their list of tracked preferences.
-   **[T-US-13]** The system shall prevent a user from adding the same store to their preferences multiple times.
-   **[T-US-14]** An attempt to add a non-existent store to a user's preferences shall be ignored.
-   **[T-US-15]** A user shall be able to remove a store from their list of tracked preferences.
-   **[T-US-16]** The system shall return an empty list when retrieving store preferences for a non-existent user.

## 2. Store Management

These requirements define how store information is managed and retrieved.

-   **[T-ST-01]** The system shall be able to retrieve a specific store's metadata using its unique slug.
-   **[T-ST-02]** The system shall return no data when queried with a non-existent store slug.
-   **[T-ST-03]** The system shall be able to retrieve a list of all available stores.
-   **[T-ST-04]** The system shall return an empty list when retrieving all stores if none exist.

---

*This document will be expanded as new features and tests are added.*