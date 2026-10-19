
from src.agent.agent import HealthcareAgent
from src.agent.tool_registry import ToolRegistry
from src.services.mock_hospital_api import MockHospitalAPI


def make_agent():
    hospital = MockHospitalAPI()
    registry = ToolRegistry(hospital)
    agent = HealthcareAgent(registry)
    return agent, hospital


def booking_action(**overrides):
    arguments = {
        "doctor_id": "DOC101",
        "appointment_date": "2026-10-19",
        "appointment_time": "11:00",
        "confirmed": True,
    }
    arguments.update(overrides)

    return {
        "tool_name": "book_appointment",
        "arguments": arguments,
    }


def test_unknown_tool_is_rejected_without_crashing():
    agent, hospital = make_agent()

    state = agent.run([
        {
            "tool_name": "delete_hospital_records",
            "arguments": {},
        }
    ])

    assert state["status"] == "error"
    assert state["history"][0]["result"]["reason"] == "unknown_tool"
    assert hospital.bookings == {}


def test_booking_without_confirmation_is_rejected():
    agent, hospital = make_agent()

    state = agent.run([
        booking_action(confirmed=False)
    ])

    assert state["status"] == "rejected"
    assert state["history"][0]["result"]["reason"] == (
        "user_confirmation_required"
    )
    assert hospital.bookings == {}


def test_string_confirmation_does_not_bypass_confirmation():
    agent, hospital = make_agent()

    state = agent.run([
        booking_action(confirmed="true")
    ])

    assert state["status"] == "rejected"
    assert state["history"][0]["result"]["reason"] == (
        "user_confirmation_required"
    )
    assert hospital.bookings == {}


def test_extra_confirmation_field_does_not_bypass_validation():
    agent, hospital = make_agent()

    state = agent.run([
        {
            "tool_name": "book_appointment",
            "arguments": {
                "doctor_id": "DOC101",
                "appointment_date": "2026-10-19",
                "appointment_time": "11:00",
                "confirmation": True,
            },
        }
    ])

    assert state["status"] == "error"
    assert state["history"][0]["result"]["reason"] == (
        "invalid_arguments"
    )
    assert hospital.bookings == {}


def test_invalid_date_is_rejected_without_booking():
    agent, hospital = make_agent()

    state = agent.run([
        booking_action(appointment_date="not-a-date")
    ])

    assert state["status"] == "rejected"
    assert state["history"][0]["result"]["reason"] == "invalid_date"
    assert hospital.bookings == {}


def test_duplicate_booking_is_rejected():
    agent, hospital = make_agent()

    first_state = agent.run([booking_action()])

    assert first_state["history"][0]["result"]["status"] == "confirmed"
    assert len(hospital.bookings) == 1

    second_state = agent.run([booking_action()])

    assert second_state["status"] == "rejected"
    assert second_state["history"][0]["result"]["reason"] == (
        "slot_unavailable"
    )
    assert len(hospital.bookings) == 1


def test_agent_stops_after_unexpected_tool_exception():
    class ExplodingRegistry:
        def __init__(self):
            self.calls = []

        def execute(self, tool_name, arguments):
            self.calls.append(tool_name)
            raise RuntimeError("Simulated internal failure")

    registry = ExplodingRegistry()
    agent = HealthcareAgent(registry)

    state = agent.run([
        {
            "tool_name": "search_doctors",
            "arguments": {"specialty": "cardiology"},
        },
        {
            "tool_name": "book_appointment",
            "arguments": {},
        },
    ])

    assert state["status"] == "error"
    assert len(registry.calls) == 1
    assert state["history"][0]["result"]["reason"] == (
        "tool_execution_failed"
    )
    assert state["history"][0]["result"]["message"] == (
        "Tool execution failed unexpectedly."
    )

def test_agent_respects_max_iterations():
    hospital = MockHospitalAPI()
    registry = ToolRegistry(hospital)
    agent = HealthcareAgent(registry, max_iterations=1)

    state = agent.run([
        {
            "tool_name": "search_doctors",
            "arguments": {"specialty": "cardiology"},
        },
        {
            "tool_name": "check_availability",
            "arguments": {
                "doctor_id": "DOC101",
                "appointment_date": "2026-10-19",
            },
        },
    ])

    assert state["status"] == "max_iterations_reached"
    assert len(state["history"]) == 1
    assert state["history"][0]["tool_name"] == "search_doctors"


def test_agent_records_rejected_booking_in_trajectory():
    agent, hospital = make_agent()

    agent.run([
        booking_action(confirmed=False)
    ])

    trajectory = agent.get_trajectory()

    booking_events = [
        event for event in trajectory
        if event["event_type"] == "booking"
    ]

    assert len(booking_events) == 1
    assert booking_events[0]["status"] == "rejected"
    assert booking_events[0]["details"]["confirmed"] is False
    assert hospital.bookings == {}
def test_tool_registry_rejects_invalid_arguments_directly():
    hospital = MockHospitalAPI()
    registry = ToolRegistry(hospital)

    result = registry.execute(
        "search_doctors",
        {
            "specialty": "cardiology",
            "unexpected_argument": True,
        },
    )

    assert result["status"] == "error"
    assert result["reason"] == "invalid_arguments"
    assert "unexpected_argument" in result["message"]
    assert hospital.bookings == {}