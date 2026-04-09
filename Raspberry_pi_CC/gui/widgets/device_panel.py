from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout)
from PyQt6.QtGui import QFont
from ..Functionality.scrollable_button import ScrollableButton
from ..Functionality.touch_scroll_area import TouchScrollArea

class DeviceListLayout(QHBoxLayout):
    def __init__(self, device_manager, screen_height):
        super().__init__()

        self._device_manager = device_manager
        self._screen_height = screen_height
        self._buttons = {}  # device_id → button widget

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
        online    = info.get("state", {}).get("online", True)

        button = self._create_device_button(name, online)

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
        self._apply_button_style(button, online)

    def _create_device_button(self, name, online=True):
        button = ScrollableButton(name) 
        button.setMinimumHeight(int(self._screen_height * 0.12))
        button.setFont(QFont('Arial', int(self._screen_height * 0.02)))
        self._apply_button_style(button, online)
        return button

    def _apply_button_style(self, button, online):
        border_radius = int(self._screen_height * 0.03)
        padding = int(self._screen_height * 0.01)

        if online:
            button.setStyleSheet(f"""
                QPushButton {{
                    background-color: #00994d;
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
        else:
            button.setStyleSheet(f"""
                QPushButton {{
                    background-color: #7f8c8d;
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