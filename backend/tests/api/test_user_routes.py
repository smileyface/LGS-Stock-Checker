import json
from managers.user_manager import add_user
from data.database.models.orm_models import User

# --- Tests for /api/stores ---

def test_get_all_stores_success(client, seeded_user):
    """
    GIVEN a logged-in user
    WHEN a GET request is made to /api/stores
    THEN the response should be 200 OK with a list of store slugs.
    """
    # Log in the user
    client.post(
        "/api/login",
        data=json.dumps({"username": "testuser", "password": "password"}),
        content_type="application/json",
    )
    response = client.get("/api/stores")
    assert response.status_code == 200
    assert isinstance(response.json, list)
    # A default store from the registry should be present
    assert "authority_games_mesa_az" in response.json

def test_get_all_stores_unauthorized(client, db_session):
    """
    GIVEN a client that is not logged in
    WHEN a GET request is made to /api/stores
    THEN the response should be 401 Unauthorized.
    """
    response = client.get("/api/stores")
    assert response.status_code == 401

# --- Security Test for Unauthorized Access ---

def test_update_another_user_is_impossible(client, db_session):
    """
    GIVEN two users exist in the database
    WHEN user 'user_A' is logged in
    AND 'user_A' sends a request to update their username
    THEN only 'user_A's username is changed, and 'user_B' is unaffected,
    proving that the endpoint correctly uses the logged-in user's session.
    """
    # Arrange: Create two users
    add_user("user_A", "password_A")
    add_user("user_B", "password_B")

    # Log in as user_A
    login_res = client.post(
        "/api/login",
        data=json.dumps({"username": "user_A", "password": "password_A"}),
        content_type="application/json",
    )
    assert login_res.status_code == 200

    # Act: user_A attempts to change their username. The endpoint should only
    # ever affect the currently logged-in user. There's no way to target user_B.
    update_res = client.post(
        "/api/account/update_username",
        data=json.dumps({"new_username": "user_A_renamed"}),
        content_type="application/json",
    )
    assert update_res.status_code == 200

    # Assert
    # Check that user_A was renamed
    renamed_user = db_session.query(User).filter_by(username="user_A_renamed").one_or_none()
    assert renamed_user is not None
    original_user_A = db_session.query(User).filter_by(username="user_A").one_or_none()
    assert original_user_A is None

    # Check that user_B was NOT affected
    user_B = db_session.query(User).filter_by(username="user_B").one_or_none()
    assert user_B is not None

# --- Tests for Invalid Input ---

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

    # Test with an empty username
    response = client.post(
        "/api/account/update_username",
        data=json.dumps({"new_username": ""}),
        content_type="application/json",
    )
    assert response.status_code == 400
    assert response.json["error"] == "New username is required"

    # Create another user to test for existing username collision
    add_user("existing_user", "password")
    
    # Test with an existing username
    response = client.post(
        "/api/account/update_username",
        data=json.dumps({"new_username": "existing_user"}),
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

    # Test with wrong current password
    response = client.post(
        "/api/account/update_password",
        data=json.dumps({"current_password": "wrongpassword", "new_password": "newpassword"}),
        content_type="application/json",
    )
    assert response.status_code == 400
    assert response.json["error"] == "Incorrect current password"

    # Test with empty new password
    response = client.post(
        "/api/account/update_password",
        data=json.dumps({"current_password": "password", "new_password": ""}),
        content_type="application/json",
    )
    assert response.status_code == 400
    assert response.json["error"] == "Both current and new passwords are required"
    
    # Test with empty current password
    response = client.post(
        "/api/account/update_password",
        data=json.dumps({"current_password" : "", "new_password": "newpassword"}),
        content_type="application/json",
    )
    assert response.status_code == 400
    assert response.json["error"] == "Both current and new passwords are required"
