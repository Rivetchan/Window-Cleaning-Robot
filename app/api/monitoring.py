"""
Monitoring API - READ-ONLY
"""

from fastapi import APIRouter
from datetime import datetime
from app.core.robot_state import robot_state

router = APIRouter(prefix="/api/monitoring", tags=["Monitoring"])

@router.get("/status")
async def get_status():
    return robot_state.to_dict()

@router.get("/health")
async def health():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "uptime": robot_state._format_time(robot_state.uptime_sec),
        "robot_status": robot_state.status,
        "esp_connected": robot_state.esp_katrol_connected or robot_state.esp_brush_connected
    }

@router.get("/logs")
async def get_logs(limit: int = 20):
    logs = robot_state.logs[-limit:]
    return [{"time": t, "level": l, "message": m} for t, l, m in logs]

@router.get("/position")
async def get_position():
    return {
        "col": robot_state.position["col"],
        "row": robot_state.position["row"],
        "floor": robot_state.current_floor,
        "max_col": robot_state.max_col,
        "max_row": robot_state.max_row
    }

@router.get("/battery")
async def get_battery():
    return {
        "percentage": round(robot_state.battery, 1),
        "voltage": round(robot_state.voltage, 2),
        "status": "critical" if robot_state.battery < 20 else "normal"
    }

@router.get("/cleaning")
async def get_cleaning():
    return {
        "progress": round(robot_state.clean_progress, 1),
        "cleaned_cells": robot_state.cleaned_cells,
        "total_cells": robot_state.total_cells,
        "water_tank": round(robot_state.water_tank, 1),
        "auto_active": robot_state.auto_active,
        "auto_complete": robot_state.auto_complete
    }
