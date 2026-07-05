"""
Robot State - Shared state untuk robot
Full Version dengan Auto Mode Zig-Zag & Brush Status
"""

from datetime import datetime
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field

@dataclass
class RobotState:
    """State lengkap robot"""
    
    # System
    status: str = "idle"
    mode: str = "manual"
    speed: float = 0.15
    katrol_system: bool = True
    brush_system: bool = True
    emergency_stop: bool = False
    
    # Position
    position: Dict = field(default_factory=lambda: {"col": 70, "row": 1})
    max_col: int = 70
    max_row: int = 90
    current_floor: int = 1
    
    # Battery
    battery: float = 85.0
    voltage: float = 7.4
    
    # Katrol
    katrol_status: str = "Diam"
    katrol_direction: str = "-"
    katrol_load: float = 0.0
    
    # Roda
    roda_direction: str = "-"
    
    # Brush
    brush_speed: int = 50
    brush_running: bool = False
    brush_direction: str = "FWD"
    brush_limit_atas: bool = False
    brush_limit_bawah: bool = False
    brush_auto_mode: bool = False
    brush_cycle: int = 0
    
    # Water
    water_tank: float = 85.0
    water_pressure: float = 2.5
    water_usage: float = 0.0
    
    # Cleaning
    cleaned_cells: int = 0
    total_cells: int = 6300
    clean_progress: float = 0.0
    going_up: bool = True
    moving: bool = False
    direction: Optional[str] = None
    
    # Auto Mode Zig-Zag
    auto_active: bool = False
    auto_complete: bool = False
    auto_step: int = 0
    kolom: int = 70
    auto_progress: float = 0.0
    
    # ESP
    esp_katrol_connected: bool = False
    esp_brush_connected: bool = False
    
    # Time
    uptime_sec: float = 0.0
    op_time_sec: float = 0.0
    last_update: datetime = field(default_factory=datetime.now)
    
    # Logs
    logs: List[Tuple[str, str, str]] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return {
            "status": self.status,
            "mode": self.mode,
            "speed": self.speed,
            "katrol_system": self.katrol_system,
            "brush_system": self.brush_system,
            "emergency_stop": self.emergency_stop,
            "position": self.position,
            "max_position": {"col": self.max_col, "row": self.max_row},
            "current_floor": self.current_floor,
            "battery": round(self.battery, 1),
            "voltage": round(self.voltage, 2),
            "katrol_status": self.katrol_status,
            "katrol_direction": self.katrol_direction,
            "katrol_load": round(self.katrol_load, 2),
            "roda_direction": self.roda_direction,
            "brush_speed": self.brush_speed,
            "brush_running": self.brush_running,
            "brush_direction": self.brush_direction,
            "brush_limit_atas": self.brush_limit_atas,
            "brush_limit_bawah": self.brush_limit_bawah,
            "brush_auto_mode": self.brush_auto_mode,
            "brush_cycle": self.brush_cycle,
            "water_tank": round(self.water_tank, 1),
            "water_pressure": round(self.water_pressure, 1),
            "water_usage": round(self.water_usage, 1),
            "clean_progress": round(self.clean_progress, 1),
            "cleaned_cells": self.cleaned_cells,
            "total_cells": self.total_cells,
            "auto_active": self.auto_active,
            "auto_complete": self.auto_complete,
            "auto_step": self.auto_step,
            "kolom": self.kolom,
            "auto_progress": round(self.auto_progress, 1),
            "esp_katrol": self.esp_katrol_connected,
            "esp_brush": self.esp_brush_connected,
            "moving": self.moving,
            "direction": self.direction,
            "uptime": self._format_time(self.uptime_sec),
            "op_time": self._format_time(self.op_time_sec),
            "last_update": self.last_update.isoformat()
        }
    
    def _format_time(self, seconds: float) -> str:
        h = int(seconds) // 3600
        m = (int(seconds) % 3600) // 60
        s = int(seconds) % 60
        return f"{h:02d}:{m:02d}:{s:02d}"
    
    def add_log(self, level: str, msg: str):
        now = datetime.now().strftime("%H:%M:%S")
        self.logs.append((now, level, msg))
        if len(self.logs) > 100:
            self.logs.pop(0)
    
    def update_from_esp(self, data: dict):
        if 'katrol_direction' in data:
            self.katrol_direction = data.get('katrol_direction', '-')
        if 'roda_direction' in data:
            self.roda_direction = data.get('roda_direction', '-')
        if 'kolom' in data:
            self.kolom = data.get('kolom', 70)
            self.position['col'] = self.kolom
        if 'emergency' in data:
            self.emergency_stop = data.get('emergency', False)
        if 'auto_mode' in data:
            self.auto_active = data.get('auto_mode', False)
        if 'auto_step' in data:
            self.auto_step = data.get('auto_step', 0)
        if 'auto_complete' in data:
            self.auto_complete = data.get('auto_complete', False)
        if 'brush_running' in data:
            self.brush_running = data.get('brush_running', False)
        if 'brush_speed' in data:
            self.brush_speed = data.get('brush_speed', 50)
        if 'brush_direction' in data:
            self.brush_direction = data.get('brush_direction', 'FWD')
        if 'brush_limit_atas' in data:
            self.brush_limit_atas = data.get('brush_limit_atas', False)
        if 'brush_limit_bawah' in data:
            self.brush_limit_bawah = data.get('brush_limit_bawah', False)
        if 'brush_auto_mode' in data:
            self.brush_auto_mode = data.get('brush_auto_mode', False)
        if 'brush_cycle' in data:
            self.brush_cycle = data.get('brush_cycle', 0)
        
        self.esp_katrol_connected = True
        
        if self.kolom > 0:
            self.auto_progress = ((70 - self.kolom) / 69) * 100

robot_state = RobotState()
