| Method | Endpoint                        | Description                                               |
|--------|---------------------------------|-----------------------------------------------------------|
|  POST  | /api/register                   | Creates a new user account.                               |
|  POST  | /api/login                      | Authenticates a user and creates a session.               |
|  POST  | /api/logout                     | Logs out the current user.                                |
|  GET   | /api/user_data                  | Retrieves the logged-in user's profile data.              |
|  GET   | /api/stores                     | Returns a list of all available store slugs.              |
|  GET   | /api/card_printings/{card_name} | Retrieves all valid printings for a given card name.      |
|  POST  | /api/account/update_username    | Updates the logged-in user's username.                    |
|  POST  | /api/account/update_password    | Updates the logged-in user's password.                    |
|  POST  | /api/account/update_stores      | Updates the logged-in user's preferred stores.            |
|  GET   | /api/stock/{card_name}          | Gets aggregated stock details for a card from all stores. |
