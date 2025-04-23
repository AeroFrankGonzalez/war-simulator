# control_panel.py

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                            QLabel, QSpinBox, QComboBox, QSlider, QPushButton,
                            QGroupBox, QGridLayout)
from PyQt5.QtCore import Qt, pyqtSignal

class TeamConfig(QGroupBox):
    def __init__(self, team_id: int, parent=None):
        super().__init__(f"Team {team_id} Configuration", parent)
        self.team_id = team_id
        layout = QGridLayout()

        # Units count
        layout.addWidget(QLabel("Units:"), 0, 0)
        self.units_spin = QSpinBox()
        self.units_spin.setRange(1, 100)
        self.units_spin.setValue(20)
        layout.addWidget(self.units_spin, 0, 1)

        # Movement speed
        layout.addWidget(QLabel("Speed:"), 1, 0)
        self.speed_spin = QSpinBox()
        self.speed_spin.setRange(1, 20)
        self.speed_spin.setValue(10)
        layout.addWidget(self.speed_spin, 1, 1)

        # Initial health
        layout.addWidget(QLabel("Health:"), 2, 0)
        self.health_spin = QSpinBox()
        self.health_spin.setRange(1, 10)
        self.health_spin.setValue(5)
        layout.addWidget(self.health_spin, 2, 1)

        self.setLayout(layout)

    def get_config(self) -> dict:
        return {
            'units': self.units_spin.value(),
            'speed': self.speed_spin.value() / 10.0,
            'health': self.health_spin.value()
        }

class ControlPanel(QWidget):
    params_changed = pyqtSignal(dict)
    simulation_control = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("War Simulator Control Panel")
        self.setFixedSize(400, 600)
        self.init_ui()
        self.current_params = self.get_current_params()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(15)

        # Title
        title = QLabel("War Simulator Control")
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(title)

        # Terrain Configuration
        terrain_group = QGroupBox("Terrain Configuration")
        terrain_layout = QGridLayout()

        # Terrain type
        terrain_layout.addWidget(QLabel("Type:"), 0, 0)
        self.terrain_combo = QComboBox()
        # --- INICIO DEL CAMBIO ---
        # Añade aquí los nombres de tus nuevos presets de terreno
        self.terrain_combo.addItems([
            "valley",
            "hills",
            "forest_map",
            "rivers_and_lakes",
            # Agrega los nombres de otros presets que implementes en Terrain.create_preset
            # "arabia",
            # "black_forest",
            # "team_islands",
        ])
        # --- FIN DEL CAMBIO ---
        self.terrain_combo.currentTextChanged.connect(self.on_params_changed)
        terrain_layout.addWidget(self.terrain_combo, 0, 1)

        # Contact radius
        terrain_layout.addWidget(QLabel("Contact Radius:"), 1, 0)
        self.contact_slider = QSlider(Qt.Horizontal)
        self.contact_slider.setRange(5, 30)
        self.contact_slider.setValue(10)
        self.contact_slider.valueChanged.connect(self.on_params_changed)
        self.contact_value_label = QLabel("1.0")
        terrain_layout.addWidget(self.contact_slider, 1, 1)
        terrain_layout.addWidget(self.contact_value_label, 1, 2)

        terrain_group.setLayout(terrain_layout)
        layout.addWidget(terrain_group)

        # Team Configurations
        self.team_configs = {}
        for team_id in [1, 2]:
            team_config = TeamConfig(team_id)
            self.team_configs[team_id] = team_config
            layout.addWidget(team_config)

        # Simulation speed
        speed_group = QGroupBox("Simulation Speed")
        speed_layout = QHBoxLayout()
        self.speed_slider = QSlider(Qt.Horizontal)
        self.speed_slider.setRange(1, 100)
        self.speed_slider.setValue(50)
        self.speed_slider.valueChanged.connect(self.on_params_changed)
        self.speed_value_label = QLabel("0.05s")
        speed_layout.addWidget(self.speed_slider)
        speed_layout.addWidget(self.speed_value_label)
        speed_group.setLayout(speed_layout)
        layout.addWidget(speed_group)

        # Control buttons
        buttons_layout = QGridLayout()

        # Start button (green)
        start_button = QPushButton("Start")
        start_button.setStyleSheet("background-color: #4CAF50; color: white; padding: 8px;")
        start_button.clicked.connect(lambda: self.simulation_control.emit("start"))
        buttons_layout.addWidget(start_button, 0, 0)

        # Pause button (orange)
        pause_button = QPushButton("Pause")
        pause_button.setStyleSheet("background-color: #FF9800; color: white; padding: 8px;")
        pause_button.clicked.connect(lambda: self.simulation_control.emit("pause"))
        buttons_layout.addWidget(pause_button, 0, 1)

        # Reset button (red)
        reset_button = QPushButton("Reset")
        reset_button.setStyleSheet("background-color: #f44336; color: white; padding: 8px;")
        reset_button.clicked.connect(lambda: self.simulation_control.emit("reset"))
        buttons_layout.addWidget(reset_button, 1, 0)

        # End button (dark red)
        end_button = QPushButton("End Simulation")
        end_button.setStyleSheet("background-color: #B71C1C; color: white; padding: 8px;")
        end_button.clicked.connect(lambda: self.simulation_control.emit("end"))
        buttons_layout.addWidget(end_button, 1, 1)

        layout.addLayout(buttons_layout)

        # Status label
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("font-style: italic;")
        layout.addWidget(self.status_label)

        self.setLayout(layout)

    def get_current_params(self) -> dict:
        contact_radius = self.contact_slider.value() / 10.0
        self.contact_value_label.setText(f"{contact_radius:.1f}")

        speed = (100 - self.speed_slider.value()) / 1000.0
        self.speed_value_label.setText(f"{speed:.3f}s")

        return {
            'terrain_preset': self.terrain_combo.currentText(),
            'contact_radius': contact_radius,
            'simulation_speed': speed,
            'teams': {
                team_id: config.get_config()
                for team_id, config in self.team_configs.items()
            }
        }

    def on_params_changed(self):
        self.current_params = self.get_current_params()
        self.params_changed.emit(self.current_params)

    def update_status(self, status: str):
        self.status_label.setText(status)