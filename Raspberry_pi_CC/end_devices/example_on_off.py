from smart_device import SmartDevice
 
# ── Change this to your control panel Pi's ZeroTier IP ─────────────────────
BROKER_HOST = "10.x.x.x"
 
 
class SimpleLight(SmartDevice):
    def __init__(self):
        super().__init__(
            broker_host  = BROKER_HOST,
            device_id    = "bedroom_light_01",
            name         = "Bedroom Light",
            device_type  = "light",
            capabilities = ["on_off"],
        )
        self.is_on = False
 
        # TODO: Set up your GPIO pin here
        # import RPi.GPIO as GPIO
        # self.pin = 17
        # GPIO.setmode(GPIO.BCM)
        # GPIO.setup(self.pin, GPIO.OUT)
        # GPIO.output(self.pin, GPIO.LOW)
 
    def handle_command(self, command: dict):
        action = command.get("action")
 
        if action == "on_off":
            self.is_on = command.get("value", False)
 
            if self.is_on:
                print("Light ON")
                # TODO: GPIO.output(self.pin, GPIO.HIGH)
            else:
                print("Light OFF")
                # TODO: GPIO.output(self.pin, GPIO.LOW)
 
            # Publish updated state back to the control panel
            self.publish_state({
                "online": True,
                "on":     self.is_on,
            })
 
        else:
            print(f"Unknown action: {action}")
 
 
if __name__ == "__main__":
    light = SimpleLight()
    light.start()  # blocks forever, handles everything
 