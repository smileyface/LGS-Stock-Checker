from app_factory import create_base_app, configure_web_app, configure_database


# This block is only for running the local development server
# directly via `python run.py`.
if __name__ == "__main__":
    # Monkey patch for the development server when run directly.
    # This must be done before other imports that might initialize sockets.
    import eventlet

    eventlet.monkey_patch()

    from managers import socket_manager

    # Create and configure the app for development
    app = create_base_app("development")
    app = configure_web_app(app)
    app = configure_database(app)

    # The host and port are passed here for the dev server run.
    # socket_manager.socketio is the same instance as the one in app_factory,
    # so it's already attached to the app.
    socket_manager.socketio.run(app, debug=True, host="0.0.0.0", port=5000)
