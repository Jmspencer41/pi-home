"""
mqtt_manager.py

Bridges the Mosquitto broker (localhost) with the PyQt6 GUI via signals.
Uses paho-mqtt 1.x callback API.

Topic structure:
    home/devices/{device_id}/announce  – devices publish their info here on boot (retained)
    home/devices/{device_id}/state     – devices publish their status here
    home/devices/{device_id}/command   – app publishes commands here
    home/sensors/{sensor_type}         – sensor data (e.g. temp/humidity)
"""

import json
import paho.mqtt.client as mqtt
from PyQt6.QtCore import QObject, pyqtSignal


class MqttManager(QObject):

    # ── Signals to the rest of the app ─────────────────────────────────────────

    connected         = pyqtSignal()                  # broker connection established
    disconnected      = pyqtSignal()                  # broker connection lost
    message_received  = pyqtSignal(str, str)          # (topic, payload)
    device_announced  = pyqtSignal(dict)              # device announce info dict
    device_update     = pyqtSignal(str, dict)         # (device_id, state_dict)

    # ── Configuration ──────────────────────────────────────────────────────────

    DEFAULT_HOST = "localhost" #TODO: make this configurable for remote brokers and mobile use
    DEFAULT_PORT = 1883
    DEFAULT_KEEPALIVE = 60

    # Topics
    TOPIC_DEVICE_ANNOUNCE = "home/devices/+/announce"    # subscribe – wildcard
    TOPIC_DEVICE_STATE    = "home/devices/+/state"       # subscribe – wildcard
    TOPIC_SENSOR_DATA     = "home/sensors/#"             # subscribe – wildcard
    TOPIC_CMD_TEMPLATE    = "home/devices/{}/command"    # publish   – per device

    def __init__(self, host=None, port=None, parent=None):
        super().__init__(parent)

        self._host = host or self.DEFAULT_HOST
        self._port = port or self.DEFAULT_PORT
        self._is_connected = False

        # ── Set up paho client ─────────────────────────────────────────────
        self._client = mqtt.Client(client_id="smart_home_pi", clean_session=True)

        # Paho 1.x callbacks
        self._client.on_connect    = self._on_connect
        self._client.on_disconnect = self._on_disconnect
        self._client.on_message    = self._on_message

    # ── Start / Stop ───────────────────────────────────────────────────────────

    def start(self):
        """Connect to the broker and start the background network loop."""
        try:
            print(f"MqttManager: connecting to {self._host}:{self._port} ...")
            self._client.connect(self._host, self._port, self.DEFAULT_KEEPALIVE)
            self._client.loop_start()          # runs paho network loop in a thread
        except Exception as e:
            print(f"MqttManager: failed to connect – {e}")

    def stop(self):
        """Disconnect cleanly and stop the network loop."""
        print("MqttManager: stopping ...")
        self._client.loop_stop()
        self._client.disconnect()
        print("MqttManager: stopped")

    # ── Paho Callbacks (called from paho's thread) ─────────────────────────────
    #    Qt signals are thread-safe, so emitting here is fine.

    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print("MqttManager: connected to broker")
            self._is_connected = True
            self.connected.emit()

            # Subscribe to device and sensor topics
            client.subscribe(self.TOPIC_DEVICE_ANNOUNCE)
            client.subscribe(self.TOPIC_DEVICE_STATE)
            client.subscribe(self.TOPIC_SENSOR_DATA)
            print(f"MqttManager: subscribed to {self.TOPIC_DEVICE_ANNOUNCE}")
            print(f"MqttManager: subscribed to {self.TOPIC_DEVICE_STATE}")
            print(f"MqttManager: subscribed to {self.TOPIC_SENSOR_DATA}")
        else:
            print(f"MqttManager: connection failed with code {rc}")

    def _on_disconnect(self, client, userdata, rc):
        self._is_connected = False
        self.disconnected.emit()
        if rc != 0:
            print(f"MqttManager: unexpected disconnect (rc={rc})")
        else:
            print("MqttManager: disconnected")

    def _on_message(self, client, userdata, msg):
        topic   = msg.topic
        payload = msg.payload.decode("utf-8", errors="replace")

        # Always emit the raw message signal
        self.message_received.emit(topic, payload)

        # Parse topic: home/devices/{device_id}/{action}
        parts = topic.split("/")
        if len(parts) == 4 and parts[0] == "home" and parts[1] == "devices":
            device_id = parts[2]
            action    = parts[3]

            # Device announce message
            if action == "announce":
                try:
                    info = json.loads(payload)
                    info["device_id"] = device_id  # ensure device_id is in the dict
                    self.device_announced.emit(info)
                    print(f"MqttManager: device announced → {device_id}")
                except json.JSONDecodeError:
                    print(f"MqttManager: bad announce payload from {device_id}")

            # Device state update
            elif action == "state":
                try:
                    state = json.loads(payload)
                except json.JSONDecodeError:
                    state = {"raw": payload}
                self.device_update.emit(device_id, state)

    # ── Public Interface ───────────────────────────────────────────────────────

    def publish(self, topic: str, payload: str, retain: bool = False):
        """Publish a message to any topic."""
        if not self._is_connected:
            print(f"MqttManager: not connected, cannot publish to {topic}")
            return
        self._client.publish(topic, payload, retain=retain)

    def send_command(self, device_id: str, command: dict):
        """Send a command to a specific device."""
        topic = self.TOPIC_CMD_TEMPLATE.format(device_id)
        payload = json.dumps(command)
        self.publish(topic, payload)
        print(f"MqttManager: sent command to {device_id} → {payload}")

    def subscribe(self, topic: str):
        """Subscribe to an additional topic at runtime."""
        self._client.subscribe(topic)
        print(f"MqttManager: subscribed to {topic}")

    def is_connected(self) -> bool:
        return self._is_connected