
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any
import json


@dataclass
class QAEvent:
    event_type: str
    status: str
    details: dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), default=str)
