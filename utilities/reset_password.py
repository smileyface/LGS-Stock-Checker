import sys
import os
from getpass import getpass
from werkzeug.security import generate_password_hash

# This script needs to be run from the LGS_Stock_Backend directory.
# It adds the project's modules to the Python path to allow imports.
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

try:
    from LGS_Stock_Backend.data.database.db_config import SessionLocal, engine
    from LGS_Stock_Backend.data.database.models.orm_models import User, Base
except ImportError as e:
    print("❌ Error: Could not import application modules.")
    print(
        "Please ensure you run this script from the 'LGS_Stock_Backend' directory."
    )
    print(f"Details: {e}")
    sys.exit(1)


def reset_user_password():
    """A command-line utility to reset a user's password or create a new user."""
    print("--- LGS Stock Checker Password Reset ---")

    # Ensure the database and tables exist before trying to query
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()

    try:
        username = input("Enter the username: ").strip()
        user = db.query(User).filter(User.username == username).one_or_none()

        if not user:
            print(f"\nUser '{username}' not found.")
            choice = (
                input("Would you like to create this user? [y/N]: ")
                .strip()
                .lower()
            )
            if choice == "y":
                user = User(username=username)
                db.add(user)
                print(f"Creating new user: {username}")
            else:
                print("Aborting.")
                return

        # Use getpass to securely prompt for the password without showing it on screen
        new_password = getpass("Enter the new password: ")
        confirm_password = getpass("Confirm the new password: ")

        if new_password != confirm_password:
            print("\n❌ Passwords do not match. Aborting.")
            return

        # Hash the new password and update the user object
        user.password_hash = generate_password_hash(new_password)
        db.commit()
        print(
            f"\n✅ Password for user '{username}' has been successfully updated."
        )

    finally:
        db.close()


if __name__ == "__main__":
    reset_user_password()
