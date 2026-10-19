
import pytest

from src.agent.agent import HealthcareAgent
from src.qa.assertions import (
    assert_event_exists,
    assert_tool_called,
)


class FakeToolRegistry:
    def execute(self, tool_name, arguments):
        return {
            "status": "success",
            "data": {"message": "Mock result"},
        }


def test_agent_records_tool_execution():
    agent = HealthcareAgent(
        FakeToolRegistry(),
        scenario_id="doctor-search-001",
    )

    agent.run([
        {
            "tool_name": "search_doctors",
            "arguments": {"specialty": "cardiology"},
        }
    ])

    trajectory = agent.get_trajectory()
    assert_event_exists(trajectory, "agent_decision")
    assert_tool_called(trajectory, "search_doctors")


def test_agent_records_final_decision():
    agent = HealthcareAgent(FakeToolRegistry())

    agent.run([
        {
            "type": "final",
            "content": "Here is your answer.",
        }
    ])

    trajectory = agent.get_trajectory()
    assert_event_exists(trajectory, "agent_decision")
    assert trajectory[-1]["details"]["action"] == "final"


def test_agent_records_booking_outcome():
    agent = HealthcareAgent(FakeToolRegistry())

    agent.run([
        {
            "tool_name": "book_appointment",
            "arguments": {"confirmed": True},
        }
    ])

    booking_events = [
        event for event in agent.get_trajectory()
        if event["event_type"] == "booking"
    ]

    assert len(booking_events) == 1
    assert booking_events[0]["details"]["confirmed"] is True


def test_agent_records_malformed_action():
    agent = HealthcareAgent(FakeToolRegistry())

    state = agent.run([None])

    assert state["status"] == "error"

    trajectory = agent.get_trajectory()
    assert_event_exists(trajectory, "agent_decision")
    assert trajectory[-1]["status"] == "error"
    assert trajectory[-1]["details"]["reason"] == "invalid_action"


def test_agent_records_rejected_tool_execution():
    class RejectingToolRegistry:
        def execute(self, tool_name, arguments):
            return {
                "status": "rejected",
                "reason": "booking_requires_confirmation",
            }

    agent = HealthcareAgent(RejectingToolRegistry())

    state = agent.run([
        {
            "tool_name": "book_appointment",
            "arguments": {"confirmed": False},
        }
    ])

    assert state["status"] == "rejected"
    assert_event_exists(agent.get_trajectory(), "tool_execution")
    assert agent.get_trajectory()[-1]["status"] == "rejected"


def test_agent_records_max_iterations_stop():
    agent = HealthcareAgent(
        FakeToolRegistry(),
        max_iterations=1,
    )

    state = agent.run([
        {
            "tool_name": "search_doctors",
            "arguments": {"specialty": "cardiology"},
        },
        {
            "tool_name": "check_availability",
            "arguments": {"doctor_id": "D001"},
        },
    ])

    assert state["status"] == "max_iterations_reached"
    assert agent.get_trajectory()[-1]["details"]["reason"] == (
        "max_iterations_reached"
    )


def test_agent_rejects_zero_max_iterations():
    with pytest.raises(
        ValueError,
        match="max_iterations must be at least 1",
    ):
        HealthcareAgent(FakeToolRegistry(), max_iterations=0)


def test_agent_updates_scenario_id():
    agent = HealthcareAgent(FakeToolRegistry())

    agent.run(
        [{"type": "final", "content": "Done"}],
        scenario_id="scenario-updated",
    )

    assert agent.recorder.scenario_id == "scenario-updated"


def test_agent_handles_non_dict_tool_result():
    class NonDictToolRegistry:
        def execute(self, tool_name, arguments):
            return "unexpected result"

    agent = HealthcareAgent(NonDictToolRegistry())

    state = agent.run([
        {"tool_name": "search_doctors", "arguments": {}}
    ])

    assert state["status"] == "error"
    assert state["history"][0]["result"] == "unexpected result"


def test_agent_stops_after_tool_execution_error():
    class ErrorToolRegistry:
        def execute(self, tool_name, arguments):
            return {
                "status": "error",
                "reason": "simulated_failure",
            }

    agent = HealthcareAgent(ErrorToolRegistry())

    state = agent.run([
        {"tool_name": "search_doctors", "arguments": {}},
        {"type": "final", "content": "Should not execute"},
    ])

    assert state["status"] == "error"
    assert len(state["history"]) == 1


def test_agent_records_booking_with_non_dict_result():
    class NonDictBookingRegistry:
        def execute(self, tool_name, arguments):
            return None

    agent = HealthcareAgent(NonDictBookingRegistry())

    state = agent.run([
        {
            "tool_name": "book_appointment",
            "arguments": {"confirmed": True},
        }
    ])

    assert state["status"] == "error"

    booking_events = [
        event for event in agent.get_trajectory()
        if event["event_type"] == "booking"
    ]

    assert len(booking_events) == 1
    assert booking_events[0]["details"]["confirmed"] is True
