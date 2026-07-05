"""
Robot Controller - Logic kontrol robot + Kirim perintah ke ESP via MQTT
"""

import asyncio
from datetime import datetime
from app.core.robot_state import robot_state
from app.mqtt.hivemq_client import get_mqtt_client

class RobotController:
    def __init__(self):
        self._task = None
        self._running = False
        self.mqtt = None
    
    def start(self):
        self._running = True
        self.mqtt = get_mqtt_client()
        self._task = asyncio.create_task(self._update_loop())
        robot_state.add_log("INFO", "🚀 Robot Controller Started")
    
    def stop(self):
        self._running = False
        if self._task:
            self._task.cancel()
        robot_state.add_log("INFO", "🛑 Robot Controller Stopped")
    
    async def _update_loop(self):
        while self._running:
            robot_state.uptime_sec += 0.5
            if robot_state.moving:
                robot_state.op_time_sec += 0.5
            await asyncio.sleep(0.5)
    
    def _send_to_esp(self, command, params=None):
        if self.mqtt and self.mqtt.is_connected():
            return self.mqtt.send_command(command, params)
        else:
            robot_state.add_log("WARN", "⚠️ MQTT not connected")
            return False
    
    def set_mode_manual(self):
        robot_state.mode = "manual"
        robot_state.auto_active = False
        robot_state.status = "idle"
        robot_state.add_log("INFO", "🎮 Mode: MANUAL")
        self._send_to_esp("AUTO_STOP")
    
    def set_mode_auto(self):
        if robot_state.auto_complete:
            self.reset()
        robot_state.mode = "auto"
        robot_state.auto_active = True
        robot_state.moving = True
        robot_state.status = "cleaning"
        robot_state.add_log("INFO", "🤖 Mode: AUTO")
        self._send_to_esp("AUTO_START")
    
    def move(self, direction: str):
        if direction == "stop":
            self.stop()
            return
        
        robot_state.mode = "manual"
        robot_state.auto_active = False
        robot_state.moving = True
        robot_state.direction = direction
        robot_state.status = "moving"
        
        if direction == "up":
            self._send_to_esp("KATROL", {"direction": "UP", "speed": robot_state.speed})
            robot_state.katrol_status = "Naik"
            robot_state.katrol_direction = "▲"
        elif direction == "down":
            self._send_to_esp("KATROL", {"direction": "DOWN", "speed": robot_state.speed})
            robot_state.katrol_status = "Turun"
            robot_state.katrol_direction = "▼"
        elif direction == "left":
            self._send_to_esp("RODA", {"direction": "LEFT", "speed": 0.12})
            robot_state.roda_direction = "⬅"
        elif direction == "right":
            self._send_to_esp("RODA", {"direction": "RIGHT", "speed": 0.12})
            robot_state.roda_direction = "➡"
        
        robot_state.add_log("INFO", f"🎮 Move: {direction}")
    
    def stop(self):
        robot_state.moving = False
        robot_state.direction = None
        robot_state.status = "idle"
        robot_state.katrol_status = "Diam"
        robot_state.katrol_direction = "-"
        robot_state.roda_direction = "-"
        self._send_to_esp("STOP_ALL")
        robot_state.add_log("INFO", "🛑 Robot STOP")
    
    def reset(self):
        robot_state.position = {"col": 70, "row": 1}
        robot_state.cleaned_cells = 0
        robot_state.clean_progress = 0.0
        robot_state.auto_active = False
        robot_state.auto_complete = False
        robot_state.moving = False
        robot_state.going_up = True
        robot_state.status = "idle"
        robot_state.op_time_sec = 0.0
        robot_state.water_tank = 85.0
        robot_state.katrol_status = "Diam"
        robot_state.katrol_direction = "-"
        robot_state.roda_direction = "-"
        self._send_to_esp("STOP_ALL")
        robot_state.add_log("INFO", "🔄 Reset")
    
    def brush_on(self):
        robot_state.brush_running = True
        self._send_to_esp("BRUSH_STATUS", {"running": True, "speed": robot_state.brush_speed})
        robot_state.add_log("INFO", f"🖌️ Brush ON (Speed: {robot_state.brush_speed}%)")
    
    def brush_off(self):
        robot_state.brush_running = False
        self._send_to_esp("BRUSH_STATUS", {"running": False, "speed": 0})
        robot_state.add_log("INFO", "🖌️ Brush OFF")
    
    def set_brush_speed(self, speed: int):
        robot_state.brush_speed = speed
        if robot_state.brush_running:
            self._send_to_esp("BRUSH_STATUS", {"running": True, "speed": speed})
        robot_state.add_log("INFO", f"🖌️ Brush Speed: {speed}%")
    
    def set_speed(self, speed: float):
        robot_state.speed = speed
        robot_state.add_log("INFO", f"⚡ Speed: {speed} m/s")
    
    def toggle_katrol_system(self):
        robot_state.katrol_system = not robot_state.katrol_system
        status = "ON" if robot_state.katrol_system else "OFF"
        if robot_state.katrol_system:
            self._send_to_esp("KATROL_SYSTEM_ON")
        else:
            self._send_to_esp("KATROL_SYSTEM_OFF")
        robot_state.add_log("INFO", f"🔘 Katrol System: {status}")
    
    def toggle_brush_system(self):
        robot_state.brush_system = not robot_state.brush_system
        status = "ON" if robot_state.brush_system else "OFF"
        robot_state.add_log("INFO", f"🖌️ Brush System: {status}")
    
    def emergency_stop(self):
        robot_state.emergency_stop = True
        robot_state.moving = False
        robot_state.auto_active = False
        robot_state.status = "emergency"
        self._send_to_esp("EMERGENCY_STOP")
        robot_state.add_log("ERROR", "⚠️ EMERGENCY STOP ACTIVATED!")
    
    def emergency_reset(self):
        robot_state.emergency_stop = False
        robot_state.status = "idle"
        self._send_to_esp("EMERGENCY_RESET")
        robot_state.add_log("INFO", "🔄 Emergency Reset")
    
    def update_from_esp(self, data: dict):
        if 'katrol_direction' in data:
            robot_state.katrol_direction = data.get('katrol_direction', '-')
        if 'roda_direction' in data:
            robot_state.roda_direction = data.get('roda_direction', '-')
        if 'kolom' in data:
            robot_state.position['col'] = data.get('kolom', 70)
        if 'emergency' in data:
            robot_state.emergency_stop = data.get('emergency', False)
        if 'auto_mode' in data:
            robot_state.auto_active = data.get('auto_mode', False)
        if 'brush_running' in data:
            robot_state.brush_running = data.get('brush_running', False)
        
        robot_state.esp_katrol_connected = True
        robot_state.add_log("INFO", "📡 ESP Status updated")

robot_controller = RobotController()
