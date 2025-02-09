import time
import redis
from flask import Blueprint, render_template, request, redirect, url_for, jsonify, session, flash
from rq import Queue

from managers.availability_manager.availability_update import load_availability_state
from managers.card_manager.card_manager import parse_card_list
from core.store_manager import STORE_REGISTRY
from worker.tasks import update_availability, update_availability_single_card
from managers.user_manager.user_manager import (
    add_user,
    authenticate_user,
    get_user,
    load_card_list,
    save_card_list,
    update_selected_stores,
    update_username,
)

main = Blueprint("main", __name__)

# Connect to Redis running in Docker
redis_conn = redis.Redis(host="localhost", port=6379)
queue = Queue(connection=redis_conn)

# Home page
@main.route("/")
def index():
    return render_template("index.html")

# Store management
@main.route("/stores/", methods=["GET", "POST"])
def stores():
    """
    Displays and updates the stores for the logged-in user.
    """
    # Ensure the user is logged in
    if "username" not in session:
        flash("You must be logged in to access this page.", "warning")
        return redirect(url_for("main.login"))

    username = session["username"]  # Get the logged-in user's username

    if request.method == "POST":
        # Update selected stores
        selected_stores = request.form.getlist("stores")
        update_selected_stores(username, selected_stores)
        flash("Stores updated successfully.", "success")

    # Fetch user data and available stores
    user = get_user(username)
    all_stores = list(STORE_REGISTRY.keys())

    # Pass selected stores to the template
    selected_stores = user["selected_stores"]

    return render_template(
        "stores.html",
        username=username,
        all_stores=all_stores,
        selected_stores=selected_stores,
    )

# Card management
@main.route("/cards", methods=["GET", "POST"])
def cards():
    if "username" not in session:
        flash("You must be logged in to access your cards.", "warning")
        return redirect(url_for("main.login"))

    username = session["username"]

    if request.method == "POST":
        file = request.files["card_file"]
        if file:
            # Save uploaded card list
            card_list = parse_card_list(file.stream.read().decode("utf-8"))
            save_card_list(username, card_list)
            flash("Card list uploaded successfully.", "success")
        return redirect(url_for("main.cards"))

    # Load the user's card list
    card_list = load_card_list(username)
    return render_template("cards.html", username=username, card_list=card_list)

@main.route("/edit-card/<int:card_index>", methods=["GET", "POST"])
def edit_card(card_index):
    if "username" not in session:
        flash("You must be logged in to edit cards.", "warning")
        return redirect(url_for("main.login"))

    username = session["username"]
    card_list = load_card_list(username)

    # Ensure the index is valid
    if card_index < 0 or card_index >= len(card_list):
        flash("Invalid card index.", "danger")
        return redirect(url_for("main.cards"))

    card = card_list[card_index]  # The card to edit

    if request.method == "POST":
        if "delete" in request.form:
            card_list.pop(card_index)
            save_card_list(username, card_list)
            flash("Card removed successfully.", "success")
            return redirect(url_for("main.cards"))

        # VALIDATE INPUTS
        try:
            amount = int(request.form.get("amount"))
            if amount <= 0:
                raise ValueError("Amount must be a positive integer.")

            card_name = request.form.get("card_name").strip()
            if not card_name or len(card_name) > 100:
                raise ValueError("Card name is required and must be under 100 characters.")

            set_code = request.form.get("set_code").strip().upper()
            collector_id = request.form.get("collector_id").strip()

            finish = request.form.get("finish")
            if finish not in ["normal", "foil", "etched", "N/A"]:
                raise ValueError("Invalid finish type selected.")

            # UPDATE CARD DETAILS
            card["amount"] = amount
            card["card_name"] = card_name
            card["set_code"] = set_code if set_code else None
            card["collector_id"] = collector_id if collector_id else None
            card["finish"] = finish

            save_card_list(username, card_list)
            flash("Card updated successfully.", "success")
            return redirect(url_for("main.cards"))

        except ValueError as e:
            flash(str(e), "danger")
            return redirect(url_for("main.edit_card", card_index=card_index))

    return render_template("edit_card.html", card=card, card_index=card_index)


# availability Management
@main.route("/availability", methods=["GET", "POST"])
def availability():
    """
    Display the cached availability and refresh outdated cards.
    """
    username = session.get("username")
    if not username:
        flash("You must be logged in to access your account.", "warning")
        return redirect(url_for("main.login"))
    
    # Load cached availability from Redis
    availability = load_availability_state(username)

    # Set up a threshold for "outdated" data (e.g., 30 minutes)
    REFRESH_RATE = 1800  # 30 minutes in seconds
    current_time = int(time.time())

    outdated_cards = []

    for card_name, stores in availability.items():
        for store_name, listings in stores.items():
            for listing in listings:
                last_updated = listing.get("last_updated", 0)

                # If the data is too old, mark it for a refresh
                if current_time - last_updated > REFRESH_RATE:
                    outdated_cards.append((username, store_name, card_name))

    # If outdated cards exist, enqueue jobs to refresh them
    for username, store_name, card_name in outdated_cards:
        update_availability_single_card(username, store_name, {"card_name": card_name})

    return render_template(
        "availability.html",
        username=username,
        availability=availability,
        last_updated=time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(current_time))
    )


@main.route("/<username>/account", methods=["GET", "POST"])
def account(username=None):
    """
    Handles user account settings, including updating the username and selected stores.
    """
    if username == None or "username" not in session or session["username"] != username:
        flash("You must be logged in to access your account.", "warning")
        return redirect(url_for("main.login"))

    if request.method == "POST":
        if "update_username" in request.form:
            # Update username
            new_username = request.form.get("new_username")
            update_username(username, new_username)
            username = new_username
        elif "update_stores" in request.form:
            # Update selected stores
            selected_stores = request.form.getlist("stores")
            update_selected_stores(username, selected_stores)

    user = get_user(username)
    all_stores = list(STORE_REGISTRY.keys())

    return render_template(
        "account.html",
        username=username,
        user=user,
        stores=all_stores,
    )

# Login route
@main.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if authenticate_user(username, password):
            session["username"] = username
            session.modified = True  # 🔧 Force session save
            print(f"✅ Login successful! Session username set: {session.get('username')}")
            return redirect(url_for("main.index"))
        else:
            print("❌ Login failed. Invalid credentials.")
            flash("Invalid username or password.", "danger")

    print(f"🔎 Session before login: {session}")
    return render_template("login.html")

@main.route("/create-account", methods=["GET", "POST"])
def create_account():
    """
    Handles user account creation.
    """
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")

        # Validate inputs
        if not username or not password or not confirm_password:
            flash("All fields are required.", "danger")
            return redirect(url_for("main.create_account"))

        if password != confirm_password:
            flash("Passwords do not match.", "danger")
            return redirect(url_for("main.create_account"))

        # Add the user
        success = add_user(username, password)
        if success:
            flash("Account created successfully. Please log in.", "success")
            return redirect(url_for("main.login"))
        else:
            flash(f"Username '{username}' already exists.", "danger")

    return render_template("create_account.html")

@main.route("/refresh-availability", methods=["POST"])
def refresh_availability():
    """
    Triggers an availability refresh.
    """
    username = session.get("username")  # Get logged-in user
    if not username:
        return jsonify({"error": "Unauthorized"}), 401

    update_availability(username)  # ✅ Enqueue jobs for updating availability

    return jsonify({"message": "availability refresh started"}), 200

@main.route("/refresh-card", methods=["POST"])
def refresh_card():
    """
    Refreshes a single card's availability.
    """
    data = request.get_json()
    store_name = data.get("store")
    card_name = data.get("card")
    username = "kason"  # TODO: Replace with session-based username

    if not store_name or not card_name:
        return jsonify({"error": "Missing parameters"}), 400

    # Run the refresh job in the background
    update_availability_single_card(username, store_name, {"card_name": card_name})

    # Load the updated availability
    availability = load_availability_state(username)
    updated_item = availability.get(card_name, {}).get(store_name, [{}])[0]

    return jsonify(updated_item)