import json

def test_login_success(client, seeded_user):
    """
    GIVEN a registered user
    WHEN a POST request is made to /api/login with correct credentials
    THEN the response should be 200 OK with a success message.
    """
    response = client.post(
        "/api/login",
        data=json.dumps({"username": "testuser", "password": "password"}),
        content_type="application/json",
    )
    assert response.status_code == 200
    assert response.json["message"] == "Login successful"


def test_login_wrong_password(client, seeded_user):
    """
    GIVEN a registered user
    WHEN a POST request is made to /api/login with an incorrect password
    THEN the response should be 401 Unauthorized.
    """
    response = client.post(
        "/api/login",
        data=json.dumps({"username": "testuser", "password": "wrongpassword"}),
        content_type="application/json",
    )
    assert response.status_code == 401
    assert "error" in response.json


def test_login_user_not_found(client, db_session):
    """
    GIVEN an unregistered user
    WHEN a POST request is made to /api/login
    THEN the response should be 401 Unauthorized.
    """
    response = client.post(
        "/api/login",
        data=json.dumps({"username": "nonexistent", "password": "password"}),
        content_type="application/json",
    )
    assert response.status_code == 401


def test_login_bad_request(client, db_session):
    """
    GIVEN a request with missing credentials
    WHEN a POST request is made to /api/login
    THEN the response should be 400 Bad Request.
    """
    response = client.post(
        "/api/login",
        data=json.dumps({"username": "testuser"}),  # Missing password
        content_type="application/json",
    )
    assert response.status_code == 400


def test_logout_success(client, seeded_user):
    """
    GIVEN a logged-in user
    WHEN a POST request is made to /api/logout
    THEN the user should be logged out successfully.
    """
    # First, log in the user
    client.post(
        "/api/login",
        data=json.dumps({"username": "testuser", "password": "password"}),
        content_type="application/json",
    )

    # Now, log out
    logout_response = client.post("/api/logout")
    assert logout_response.status_code == 200
    assert logout_response.json["message"] == "Logout successful"

    # Verify user is logged out by trying to access a protected route
    user_data_response = client.get("/api/user_data")
    assert user_data_response.status_code == 401  # Unauthorized


def test_logout_not_logged_in(client, db_session):
    """
    GIVEN a client that is not logged in
    WHEN a POST request is made to /api/logout
    THEN the response should be 401 Unauthorized.
    """
    response = client.post("/api/logout")
    assert response.status_code == 401


def test_user_data_success(client, seeded_user_with_stores):
    """
    GIVEN a logged-in user with associated data
    WHEN a GET request is made to /api/user_data
    THEN the response should be 200 OK with the user's data.
    """
    # Log in the user
    client.post(
        "/api/login",
        data=json.dumps({"username": "testuser", "password": "password"}),
        content_type="application/json",
    )

    response = client.get("/api/user_data")
    assert response.status_code == 200
    data = response.json
    assert data["username"] == "testuser"
    assert "test_store" in data["stores"]
    assert "another_store" in data["stores"]

def test_invalid_user_data_request(client, db_session):
    """
    GIVEN a client that is not logged in
    WHEN a GET request is made to /api/user_data
    THEN the response should be 401 Unauthorized.
    """
    client.post(
        "/api/login",
        data=json.dumps({"username": "invaliduser", "password": "password"}),
        content_type="application/json",
    )

    responce = client.get("/api/user_data")
    assert responce.status_code == 401

def test_update_invalid_username(client, seeded_user):
    """
    GIVEN a logged-in user
    WHEN a POST request is made to /api/account/update_username with an invalid username
    THEN the response should be 400 Bad Request.
    """
    client.post(
        "/api/login",
        data=json.dumps({"username": "testuser", "password": "password"}),
        content_type="application/json",
    )

    response = client.post(
        "/api/account/update_username",
        data=json.dumps({"new_username": ""}),  # Empty username
        content_type="application/json",
    )
    assert response.status_code == 400
    assert response.json["error"] == "New username is required"

    response = client.post(
        "/api/account/update_username",
        data=json.dumps({"new_username": "testuser"}),  # Existing username
        content_type="application/json",
    )
    assert response.status_code == 400
    assert response.json["error"] == "Username already exists"

def test_update_invalid_password(client, seeded_user):
    """
    GIVEN a logged-in user
    WHEN a POST request is made to /api/account/update_password with an invalid password
    THEN the response should be 400 Bad Request.
    """
    client.post(
        "/api/login",
        data=json.dumps({"username": "testuser", "password": "password"}),
        content_type="application/json",
    )

    response = client.post(
        "/api/account/update_password",
        data=json.dumps({"current_password": "wrongpassword", "new_password": "newpassword"}),
        content_type="application/json",
    )
    assert response.status_code == 400
    assert response.json["error"] == "Incorrect current password"

    response = client.post(
        "/api/account/update_password",
        data=json.dumps({"current_password": "password", "new_password": ""}),
        content_type="application/json",
    )
    assert response.status_code == 400
    assert response.json["error"] == "Both current and new passwords are required"
    
    #Test current password entered
    response = client.post(
        "/api/account/update_password",
        data=json.dumps({"current_password" : "", "new_password": "newpassword"}),
        content_type="application/json",
    )
    assert response.status_code == 400
    assert response.json["error"] == "Both current and new passwords are required"

def test_user_data_unauthorized(client, db_session):
    """
    GIVEN a client that is not logged in
    WHEN a GET request is made to /api/user_data
    THEN the response should be 401 Unauthorized.
    """
    response = client.get("/api/user_data")
    assert response.status_code == 401

    