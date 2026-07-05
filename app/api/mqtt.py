"""
MQTT API Endpoints
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime

from app.mqtt.hivemq_client import get_mqtt_client

router = APIRouter(prefix="/api/mqtt", tags=["MQTT"])

class MQTTCommand(BaseModel):
    command: str
    params: Optional[Dict[str, Any]] = None

@router.get("/status")
async def get_mqtt_status():
    client = get_mqtt_client()
    return {
        "connected": client.is_connected(),
        "last_status": client.get_last_status(),
        "timestamp": datetime.now().isoformat()
    }

@router.post("/command")
async def send_mqtt_command(command: MQTTCommand):
    client = get_mqtt_client()
    if not client.is_connected():
        raise HTTPException(status_code=503, detail="MQTT not connected")
    success = client.send_command(command.command, command.params)
    if success:
        return {"success": True, "command": command.command, "timestamp": datetime.now().isoformat()}
    raise HTTPException(status_code=500, detail="Failed to send command")
