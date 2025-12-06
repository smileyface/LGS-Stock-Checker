from app_factory import create_base_app, configure_scheduler_app, configure_database

if __name__ == "__main__":
    # Monkey patch for eventlet-based concurrency.
    import eventlet

    eventlet.monkey_patch()

    # These imports must come AFTER monkey_patching
    from managers.flask_manager import scheduler_listener
    from managers import redis_manager
    from tasks.scheduler_setup import schedule_recurring_tasks
    from utility import logger

    # Create and configure the app for scheduling.
    app = create_base_app()
    app = configure_scheduler_app(app)
    app = configure_database(app)

    with app.app_context():
        # Schedule recurring jobs like catalog updates and availability checks.
        schedule_recurring_tasks()

        scheduler_listener.start_scheduler_listener(app)
        logger.info(
            "🎧 Scheduler process is now up and listening for commands."
        )
        redis_manager.scheduler.run()
