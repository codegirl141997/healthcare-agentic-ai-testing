from typing import Any

from src.qa.events import QAEvent


class TrajectoryRecorder:
    def __init__(self, scenario_id: str):
        self.scenario_id = scenario_id
        self.events: list[QAEvent] = []

    def record(
        self,
        event_type: str,
        status: str,
        details: dict[str, Any] | None = None,
    ) -> QAEvent:
        event = QAEvent(
            event_type=event_type,
            status=status,
            details=details or {},
        )
        self.events.append(event)
        return event

    def get_trajectory(self) -> list[dict[str, Any]]:
        return [event.to_dict() for event in self.events]

    def count_events(self, event_type: str) -> int:
        return sum(
            event.event_type == event_type
            for event in self.events
        )

    def clear(self) -> None:
        self.events.clear()
