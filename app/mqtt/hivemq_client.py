"""
MQTT Client untuk HiveMQ Cloud
"""

import paho.mqtt.client as mqtt
import json
import threading
import time
from datetime import datetime
import logging
from typing import Dict, Any, Optional, Callable
import ssl
import os
from dotenv import load_dotenv

load_dotenv()

HIVE_MQTT_BROKER = os.getenv("HIVEMQ_BROKER", "70f994e2717f4e2bbfb48f7fad93a99f.s1.eu.hivemq.cloud")
HIVE_MQTT_PORT = int(os.getenv("HIVEMQ_PORT", 8883))
HIVE_MQTT_USERNAME = os.getenv("HIVEMQ_USERNAME", "robot_pembersih_kaca")
HIVE_MQTT_PASSWORD = os.getenv("HIVEMQ_PASSWORD", "Drags421")

TOPIC_STATUS = "robot/status"
TOPIC_COMMAND = "robot/command"
TOPIC_ESP_STATUS = "robot/esp/status"

logger = logging.getLogger(__name__)

class HiveMQClient:
    def __init__(self):
        self.client = None
        self.connected = False
        self.last_status = {}
        self._on_status_callback = None
        self._running = False
        self._thread = None
        self._reconnect_attempts = 0
    
    def start(self, on_status_callback: Optional[Callable] = None):
        self._on_status_callback = on_status_callback
        self._running = True
        
        self.client = mqtt.Client()
        self.client.username_pw_set(HIVE_MQTT_USERNAME, HIVE_MQTT_PASSWORD)
        self.client.tls_set()
        
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        self.client.on_disconnect = self._on_disconnect
        
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        
        logger.info(f"🚀 MQTT Client started, connecting to {HIVE_MQTT_BROKER}")
    
    def _run_loop(self):
        while self._running:
            try:
                if not self.connected:
                    self.client.connect(HIVE_MQTT_BROKER, HIVE_MQTT_PORT, 60)
                    self.client.loop_start()
                time.sleep(2)
            except Exception as e:
                logger.error(f"MQTT Connection error: {e}")
                time.sleep(5)
    
    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self.connected = True
            logger.info("✅ MQTT Connected to HiveMQ Cloud!")
            client.subscribe(TOPIC_STATUS)
            client.subscribe(TOPIC_ESP_STATUS)
            logger.info(f"📡 Subscribed to: {TOPIC_STATUS}, {TOPIC_ESP_STATUS}")
        else:
            self.connected = False
            logger.error(f"❌ MQTT Connection failed with code: {rc}")
    
    def _on_disconnect(self, client, userdata, rc):
        self.connected = False
        logger.warning("⚠️ MQTT Disconnected")
    
    def _on_message(self, client, userdata, msg):
        try:
            payload = msg.payload.decode()
            data = json.loads(payload)
            
            if msg.topic in [TOPIC_STATUS, TOPIC_ESP_STATUS]:
                self.last_status = data
                self.last_status['_timestamp'] = datetime.now().isoformat()
                self.last_status['_topic'] = msg.topic
                
                if self._on_status_callback:
                    self._on_status_callback(self.last_status)
                    
        except Exception as e:
            logger.error(f"❌ Message handler error: {e}")
    
    def send_command(self, command: str, params: Optional[Dict] = None) -> bool:
        if not self.connected or not self.client:
            return False
        try:
            data = {"command": command}
            if params:
                data["params"] = params
            payload = json.dumps(data)
            result = self.client.publish(TOPIC_COMMAND, payload)
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                logger.info(f"📤 Published to {TOPIC_COMMAND}: {command}")
                return True
            return False
        except Exception as e:
            logger.error(f"❌ Publish error: {e}")
            return False
    
    def get_last_status(self) -> Dict:
        return self.last_status
    
    def is_connected(self) -> bool:
        return self.connected
    
    def stop(self):
        self._running = False
        if self.client:
            self.client.loop_stop()
            self.client.disconnect()
        logger.info("🛑 MQTT Client stopped")

_mqtt_client = None

def get_mqtt_client() -> HiveMQClient:
    global _mqtt_client
    if _mqtt_client is None:
        _mqtt_client = HiveMQClient()
    return _mqtt_client
