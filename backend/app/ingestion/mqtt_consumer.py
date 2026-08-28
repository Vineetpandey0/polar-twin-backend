import json
import logging
import asyncio
import paho.mqtt.client as mqtt
from app.core.config import settings
from app.schemas.telemetry import TelemetryMessage
from app.services.ingestion_service import ingestion_service

logger = logging.getLogger("mqtt_consumer")


class MQTTConsumer:
    def __init__(self) -> None:
        self.client = mqtt.Client()
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        self.client.on_disconnect = self._on_disconnect
        self.loop = None

    def _on_connect(self, client, userdata, flags, rc) -> None:
        if rc == 0:
            logger.info("Backend MQTT Consumer connected to broker. Subscribing to stations/#...")
            client.subscribe("stations/#")
        else:
            logger.error(f"Backend MQTT Consumer failed connect, code: {rc}")

    def _on_disconnect(self, client, userdata, rc) -> None:
        logger.warning(f"Backend MQTT Consumer disconnected (code {rc})")

    def _on_message(self, client, userdata, msg) -> None:
        try:
            payload = json.loads(msg.payload.decode("utf-8"))
            telemetry = TelemetryMessage(**payload)
            if self.loop and self.loop.is_running():
                asyncio.run_coroutine_threadsafe(
                    ingestion_service.process(telemetry), self.loop
                )
        except Exception as e:
            logger.warning(f"Malformed MQTT message received on topic {msg.topic}: {e}")

    def start(self, loop: asyncio.AbstractEventLoop) -> None:
        self.loop = loop
        try:
            self.client.connect(settings.MQTT_HOST, settings.MQTT_PORT, 60)
            self.client.loop_start()
            logger.info("MQTT Consumer loop started.")
        except Exception as e:
            logger.error(f"Failed to start MQTT Consumer: {e}")

    def stop(self) -> None:
        self.client.loop_stop()
        self.client.disconnect()


mqtt_consumer = MQTTConsumer()
