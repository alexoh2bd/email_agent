"""Shared agent state for the two-node pipeline."""

from typing import Any, TypedDict


class AgentState(TypedDict, total=False):
    user_task: str
    working_memory: dict[str, Any]
    strategy_plan: str | None
    draft: str
    email_history: list[str]
    node: str


def initial_state(user_task: str) -> dict[str, Any]:
    return {
        "user_task": user_task,
        "working_memory": {},
        "strategy_plan": None,
        "draft": "",
        "email_history": [],
        "node": "research",
    }
