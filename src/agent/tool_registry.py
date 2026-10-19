
from typing import Any, Callable

from src.tools.doctor_tools import search_doctors_tool
from src.tools.appointment_tools import check_availability_tool
from src.tools.booking_tools import book_appointment_tool


class ToolRegistry:
    """Registry for healthcare agent tools."""

    def __init__(self, hospital_api: Any) -> None:
        self.hospital_api = hospital_api

        self._tools: dict[str, Callable[..., Any]] = {
            "search_doctors": search_doctors_tool,
            "check_availability": check_availability_tool,
            "book_appointment": book_appointment_tool,
        }

    def list_tools(self) -> list[str]:
        """Return the registered tool names."""
        return list(self._tools.keys())

    def execute(
        self,
        tool_name: str,
        arguments: dict[str, Any],
    ) -> Any:
        """Execute a registered tool with the hospital dependency."""

        if tool_name not in self._tools:
            return {
                "status": "error",
                "reason": "unknown_tool",
                "tool_name": tool_name,
            }

        try:
            return self._tools[tool_name](
                hospital=self.hospital_api,
                **arguments,
            )
        except TypeError as exc:
            return {
                "status": "error",
                "reason": "invalid_arguments",
                "message": str(exc),
            }
