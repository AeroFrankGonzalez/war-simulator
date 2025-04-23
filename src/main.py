import sys
import time
import random
import yaml
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer
from terrain import Terrain
from unit import Unit
from battle import Battle
from visualizer import Visualizer
from control_panel import ControlPanel

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
                movement_speed=speed
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
            for unit in team_units:
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
                
                # Move unit with boundary checking
                if unit.target:
                    x, y = int(unit.position[0]), int(unit.position[1])
                    terrain_mod = self.terrain.get_movement_modifier(x, y)
                    unit.move(unit.target, terrain_mod, terrain_bounds)

        # Execute simulation step
        battle_stats = self.battle.step()
        
        # Update visualization
        if not self.visualizer.update(self.battle):
            self.stop_simulation()
            return
            
        # Check win conditions
        remaining_teams = [team_id for team_id, units in self.battle.units.items() if units]
        if len(remaining_teams) <= 1:
            self.stop_simulation()
            if remaining_teams:
                print(f"Team {remaining_teams[0]} wins!")
                print(f"Territory control: {battle_stats['territory_control']}%")
                print(f"Total kills: {battle_stats['total_kills']}")
            else:
                print("Draw - all units destroyed!")

    def update_params(self, params: dict):
        """Update simulation parameters from control panel"""
        self.config['terrain']['preset'] = params['terrain_preset']
        self.config['terrain']['contact_radius'] = params['contact_radius']
        self.config['simulation']['simulation_speed'] = params['simulation_speed']
        self.config['teams'] = params['teams']
        
        # Update timer interval
        self.timer.setInterval(int(params['simulation_speed'] * 1000))

    def handle_control(self, command: str):
        """Handle control commands from the panel"""
        if command == "start":
            self.start_simulation()
        elif command == "pause":
            self.pause_simulation()
        elif command == "reset":
            self.reset_simulation()
        elif command == "end":
            self.end_simulation()

    def start_simulation(self):
        """Start or resume the simulation"""
        self.running = True
        self.timer.start(int(self.config['simulation']['simulation_speed'] * 1000))

    def pause_simulation(self):
        """Pause the simulation"""
        self.running = False
        self.timer.stop()

    def stop_simulation(self):
        """Stop the simulation completely"""
        self.running = False
        self.timer.stop()

    def reset_simulation(self):
        """Reset the simulation to initial state"""
        self.stop_simulation()
        self.init_simulation()
        
    def end_simulation(self):
        """End the simulation and close the application"""
        self.stop_simulation()
        QApplication.quit()

def main():
    app = QApplication(sys.argv)
    
    # Create simulator first
    simulator = WarSimulator()
    
    # Create and show control panel
    control_panel = ControlPanel()
    control_panel.show()
    
    # Connect control panel signals
    control_panel.params_changed.connect(simulator.update_params)
    control_panel.simulation_control.connect(simulator.handle_control)
    
    # Start the simulation
    simulator.start_simulation()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()