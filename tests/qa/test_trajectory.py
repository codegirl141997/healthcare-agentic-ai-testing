from src.qa.trajectory import TrajectoryRecorder


def test_recorder_preserves_event_order():
    recorder = TrajectoryRecorder("test-001")

    recorder.record("agent_decision", "success")
    recorder.record(
        "tool_execution",
        "success",
        {"tool": "search_doctors"},
    )

    trajectory = recorder.get_trajectory()

    assert len(trajectory) == 2
    assert trajectory[0]["event_type"] == "agent_decision"
    assert trajectory[1]["event_type"] == "tool_execution"


def test_recorder_counts_events():
    recorder = TrajectoryRecorder("test-002")

    recorder.record("tool_execution", "success")
    recorder.record("tool_execution", "error")
    recorder.record("agent_decision", "success")

    assert recorder.count_events("tool_execution") == 2


def test_recorder_clear_removes_events():
    recorder = TrajectoryRecorder("test-003")

    recorder.record("agent_decision", "success")
    recorder.clear()

    assert recorder.get_trajectory() == []
