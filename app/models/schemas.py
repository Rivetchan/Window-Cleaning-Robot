"""
Data Models untuk Robot Pembersih Kaca
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum

class RobotMode(str, Enum):
    IDLE = "idle"
    MANUAL = "manual"
    AUTO = "auto"
    ERROR = "error"
    EMERGENCY = "emergency"

class Direction(str, Enum):
    UP = "up"
    DOWN = "down"
    LEFT = "left"
    RIGHT = "right"
    STOP = "stop"

class MoveCommand(BaseModel):
    direction: Direction
    speed: Optional[float] = Field(None, ge=0.05, le=0.25)

class SpeedCommand(BaseModel):
    speed: float = Field(..., ge=0.05, le=0.25)

class BrushCommand(BaseModel):
    action: str = Field(..., pattern="^(on|off)$")
    speed: Optional[int] = Field(None, ge=0, le=100)

class CleanCommand(BaseModel):
    mode: str = Field(..., pattern="^(auto|manual)$")
    duration: Optional[int] = Field(300, ge=60, le=3600)

class EmergencyCommand(BaseModel):
    action: str = Field(..., pattern="^(stop|reset)$")

class RobotPosition(BaseModel):
    col: int = Field(..., ge=1, le=70)
    row: int = Field(..., ge=1, le=90)
    floor: int = Field(..., ge=1, le=12)

class RobotStatus(BaseModel):
    status: str
    mode: str
    battery: float
    position: RobotPosition
    speed: float
    katrol_system: bool
    brush_system: bool
    brush_speed: int
    brush_running: bool
    water_tank: float
    clean_progress: float
    cleaned_cells: int
    total_cells: int
    uptime: str
    op_time: str
    emergency_stop: bool
    esp_katrol: bool
    esp_brush: bool
    moving: bool
    direction: Optional[str]
    last_update: str

class RobotLog(BaseModel):
    time: str
    level: str
    message: str

class RobotHealth(BaseModel):
    status: str
    timestamp: str
    uptime: str
    robot_status: str
    esp_connected: bool
