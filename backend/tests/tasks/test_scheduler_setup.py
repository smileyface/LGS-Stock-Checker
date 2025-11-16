import pytest
from unittest.mock import patch, call, ANY
from datetime import timedelta

from tasks.scheduler_setup import (
    schedule_recurring_tasks,
    CATALOG_UPDATE_INTERVAL_HOURS,
    AVAILABILITY_UPDATE_INTERVAL_MINUTES,
)
from managers.task_manager import task_definitions

# Define paths for patching where the objects are used
SCHEDULER_PATH = "tasks.scheduler_setup.redis_manager.scheduler"
LOGGER_ERROR_PATH = "tasks.scheduler_setup.logger.error"


@pytest.fixture
def mock_scheduler():
    """
    Fixture to mock the scheduler object, simulating it's empty by default.
    """
    with patch(SCHEDULER_PATH) as mock:
        # To make `job_id in scheduler` work, we mock __contains__
        mock.__contains__.return_value = False
        yield mock


def test_schedule_recurring_tasks_all_new(mock_scheduler):
    """
    GIVEN an empty scheduler (no tasks are scheduled yet)
    WHEN schedule_recurring_tasks is called
    THEN it should schedule all recurring tasks with the correct parameters.
    """
    # Arrange
    # The mock_scheduler fixture already simulates an empty scheduler.

    # Act
    schedule_recurring_tasks()

    # Assert
    assert mock_scheduler.schedule.call_count == 2

    # Check that each task was scheduled with the correct function and ID
    calls = mock_scheduler.schedule.call_args_list

    catalog_interval = timedelta(
        hours=CATALOG_UPDATE_INTERVAL_HOURS
    ).total_seconds()
    availability_interval = timedelta(
        minutes=AVAILABILITY_UPDATE_INTERVAL_MINUTES
    ).total_seconds()

    # Verify card catalog update task
    assert any(
        c == call(
            scheduled_time=ANY,
            func="tasks.catalog_tasks.update_full_catalog",
            interval=catalog_interval,
            id=task_definitions.FULL_CATALOG_TASK_ID,
            description="Periodically updates the full card, set, printing, "
                        "and finish catalog from Scryfall.",
        )
        for c in calls
    )

    # Verify availability update task
    assert any(
        c == call(
            scheduled_time=ANY,
            func="tasks.card_availability_tasks."
            "update_all_tracked_cards_availability",
            interval=availability_interval,
            id=task_definitions.AVAILABILITY_TASK_ID,
            description="Periodically checks for card availability for"
            " all users.",
        )
        for c in calls
    )


def test_schedule_recurring_tasks_are_idempotent(mock_scheduler):
    """
    GIVEN a scheduler where all tasks are already scheduled
    WHEN schedule_recurring_tasks is called
    THEN it should not schedule any new tasks.
    """
    # Arrange
    # Simulate that all task IDs are already in the scheduler
    mock_scheduler.__contains__.return_value = True

    # Act
    schedule_recurring_tasks()

    # Assert
    mock_scheduler.schedule.assert_not_called()


def test_schedule_recurring_tasks_mixed_state(mock_scheduler):
    """
    GIVEN a scheduler where some tasks exist and some do not
    WHEN schedule_recurring_tasks is called
    THEN it should only schedule the missing tasks.
    """
    # Arrange
    # Simulate that catalog tasks exist, but the availability task does not.
    existing_tasks = [
        task_definitions.FULL_CATALOG_TASK_ID,
    ]
    mock_scheduler.__contains__.side_effect = (
        lambda task_id: task_id in existing_tasks
    )

    # Act
    schedule_recurring_tasks()

    # Assert
    # Only the availability task should have been scheduled.
    availability_interval = timedelta(
        minutes=AVAILABILITY_UPDATE_INTERVAL_MINUTES
    ).total_seconds()

    mock_scheduler.schedule.assert_called_once_with(
        scheduled_time=ANY,
        func="tasks.card_availability_tasks."
        "update_all_tracked_cards_availability",
        interval=availability_interval,
        id=task_definitions.AVAILABILITY_TASK_ID,
        description="Periodically checks for card availability "
                    "for all users.",
    )


@patch(LOGGER_ERROR_PATH)
def test_schedule_recurring_tasks_handles_exception(
    mock_logger_error, mock_scheduler
):
    """
    GIVEN the scheduler raises an exception
    WHEN schedule_recurring_tasks is called
    THEN it should catch the exception and log an error.
    """
    # Arrange
    mock_scheduler.schedule.side_effect = Exception("Redis connection failed")

    # Act
    schedule_recurring_tasks()

    # Assert
    mock_logger_error.assert_called_once()
    assert "Failed to schedule tasks" in mock_logger_error.call_args[0][0]
