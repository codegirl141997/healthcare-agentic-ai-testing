
import json

from src.qa.events import QAEvent


def test_event_contains_required_fields():
    event = QAEvent(
        event_type="tool_execution",
        status="success",
        details={"tool": "search_doctors"},
    )

    result = event.to_dict()

    assert result["event_type"] == "tool_execution"
    assert result["status"] == "success"
    assert result["details"]["tool"] == "search_doctors"
    assert result["timestamp"]


def test_event_serializes_to_json():
    event = QAEvent("agent_decision", "success")

    result = json.loads(event.to_json())

    assert result["event_type"] == "agent_decision"
    assert result["status"] == "success"

