import json
import time
import paho.mqtt.client as mqtt
 
 
class SmartDevice:
 
    def __init__(self, broker_host, device_id, name, device_type, capabilities=None):
        self._broker_host = broker_host
        self._device_id   = device_id
        self._name        = name
        self._device_type = device_type
        self._capabilities = capabilities or []
 
        # ── Topics ─────────────────────────────────────────────────────────
        self._topic_announce = f"home/devices/{self._device_id}/announce"
        self._topic_state    = f"home/devices/{self._device_id}/state"
        self._topic_command  = f"home/devices/{self._device_id}/command"
 
        # ── MQTT client ────────────────────────────────────────────────────
        self._client = mqtt.Client(client_id=self._device_id, clean_session=True)
 
        # Set LWT — broker publishes this if we disconnect unexpectedly
        will_payload = json.dumps({"online": False})
        self._client.will_set(self._topic_state, will_payload, retain=True)
 
        # Paho 1.x callbacks
        self._client.on_connect    = self._on_connect
        self._client.on_disconnect = self._on_disconnect
        self._client.on_message    = self._on_message
 
        self._running = False
 
    # ── Connection ─────────────────────────────────────────────────────────────
 
    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print(f"[{self._device_id}] Connected to broker")
 
            # Announce ourselves (retained so the panel picks it up on restart)
            announce = {
                "device_id":    self._device_id,
                "name":         self._name,
                "type":         self._device_type,
                "capabilities": self._capabilities,
            }
            client.publish(self._topic_announce, json.dumps(announce), retain=True)
            print(f"[{self._device_id}] Announced on {self._topic_announce}")
 
            # Publish online state (retained)
            self.publish_state({"online": True})
 
            # Subscribe to our command topic
            client.subscribe(self._topic_command)
            print(f"[{self._device_id}] Subscribed to {self._topic_command}")
 
            # Called after connection is fully set up
            self.on_ready()
        else:
            print(f"[{self._device_id}] Connection failed (rc={rc})")
 
    def _on_disconnect(self, client, userdata, rc):
        if rc != 0:
            print(f"[{self._device_id}] Unexpected disconnect (rc={rc})")
        else:
            print(f"[{self._device_id}] Disconnected")
 
    def _on_message(self, client, userdata, msg):
        payload = msg.payload.decode("utf-8", errors="replace")
        print(f"[{self._device_id}] Command received: {payload}")
 
        try:
            command = json.loads(payload)
        except json.JSONDecodeError:
            print(f"[{self._device_id}] Bad command payload, ignoring")
            return
 
        self.handle_command(command)
 
    # ── Public Methods ─────────────────────────────────────────────────────────
 
    def publish_state(self, state: dict):
        ### Publish device state. Called by your subclass whenever state changes.
        payload = json.dumps(state)
        self._client.publish(self._topic_state, payload, retain=True)
        print(f"[{self._device_id}] State published: {payload}")
 
    def start(self):
        ### Connect to the broker and block forever (call this at the end of your script).
        try:
            print(f"[{self._device_id}] Connecting to {self._broker_host}:1883 ...")
            self._client.connect(self._broker_host, 1883, keepalive=60)
            self._running = True
            self._client.loop_forever()  # blocks — handles reconnects automatically
        except KeyboardInterrupt:
            print(f"\n[{self._device_id}] Shutting down ...")
            self.stop()
        except Exception as e:
            print(f"[{self._device_id}] Failed to connect: {e}")
 
    def stop(self):
        ###Publish offline state and disconnect cleanly.
        self._running = False
        self.publish_state({"online": False})
        self._client.disconnect()
        self._client.loop_stop()
        print(f"[{self._device_id}] Stopped")
 
    # ── Override These ─────────────────────────────────────────────────────────
 
    def handle_command(self, command: dict):
        ### Override this in your subclass to handle incoming commands.
        print(f"[{self._device_id}] Unhandled command: {command}")
 
    def on_ready(self):
        ### Override this if you need to do something after connecting (e.g. start a sensor loop).
        pass
 