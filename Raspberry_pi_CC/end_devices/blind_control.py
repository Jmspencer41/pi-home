# CIT 381 - 001 Spring 2026
# Author: Evan McQueary
# Created: 4/21/2026
# Opens and closes blinds utilizing a stepper motor. Home Pi is only updated on blind state once motion has been complete.
# Communicates with Home Pi utilizing MQTT via the Smart_Device program. PAckages device state and handles commands
# from Home Pi within this program. 

from Smart_Device import SmartDevice
import RPi.GPIO as GPIO
import time

# MQTT Broker Host and Master PI IP address.
BROKER_HOST = "172.22.157.131"

#Blind control utilizes SmartDevice program.
class SmartBlinds(SmartDevice):
    def __init__(self):
        super().__init__(
            #Information for device connection using MQTT.
            broker_host=BROKER_HOST,
            device_id="bedroom_blinds_01",
            name="Bedroom Blinds",
            device_type="blinds",
            capabilities=["on_off"]   # Changed to on and off specification for central device control.
        )

        #Initiate GPIO
        GPIO.setmode(GPIO.BCM)

        #Pins for wirring of stepper motor.
        self.pins = [17, 18, 27, 22]

        for pin in self.pins:
            GPIO.setup(pin, GPIO.OUT)
            GPIO.output(pin, 0)

        # Sequence for step motor.
        self.step_sequence = [
            [1,0,0,0],
            [1,1,0,0],
            [0,1,0,0],
            [0,1,1,0],
            [0,0,1,0],
            [0,0,1,1],
            [0,0,0,1],
            [1,0,0,1]
        ]

        self.is_open = False  # Replaces position

    # Causes step motor to go forward is direction=1 but can be reveresed if direction=-1.
    def step_motor(self, steps, direction=1, delay=0.002):
        seq = self.step_sequence if direction == 1 else list(reversed(self.step_sequence))

        for _ in range(steps):
            for step in seq:
                for i in range(4):
                    GPIO.output(self.pins[i], step[i])
                time.sleep(delay)

        for pin in self.pins:
            GPIO.output(pin, 0)

    #Open blinds
    def open_blinds(self):
        print("Opening blinds")
        self.step_motor(512, direction=1)
        # Tells home Pi that blinds are open once motion complete.
        self.is_open = True

    #Close blinds
    def close_blinds(self):
        print("Closing blinds")
        self.step_motor(512, direction=-1)
        # Tells home Pi that blinds are closed once motion complete.
        self.is_open = False

    #Handles commands from home system controller pi to open or close blinds and report state.
    def handle_command(self, command: dict):
        action = command.get("action")

        if action == "on_off":
            value = command.get("value", False)

            if value:
                self.open_blinds()
            else:
                self.close_blinds()

        else:
            print(f"Invalid action: {action}")
            return

        # Publish state in same format UI expects
        self.publish_state({
            "online": True,
            "on": self.is_open
        })

#Start blind control.
if __name__ == "__main__":
    device = SmartBlinds()
    device.start()
