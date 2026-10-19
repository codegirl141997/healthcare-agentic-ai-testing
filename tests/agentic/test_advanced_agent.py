import pytest

from src.agent.agent import HealthcareAgent
from src.agent.tool_registry import ToolRegistry
from src.services.mock_hospital_api import MockHospitalAPI


def test_agent_handles_unexpected_tool_exception():
    class CrashingRegistry:
        def execute(self, tool_name, arguments):
            raise RuntimeError("Hospital service unavailable")

    agent = HealthcareAgent(CrashingRegistry())

    state = agent.run([
        {
            "tool_name": "search_doctors",
            "arguments": {"specialty": "cardiology"},
        },
        {
            "type": "final",
            "content": "Search completed.",
        },
    ])

    assert state["status"] == "error"
    assert len(state["history"]) == 1
    assert state["history"][0]["result"]["reason"] == "tool_execution_failed"
