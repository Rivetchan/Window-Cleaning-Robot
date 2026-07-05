"""
Control API - WRITE
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from datetime import datetime
from typing import Optional

from app.core.robot_controller import robot_controller
from app.core.robot_state import robot_state

router = APIRouter(prefix="/api/control", tags=["Control"])

class MoveCommand(BaseModel):
    direction: str

class SpeedCommand(BaseModel):
    speed: float

class BrushCommand(BaseModel):
    action: str
    speed: Optional[int] = None

class KatrolCommand(BaseModel):
    command: str
    params: Optional[dict] = None

@router.post("/mode/manual")
async def set_manual():
    robot_controller.set_mode_manual()
    return {"success": True, "mode": "manual"}

@router.post("/mode/auto")
async def set_auto():
    robot_controller.set_mode_auto()
    return {"success": True, "mode": "auto"}

@router.post("/move")
async def move(command: MoveCommand):
    if command.direction not in ["up", "down", "left", "right", "stop"]:
        raise HTTPException(400, "Invalid direction")
    robot_controller.move(command.direction)
    return {"success": True, "direction": command.direction}

@router.post("/stop")
async def stop():
    robot_controller.stop()
    return {"success": True}

@router.post("/reset")
async def reset():
    robot_controller.reset()
    return {"success": True}

@router.post("/speed")
async def set_speed(command: SpeedCommand):
    if command.speed < 0.05 or command.speed > 0.25:
        raise HTTPException(400, "Speed must be between 0.05 and 0.25")
    robot_controller.set_speed(command.speed)
    return {"success": True, "speed": command.speed}

@router.post("/brush")
async def brush(command: BrushCommand):
    if command.action == "on":
        if command.speed:
            robot_controller.set_brush_speed(command.speed)
        robot_controller.brush_on()
    else:
        robot_controller.brush_off()
    return {"success": True, "action": command.action}

@router.post("/system/katrol/toggle")
async def toggle_katrol():
    robot_controller.toggle_katrol_system()
    return {"success": True, "katrol_system": robot_state.katrol_system}

@router.post("/system/brush/toggle")
async def toggle_brush():
    robot_controller.toggle_brush_system()
    return {"success": True, "brush_system": robot_state.brush_system}

@router.post("/emergency/stop")
async def emergency_stop():
    robot_controller.emergency_stop()
    return {"success": True, "emergency": True}

@router.post("/emergency/reset")
async def emergency_reset():
    robot_controller.emergency_reset()
    return {"success": True, "emergency": False}

@router.post("/katrol/command")
async def send_katrol_command(command: KatrolCommand):
    from app.mqtt.hivemq_client import get_mqtt_client
    client = get_mqtt_client()
    if not client.is_connected():
        raise HTTPException(status_code=503, detail="MQTT not connected")
    
    success = client.send_command(command.command, command.params)
    if success:
        return {
            "success": True,
            "command": command.command,
            "params": command.params,
            "timestamp": datetime.now().isoformat()
        }
    raise HTTPException(status_code=500, detail="Failed to send command")
