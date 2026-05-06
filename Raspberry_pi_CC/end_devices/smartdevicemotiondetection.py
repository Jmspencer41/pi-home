from smart_device import SmartDevice
from gpiozero import LED, DigitalInputDevice
from time import sleep
import threading

# ── Change this to your control panel Pi's ZeroTier IP ─────────────────────
BROKER_HOST = "172.22.157.131"


class AlarmSystem(SmartDevice):
    def __init__(self):
        super().__init__(
            broker_host  = BROKER_HOST,
            device_id    = "alarm_system_01",
            name         = "Alarm System",
            device_type  = "alarm",
            capabilities = ["on_off"],
        )

        # Alarm state
        self.armed = False
        self.alarm_active = False

        # Motion sensor
        self.motion = DigitalInputDevice(23)

        # LEDs (active low)
        self.led1 = LED(5, active_high=False)
        self.led2 = LED(6, active_high=False)
        self.led3 = LED(13, active_high=False)
        self.led4 = LED(19, active_high=False)
        self.led5 = LED(26, active_high=False)

        self.leds_off()

        # Start background monitoring thread
        self.thread = threading.Thread(target=self.monitor_motion, daemon=True)
        self.thread.start()

    # ── LED control ─────────────────────────────────────────
    def leds_on(self):
        self.led1.on()
        self.led2.on()
        self.led3.on()
        self.led4.on()
        self.led5.on()

    def leds_off(self):
        self.led1.off()
        self.led2.off()
        self.led3.off()
        self.led4.off()
        self.led5.off()

    # ── Motion monitoring (runs in background) ──────────────
    def monitor_motion(self):
        while True:
            if self.armed:
                if self.motion.value == 1:
                    if not self.alarm_active:
                        print("MOTION DETECTED")
                        self.leds_on()
                        self.alarm_active = True
                else:
                    if self.alarm_active:
                        self.leds_off()
                        self.alarm_active = False
            sleep(0.2)

    # ── Handle commands from control panel ──────────────────
    def handle_command(self, command: dict):
        action = command.get("action")

        if action == "on_off":
            turn_on = command.get("value", False)

            if turn_on:
                print("ARMING SYSTEM (15 second delay)")

                # 15 second exit delay
                for i in range(15, 0, -1):
                    print(f"Arming in {i} seconds...")
                    sleep(1)

                self.armed = True
                print("SYSTEM ARMED")

            else:
                print("SYSTEM DISARMED")
                self.armed = False
                self.alarm_active = False
                self.leds_off()

            # Publish state
            self.publish_state({
                "online": True,
                "on": self.armed,
            })

        else:
            print(f"Unknown action: {action}")


# ── Main ───────────────────────────────────────────────────
if __name__ == "__main__":
    alarm = AlarmSystem()
    alarm.start()