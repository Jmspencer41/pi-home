
from PyQt6.QtCore import QObject, pyqtSignal

from Raspberry_pi_CC.sensors.sht41 import TempHumidSensor


class DeviceManager(QObject):

    # ── Signals to the GUI ─────────────────────────────────────────────────────

    device_added = pyqtSignal(object)
    device_state_changed = pyqtSignal(str, str, object)

    def __init__(self):
        super().__init__()

        # ── SHT41 sensor ──────────────────────────────────────────────────
        self.temperature = None
        self.humidity    = None
        self._temp_humid_sensor = TempHumidSensor(interval=15)
        self._temp_humid_sensor.data_updated.connect(self._on_temp_humid_update)
        self._temp_humid_sensor.start()

        print("DeviceManager initialized")

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

    def stop(self):
        print("DeviceManager: stopping...")
        self._temp_humid_sensor.stop()
        print("DeviceManager: stopped")