from __future__ import annotations

import importlib
import importlib.util
import json
import os
from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import Any, Protocol


class RobotAdapterUnavailable(RuntimeError):
    def __init__(self, detail: dict[str, Any]):
        super().__init__(str(detail))
        self.detail = detail


class RobotAdapterCommandError(RuntimeError):
    def __init__(self, detail: dict[str, Any]):
        super().__init__(str(detail))
        self.detail = detail


class RobotAdapter(Protocol):
    mode: str
    transport: str

    def status(self) -> dict[str, Any]:
        ...

    def execute(
        self,
        robot_id: str,
        action_type: str,
        payload: dict[str, Any],
        priority: int,
        trace_id: str,
    ) -> dict[str, Any]:
        ...


@dataclass(frozen=True)
class ActionSpec:
    action_type: str
    aimdk_type: str
    transport: str
    aimdk_service: str | None = None
    aimdk_topic: str | None = None
    required_payload: tuple[str, ...] = ()
    notes: tuple[str, ...] = ()

    def public_dict(self) -> dict[str, Any]:
        return {
            "action_type": self.action_type,
            "aimdk_type": self.aimdk_type,
            "transport": self.transport,
            "aimdk_service": self.aimdk_service,
            "aimdk_topic": self.aimdk_topic,
            "required_payload": list(self.required_payload),
            "notes": list(self.notes),
        }


SUPPORTED_ACTIONS: dict[str, ActionSpec] = {
    "tts": ActionSpec(
        action_type="tts",
        aimdk_type="PlayTts",
        transport="service",
        aimdk_service="/aimdk_5Fmsgs/srv/PlayTts",
        required_payload=("text",),
        notes=("Maps platform priority to AimDK TtsPriorityLevel and priority_weight.",),
    ),
    "audio_file": ActionSpec(
        action_type="audio_file",
        aimdk_type="PlayAudioFile",
        transport="service",
        aimdk_service="/aimdk_5Fmsgs/srv/PlayAudioFile",
        required_payload=("file_path", "file_name"),
        notes=("AimDK requires PCM or WAV, 16 kHz, 16-bit, mono, stored on PC3.",),
    ),
    "screen_video": ActionSpec(
        action_type="screen_video",
        aimdk_type="PlayVideo",
        transport="service",
        aimdk_service="/face_ui_proxy/play_video",
        required_payload=("video_path",),
        notes=("AimDK requires an absolute readable path on the interaction compute unit.",),
    ),
    "emoji": ActionSpec(
        action_type="emoji",
        aimdk_type="PlayEmoji",
        transport="service",
        aimdk_service="/face_ui_proxy/play_emoji",
        required_payload=("emoji_id",),
    ),
    "motion": ActionSpec(
        action_type="motion",
        aimdk_type="SetMcPresetMotion",
        transport="service",
        aimdk_service="/aimdk_5Fmsgs/srv/SetMcPresetMotion",
        required_payload=("motion_id",),
        notes=("Robot must be switched to Stable Stand before preset motions.",),
    ),
    "linkcraft": ActionSpec(
        action_type="linkcraft",
        aimdk_type="ExecuteActionResource",
        transport="service",
        aimdk_service="/aimdk_5Fmsgs/srv/ExecuteActionResource",
        required_payload=("resource_key",),
    ),
    "led": ActionSpec(
        action_type="led",
        aimdk_type="SetPmuLed",
        transport="service",
        aimdk_service="/aimdk_5Fmsgs/srv/SetPmuLed",
        required_payload=("r", "g", "b"),
        notes=("AimDK LED calls can take about five seconds; keep them asynchronous in flows.",),
    ),
    "locomotion": ActionSpec(
        action_type="locomotion",
        aimdk_type="McLocomotionVelocity",
        transport="topic",
        aimdk_topic="/aima/mc/locomotion/velocity",
        required_payload=("forward_velocity", "lateral_velocity", "angular_velocity"),
        notes=("Registers a custom MC input source before publishing velocity commands.",),
    ),
}

ACTION_ALIASES = {
    "audio": "audio_file",
    "video": "screen_video",
}

MOTION_PRESETS: dict[str, tuple[int, int]] = {
    "wave": (1002, 2),
    "right_hand_wave": (1002, 2),
    "left_hand_wave": (1002, 1),
    "right_hand_handshake": (1003, 2),
    "left_hand_handshake": (1003, 1),
    "right_hand_raise": (1001, 2),
    "left_hand_raise": (1001, 1),
    "clap": (3017, 11),
    "heart_both_hands": (1007, 3),
    "right_hand_heart": (1007, 2),
    "left_hand_heart": (1007, 1),
    "hug": (3008, 11),
    "cheer": (3011, 11),
    "raise_both_hands": (1010, 3),
    "wave_goodbye": (3031, 11),
    "bow": (3001, 11),
}

LED_MODES = {
    "steady": 0,
    "breathing": 1,
    "blinking": 2,
    "flowing": 3,
}


def get_action_spec(action_type: str) -> ActionSpec | None:
    return SUPPORTED_ACTIONS.get(ACTION_ALIASES.get(action_type, action_type))


def supported_actions_for_status() -> dict[str, dict[str, Any]]:
    return {key: spec.public_dict() for key, spec in SUPPORTED_ACTIONS.items()}


def build_target(action_type: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    spec = get_action_spec(action_type)
    if not spec:
        return {
            "action_type": action_type,
            "resolved_action_type": action_type,
            "unsupported": True,
            "aimdk_service": None,
            "aimdk_topic": None,
        }

    target = spec.public_dict()
    target["resolved_action_type"] = spec.action_type
    if spec.action_type == "motion":
        target["preset_motion"] = resolve_motion_preset((payload or {}).get("motion_id", "wave"))
    if spec.action_type == "locomotion":
        target["input_source"] = aimdk_input_source_name()
    return target


def resolve_motion_preset(motion_id: Any) -> dict[str, int | str]:
    if isinstance(motion_id, str) and motion_id in MOTION_PRESETS:
        motion, area = MOTION_PRESETS[motion_id]
        return {"motion_id": motion_id, "motion": motion, "area": area}
    return {
        "motion_id": str(motion_id),
        "motion": int(motion_id) if str(motion_id).isdigit() else MOTION_PRESETS["wave"][0],
        "area": MOTION_PRESETS["wave"][1],
    }


def adapter_mode_from_env() -> str:
    return os.getenv("X2_ROBOT_ADAPTER", "mock").strip().lower() or "mock"


def aimdk_missing_dependencies() -> list[str]:
    missing = []
    for module_name in ("rclpy", "aimdk_msgs"):
        if importlib.util.find_spec(module_name) is None:
            missing.append(module_name)
    return missing


def aimdk_input_source_name() -> str:
    return os.getenv("X2_AIMDK_INPUT_SOURCE", "x2_rental_platform")


def aimdk_service_timeout() -> float:
    return float(os.getenv("X2_AIMDK_SERVICE_TIMEOUT_SECONDS", "5.0"))


def get_robot_adapter() -> RobotAdapter:
    mode = adapter_mode_from_env()
    if mode == "aimdk":
        return X2AimdkRos2Adapter()
    return MockRobotAdapter()


class MockRobotAdapter:
    mode = "mock"
    transport = "simulated"

    def status(self) -> dict[str, Any]:
        return {
            "mode": self.mode,
            "available": True,
            "transport": self.transport,
            "supported_actions": supported_actions_for_status(),
        }

    def execute(
        self,
        robot_id: str,
        action_type: str,
        payload: dict[str, Any],
        priority: int,
        trace_id: str,
    ) -> dict[str, Any]:
        return {
            "adapter": self.mode,
            "transport": self.transport,
            "status": "completed",
            "target": build_target(action_type, payload),
            "trace_id": trace_id,
            "adapter_receipt": {
                "robot_id": robot_id,
                "simulated": True,
                "priority": priority,
            },
        }


class X2AimdkRos2Adapter:
    mode = "aimdk"
    transport = "ros2"

    def __init__(self):
        self._node = None
        self._rclpy = None
        self._publishers: dict[str, Any] = {}
        self._input_source_registered = False
        self.service_timeout_sec = aimdk_service_timeout()

    def status(self) -> dict[str, Any]:
        missing = aimdk_missing_dependencies()
        return {
            "mode": self.mode,
            "available": not missing,
            "transport": self.transport,
            "missing_dependencies": missing,
            "supported_actions": supported_actions_for_status(),
            "input_source": aimdk_input_source_name(),
            "service_timeout_seconds": self.service_timeout_sec,
        }

    def execute(
        self,
        robot_id: str,
        action_type: str,
        payload: dict[str, Any],
        priority: int,
        trace_id: str,
    ) -> dict[str, Any]:
        missing = aimdk_missing_dependencies()
        if missing:
            raise RobotAdapterUnavailable(
                {
                    "error": "aimdk_runtime_unavailable",
                    "adapter": self.mode,
                    "missing_dependencies": missing,
                    "message": "Run this adapter inside the X2 AimDK ROS 2 workspace.",
                }
            )

        spec = get_action_spec(action_type)
        if not spec:
            raise RobotAdapterCommandError(
                {"error": "unsupported_robot_action", "action_type": action_type, "adapter": self.mode}
            )

        if spec.transport == "topic":
            return self._publish_locomotion(robot_id, spec, payload, priority, trace_id)
        return self._call_action_service(robot_id, spec, payload, priority, trace_id)

    def _get_rclpy(self):
        if self._rclpy is None:
            self._rclpy = importlib.import_module("rclpy")
        return self._rclpy

    def _get_node(self):
        if self._node is not None:
            return self._node

        rclpy = self._get_rclpy()
        if not rclpy.ok():
            rclpy.init(args=None)
        node_module = importlib.import_module("rclpy.node")
        self._node = node_module.Node("x2_rental_platform_adapter")
        return self._node

    def _load_aimdk_type(self, namespace: str, type_name: str):
        module = importlib.import_module(f"aimdk_msgs.{namespace}")
        return getattr(module, type_name)

    def _call_action_service(
        self,
        robot_id: str,
        spec: ActionSpec,
        payload: dict[str, Any],
        priority: int,
        trace_id: str,
    ) -> dict[str, Any]:
        service_type = self._load_aimdk_type("srv", spec.aimdk_type)
        request = service_type.Request()
        SERVICE_BUILDERS[spec.action_type](request, payload, priority, trace_id)
        result = self._call_service(spec.aimdk_service or "", service_type, request)
        return {
            "adapter": self.mode,
            "transport": self.transport,
            "status": result["status"],
            "target": build_target(spec.action_type, payload),
            "trace_id": trace_id,
            "adapter_receipt": {
                "robot_id": robot_id,
                "service": spec.aimdk_service,
                "response": result["response"],
            },
        }

    def _call_service(self, service_name: str, service_type: Any, request: Any) -> dict[str, Any]:
        rclpy = self._get_rclpy()
        node = self._get_node()
        client = node.create_client(service_type, service_name)
        if not client.wait_for_service(timeout_sec=self.service_timeout_sec):
            raise RobotAdapterUnavailable(
                {
                    "error": "aimdk_service_unavailable",
                    "service": service_name,
                    "timeout_seconds": self.service_timeout_sec,
                }
            )

        stamp_ros_request(request, node)
        future = client.call_async(request)
        rclpy.spin_until_future_complete(node, future, timeout_sec=self.service_timeout_sec)
        if not future.done():
            raise RobotAdapterUnavailable(
                {
                    "error": "aimdk_service_timeout",
                    "service": service_name,
                    "timeout_seconds": self.service_timeout_sec,
                }
            )

        if future.exception():
            raise RobotAdapterUnavailable(
                {
                    "error": "aimdk_service_call_failed",
                    "service": service_name,
                    "message": str(future.exception()),
                }
            )

        response = future.result()
        if response is None:
            return {"status": "failed", "response": {"error": "empty_response"}}
        return {
            "status": "completed" if response_succeeded(response) else "failed",
            "response": summarize_ros_object(response),
        }

    def _publish_locomotion(
        self,
        robot_id: str,
        spec: ActionSpec,
        payload: dict[str, Any],
        priority: int,
        trace_id: str,
    ) -> dict[str, Any]:
        self._ensure_input_source_registered()
        rclpy = self._get_rclpy()
        node = self._get_node()
        message_type = self._load_aimdk_type("msg", spec.aimdk_type)
        publisher = self._publishers.get(spec.aimdk_topic or "")
        if publisher is None:
            publisher = node.create_publisher(message_type, spec.aimdk_topic, 10)
            self._publishers[spec.aimdk_topic or ""] = publisher

        message = message_type()
        build_locomotion_message(message, payload)
        stamp_ros_request(message, node)
        publisher.publish(message)
        rclpy.spin_once(node, timeout_sec=0.01)
        return {
            "adapter": self.mode,
            "transport": self.transport,
            "status": "completed",
            "target": build_target(spec.action_type, payload),
            "trace_id": trace_id,
            "adapter_receipt": {
                "robot_id": robot_id,
                "topic": spec.aimdk_topic,
                "input_source": aimdk_input_source_name(),
                "priority": priority,
            },
        }

    def _ensure_input_source_registered(self):
        if self._input_source_registered:
            return
        if os.getenv("X2_AIMDK_AUTO_REGISTER_INPUT_SOURCE", "true").lower() not in {"true", "1", "yes"}:
            return

        service_type = self._load_aimdk_type("srv", "SetMcInputSource")
        add_request = service_type.Request()
        build_input_source_request(add_request, action_value=1001)
        add_result = self._call_service("/aimdk_5Fmsgs/srv/SetMcInputSource", service_type, add_request)
        if add_result["status"] != "completed":
            modify_request = service_type.Request()
            build_input_source_request(modify_request, action_value=1002)
            modify_result = self._call_service("/aimdk_5Fmsgs/srv/SetMcInputSource", service_type, modify_request)
            if modify_result["status"] != "completed":
                raise RobotAdapterCommandError(
                    {
                        "error": "aimdk_input_source_registration_failed",
                        "add_response": add_result["response"],
                        "modify_response": modify_result["response"],
                    }
                )
        self._input_source_registered = True


def set_nested_attr(target: Any, path: str, value: Any) -> bool:
    current = target
    parts = path.split(".")
    for part in parts[:-1]:
        if not hasattr(current, part):
            return False
        current = getattr(current, part)
    if not hasattr(current, parts[-1]):
        return False
    setattr(current, parts[-1], value)
    return True


def stamp_ros_request(target: Any, node: Any) -> bool:
    stamp = node.get_clock().now().to_msg()
    for path in ("header.header.stamp", "request.header.stamp", "header.stamp"):
        if set_nested_attr(target, path, stamp):
            return True
    return False


def tts_priority_level(priority: int) -> int:
    if priority >= 10:
        return 10
    if priority >= 8:
        return 8
    if priority >= 7:
        return 7
    if priority >= 6:
        return 6
    if priority >= 4:
        return 4
    if priority >= 2:
        return 2
    return 1


def build_tts_request(request: Any, payload: dict[str, Any], priority: int, trace_id: str):
    text = payload.get("text") or payload.get("content")
    if not text:
        raise RobotAdapterCommandError({"error": "tts_text_required"})
    set_nested_attr(request, "tts_req.text", str(text))
    set_nested_attr(request, "tts_req.priority_level.value", tts_priority_level(priority))
    set_nested_attr(request, "tts_req.priority_weight", int(payload.get("priority_weight", 0)))
    set_nested_attr(request, "tts_req.domain", payload.get("domain", "x2_rental_platform"))
    set_nested_attr(request, "tts_req.trace_id", trace_id)
    set_nested_attr(request, "tts_req.is_interrupted", bool(payload.get("interrupt", True)))


def build_audio_file_request(request: Any, payload: dict[str, Any], priority: int, trace_id: str):
    file_path, file_name = resolve_audio_file_parts(payload)
    set_nested_attr(request, "file.pkg_name", payload.get("pkg_name", "x2_rental_platform"))
    set_nested_attr(request, "file.file_path", file_path)
    set_nested_attr(request, "file.file_name", file_name)
    set_nested_attr(request, "file.priority", int(payload.get("audio_priority", priority)))
    set_nested_attr(request, "file.priority_weight", int(payload.get("priority_weight", 0)))


def build_video_request(request: Any, payload: dict[str, Any], priority: int, trace_id: str):
    video_path = payload.get("video_path") or payload.get("absolute_path") or payload.get("asset_uri") or payload.get("uri")
    if not video_path or not str(video_path).startswith("/"):
        raise RobotAdapterCommandError(
            {
                "error": "video_absolute_path_required",
                "message": "AimDK PlayVideo requires an absolute readable path on PC3.",
            }
        )
    set_nested_attr(request, "video_path", str(video_path))
    set_nested_attr(request, "mode", int(payload.get("mode", 1)))
    set_nested_attr(request, "priority", int(priority))


def build_emoji_request(request: Any, payload: dict[str, Any], priority: int, trace_id: str):
    emoji_id = payload.get("emoji_id", payload.get("emotion_id", 90))
    set_nested_attr(request, "emotion_id", int(emoji_id))
    set_nested_attr(request, "mode", int(payload.get("mode", 1)))
    set_nested_attr(request, "priority", int(priority))


def build_motion_request(request: Any, payload: dict[str, Any], priority: int, trace_id: str):
    preset = resolve_motion_preset(payload.get("motion_id", "wave"))
    set_nested_attr(request, "motion.value", int(payload.get("motion", preset["motion"])))
    set_nested_attr(request, "area.value", int(payload.get("area", preset["area"])))
    set_nested_attr(request, "interrupt", bool(payload.get("interrupt", True)))
    set_nested_attr(request, "ani_path", str(payload.get("ani_path", "")))
    set_nested_attr(request, "play_timestamp", int(payload.get("play_timestamp", 0)))


def build_led_request(request: Any, payload: dict[str, Any], priority: int, trace_id: str):
    color = payload.get("color") or {}
    mode = payload.get("led_strip_mode", payload.get("mode", "steady"))
    if isinstance(mode, str):
        mode = LED_MODES.get(mode, 0)
    set_nested_attr(request, "trace_id", trace_id)
    set_nested_attr(request, "led_strip_mode", int(mode))
    set_nested_attr(request, "r", int(payload.get("r", color.get("r", 0))))
    set_nested_attr(request, "g", int(payload.get("g", color.get("g", 0))))
    set_nested_attr(request, "b", int(payload.get("b", color.get("b", 0))))
    set_nested_attr(request, "priority", int(priority))
    set_nested_attr(request, "reset_priority", bool(payload.get("reset_priority", False)))


def build_linkcraft_request(request: Any, payload: dict[str, Any], priority: int, trace_id: str):
    resource_key = payload.get("resource_key")
    if not resource_key:
        raise RobotAdapterCommandError({"error": "linkcraft_resource_key_required"})
    set_nested_attr(request, "resource_key", str(resource_key))
    set_nested_attr(request, "resource_version", str(payload.get("resource_version", payload.get("version", ""))))
    meta = payload.get("meta")
    if isinstance(meta, dict):
        meta = json.dumps(meta)
    if not meta:
        resource_type = "BODY_MONTION" if "onnx" in str(resource_key).lower() else "ARM_MONTION"
        meta = json.dumps({"resource_type": resource_type})
    set_nested_attr(request, "meta", meta)


def build_locomotion_message(message: Any, payload: dict[str, Any]):
    set_nested_attr(message, "source", aimdk_input_source_name())
    set_nested_attr(message, "forward_velocity", float(payload.get("forward_velocity", payload.get("forward", 0.0))))
    set_nested_attr(message, "lateral_velocity", float(payload.get("lateral_velocity", payload.get("lateral", 0.0))))
    set_nested_attr(message, "angular_velocity", float(payload.get("angular_velocity", payload.get("angular", 0.0))))


def build_input_source_request(request: Any, action_value: int):
    set_nested_attr(request, "action.value", action_value)
    set_nested_attr(request, "input_source.name", aimdk_input_source_name())
    set_nested_attr(request, "input_source.priority", int(os.getenv("X2_AIMDK_INPUT_SOURCE_PRIORITY", "40")))
    set_nested_attr(request, "input_source.timeout", int(os.getenv("X2_AIMDK_INPUT_SOURCE_TIMEOUT_MS", "1000")))


SERVICE_BUILDERS = {
    "tts": build_tts_request,
    "audio_file": build_audio_file_request,
    "screen_video": build_video_request,
    "emoji": build_emoji_request,
    "motion": build_motion_request,
    "led": build_led_request,
    "linkcraft": build_linkcraft_request,
}


def resolve_audio_file_parts(payload: dict[str, Any]) -> tuple[str, str]:
    file_path = payload.get("file_path")
    file_name = payload.get("file_name")
    absolute_path = payload.get("absolute_path") or payload.get("audio_path") or payload.get("asset_uri") or payload.get("uri")
    if absolute_path and str(absolute_path).startswith("local://"):
        raise RobotAdapterCommandError(
            {
                "error": "audio_robot_path_required",
                "message": "AimDK audio files must be copied to PC3 and referenced by an absolute path.",
            }
        )
    if absolute_path and not file_name:
        posix_path = PurePosixPath(str(absolute_path))
        file_path = str(posix_path.parent)
        file_name = posix_path.name
    if not file_path or not file_name:
        raise RobotAdapterCommandError({"error": "audio_file_path_and_name_required"})
    file_path = str(file_path)
    if file_path != "/" and not file_path.endswith("/"):
        file_path = f"{file_path}/"
    return file_path, str(file_name)


def response_succeeded(response: Any) -> bool:
    if response is None:
        return False

    for path in ("success", "tts_resp.is_success"):
        value = nested_attr(response, path)
        if isinstance(value, bool):
            return value

    status_code = nested_attr(response, "status_code")
    if status_code is not None:
        return int(status_code) == 0

    common_status = nested_attr(response, "header.status.value")
    if common_status is not None:
        return int(common_status) == 1

    typo_common_status = nested_attr(response, "reponse.status.value")
    if typo_common_status is not None:
        return int(typo_common_status) == 1

    task_code = nested_attr(response, "response.header.code")
    task_state = nested_attr(response, "response.state.value")
    if task_code is not None and int(task_code) == 0:
        return True
    if task_state is not None and int(task_state) == 400:
        return True
    if task_code is not None:
        return False

    header_code = nested_attr(response, "header.code")
    if header_code is not None:
        return int(header_code) == 0

    return False


def nested_attr(target: Any, path: str) -> Any:
    current = target
    for part in path.split("."):
        if not hasattr(current, part):
            return None
        current = getattr(current, part)
    return current


def summarize_ros_object(response: Any) -> dict[str, Any]:
    summary: dict[str, Any] = {}
    for path in (
        "success",
        "message",
        "status_code",
        "header.code",
        "header.status.value",
        "header.message",
        "response.header.code",
        "response.state.value",
        "response.task_id",
        "reponse.status.value",
        "reponse.message",
        "tts_resp.is_success",
        "tts_resp.error_message",
        "tts_resp.estimated_duration",
    ):
        value = nested_attr(response, path)
        if value is not None:
            summary[path.replace(".", "_")] = value
    return summary
