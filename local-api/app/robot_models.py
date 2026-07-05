from typing import Any

from pydantic import BaseModel, Field


class RobotCommandCreate(BaseModel):
    action_type: str
    payload: dict[str, Any] = Field(default_factory=dict)
    priority: int = 5


class SafetyRobotRequest(BaseModel):
    robot_id: str
