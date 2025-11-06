# Socket.IO API Reference

This document provides a detailed reference for the real-time events used to communicate between the client (frontend) and the server (backend) via Socket.IO.

## Connection

First, the client must establish a connection to the Socket.IO server.

```javascript
// Example using socket.io-client
import { io } from 'socket.io-client';

const VITE_SOCKET_URL = 'http://localhost:5000'; // Or your production server URL
const socket = io(VITE_SOCKET_URL, {
    withCredentials: true, // Required for session-based authentication
    autoConnect: true      // Or false, if you want to connect manually with socket.connect()
});
```

---

## Client-to-Server Events (Emitters)

These are events that the client emits to the server to request data or perform actions.

### `get_cards`

Requests the user's complete list of tracked cards. This is typically sent immediately after a successful connection.

* **Payload:** `None`
* **Example:**

    ```javascript
    socket.emit('get_cards');
    ```

* **Server Response:** `cards_data`

### `add_card`

Adds a new card to the user's tracked list. The server will process the request, add the card to the database, and respond with the user's updated card list.

* **Payload:** `Object`

    ```javascript
    {
      "card": "Card Name", // string, required
      "amount": 1,         // integer, required
      "card_specs": {      // object, optional
        "set_code": "M21",
        "collector_number": "123",
        "finish": "foil"
      }
    }
    ```

* **Example:**

    ```javascript
    const newCard = { card: "Sol Ring", amount: 1, card_specs: { set_code: "C21" } };
    socket.emit('add_card', newCard);
    ```

* **Server Response:** `cards_data`

### `update_card`

Updates an existing tracked card, such as changing the amount or primary specification.

* **Payload:** `Object`

    ```javascript
    {
      "card": "Card Name", // string, required. The name of the card to update.
      "update_data": {     // object, required. The fields to change.
        "amount": 2,
        "specifications": {
          "set_code": "2X2"
        }
      }
    }
    ```

* **Example:**

    ```javascript
    const cardUpdate = { card: "Sol Ring", update_data: { amount: 4 } };
    socket.emit('update_card', cardUpdate);
    ```

* **Server Response:** `cards_data`

### `delete_card`

Removes a card from the user's tracked list.

* **Payload:** `Object`

    ```javascript
    {
      "card": "Card Name" // string, required. The name of the card to delete.
    }
    ```

* **Example:**

    ```javascript
    socket.emit('delete_card', { card: "Lightning Bolt" });
    ```

* **Server Response:** `cards_data`

### `search_card_names`

Requests a list of card names that match a partial search query. Used for autocomplete functionality.

* **Payload:** `Object`

    ```javascript
    {
      "query": "search term" // string, required.
    }
    ```

* **Example:**

    ```javascript
    socket.emit('search_card_names', { query: "Ligh" });
    ```

* **Server Response:** `card_name_search_results`

### `get_card_availability`

Triggers background tasks on the server to check for the availability of all the user's tracked cards across their preferred stores.

* **Payload:** `None`
* **Example:**

    ```javascript
    socket.emit('get_card_availability');
    ```

* **Server Response:** `availability_check_started`, `card_availability_data`

---

## Server-to-Client Events (Listeners)

These are events that the client should listen for to receive data and status updates from the server.

### `cards_data`

Provides the client with the user's complete and updated list of tracked cards. This is sent in response to `get_cards`, `add_card`, `update_card`, and `delete_card`.

* **Payload:** `Object` containing an array of card objects.
* **Example Listener:**

    ```javascript
    socket.on('cards_data', (data) => {
      // data = { tracked_cards: [ { card_name: "...", amount: 1, ... }, ... ] }
      console.log('Received updated card list:', data.tracked_cards);
      // Update UI state with the new list
    });
    ```

### `card_name_search_results`

Returns a list of autocomplete suggestions in response to a `search_card_names` event.

* **Payload:** `Object` containing an array of strings.
* **Example Listener:**

    ```javascript
    socket.on('card_name_search_results', (data) => {
      // data = { card_names: ["Lightning Bolt", "Lightning Greaves", ...] }
      console.log('Received search results:', data.card_names);
      // Update autocomplete UI
    });
    ```

### `availability_check_started`

Notifies the client that a background availability check has started for a specific card at a specific store. This is useful for showing a "Searching..." or loading state in the UI.

* **Payload:** `Object`
* **Example Listener:**

    ```javascript
    socket.on('availability_check_started', (data) => {
      // data = { store: "store-slug", card: "Card Name" }
      console.log(`Availability check started for ${data.card} at ${data.store}.`);
      // Set UI status for this card to 'searching'
    });
    ```

## Worker-to-Server Events

These messages are sent to the central server from the federated workers.

### `card_availability_data`

Sends real-time stock information for a specific card from a specific store. This is the result of a completed background check.

* **Payload:** 
  `
{
  "store": "store-slug",
  "card": "Card Name",
  "items": [
    {
      "price": 1.99,
      "stock": 4,
      "condition": "Near Mint",
      "set": "tst",
      "collector_number": "123",
      "finish": "non-foil",
      "url": "http://example.com/product/123"
    }
  ]
}
  `  on find. `[]` on not found.

## Server-to-Scheduler Events

### `update_card_availability`

Sends a command to the scheduler that adds an availability job on the queue for specified cards.

* **Payload:** 
  `
  {
    card: "Card Name"
  }
  `
