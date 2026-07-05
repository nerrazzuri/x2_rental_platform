from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any, Protocol

from .robot_adapters import RobotAdapterCommandError, RobotAdapterUnavailable, get_robot_adapter
from .robot_models import RobotCommandCreate


class RobotCommandExecutor(Protocol):
    def status(self) -> dict[str, Any]:
        ...

    def execute(
        self,
        robot_id: str,
        command: RobotCommandCreate,
        trace_id: str,
    ) -> dict[str, Any]:
        ...


class RobotGatewayHttpError(RuntimeError):
    def __init__(self, status_code: int, detail: dict[str, Any]):
        super().__init__(str(detail))
        self.status_code = status_code
        self.detail = detail


def robot_gateway_url() -> str | None:
    value = os.getenv("X2_ROBOT_GATEWAY_URL", "").strip().rstrip("/")
    return value or None


def robot_gateway_timeout() -> float:
    return float(os.getenv("X2_ROBOT_GATEWAY_TIMEOUT_SECONDS", "5.0"))


def get_robot_executor() -> RobotCommandExecutor:
    gateway_url = robot_gateway_url()
    if gateway_url:
        return HttpRobotGatewayClient(gateway_url, robot_gateway_timeout())
    return LocalRobotExecutor()


class LocalRobotExecutor:
    def status(self) -> dict[str, Any]:
        return {
            **get_robot_adapter().status(),
            "execution_location": "local",
            "gateway_url": None,
        }

    def execute(
        self,
        robot_id: str,
        command: RobotCommandCreate,
        trace_id: str,
    ) -> dict[str, Any]:
        return {
            **get_robot_adapter().execute(
                robot_id=robot_id,
                action_type=command.action_type,
                payload=command.payload,
                priority=command.priority,
                trace_id=trace_id,
            ),
            "execution_location": "local",
            "gateway_url": None,
        }


class HttpRobotGatewayClient:
    def __init__(self, base_url: str, timeout: float = 5.0):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def status(self) -> dict[str, Any]:
        try:
            response = request_json("GET", f"{self.base_url}/robot-adapter/status", timeout=self.timeout)
        except RobotGatewayHttpError as exc:
            raise RobotAdapterUnavailable(
                {
                    "error": "robot_gateway_status_failed",
                    "gateway_url": self.base_url,
                    "status_code": exc.status_code,
                    "detail": normalize_gateway_detail(exc.detail),
                }
            ) from exc
        return {
            **response,
            "execution_location": "remote",
            "gateway_url": self.base_url,
        }

    def execute(
        self,
        robot_id: str,
        command: RobotCommandCreate,
        trace_id: str,
    ) -> dict[str, Any]:
        payload = command.model_dump()
        try:
            response = request_json(
                "POST",
                f"{self.base_url}/robots/{robot_id}/commands",
                payload=payload,
                timeout=self.timeout,
            )
        except RobotGatewayHttpError as exc:
            detail = normalize_gateway_detail(exc.detail)
            if exc.status_code == 422:
                raise RobotAdapterCommandError(detail) from exc
            raise RobotAdapterUnavailable(
                {
                    "error": "robot_gateway_command_failed",
                    "gateway_url": self.base_url,
                    "status_code": exc.status_code,
                    "detail": detail,
                }
            ) from exc

        return {
            **response,
            "trace_id": trace_id,
            "execution_location": "remote",
            "gateway_url": self.base_url,
        }


def request_json(
    method: str,
    url: str,
    payload: dict[str, Any] | None = None,
    timeout: float = 5.0,
) -> dict[str, Any]:
    data = None
    headers = {"Accept": "application/json"}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"

    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return parse_json_bytes(response.read())
    except urllib.error.HTTPError as exc:
        raise RobotGatewayHttpError(status_code=exc.code, detail=parse_json_bytes(exc.read())) from exc
    except Exception as exc:
        raise RobotGatewayHttpError(
            status_code=503,
            detail={"detail": {"error": "robot_gateway_unreachable", "message": str(exc)}},
        ) from exc


def parse_json_bytes(raw: bytes) -> dict[str, Any]:
    if not raw:
        return {}
    value = json.loads(raw.decode("utf-8"))
    return value if isinstance(value, dict) else {"value": value}


def normalize_gateway_detail(detail: dict[str, Any]) -> dict[str, Any]:
    nested = detail.get("detail")
    if isinstance(nested, dict):
        return nested
    return detail
