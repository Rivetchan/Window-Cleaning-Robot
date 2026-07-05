"""
Robot Pembersih Kaca - Backend API
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from datetime import datetime
import socket
import logging
import os
from dotenv import load_dotenv

load_dotenv()

from app.core.robot_state import robot_state
from app.core.robot_controller import robot_controller
from app.api import monitoring, control, mqtt
from app.mqtt.hivemq_client import get_mqtt_client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================
# MQTT CALLBACK
# ============================================

def on_mqtt_status(data: dict):
    logger.info("📡 MQTT Status received from ESP")
    try:
        robot_controller.update_from_esp(data)
        
        if 'katrol_direction' in data:
            robot_state.katrol_direction = data.get('katrol_direction', '-')
        if 'roda_direction' in data:
            robot_state.roda_direction = data.get('roda_direction', '-')
        if 'kolom' in data:
            robot_state.position['col'] = data.get('kolom', 10)
        if 'emergency' in data:
            robot_state.emergency_stop = data.get('emergency', False)
        if 'auto_mode' in data:
            robot_state.auto_active = data.get('auto_mode', False)
        if 'brush_running' in data:
            robot_state.brush_running = data.get('brush_running', False)
        
        robot_state.esp_katrol_connected = True
        
    except Exception as e:
        logger.error(f"❌ Error processing MQTT data: {e}")

# ============================================
# LIFESPAN
# ============================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 Robot Backend Starting...")
    robot_state.add_log("INFO", "🏢 SISTEM ROBOT DINYALAKAN")
    robot_controller.start()
    
    try:
        mqtt_client = get_mqtt_client()
        mqtt_client.start(on_status_callback=on_mqtt_status)
        logger.info("📡 MQTT Client started")
    except Exception as e:
        logger.error(f"❌ MQTT failed: {e}")
    
    yield
    
    robot_controller.stop()
    try:
        get_mqtt_client().stop()
    except:
        pass
    logger.info("🛑 Robot Backend Stopped")

# ============================================
# FASTAPI APP
# ============================================

app = FastAPI(
    title="Robot Pembersih Kaca API",
    version="2.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(monitoring.router)
app.include_router(control.router)
app.include_router(mqtt.router)

@app.get("/")
async def root():
    return {
        "name": "Robot Pembersih Kaca API",
        "version": "2.0.0",
        "status": "running",
        "timestamp": datetime.now().isoformat(),
        "hostname": socket.gethostname(),
        "apis": {
            "monitoring": "/api/monitoring",
            "control": "/api/control",
            "mqtt": "/api/mqtt",
            "docs": "/docs"
        }
    }

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "uptime": robot_state._format_time(robot_state.uptime_sec),
        "robot_status": robot_state.status,
        "esp_connected": robot_state.esp_katrol_connected or robot_state.esp_brush_connected,
        "mqtt_connected": get_mqtt_client().is_connected()
    }
