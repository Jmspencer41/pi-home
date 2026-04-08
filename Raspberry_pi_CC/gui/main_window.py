"""
main_window.py  (UPDATED — network status + zero-config support)

Changes:
  - Added NetworkStatusWidget below the title
  - Wired gateway_connection_changed and gateway_ready_received to status widget
  - Wired config_requested to show ConfigureGatewayDialog
"""

from PyQt6.QtWidgets import (QMainWindow,
                             QWidget,
                             QVBoxLayout,
                             QHBoxLayout,
                             QLabel)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from .top_layer_buttons import TopLayerButtons
from .widgets.device_panel import DeviceListLayout
from .widgets.environment_panel import EnvironmentLayout
from .widgets.network_status import NetworkStatusWidget
from .dialogs.configure_gateway import ConfigureGatewayDialog
from Raspberry_pi_CC.core.device_manager import DeviceManager


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.device_manager = DeviceManager()
        self.init_ui()
        self._connect_signals()

    def init_ui(self):
        screen = self.screen()
        height = screen.geometry().height()

        titleSize = int(height * 0.04)
        spacingSize = int(height * 0.03)

        Title = "Smart Home Control Center"

        self.setWindowTitle(Title)
        self.showFullScreen()
        self.setStyleSheet("background-color: #2c3e50;")

        Central_widget = QWidget()
        main_layout = QVBoxLayout()
        Central_widget.setLayout(main_layout)
        self.setCentralWidget(Central_widget)

        ###### Title ######
        title_widget = QLabel(Title)
        title_widget.setFont(QFont('Arial', titleSize, QFont.Weight.Bold))
        title_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_widget.setStyleSheet("color: #ecf0f1; padding: 20px;")
        main_layout.addWidget(title_widget)

        ###### Network Status Indicator ######
        self.network_status = NetworkStatusWidget(height)
        main_layout.addWidget(self.network_status, alignment=Qt.AlignmentFlag.AlignCenter)

        main_layout.addSpacing(int(spacingSize * 0.5))

        ###### Top Buttons ######
        top_layer_buttons = TopLayerButtons(height)
        main_layout.addLayout(top_layer_buttons)

        main_layout.addSpacing(spacingSize)

        ###### Devices and Environment Area ######
        Devices_layout = QHBoxLayout()
        Devices_layout.setSpacing(int(height * 0.015))
        device_list_layout = DeviceListLayout(height)

        sensor = self.device_manager.get_sensor()
        envi_area_layout = EnvironmentLayout(sensor, height)

        Devices_layout.addLayout(device_list_layout)
        Devices_layout.setStretch(Devices_layout.count() - 1, 1)

        Devices_layout.addLayout(envi_area_layout)
        Devices_layout.setStretch(Devices_layout.count() - 1, 1)

        main_layout.addLayout(Devices_layout)
        

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.close()
        else:
            super().keyPressEvent(event)

    def closeEvent(self, event):
        print("Closing application...")
        self.device_manager.stop()
        event.accept()
        print("Application closed")