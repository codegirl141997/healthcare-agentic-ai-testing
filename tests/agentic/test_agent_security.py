
import pytest

from src.agent.agent import HealthcareAgent
from src.agent.tool_registry import ToolRegistry
from src.services.mock_hospital_api import MockHospitalAPI


def make_agent():
    hospital = MockHospitalAPI()
    registry = ToolRegistry(hospital)
    return HealthcareAgent(registry), hospital


def test_empty_action_list_does_not_crash():
    agent, _ = make_agent()

    state = agent.run([])

    assert isinstance(state, dict)
    assert "status" in state
    assert "history" in state


@pytest.mark.parametrize(
    "action",
    [
        None,
        "book_appointment",
        {},
        {"tool_name": "search_doctors"},
        {"tool_name": "", "arguments": {}},
        {"tool_name": "search_doctors", "arguments": None},
        {"tool_name": "search_doctors", "arguments": "invalid"},
    ],
)
def test_malformed_actions_are_handled_safely(action):
    agent, hospital = make_agent()

    state = agent.run([action])

    assert isinstance(state, dict)
    assert "status" in state
    assert hospital.bookings == {}


def test_unknown_tool_does_not_create_a_booking():
    agent, hospital = make_agent()

    state = agent.run([
        {
            "tool_name": "admin_delete_all",
            "arguments": {},
        }
    ])

    assert state["status"] == "error"
    assert hospital.bookings == {}
