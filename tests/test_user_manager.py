import unittest
from unittest.mock import patch, mock_open
from managers.user_manager import add_user, authenticate_user, update_username, load_card_list, save_card_list, \
    load_users, save_users, get_user, get_all_users, update_selected_stores, get_selected_stores, load_user_config, \
    save_user_config, load_json, save_json, get_user_directory


class TestUserAuth(unittest.TestCase):

    @patch("managers.user_manager.user_storage.load_json", return_value={})
    @patch("managers.user_manager.user_storage.save_json")
    def test_add_user(self, mock_save_json, mock_load_json):
        self.assertTrue(add_user("testuser", "password123"))
        mock_save_json.assert_called()


    @patch("managers.user_manager.user_storage.load_json", return_value={"testuser": {"password": "hashedpassword"}})
    @patch("managers.user_manager.user_auth.check_password_hash", return_value=True)
    def test_authenticate_user_success(self, mock_check, mock_load_json):
        self.assertTrue(authenticate_user("testuser", "password123"))
        mock_check.assert_called()


class TestUserCards(unittest.TestCase):

    @patch("managers.user_manager.user_storage.load_json", return_value=["card1", "card2"])
    def test_load_card_list(self, mock_load_json):
        self.assertEqual(load_card_list("testuser"), ["card1", "card2"])
        mock_load_json.assert_called()

    @patch("managers.user_manager.user_storage.save_json")
    def test_save_card_list(self, mock_save_json):
        save_card_list("testuser", ["card1", "card2"])
        mock_save_json.assert_called()


class TestUserPreferences(unittest.TestCase):

    @patch("managers.user_manager.user_storage.load_users", return_value={"testuser": {"selected_stores": []}})
    @patch("managers.user_manager.user_storage.save_users")
    def test_update_selected_stores(self, mock_save_users, mock_load_users):
        update_selected_stores("testuser", ["Store A", "Store B"])
        mock_save_users.assert_called()

    @patch("managers.user_manager.user_storage.load_users", return_value={"testuser": {"selected_stores": ["Store A"]}})
    def test_get_selected_stores(self, mock_load_users):
        self.assertEqual(get_selected_stores("testuser"), ["Store A"])
        mock_load_users.assert_called()


if __name__ == "__main__":
    unittest.main()
