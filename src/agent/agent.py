

from src.agent.tool_registry import ToolRegistry
from src.qa.trajectory import TrajectoryRecorder


class HealthcareAgent:
    """Deterministic healthcare agent with QA trajectory recording."""

    def __init__(
        self,
        tool_registry,
        max_iterations=10,
        scenario_id="default",
        trajectory_recorder=None,
    ):
        if max_iterations < 1:
            raise ValueError("max_iterations must be at least 1")

        self.tool_registry = tool_registry
        self.max_iterations = max_iterations

        self.recorder = trajectory_recorder or TrajectoryRecorder(
            scenario_id
        )

        self.state = {
            "history": [],
            "results": {},
            "status": "idle",
        }

    def _record_decision(self, status, details):
        self.recorder.record(
            event_type="agent_decision",
            status=status,
            details=details,
        )

    def run(self, actions, scenario_id=None):
        """Execute actions and record the agent's trajectory."""

        if scenario_id is not None:
            self.recorder.scenario_id = scenario_id

        # Start a fresh trajectory for each run.
        self.recorder.clear()

        self.state = {
            "history": [],
            "results": {},
            "status": "running",
        }

        for iteration, action in enumerate(actions):
            if iteration >= self.max_iterations:
                self.state["status"] = "max_iterations_reached"

                self._record_decision(
                    "rejected",
                    {
                        "reason": "max_iterations_reached",
                        "limit": self.max_iterations,
                    },
                )
                break

            if not isinstance(action, dict):
                self.state["status"] = "error"

                self.state["history"].append(
                    {
                        "status": "error",
                        "reason": "invalid_action",
                    }
                )

                self._record_decision(
                    "error",
                    {"reason": "invalid_action"},
                )
                break

            if action.get("type") == "final":
                self.state["status"] = "completed"
                self.state["final_answer"] = action.get(
                    "content", ""
                )

                self._record_decision(
                    "success",
                    {
                        "action": "final",
                        "content": self.state["final_answer"],
                    },
                )
                break

            tool_name = action.get("tool_name")
            arguments = action.get("arguments", {})

            if (
                not isinstance(tool_name, str)
                or not tool_name
                or not isinstance(arguments, dict)
            ):
                self.state["status"] = "error"

                self.state["history"].append(
                    {
                        "status": "error",
                        "reason": "invalid_action",
                    }
                )

                self._record_decision(
                    "error",
                    {"reason": "invalid_action"},
                )
                break

            self._record_decision(
                "success",
                {
                    "action": "execute_tool",
                    "tool": tool_name,
                    "iteration": iteration + 1,
                },
            )

            try:
                result = self.tool_registry.execute(
                    tool_name,
                    arguments,
                )
            except Exception:
                result = {
                    "status": "error",
                    "reason": "tool_execution_failed",
                    "message": "Tool execution failed unexpectedly.",
                }

            event = {
                "iteration": iteration + 1,
                "tool_name": tool_name,
                "arguments": arguments,
                "result": result,
            }

            self.state["history"].append(event)

            self.state["results"][
                f"step_{iteration + 1}"
            ] = result

            if not isinstance(result, dict):
                self.state["status"] = "error"
                execution_status = "error"
            else:
                execution_status = result.get("status", "success")

            self.recorder.record(
                event_type="tool_execution",
                status=execution_status,
                details={
                    "tool": tool_name,
                    "arguments": arguments,
                    "result": result,
                    "iteration": iteration + 1,
                },
            )

            if tool_name == "book_appointment":
                self.recorder.record(
                    event_type="booking",
                    status=execution_status,
                    details={
                        "confirmed": (
                            arguments.get("confirmed") is True
                            or arguments.get("confirmation") is True
                        ),
                        "tool": tool_name,
                        "result": result,
                    },
                )

            if not isinstance(result, dict):
                self.state["status"] = "error"
                break

            if result.get("status") == "error":
                self.state["status"] = "error"
                break

            if result.get("status") == "rejected":
                self.state["status"] = "rejected"
                break

        else:
            self.state["status"] = "completed"

        return self.state

    def get_trajectory(self):
        """Return recorded events as dictionaries."""
        return self.recorder.get_trajectory()
