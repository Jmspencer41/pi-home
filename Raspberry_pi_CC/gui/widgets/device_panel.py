from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout)
from PyQt6.QtGui import QFont
from ..Functionality.scrollable_button import ScrollableButton
from ..Functionality.touch_scroll_area import TouchScrollArea

class DeviceListLayout(QHBoxLayout):
    def __init__(self, device_manager, screen_height):
        super().__init__()

        self._device_manager = device_manager
        self._screen_height = screen_height
        self._buttons = {}   # device_id → button widget
        self._states  = {}   # device_id → True/False (on/off)

        scrollable_area = TouchScrollArea()

        self._device_list_widget = QWidget()
        self._device_list_widget.setStyleSheet("background-color: #99ddff; border-radius: 15px;")
        self._device_list_layout = QVBoxLayout()

        padding = int(screen_height * 0.01)
        self._device_list_layout.setContentsMargins(padding, padding, padding, padding)
        self._device_list_widget.setLayout(self._device_list_layout)

        # Push buttons to the top when there are only a few
        self._device_list_layout.addStretch()

        scrollable_area.setWidget(self._device_list_widget)
        scrollable_area.setWidgetResizable(True)

        self.addWidget(scrollable_area)

        # ── Connect to DeviceManager signals ──────────────────────────────
        self._device_manager.device_added.connect(self._on_device_added)
        self._device_manager.device_state_changed.connect(self._on_device_state_changed)

    def _on_device_added(self, info: dict):
        device_id = info.get("device_id", "unknown")
        name      = info.get("name", device_id)
        is_on     = info.get("state", {}).get("on", False)
        online    = info.get("state", {}).get("online", True)

        self._states[device_id] = is_on

        button = self._create_device_button(device_id, name, is_on, online)

        # Insert before the stretch at the end
        count = self._device_list_layout.count()
        self._device_list_layout.insertWidget(count - 1, button)
        self._device_list_layout.insertSpacing(count - 1, int(self._screen_height * 0.03))

        self._buttons[device_id] = button
        print(f"DevicePanel: added button for {device_id}")

    def _on_device_state_changed(self, device_id: str, state: dict):
        button = self._buttons.get(device_id)
        if not button:
            return

        online = state.get("online", True)
        is_on  = state.get("on", self._states.get(device_id, False))

        self._states[device_id] = is_on
        self._apply_button_style(button, is_on, online)

        # Update button text to show on/off status
        name = self._device_manager.get_device(device_id).get("name", device_id)
        status_text = "ON" if is_on else "OFF"
        button.setText(f"{name}  —  {status_text}")

    def _on_button_clicked(self, device_id: str):
        # Toggle the state
        current = self._states.get(device_id, False)
        new_state = not current

        # Send command to the device
        self._device_manager.send_command(device_id, {
            "action": "on_off",
            "value": new_state,
        })
        print(f"DevicePanel: toggled {device_id} → {'ON' if new_state else 'OFF'}")

    def _create_device_button(self, device_id, name, is_on=False, online=True):
        status_text = "ON" if is_on else "OFF"
        button = ScrollableButton(f"{name}  —  {status_text}") 
        button.setMinimumHeight(int(self._screen_height * 0.12))
        button.setFont(QFont('Arial', int(self._screen_height * 0.02)))
        self._apply_button_style(button, is_on, online)

        # Connect click to toggle
        button.clicked.connect(lambda checked, did=device_id: self._on_button_clicked(did))

        return button

    def _apply_button_style(self, button, is_on, online=True):
        border_radius = int(self._screen_height * 0.03)
        padding = int(self._screen_height * 0.01)

        if not online:
            # Offline — grey
            bg_color = "#7f8c8d"
        elif is_on:
            # Online and ON — green
            bg_color = "#00994d"
        else:
            # Online and OFF — dark red
            bg_color = "#c0392b"

        button.setStyleSheet(f"""
            QPushButton {{
                background-color: {bg_color};
                color: white;
                border-radius: {border_radius}px;
                padding: {padding}px;
                text-align: left;
                border: 2px solid rgba(0, 0, 0, 0.2);
            }}
            QPushButton:pressed {{
                background-color: #626d6e;
            }}
        """)