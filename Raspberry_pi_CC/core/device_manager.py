from PyQt6.QtCore import QObject, pyqtSignal

from Raspberry_pi_CC.sensors.sht41 import TempHumidSensor
from Raspberry_pi_CC.core.mqtt_manager import MqttManager


class DeviceManager(QObject):

    # ── Signals to the GUI ─────────────────────────────────────────────────────

    device_added         = pyqtSignal(dict)              # new device info dict
    device_state_changed = pyqtSignal(str, dict)         # (device_id, state_dict)
    mqtt_connected       = pyqtSignal()                  # broker connection up
    mqtt_disconnected    = pyqtSignal()                  # broker connection lost

    def __init__(self):
        super().__init__()

        # ── Device registry ───────────────────────────────────────────────
        # Keyed by device_id, value is the announce info dict
        self._devices = {}

        # ── MQTT ──────────────────────────────────────────────────────────
        self._mqtt = MqttManager()
        self._mqtt.connected.connect(self._on_mqtt_connected)
        self._mqtt.disconnected.connect(self._on_mqtt_disconnected)
        self._mqtt.device_announced.connect(self._on_device_announced)
        self._mqtt.device_update.connect(self._on_device_update)
        self._mqtt.start()

        # ── SHT41 sensor ──────────────────────────────────────────────────
        self.temperature = None
        self.humidity    = None
        self._temp_humid_sensor = TempHumidSensor(interval=15)
        self._temp_humid_sensor.data_updated.connect(self._on_temp_humid_update)
        self._temp_humid_sensor.start()

        print("DeviceManager initialized")

    # ── MQTT Handlers ──────────────────────────────────────────────────────────

    def _on_mqtt_connected(self):
        print("DeviceManager: MQTT broker connected")
        self.mqtt_connected.emit()

    def _on_mqtt_disconnected(self):
        print("DeviceManager: MQTT broker disconnected")
        self.mqtt_disconnected.emit()

    def _on_device_announced(self, info: dict):
        device_id = info.get("device_id")
        if not device_id:
            print("DeviceManager: announce missing device_id, ignoring")
            return

        if device_id in self._devices:
            # Device already known — update its info
            self._devices[device_id].update(info)
            print(f"DeviceManager: updated existing device → {device_id}")
        else:
            # New device — add to registry and notify GUI
            self._devices[device_id] = info
            self.device_added.emit(info)
            print(f"DeviceManager: new device added → {device_id}")

    def _on_device_update(self, device_id: str, state: dict):
        if device_id in self._devices:
            self._devices[device_id]["state"] = state
        else:
            # Got a state update for an unknown device — register it with minimal info
            self._devices[device_id] = {"device_id": device_id, "name": device_id, "state": state}
            self.device_added.emit(self._devices[device_id])
            print(f"DeviceManager: unknown device registered from state → {device_id}")

        self.device_state_changed.emit(device_id, state)

    # ── Sensor ─────────────────────────────────────────────────────────────────

    def _on_temp_humid_update(self, temp: float, humid: float):
        self.temperature = temp
        self.humidity    = humid

    # ── Public Interface ───────────────────────────────────────────────────────

    def get_sensor(self):
        return self._temp_humid_sensor

    def get_temperature(self):
        return self.temperature

    def get_humidity(self):
        return self.humidity

    def get_mqtt(self):
        return self._mqtt

    def get_device(self, device_id: str):
        return self._devices.get(device_id)

    def get_all_devices(self):
        return dict(self._devices)

    def send_command(self, device_id: str, command: dict):
        self._mqtt.send_command(device_id, command)

    def stop(self):
        print("DeviceManager: stopping...")
        self._temp_humid_sensor.stop()
        self._mqtt.stop()
        print("DeviceManager: stopped")