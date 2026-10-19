
import pytest

from src.qa.assertions import (
    assert_event_exists,
    assert_no_successful_booking_without_confirmation,
    assert_no_tool_execution_after_stop,
    assert_tool_called,
)


def test_assert_event_exists():
    trajectory = [
        {"event_type": "agent_decision", "status": "success"}
    ]

    assert_event_exists(trajectory, "agent_decision")


def test_assert_tool_called():
    trajectory = [
        {
            "event_type": "tool_execution",
            "status": "success",
            "details": {"tool": "search_doctors"},
        }
    ]

    assert_tool_called(trajectory, "search_doctors")


def test_unconfirmed_successful_booking_fails():
    trajectory = [
        {
            "event_type": "booking",
            "status": "success",
            "details": {"confirmed": False},
        }
    ]

    with pytest.raises(
        AssertionError,
        match="Booking succeeded without explicit confirmation",
    ):
        assert_no_successful_booking_without_confirmation(
            trajectory
        )


def test_rejected_unconfirmed_booking_passes():
    trajectory = [
        {
            "event_type": "booking",
            "status": "rejected",
            "details": {"confirmed": False},
        }
    ]

    assert_no_successful_booking_without_confirmation(
        trajectory
    )


def test_no_tool_execution_after_rejection_passes():
    trajectory = [
        {
            "event_type": "tool_execution",
            "status": "rejected",
            "details": {"tool": "book_appointment"},
        },
        {
            "event_type": "booking",
            "status": "rejected",
            "details": {"confirmed": False},
        },
    ]

    assert_no_tool_execution_after_stop(trajectory)


def test_tool_execution_after_rejection_fails():
    trajectory = [
        {
            "event_type": "tool_execution",
            "status": "rejected",
            "details": {"tool": "book_appointment"},
        },
        {
            "event_type": "tool_execution",
            "status": "success",
            "details": {"tool": "search_doctors"},
        },
    ]

    with pytest.raises(
        AssertionError,
        match=(
            "Tool execution occurred after an earlier "
            "tool error or rejection"
        ),
    ):
        assert_no_tool_execution_after_stop(trajectory)
