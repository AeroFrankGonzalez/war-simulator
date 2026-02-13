from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                            QLabel, QSpinBox, QComboBox, QSlider, QPushButton,
                            QGroupBox, QGridLayout)
from PyQt5.QtCore import Qt, pyqtSignal

class TeamConfig(QGroupBox):
    def __init__(self, team_id: int, parent=None):
        super().__init__(f"Team {team_id} Configuration", parent)
        self.team_id = team_id
        layout = QGridLayout()

        # Density % (Formerly Units count)
        layout.addWidget(QLabel("Density (%):"), 0, 0)
        self.density_spin = QSpinBox()
        self.density_spin.setRange(1, 100)
        self.density_spin.setValue(20) # Default 20%
        layout.addWidget(self.density_spin, 0, 1)

        # Movement speed (Not used in CA but kept for compatibility/future)
        # layout.addWidget(QLabel("Speed:"), 1, 0)
        # self.speed_spin = QSpinBox()
        # self.speed_spin.setRange(1, 20)
        # self.speed_spin.setValue(10)
        # layout.addWidget(self.speed_spin, 1, 1)

        # Health (Simplified in CA)
        # layout.addWidget(QLabel("Health:"), 2, 0)
        # self.health_spin = QSpinBox()
        # self.health_spin.setRange(1, 10)
        # self.health_spin.setValue(1)
        # layout.addWidget(self.health_spin, 2, 1)

        self.setLayout(layout)

    def get_config(self) -> dict:
        return {
            'initial_pop_percent': self.density_spin.value() / 100.0,
        }

class ControlPanel(QWidget):
    params_changed = pyqtSignal(dict)
    simulation_control = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("War Simulator Control - CA Edition")
        self.setFixedSize(400, 500)
        self.init_ui()
        self.connect_signals()
        self.current_params = self.get_current_params()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(15)

        title = QLabel("War Simulator Control")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # Terrain Config
        terrain_group = QGroupBox("Terrain Configuration")
        terrain_layout = QGridLayout()

        terrain_layout.addWidget(QLabel("Type:"), 0, 0)
        self.terrain_combo = QComboBox()
        self.terrain_combo.addItems([
            "valley", "hills", "forest_map", "rivers_and_lakes"
        ])
        terrain_layout.addWidget(self.terrain_combo, 0, 1)

        terrain_group.setLayout(terrain_layout)
        layout.addWidget(terrain_group)

        # Team Configs
        self.team_configs = {}
        for team_id in [1, 2]:
            team_config = TeamConfig(team_id)
            self.team_configs[team_id] = team_config
            layout.addWidget(team_config)

        # Speed Config
        speed_group = QGroupBox("Simulation Speed")
        speed_layout = QHBoxLayout()
        speed_layout.addWidget(QLabel("Speed:"))
        self.speed_slider = QSlider(Qt.Horizontal)
        self.speed_slider.setRange(1, 100)
        self.speed_slider.setValue(50)
        self.speed_value_label = QLabel("0.100s")
        speed_layout.addWidget(self.speed_slider)
        speed_layout.addWidget(self.speed_value_label)
        speed_group.setLayout(speed_layout)
        layout.addWidget(speed_group)

        # Buttons
        buttons_layout = QGridLayout()
        
        start_button = QPushButton("Start")
        start_button.setStyleSheet("background-color: #4CAF50; color: white; padding: 8px;")
        start_button.clicked.connect(lambda: self.simulation_control.emit("start"))
        buttons_layout.addWidget(start_button, 0, 0)

        pause_button = QPushButton("Pause")
        pause_button.setStyleSheet("background-color: #FF9800; color: white; padding: 8px;")
        pause_button.clicked.connect(lambda: self.simulation_control.emit("pause"))
        buttons_layout.addWidget(pause_button, 0, 1)

        reset_button = QPushButton("Reset")
        reset_button.setStyleSheet("background-color: #f44336; color: white; padding: 8px;")
        reset_button.clicked.connect(lambda: self.simulation_control.emit("reset"))
        buttons_layout.addWidget(reset_button, 1, 0)

        end_button = QPushButton("End Simulation")
        end_button.setStyleSheet("background-color: #B71C1C; color: white; padding: 8px;")
        end_button.clicked.connect(lambda: self.simulation_control.emit("end"))
        buttons_layout.addWidget(end_button, 1, 1)

        layout.addLayout(buttons_layout)

        self.status_label = QLabel("Ready")
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)

        layout.addStretch(1)
        self.setLayout(layout)

    def connect_signals(self):
        self.terrain_combo.currentTextChanged.connect(self.on_params_changed)
        self.speed_slider.valueChanged.connect(self.on_params_changed)
        
        for team_id, config_widget in self.team_configs.items():
            config_widget.density_spin.valueChanged.connect(self.on_params_changed)

    def get_current_params(self) -> dict:
        speed = (101 - self.speed_slider.value()) / 200.0 # Adjusted scale
        self.speed_value_label.setText(f"{speed:.3f}s")

        params = {
            'terrain_preset': self.terrain_combo.currentText(),
            'simulation_speed': speed,
            'teams': {
                team_id: config.get_config()
                for team_id, config in self.team_configs.items()
            }
        }
        return params

    def on_params_changed(self):
        self.current_params = self.get_current_params()
        self.params_changed.emit(self.current_params)

    def update_status(self, status: str):
        self.status_label.setText(status)