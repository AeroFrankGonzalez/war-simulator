# main.py

import sys
import time
import random
import yaml
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer
from terrain import Terrain, TerrainType # Asegúrate de que esta importación sea correcta
from unit import Unit
from battle import Battle
from visualizer import Visualizer # Asegúrate de que esta importación sea correcta
from control_panel import ControlPanel # Asegúrate de que esta importación sea correcta

class WarSimulator:
    def __init__(self):
        self.load_config()
        self.init_simulation()
        self.running = False
        self.timer = QTimer()
        self.timer.timeout.connect(self.simulation_step)

    def load_config(self, config_path: str = 'config.yaml'):
        """Load initial configuration from YAML file"""
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)

    def init_simulation(self):
        """Initialize or reset the simulation"""
        self.terrain = Terrain.create_preset(
            self.config['terrain']['preset'],
            self.config['simulation']['grid_size'],
            self.config['simulation']['grid_size']
        )

        self.battle = Battle(self.terrain, contact_radius=self.config['terrain']['contact_radius'])
        self.visualizer = Visualizer(
            self.config['simulation']['grid_size'],
            self.config['simulation']['grid_size'],
            cell_size=self.config['simulation']['cell_size']
        )

        # Create initial units
        self.create_teams()

    def create_teams(self):
        """Create teams with current configuration"""
        # Limpiar unidades existentes antes de crear nuevas (para reset)
        self.battle.units = {}

        for team_id in [1, 2]:
            team_config = self.config['teams'].get(team_id, {
                'units': 20,
                'speed': 1.0,
                'health': 5
            })

            units = self.create_random_units(
                team_config['units'],
                team_id,
                team_config['speed'],
                team_config['health']
            )

            for unit in units:
                battle_width = self.config['simulation']['grid_size']
                # Consider if starting positions need to avoid impassable terrain on new maps
                # For now, random placement in halves is kept.
                if team_id == 1:
                    # Team 1 starts on the left side
                    x = random.uniform(0, battle_width * 0.3)
                else:
                    # Team 2 starts on the right side
                    x = random.uniform(battle_width * 0.7, battle_width)
                y = random.uniform(0, self.terrain.height)
                unit.position = (x, y)
                self.battle.add_unit(unit)

    def create_random_units(self, num_units: int, team_id: int, speed: float, health: int) -> list[Unit]:
        """Create random units for a team with specific configurations"""
        units = []
        for _ in range(num_units):
            unit = Unit(
                team_id=team_id,
                position=(0, 0),  # Position will be set in create_teams
                health=health,
                movement_speed=speed,
                # --- INICIO DEL CAMBIO ---
                # Opcional: Asignar un target inicial al crear la unidad
                # Esto evita el error si la probabilidad de cambio de target es baja al inicio
                # Puedes ajustar el rango del target inicial si lo deseas
                target=(
                     random.uniform(self.terrain.width * (0.6 if team_id == 1 else 0.0), self.terrain.width * (1.0 if team_id == 1 else 0.4)),
                     random.uniform(0, self.terrain.height)
                )
                # --- FIN DEL CAMBIO ---
            )
            units.append(unit)
        return units


    def simulation_step(self):
        """Execute one step of the simulation"""
        if not self.running:
            return

        # Update unit targets
        terrain_bounds = (self.terrain.width, self.terrain.height)
        for team_units in self.battle.units.values():
            # Create a copy to allow target changes during iteration
            team_units_copy = list(team_units)
            for unit in team_units_copy:
                # Check if unit is still alive before processing
                if unit.health > 0:
                    if random.random() < self.config['units']['target_change_probability']:
                        # Target enemy territory
                        if unit.team_id == 1:
                            # Team 1 targets right side
                            target_x = random.uniform(
                                self.terrain.width * 0.6,
                                self.terrain.width
                            )
                        else:
                            # Team 2 targets left side
                            target_x = random.uniform(
                                0,
                                self.terrain.width * 0.4
                            )
                        target_y = random.uniform(0, self.terrain.height)
                        unit.target = (target_x, target_y)

                    # --- INICIO DEL CAMBIO ---
                    # Mover la unidad solo si tiene un target asignado
                    if unit.target:
                        x, y = int(unit.position[0]), int(unit.position[1])
                        terrain_mod = self.terrain.get_movement_modifier(x, y)
                        unit.move(unit.target, terrain_mod, terrain_bounds)
                    # --- FIN DEL CAMBIO ---


        # Execute simulation step
        battle_stats = self.battle.step()

        # Update visualization
        # Pass the battle object to the visualizer update method
        if not self.visualizer.update(self.battle):
            self.stop_simulation()
            # Update status label in control panel before exiting
            if hasattr(self, 'control_panel') and self.control_panel:
                 self.control_panel.update_status("Simulation Ended (Window Closed)")
            return

        # Check win conditions
        remaining_teams = [team_id for team_id, units in self.battle.units.items() if units]
        if len(remaining_teams) <= 1:
            self.stop_simulation()
            # Update status label in control panel
            win_message = ""
            if remaining_teams:
                winner_team_id = remaining_teams[0]
                win_message = f"Team {winner_team_id} wins!"
                print(win_message)
                print(f"Territory control: {battle_stats['territory_control'].get(winner_team_id, 0):.1f}%")
                print(f"Total kills: {battle_stats['total_kills'].get(winner_team_id, 0)}")
            else:
                win_message = "Draw - all units destroyed!"
                print(win_message)

            if hasattr(self, 'control_panel') and self.control_panel:
                 self.control_panel.update_status(win_message)


    def update_params(self, params: dict):
        """Update simulation parameters from control panel"""
        self.config['terrain']['preset'] = params['terrain_preset']
        self.config['terrain']['contact_radius'] = params['contact_radius']
        self.config['simulation']['simulation_speed'] = params['simulation_speed']
        self.config['teams'] = params['teams']

        # Update timer interval
        self.timer.setInterval(int(params['simulation_speed'] * 1000))
        # If terrain preset changed, re-initialize simulation
        # This is a simple way to handle terrain changes from the UI
        # A more complex approach might involve dynamically updating the existing terrain
        self.reset_simulation() # Reset simulation on parameter change for simplicity


    def handle_control(self, command: str):
        """Handle control commands from the panel"""
        if hasattr(self, 'control_panel') and self.control_panel:
            if command == "start":
                self.start_simulation()
                self.control_panel.update_status("Running")
            elif command == "pause":
                self.pause_simulation()
                self.control_panel.update_status("Paused")
            elif command == "reset":
                self.reset_simulation()
                self.control_panel.update_status("Ready")
            elif command == "end":
                self.end_simulation()


    def start_simulation(self):
        """Start or resume the simulation"""
        if not self.running:
            self.running = True
            self.timer.start(int(self.config['simulation']['simulation_speed'] * 1000))

    def pause_simulation(self):
        """Pause the simulation"""
        if self.running:
            self.running = False
            self.timer.stop()

    def stop_simulation(self):
        """Stop the simulation completely"""
        self.running = False
        self.timer.stop()
        # Ensure Pygame window is closed when simulation stops explicitly
        if hasattr(self, 'visualizer') and self.visualizer:
            self.visualizer.quit_pygame()


    def reset_simulation(self):
        """Reset the simulation to initial state"""
        self.stop_simulation()
        self.init_simulation()
        # Reset visualizer as well
        if hasattr(self, 'visualizer') and self.visualizer:
             self.visualizer.reset_display(self.terrain.width, self.terrain.height, self.config['simulation']['cell_size'])


    def end_simulation(self):
        """End the simulation and close the application"""
        self.stop_simulation()
        # Ensure the control panel is closed as well
        if hasattr(self, 'control_panel') and self.control_panel:
             self.control_panel.close()
        QApplication.quit()

def main():
    app = QApplication(sys.argv)

    # Create simulator first
    simulator = WarSimulator()

    # Create and show control panel
    control_panel = ControlPanel()
    control_panel.show()
    # Store a reference to the control panel in the simulator
    simulator.control_panel = control_panel

    # Connect control panel signals
    control_panel.params_changed.connect(simulator.update_params)
    control_panel.simulation_control.connect(simulator.handle_control)

    # The simulation will start when the user clicks 'Start' or when init_simulation is called
    # Let's keep the initial start call here for immediate simulation on launch
    simulator.start_simulation()

    sys.exit(app.exec_())

if __name__ == "__main__":
    main()