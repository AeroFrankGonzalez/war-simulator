# control_panel.py

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                            QLabel, QSpinBox, QComboBox, QSlider, QPushButton,
                            QGroupBox, QGridLayout)
from PyQt5.QtCore import Qt, pyqtSignal

# Definir los tipos de comportamiento disponibles (debe coincidir con la lógica en main.py)
BEHAVIOR_TYPES = [
    'aggressive_advance',
    'seek_and_destroy',
    'random_walk',
    # Añade aquí otros comportamientos si los implementas en main.py
]


class TeamConfig(QGroupBox):
    def __init__(self, team_id: int, parent=None):
        super().__init__(f"Team {team_id} Configuration", parent)
        self.team_id = team_id
        layout = QGridLayout()

        # Units count
        layout.addWidget(QLabel("Units:"), 0, 0)
        self.units_spin = QSpinBox()
        self.units_spin.setRange(1, 500) # Aumentar el rango máximo de unidades
        self.units_spin.setValue(50)
        layout.addWidget(self.units_spin, 0, 1)

        # Movement speed (escalado por 10.0 en get_config)
        layout.addWidget(QLabel("Speed:"), 1, 0)
        self.speed_spin = QSpinBox()
        self.speed_spin.setRange(1, 20) # Rango de 1 a 20 -> 0.1 a 2.0
        self.speed_spin.setValue(10) # Corresponde a 1.0
        self.speed_spin.setSingleStep(1)
        layout.addWidget(self.speed_spin, 1, 1)

        # Initial health
        layout.addWidget(QLabel("Health:"), 2, 0)
        self.health_spin = QSpinBox()
        self.health_spin.setRange(1, 10)
        self.health_spin.setValue(5)
        layout.addWidget(self.health_spin, 2, 1)

        # Comportamiento (Behavior)
        layout.addWidget(QLabel("Behavior:"), 3, 0)
        self.behavior_combo = QComboBox()
        self.behavior_combo.addItems(BEHAVIOR_TYPES)
        self.behavior_combo.setCurrentText('aggressive_advance') # Comportamiento por defecto inicial
        layout.addWidget(self.behavior_combo, 3, 1)

        self.setLayout(layout)

    def get_config(self) -> dict:
        return {
            'units': self.units_spin.value(),
            'speed': self.speed_spin.value() / 10.0, # Escalar el valor del spin box a la velocidad real
            'health': self.health_spin.value(),
            'behavior': self.behavior_combo.currentText()
        }

class ControlPanel(QWidget):
    # Señales para notificar cambios en parámetros y comandos de control
    params_changed = pyqtSignal(dict)
    simulation_control = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("War Simulator Control Panel")
        self.setFixedSize(400, 650) # Ajustar tamaño de la ventana del panel si es necesario
        self.init_ui()
        # Conectar señales *después* de inicializar la UI y obtener los parámetros iniciales
        self.connect_signals() # Llamar al nuevo método para conectar señales
        self.current_params = self.get_current_params() # Obtener los parámetros iniciales DESPUÉS de configurar widgets


    def init_ui(self):
        # Configurar el layout principal de la ventana del panel
        layout = QVBoxLayout()
        layout.setSpacing(15) # Espacio entre widgets/grupos

        # Título del panel
        title = QLabel("War Simulator Control")
        title.setStyleSheet("font-size: 18px; font-weight: bold; text-align: center;") # Estilo para el título
        title.setAlignment(Qt.AlignCenter) # Centrar el texto del título
        layout.addWidget(title)

        # Grupo de configuración del terreno
        terrain_group = QGroupBox("Terrain Configuration")
        terrain_layout = QGridLayout() # Usar grid layout para los elementos del terreno

        # Tipo de terreno (ComboBox)
        terrain_layout.addWidget(QLabel("Type:"), 0, 0)
        self.terrain_combo = QComboBox()
        self.terrain_combo.addItems([
            "valley",
            "hills",
            "forest_map",
            "rivers_and_lakes",
            # Agrega los nombres de otros presets de terreno que hayas implementado en Terrain.create_preset aquí
            # "arabia",
            # "black_forest",
            # "team_islands",
        ])
        # No conectar la señal aquí, se hace en connect_signals()
        terrain_layout.addWidget(self.terrain_combo, 0, 1)

        # Radio de contacto (Slider con etiqueta de valor)
        terrain_layout.addWidget(QLabel("Contact Radius:"), 1, 0)
        self.contact_slider = QSlider(Qt.Horizontal)
        self.contact_slider.setRange(5, 30) # Rango de 0.5 a 3.0
        self.contact_slider.setValue(10)    # Valor por defecto 1.0
        self.contact_slider.setSingleStep(1) # Incrementos de 0.1
        # No conectar la señal aquí
        self.contact_value_label = QLabel("1.0") # Etiqueta para mostrar el valor del slider
        terrain_layout.addWidget(self.contact_slider, 1, 1)
        terrain_layout.addWidget(self.contact_value_label, 1, 2)

        terrain_group.setLayout(terrain_layout) # Asignar el layout al grupo del terreno
        layout.addWidget(terrain_group) # Añadir el grupo del terreno al layout principal

        # Grupos de configuración de los equipos
        self.team_configs = {} # Diccionario para almacenar los widgets de configuración de equipo
        for team_id in [1, 2]: # Para cada equipo (1 y 2)
            team_config = TeamConfig(team_id) # Crear una instancia de TeamConfig
            self.team_configs[team_id] = team_config # Almacenarla en el diccionario
            # No conectar señales de TeamConfig aquí, se hace en connect_signals()
            layout.addWidget(team_config) # Añadir el grupo de configuración del equipo al layout principal

        # Grupo de configuración de la velocidad de simulación
        speed_group = QGroupBox("Simulation Speed")
        speed_layout = QHBoxLayout() # Layout horizontal para slider y etiqueta

        # Slider de velocidad de simulación
        speed_layout.addWidget(QLabel("Speed:"))
        self.speed_slider = QSlider(Qt.Horizontal)
        self.speed_slider.setRange(1, 100) # Rango del slider (inverso a la velocidad real)
        self.speed_slider.setValue(50) # Valor por defecto (corresponde a 0.050s)
        self.speed_slider.setSingleStep(1) # Incrementos
        # No conectar la señal aquí
        self.speed_value_label = QLabel("0.050s") # Etiqueta para mostrar el valor en segundos
        speed_layout.addWidget(self.speed_slider) # Añadir slider al layout de velocidad
        speed_layout.addWidget(self.speed_value_label) # Añadir etiqueta al layout de velocidad

        speed_group.setLayout(speed_layout) # Asignar layout al grupo de velocidad
        layout.addWidget(speed_group) # Añadir grupo de velocidad al layout principal

        # Layout para los botones de control
        buttons_layout = QGridLayout() # Usar grid layout para organizar los botones

        # Botones de control
        start_button = QPushButton("Start")
        start_button.setStyleSheet("background-color: #4CAF50; color: white; padding: 8px;") # Estilo verde
        start_button.clicked.connect(lambda: self.simulation_control.emit("start")) # Conectar click a señal
        buttons_layout.addWidget(start_button, 0, 0) # Añadir botón al grid

        pause_button = QPushButton("Pause")
        pause_button.setStyleSheet("background-color: #FF9800; color: white; padding: 8px;") # Estilo naranja
        pause_button.clicked.connect(lambda: self.simulation_control.emit("pause"))
        buttons_layout.addWidget(pause_button, 0, 1)

        reset_button = QPushButton("Reset")
        reset_button.setStyleSheet("background-color: #f44336; color: white; padding: 8px;") # Estilo rojo
        reset_button.clicked.connect(lambda: self.simulation_control.emit("reset"))
        buttons_layout.addWidget(reset_button, 1, 0)

        end_button = QPushButton("End Simulation")
        end_button.setStyleSheet("background-color: #B71C1C; color: white; padding: 8px;") # Estilo rojo oscuro
        end_button.clicked.connect(lambda: self.simulation_control.emit("end"))
        buttons_layout.addWidget(end_button, 1, 1)

        layout.addLayout(buttons_layout) # Añadir el layout de botones al layout principal

        # Etiqueta de estado de la simulación
        self.status_label = QLabel("Ready") # Etiqueta para mostrar el estado
        self.status_label.setStyleSheet("font-style: italic; text-align: center;") # Estilo cursiva
        self.status_label.setAlignment(Qt.AlignCenter) # Centrar el texto de estado
        layout.addWidget(self.status_label) # Añadir etiqueta al layout principal

        layout.addStretch(1) # Añadir un stretch al final para empujar los widgets hacia arriba

        self.setLayout(layout) # Establecer el layout principal para el widget

    def connect_signals(self):
        """Connect signals from UI elements to the on_params_changed slot."""
        # Conectar señales de los widgets principales (terreno, velocidad)
        self.terrain_combo.currentTextChanged.connect(self.on_params_changed)
        self.contact_slider.valueChanged.connect(self.on_params_changed)
        self.speed_slider.valueChanged.connect(self.on_params_changed)

        # Conectar señales de los TeamConfig widgets (SpinBoxes y ComboBox de Behavior)
        for team_id, config_widget in self.team_configs.items():
            config_widget.units_spin.valueChanged.connect(self.on_params_changed)
            config_widget.speed_spin.valueChanged.connect(self.on_params_changed)
            config_widget.health_spin.valueChanged.connect(self.on_params_changed)
            config_widget.behavior_combo.currentTextChanged.connect(self.on_params_changed)

    def get_current_params(self) -> dict:
        """Retrieve the current parameters from the UI elements."""
        # Obtener el valor del slider de Contact Radius y actualizar la etiqueta.
        contact_radius = self.contact_slider.value() / 10.0
        self.contact_value_label.setText(f"{contact_radius:.1f}")

        # Obtener el valor del slider de Simulation Speed y actualizar la etiqueta.
        # La velocidad es inversamente proporcional al valor del slider.
        # Slider 1 -> 0.100s, Slider 100 -> 0.001s
        # (101 - valor_slider) / 1000.0
        speed = (101 - self.speed_slider.value()) / 1000.0
        self.speed_value_label.setText(f"{speed:.3f}s")

        # Construir el diccionario de parámetros
        params = {
            'terrain_preset': self.terrain_combo.currentText(),
            'contact_radius': contact_radius,
            'simulation_speed': speed,
            'teams': {
                team_id: config.get_config() # Llamar a get_config() de cada TeamConfig
                for team_id, config in self.team_configs.items()
            }
        }
        return params

    def on_params_changed(self):
        """Slot to handle changes in UI parameters. Emits params_changed signal."""
        self.current_params = self.get_current_params() # Obtener los parámetros actualizados
        self.params_changed.emit(self.current_params) # Emitir la señal con los nuevos parámetros

    def update_status(self, status: str):
        """Update the status label text."""
        self.status_label.setText(status)