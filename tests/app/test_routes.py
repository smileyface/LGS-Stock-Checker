import pytest
from unittest.mock import patch, MagicMock

from app import create_app


@pytest.fixture
def client():
    """A test client for the Flask application."""
    app = create_app()
    app.config["TESTING"] = True
    app.config["WTF_CSRF_ENABLED"] = False  # Disable CSRF for form tests
    with app.test_client() as client:
        yield client


# Define paths to objects that will be mocked. These paths are where the
# objects are *looked up* (i.e., in the routes file).
USER_MANAGER_PATH = "app.routes.user_routes.user_manager"
LOGIN_USER_PATH = "app.routes.user_routes.login_user"
LOGOUT_USER_PATH = "app.routes.user_routes.logout_user"
CURRENT_USER_PATH = "app.routes.user_routes.current_user"


# --- Test Login Routes ---

def test_login_page_loads(client):
    """
    GIVEN a Flask application
    WHEN the '/login' page is requested (GET)
    THEN check that the response is valid and the login form is present.
    """
    response = client.get("/login")
    assert response.status_code == 200
    assert b"Login" in response.data
    assert b"Username" in response.data
    assert b"Password" in response.data


@patch(LOGIN_USER_PATH)
@patch(USER_MANAGER_PATH)
def test_login_success(mock_user_manager, mock_login_user, client):
    """
    GIVEN a Flask application
    WHEN the '/login' page is posted to (POST) with valid credentials
    THEN check that the user is authenticated and redirected to the dashboard.
    """
    # Arrange
    mock_user = MagicMock()
    mock_user_manager.authenticate_user.return_value = True
    mock_user_manager.get_user.return_value = mock_user

    # Act
    response = client.post(
        "/login",
        data={"username": "testuser", "password": "password"},
        follow_redirects=True,
    )

    # Assert
    mock_user_manager.authenticate_user.assert_called_once_with("testuser", "password")
    mock_user_manager.get_user.assert_called_once_with("testuser")
    mock_login_user.assert_called_once_with(mock_user)
    assert response.status_code == 200
    assert b"Dashboard" in response.data  # Assuming successful login goes to dashboard


@patch(LOGIN_USER_PATH)
@patch(USER_MANAGER_PATH)
def test_login_failure(mock_user_manager, mock_login_user, client):
    """
    GIVEN a Flask application
    WHEN the '/login' page is posted to (POST) with invalid credentials
    THEN check that an error message is shown and the user is not logged in.
    """
    # Arrange
    mock_user_manager.authenticate_user.return_value = False

    # Act
    response = client.post(
        "/login",
        data={"username": "testuser", "password": "wrongpassword"},
        follow_redirects=True,
    )

    # Assert
    mock_user_manager.authenticate_user.assert_called_once_with(
        "testuser", "wrongpassword"
    )
    mock_login_user.assert_not_called()
    assert response.status_code == 200
    assert b"Invalid username or password" in response.data


# --- Test Registration Routes ---

def test_register_page_loads(client):
    """
    GIVEN a Flask application
    WHEN the '/register' page is requested (GET)
    THEN check that the response is valid and the registration form is present.
    """
    response = client.get("/register")
    assert response.status_code == 200
    assert b"Register" in response.data


@patch(USER_MANAGER_PATH)
def test_register_success(mock_user_manager, client):
    """
    GIVEN a Flask application
    WHEN the '/register' page is posted to (POST) with a new username
    THEN check that the user is created and redirected to the login page.
    """
    # Arrange
    mock_user_manager.user_exists.return_value = False  # No existing user
    mock_user_manager.add_user.return_value = True  # User added successfully

    # Act
    response = client.post(
        "/register",
        data={"username": "newuser", "password": "password", "confirm_password": "password"},
        follow_redirects=True,
    )

    # Assert
    mock_user_manager.user_exists.assert_called_once_with("newuser")
    mock_user_manager.add_user.assert_called_once_with("newuser", "password")
    assert response.status_code == 200
    assert b"Account created successfully" in response.data
    assert b"Login" in response.data  # Should be on the login page


@patch(USER_MANAGER_PATH)
def test_register_user_exists(mock_user_manager, client):
    """
    GIVEN a Flask application
    WHEN the '/register' page is posted to (POST) with an existing username
    THEN check that an error message is shown.
    """
    # Arrange
    mock_user_manager.user_exists.return_value = True  # Simulate existing user

    # Act
    response = client.post("/register", data={"username": "existinguser", "password": "password", "confirm_password": "password"})

    # Assert
    mock_user_manager.user_exists.assert_called_once_with("existinguser")
    mock_user_manager.add_user.assert_not_called()
    assert response.status_code == 200
    assert b"Username already exists" in response.data


# --- Test Authenticated Access ---

def test_dashboard_unauthenticated(client):
    """
    GIVEN a Flask application
    WHEN the dashboard '/' is requested by an unauthenticated user
    THEN check that they are redirected to the login page.
    """
    response = client.get("/", follow_redirects=True)
    assert response.status_code == 200
    assert b"Login" in response.data
    assert b"Dashboard" not in response.data


@patch(LOGOUT_USER_PATH)
def test_logout(mock_logout_user, client):
    """
    GIVEN a Flask application
    WHEN the '/logout' route is requested
    THEN check that the user is logged out and redirected to the login page.
    """
    response = client.get("/logout", follow_redirects=True)

    mock_logout_user.assert_called_once()
    assert response.status_code == 200
    assert b"You have been logged out" in response.data
    assert b"Login" in response.data