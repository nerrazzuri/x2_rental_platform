from fastapi import APIRouter, HTTPException, status

from .robot_adapters import RobotAdapterCommandError, RobotAdapterUnavailable, get_robot_adapter
from .robot_models import RobotCommandCreate

router = APIRouter()


@router.get("/robot-adapter/status")
def robot_adapter_status():
    return {
        **get_robot_adapter().status(),
        "execution_location": "pc2",
        "gateway_url": None,
    }


@router.post("/robots/{robot_id}/commands")
def robot_command(robot_id: str, payload: RobotCommandCreate):
    try:
        adapter_receipt = get_robot_adapter().execute(
            robot_id=robot_id,
            action_type=payload.action_type,
            payload=payload.payload,
            priority=payload.priority,
            trace_id=f"pc2-{robot_id}",
        )
    except RobotAdapterUnavailable as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=exc.detail) from exc
    except RobotAdapterCommandError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=exc.detail) from exc

    return {
        "robot_id": robot_id,
        "action_type": payload.action_type,
        "payload": payload.payload,
        "priority": payload.priority,
        "status": "completed",
        **adapter_receipt,
        "execution_location": "pc2",
        "gateway_url": None,
    }
