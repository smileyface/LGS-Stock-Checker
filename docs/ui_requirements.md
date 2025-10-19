# UI/Frontend Functional Requirements

This document outlines the functional requirements for the LGS-Stock-Checker frontend, focusing on user interface (UI) behavior and user interactions.

## 1. Authentication

### 1.1 Login View (`Login.vue`)
-   **[UI-1.1.1]** The Login page shall display a form with input fields for "Username" and "Password".
-   **[UI-1.1.2]** The Login page shall display a "Login" button to submit the form.
-   **[UI-1.1.3]** Upon successful login, the user shall be automatically redirected to the Dashboard view.
-   **[UI-1.1.4]** If login fails due to incorrect credentials, a clear error message (e.g., "Login failed. Please check your username and password.") shall be displayed to the user on the Login page.
-   **[UI-1.1.5]** The "Login" button shall enter a disabled state and display feedback (e.g., "Logging in...") while an authentication attempt is in progress.
-   **[UI-1.1.6]** An already authenticated user who navigates to the `/login` path shall be automatically redirected to the Dashboard.

## 2. Main Dashboard (`Dashboard.vue`)

### 2.1 Card Display
-   **[UI-2.1.1]** The Dashboard shall display a table listing all of the user's currently tracked cards.
-   **[UI-2.1.2]** Each row in the table shall represent one tracked card and display its amount, name, and primary specification details (set code, collector number, finish).
-   **[UI-2.1.3]** If a card has no specifications, appropriate placeholders (e.g., "N/A") shall be displayed in the specification columns.

### 2.2 Availability Status
-   **[UI-2.2.1]** For each card in the table, a real-time availability status shall be displayed.
-   **[UI-2.2.2]** While an availability check is in progress for a card, a "Searching" status with a visual loading indicator (e.g., a spinner) shall be displayed.
-   **[UI-2.2.3]** If a card is found to be in stock at any of the user's preferred stores, a distinct "Available" status (e.g., a green badge) shall be displayed.
-   **[UI-2.2.4]** If a card is confirmed to be out of stock at all preferred stores, a "Not Available" status (e.g., a gray badge) shall be displayed.
-   **[UI-2.2.5]** Before an initial availability check has been completed for a card, its status shall default to "Not Available".

### 2.3 Availability Details
-   **[UI-2.3.1]** Double-clicking the "Available" status badge for a card shall open the "In Stock Details Modal".
-   **[UI-2.3.2]** If a user double-clicks a non-"Available" badge, no action shall be taken.

### 2.3 Card Management Actions
-   **[UI-2.3.1]** Each card row shall contain an "Edit" button that, when clicked, opens the Edit Card Modal pre-filled with that card's data.
-   **[UI-2.3.2]** Each card row shall contain a "Delete" button that, when clicked, removes the card from the user's tracked list.
-   **[UI-2.3.3]** The Dashboard shall contain an "Add Card" button that, when clicked, opens the Add Card Modal.

## 3. Modals

### 3.1 Add Card Modal (`AddCardModal.vue`)
-   **[UI-3.1.1]** The Add Card Modal shall provide a form for adding a new card, including fields for Card Name, Amount, and optional specifications (Set Code, Collector Number, Finish).
-   **[UI-3.1.2]** As the user types a card name, a datalist shall provide auto-complete suggestions based on real-time search results from the server. This search shall be debounced to prevent excessive requests.
-   **[UI-3.1.3]** Upon submitting the form, the modal shall emit a `save-card` event with the new card's data.
-   **[UI-3.1.4]** After submission, the modal shall automatically close and reset its form fields to their default state.

### 3.2 Edit Card Modal (`EditCardModal.vue`)
-   **[UI-3.2.1]** When opened, the Edit Card Modal shall be pre-populated with the data of the card being edited.
-   **[UI-3.2.2]** The modal shall allow the user to modify the card's amount and its primary specification.
-   **[UI-3.2.3]** The card name field shall be read-only.
-   **[UI-3.2.4]** Upon saving changes, the modal shall emit an `update-card` event with the modified card data.
-   **[UI-3.2.5]** After saving, the modal shall automatically close.

### 3.3 In Stock Details Modal (`InStockModal.vue`)
-   **[UI-3.3.1]** The modal shall display a list of all available printings for the selected card across all of the user's preferred stores.
-   **[UI-3.3.2]** Each item in the list shall represent a unique available printing at a specific store.
-   **[UI-3.3.3]** Each item shall display the store name, price, set code, collector number, and finish.
-   **[UI-3.3.4]** Each item shall display the card's image for that specific printing. The image shall be linked directly from an external service (e.g., Scryfall) using the set code and collector number, not stored locally.
-   **[UI-3.3.5]** The list of available printings shall be sortable by price.
-   **[UI-3.3.6]** The modal shall include a "Close" button to dismiss it.

## 4. Account Management (`Account.vue`)

### 4.1 User Information
-   **[UI-4.1.1]** The Account page shall display the currently logged-in user's username.
-   **[UI-4.1.2]** The page shall provide a form to update the user's username.
-   **[UI-4.1.3]** The page shall provide a separate form to update the user's password, requiring fields for the current password and the new password.

### 4.2 Store Preferences
-   **[UI-4.2.1]** The Account page shall display a list of all available stores as a series of checkboxes.
-   **[UI-4.2.2]** The checkboxes shall reflect the user's currently saved store preferences.
-   **[UI-4.2.3]** The user shall be able to modify their store preferences by checking or unchecking the boxes.
-   **[UI-4.2.4]** A "Save Preferences" button shall be present to persist any changes to the store selection.

## 5. General Layout & Navigation (`BaseLayout.vue`)

-   **[UI-5.1.1]** The application shall feature a consistent navigation bar across all authenticated views.
-   **[UI-5.1.2]** The navigation bar shall include links to the "Dashboard" and "Account" pages.
-   **[UI-5.1.3]** The navigation bar shall include a "Logout" button that, when clicked, ends the user's session and redirects them to the Login page.

---

*This document will be expanded as new UI features are added.*
-   **[UI-4.2.3]** The user shall be able to modify their store preferences by checking or unchecking the boxes.
-   **[UI-4.2.4]** A "Save Preferences" button shall be present to persist any changes to the store selection.

## 5. General Layout & Navigation (`BaseLayout.vue`)

-   **[UI-5.1.1]** The application shall feature a consistent navigation bar across all authenticated views.
-   **[UI-5.1.2]** The navigation bar shall include links to the "Dashboard" and "Account" pages.
-   **[UI-5.1.3]** The navigation bar shall include a "Logout" button that, when clicked, ends the user's session and redirects them to the Login page.

---

*This document will be expanded as new UI features are added.*
