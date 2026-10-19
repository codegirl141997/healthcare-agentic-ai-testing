
import pytest

from src.agent.agent import HealthcareAgent
from src.agent.tool_registry import ToolRegistry
from src.services.mock_hospital_api import MockHospitalAPI


class FakeToolRegistry:
    """Fake registry used to test agent behavior."""

    def __init__(self):
        self.calls = []

    def execute(self, tool_name, arguments):
        self.calls.append((tool_name, arguments))
        return {"status": "success", "data": {}}


def test_agent_stops_after_booking_requires_confirmation():
    hospital = MockHospitalAPI()
    registry = ToolRegistry(hospital)
    agent = HealthcareAgent(registry)

    state = agent.run([
        {
            "tool_name": "book_appointment",
            "arguments": {
                "doctor_id": "DOC101",
                "appointment_date": "2026-10-19",
                "appointment_time": "11:00",
            },
        },
        {
            "tool_name": "search_doctors",
            "arguments": {"specialty": "cardiology"},
        },
    ])

    assert state["status"] == "rejected"
    assert len(state["history"]) == 1
    assert hospital.bookings == {}


def test_agent_rejects_malformed_action_without_crashing():
    registry = FakeToolRegistry()
    agent = HealthcareAgent(registry)

    state = agent.run([None])

    assert state["status"] == "error"
    assert state["history"][0]["reason"] == "invalid_action"
    assert registry.calls == []


def test_agent_stops_after_rejected_booking():
    class RejectedBookingRegistry:
        def __init__(self):
            self.calls = []

        def execute(self, tool_name, arguments):
            self.calls.append((tool_name, arguments))
            return {
                "status": "rejected",
                "reason": "user_confirmation_required",
            }

    registry = RejectedBookingRegistry()
    agent = HealthcareAgent(registry)

    state = agent.run([
        {
            "tool_name": "book_appointment",
            "arguments": {"confirmed": False},
        },
        {
            "tool_name": "search_doctors",
            "arguments": {"specialty": "cardiology"},
        },
    ])

    assert state["status"] == "rejected"
    assert len(registry.calls) == 1
