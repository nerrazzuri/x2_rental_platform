from datetime import date
from itertools import count
from typing import Any

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from .robot_adapters import RobotAdapterCommandError, RobotAdapterUnavailable, get_robot_adapter
from .templates import SCENARIO_TEMPLATES, build_steps, get_template

router = APIRouter()


class PlatformState:
    def __init__(self):
        self.counters = {
            "client": count(1),
            "event": count(1),
            "license": count(1),
            "asset": count(1),
            "script": count(1),
            "scenario": count(1),
            "run": count(1),
            "command": count(1),
            "log": count(1),
        }
        self.clients: dict[str, dict[str, Any]] = {}
        self.events: dict[str, dict[str, Any]] = {}
        self.licenses: dict[str, dict[str, Any]] = {}
        self.assets: dict[str, dict[str, Any]] = {}
        self.scripts: dict[str, dict[str, Any]] = {}
        self.scenarios: dict[str, dict[str, Any]] = {}
        self.runs: dict[str, dict[str, Any]] = {}
        self.commands: dict[str, dict[str, Any]] = {}
        self.logs: list[dict[str, Any]] = []
        self.robot_status: dict[str, dict[str, Any]] = {}
        self.safety_state: dict[str, str] = {}

    def next_id(self, prefix: str) -> str:
        return f"{prefix}_{next(self.counters[prefix]):04d}"


state = PlatformState()


class ClientCreate(BaseModel):
    name: str
    contact_name: str | None = None


class EventCreate(BaseModel):
    client_id: str
    name: str
    robot_id: str
    language: str = "en"


class LicenseCreate(BaseModel):
    event_id: str
    robot_id: str
    license_type: str
    start_date: date
    end_date: date


class AssetCreate(BaseModel):
    asset_type: str
    name: str
    uri: str
    mime_type: str | None = None


class ScriptCreate(BaseModel):
    name: str
    language: str = "en"
    content: str


class ScenarioPublish(BaseModel):
    template_id: str
    name: str
    config: dict[str, Any] = Field(default_factory=dict)


class RunCreate(BaseModel):
    event_id: str
    scenario_id: str
    robot_id: str


class RobotCommandCreate(BaseModel):
    action_type: str
    payload: dict[str, Any] = Field(default_factory=dict)
    priority: int = 5


class SafetyRobotRequest(BaseModel):
    robot_id: str


class RagProductIntroRequest(BaseModel):
    product_name: str
    language: str = "en"
    duration_seconds: int = 30
    materials: str


class FaqAnswerRequest(BaseModel):
    question: str
    fallback_answer: str = "The current material is not enough to answer accurately."


class MovementSimulationRequest(BaseModel):
    robot_id: str
    script: list[dict[str, Any]]


class VisualDockingSimulationRequest(BaseModel):
    robot_id: str
    marker_id: int
    stop_distance_m: float = 0.5


def add_log(event_id: str | None, log_type: str, message: str, data: dict[str, Any] | None = None):
    log = {
        "log_id": state.next_id("log"),
        "event_id": event_id,
        "type": log_type,
        "message": message,
        "data": data or {},
    }
    state.logs.append(log)
    return log


def license_status(event_id: str, robot_id: str | None = None):
    today = date.today()
    licenses = [
        license_record
        for license_record in state.licenses.values()
        if license_record["event_id"] == event_id and (robot_id is None or license_record["robot_id"] == robot_id)
    ]
    if not licenses:
        return {"event_id": event_id, "robot_id": robot_id, "status": "missing", "can_execute_robot_action": False}

    active = next(
        (
            license_record
            for license_record in licenses
            if license_record["start_date"] <= today <= license_record["end_date"]
        ),
        None,
    )
    license_record = active or licenses[-1]
    status_value = "active" if active else "inactive"
    return {
        **license_record,
        "status": status_value,
        "can_execute_robot_action": status_value == "active",
    }


def resolve_action_payload(action: dict[str, Any]):
    payload = dict(action.get("payload", {}))
    script_id = payload.get("script_id")
    if script_id:
        script = state.scripts.get(script_id)
        payload["text"] = script["content"] if script else ""
    asset_id = payload.get("asset_id")
    if asset_id:
        asset = state.assets.get(asset_id)
        if asset:
            payload["asset_uri"] = asset["uri"]
            payload["asset_mime_type"] = asset.get("mime_type")
    return payload


def get_robot_status(robot_id: str):
    return state.robot_status.setdefault(
        robot_id,
        {
            "robot_id": robot_id,
            "online": True,
            "battery_percent": 86,
            "is_stable": True,
            "pose_available": True,
            "network_ok": True,
            "current_action": None,
        },
    )


def execute_robot_command(robot_id: str, command: RobotCommandCreate, event_id: str | None = None):
    if state.safety_state.get(robot_id) == "emergency_stopped" and command.action_type == "locomotion":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="emergency_stop_active")

    command_id = state.next_id("command")
    adapter = get_robot_adapter()
    try:
        adapter_receipt = adapter.execute(
            robot_id=robot_id,
            action_type=command.action_type,
            payload=command.payload,
            priority=command.priority,
            trace_id=command_id,
        )
    except RobotAdapterUnavailable as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=exc.detail) from exc
    except RobotAdapterCommandError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=exc.detail) from exc

    receipt = {
        "command_id": command_id,
        "robot_id": robot_id,
        "action_type": command.action_type,
        "payload": command.payload,
        "priority": command.priority,
        "status": "completed",
        **adapter_receipt,
    }
    state.commands[command_id] = receipt
    get_robot_status(robot_id)["current_action"] = command.action_type
    add_log(event_id, "robot_command", f"Executed {command.action_type} via {adapter.mode}", receipt)
    return receipt


def execute_step(run: dict[str, Any]):
    scenario = state.scenarios[run["scenario_id"]]
    step = scenario["steps"][run["current_step_index"]]
    receipts = []
    for action in step["actions"]:
        command = RobotCommandCreate(
            action_type=action["action_type"],
            payload=resolve_action_payload(action),
            priority=action.get("priority", 5),
        )
        receipts.append(execute_robot_command(run["robot_id"], command, run["event_id"]))
    run["last_command_receipts"] = receipts
    return step


@router.post("/clients", status_code=status.HTTP_201_CREATED)
def create_client(payload: ClientCreate):
    client_id = state.next_id("client")
    record = {"client_id": client_id, **payload.model_dump()}
    state.clients[client_id] = record
    add_log(None, "client_created", f"Created client {payload.name}", record)
    return record


@router.get("/clients")
def list_clients():
    return list(state.clients.values())


@router.post("/events", status_code=status.HTTP_201_CREATED)
def create_event(payload: EventCreate):
    if payload.client_id not in state.clients:
        raise HTTPException(status_code=404, detail="client_not_found")
    event_id = state.next_id("event")
    record = {"event_id": event_id, **payload.model_dump()}
    state.events[event_id] = record
    add_log(event_id, "event_created", f"Created event {payload.name}", record)
    return record


@router.get("/events")
def list_events():
    return list(state.events.values())


@router.post("/events/{event_id}/copy", status_code=status.HTTP_201_CREATED)
def copy_event(event_id: str):
    source = state.events.get(event_id)
    if not source:
        raise HTTPException(status_code=404, detail="event_not_found")
    copied_id = state.next_id("event")
    record = {**source, "event_id": copied_id, "name": f"{source['name']} Copy"}
    state.events[copied_id] = record
    add_log(copied_id, "event_copied", f"Copied event {event_id}", {"source_event_id": event_id})
    return record


@router.post("/licenses", status_code=status.HTTP_201_CREATED)
def create_license(payload: LicenseCreate):
    if payload.event_id not in state.events:
        raise HTTPException(status_code=404, detail="event_not_found")
    license_id = state.next_id("license")
    record = {"license_id": license_id, **payload.model_dump()}
    state.licenses[license_id] = record
    response = license_status(payload.event_id, payload.robot_id)
    add_log(payload.event_id, "license_created", f"Created {payload.license_type} license", response)
    return response


@router.get("/licenses/{event_id}/status")
def get_license_status(event_id: str):
    return license_status(event_id)


@router.post("/events/{event_id}/assets", status_code=status.HTTP_201_CREATED)
def create_asset(event_id: str, payload: AssetCreate):
    if event_id not in state.events:
        raise HTTPException(status_code=404, detail="event_not_found")
    asset_id = state.next_id("asset")
    record = {"asset_id": asset_id, "event_id": event_id, **payload.model_dump()}
    state.assets[asset_id] = record
    add_log(event_id, "asset_created", f"Created asset {payload.name}", record)
    return record


@router.get("/events/{event_id}/assets")
def list_assets(event_id: str):
    return [asset for asset in state.assets.values() if asset["event_id"] == event_id]


@router.post("/events/{event_id}/scripts", status_code=status.HTTP_201_CREATED)
def create_script(event_id: str, payload: ScriptCreate):
    if event_id not in state.events:
        raise HTTPException(status_code=404, detail="event_not_found")
    script_id = state.next_id("script")
    record = {"script_id": script_id, "event_id": event_id, **payload.model_dump()}
    state.scripts[script_id] = record
    add_log(event_id, "script_created", f"Created script {payload.name}", record)
    return record


@router.get("/events/{event_id}/scripts")
def list_scripts(event_id: str):
    return [script for script in state.scripts.values() if script["event_id"] == event_id]


@router.get("/templates")
def list_templates():
    return SCENARIO_TEMPLATES


@router.get("/templates/{template_id}")
def get_template_route(template_id: str):
    template = get_template(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="template_not_found")
    return template


@router.post("/events/{event_id}/scenarios/publish", status_code=status.HTTP_201_CREATED)
def publish_scenario(event_id: str, payload: ScenarioPublish):
    if event_id not in state.events:
        raise HTTPException(status_code=404, detail="event_not_found")
    template = get_template(payload.template_id)
    if not template:
        raise HTTPException(status_code=404, detail="template_not_found")

    missing_fields = [
        field
        for field in template["required_scripts"] + template["required_assets"]
        if not payload.config.get(field)
    ]
    if missing_fields:
        raise HTTPException(status_code=422, detail={"missing_fields": missing_fields})

    scenario_id = state.next_id("scenario")
    record = {
        "scenario_id": scenario_id,
        "event_id": event_id,
        "template_id": payload.template_id,
        "name": payload.name,
        "config": payload.config,
        "steps": build_steps(payload.template_id, payload.config),
        "status": "published",
    }
    state.scenarios[scenario_id] = record
    add_log(event_id, "scenario_published", f"Published scenario {payload.name}", record)
    return record


@router.post("/runs", status_code=status.HTTP_201_CREATED)
def create_run(payload: RunCreate):
    if payload.event_id not in state.events:
        raise HTTPException(status_code=404, detail="event_not_found")
    if payload.scenario_id not in state.scenarios:
        raise HTTPException(status_code=404, detail="scenario_not_found")
    run_id = state.next_id("run")
    record = {
        "run_id": run_id,
        **payload.model_dump(),
        "status": "created",
        "current_step_index": 0,
        "current_step_id": None,
        "last_command_receipts": [],
    }
    state.runs[run_id] = record
    add_log(payload.event_id, "run_created", f"Created run {run_id}", record)
    return record


@router.get("/runs/{run_id}")
def get_run(run_id: str):
    run = state.runs.get(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="run_not_found")
    return run


@router.post("/runs/{run_id}/start")
def start_run(run_id: str):
    run = state.runs.get(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="run_not_found")
    if not license_status(run["event_id"], run["robot_id"])["can_execute_robot_action"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="license_inactive")

    run["status"] = "running"
    run["current_step_index"] = 0
    step = execute_step(run)
    run["current_step_id"] = step["step_id"]
    add_log(run["event_id"], "run_started", f"Started run {run_id}", {"step_id": step["step_id"]})
    return run


@router.post("/runs/{run_id}/next")
def next_step(run_id: str):
    run = state.runs.get(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="run_not_found")
    scenario = state.scenarios[run["scenario_id"]]
    run["current_step_index"] = min(run["current_step_index"] + 1, len(scenario["steps"]) - 1)
    step = execute_step(run)
    run["current_step_id"] = step["step_id"]
    add_log(run["event_id"], "run_next", f"Advanced run {run_id}", {"step_id": step["step_id"]})
    return run


@router.post("/runs/{run_id}/previous")
def previous_step(run_id: str):
    run = state.runs.get(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="run_not_found")
    run["current_step_index"] = max(run["current_step_index"] - 1, 0)
    step = execute_step(run)
    run["current_step_id"] = step["step_id"]
    add_log(run["event_id"], "run_previous", f"Moved run {run_id} back", {"step_id": step["step_id"]})
    return run


@router.post("/runs/{run_id}/replay")
def replay_step(run_id: str):
    run = state.runs.get(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="run_not_found")
    step = execute_step(run)
    run["current_step_id"] = step["step_id"]
    add_log(run["event_id"], "run_replay", f"Replayed run {run_id}", {"step_id": step["step_id"]})
    return run


@router.post("/runs/{run_id}/stop")
def stop_run(run_id: str):
    run = state.runs.get(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="run_not_found")
    run["status"] = "stopped"
    add_log(run["event_id"], "run_stopped", f"Stopped run {run_id}", {})
    return run


@router.get("/robots/{robot_id}/status")
def robot_status(robot_id: str):
    return get_robot_status(robot_id)


@router.post("/robots/{robot_id}/commands")
def robot_command(robot_id: str, payload: RobotCommandCreate):
    return execute_robot_command(robot_id, payload)


@router.get("/robot-adapter/status")
def robot_adapter_status():
    return get_robot_adapter().status()


@router.post("/safety/emergency-stop")
def emergency_stop(payload: SafetyRobotRequest):
    state.safety_state[payload.robot_id] = "emergency_stopped"
    get_robot_status(payload.robot_id)["current_action"] = "emergency_stop"
    add_log(None, "safety_emergency_stop", f"Emergency stop for {payload.robot_id}", payload.model_dump())
    return {"robot_id": payload.robot_id, "safety_state": "emergency_stopped"}


@router.post("/safety/reset")
def reset_safety(payload: SafetyRobotRequest):
    state.safety_state[payload.robot_id] = "ready"
    get_robot_status(payload.robot_id)["current_action"] = None
    add_log(None, "safety_reset", f"Safety reset for {payload.robot_id}", payload.model_dump())
    return {"robot_id": payload.robot_id, "safety_state": "ready"}


@router.post("/rag/product-intros")
def rag_product_intro(payload: RagProductIntroRequest):
    if not payload.materials.strip():
        raise HTTPException(status_code=422, detail="materials_required")
    draft = (
        f"{payload.product_name} is prepared for this event as a concise "
        f"{payload.duration_seconds}-second {payload.language} introduction. "
        f"{payload.materials.strip()}"
    )
    return {
        "product_name": payload.product_name,
        "language": payload.language,
        "duration_seconds": payload.duration_seconds,
        "draft": draft,
        "requires_human_review": True,
    }


@router.post("/faq/answer")
def faq_answer(payload: FaqAnswerRequest):
    return {"question": payload.question, "answer": payload.fallback_answer, "source": "curated_fallback"}


@router.post("/movement/scripts/simulate")
def simulate_movement(payload: MovementSimulationRequest):
    total_distance = sum(float(step.get("distance_m", 0)) for step in payload.script)
    return {
        "robot_id": payload.robot_id,
        "status": "completed",
        "total_distance_m": round(total_distance, 3),
        "safety_checked": True,
    }


@router.post("/visual-marker/docking/simulate")
def simulate_visual_docking(payload: VisualDockingSimulationRequest):
    return {
        "robot_id": payload.robot_id,
        "marker_id": payload.marker_id,
        "stop_distance_m": payload.stop_distance_m,
        "status": "docking_completed",
        "target_lost": False,
    }


@router.get("/events/{event_id}/logs")
def event_logs(event_id: str):
    return [log for log in state.logs if log["event_id"] in {event_id, None}]
