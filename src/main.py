import sys
import time
import random
import yaml
import numpy as np
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer
import pygame

from terrain import Terrain
from unit import Unit
from battle import Battle
from visualizer import Visualizer
from control_panel import ControlPanel

class WarSimulator:
    def __init__(self):
        self.load_config()
        self.visualizer = None
        self.init_simulation()
        self.running = False
        self.timer = QTimer()
        self.timer.timeout.connect(self.simulation_step)
        self.control_panel = None

    def load_config(self, config_path: str = 'config.yaml'):
        try:
            with open(config_path, 'r') as f:
                self.config = yaml.safe_load(f)
        except Exception as e:
            print(f"Error loading config: {e}")
            sys.exit(1)

    def init_simulation(self):
        """Initialize or reset the simulation state."""
        grid_size = self.config.get('simulation', {}).get('grid_size', 50)
        terrain_preset = self.config.get('terrain', {}).get('preset', 'valley')

        # Create Terrain
        self.terrain = Terrain.create_preset(terrain_preset, grid_size, grid_size)

        # Create Battle (Populates grid based on config)
        self.battle = Battle(self.terrain, self.config)

        # Create/Reset Visualizer
        cell_size = self.config.get('simulation', {}).get('cell_size', 12)
        if self.visualizer:
            self.visualizer.reset_display(grid_size, grid_size, cell_size)
        else:
            self.visualizer = Visualizer(grid_size, grid_size, cell_size=cell_size)

        if hasattr(self, 'control_panel') and self.control_panel:
             self.control_panel.update_status("Ready")

    def simulation_step(self):
        """Execute one step of the simulation."""
        if not self.running:
            return

        # Execute Battle Step (CA Logic)
        battle_stats = self.battle.step()

        # Update Visualization
        if not self.visualizer.update(self.battle):
            self.stop_simulation()
            if self.control_panel:
                 self.control_panel.update_status("Ended (Window Closed)")
            return

        # Check Victory Conditions
        winners = []
        
        # 1. Conquest Victory
        conquest_threshold = self.config.get('victory', {}).get('conquest_percentage', 70.0)
        for team_id, percentage in battle_stats['territory_control'].items():
            if percentage >= conquest_threshold:
                winners.append(f"Team {team_id} (Conquest)")

        # 2. Annihilation Victory (No units left for enemy)
        active_teams = [tid for tid, count in battle_stats['units_remaining'].items() if count > 0]
        if len(active_teams) == 1:
            winners.append(f"Team {active_teams[0]} (Annihilation)")
        elif len(active_teams) == 0:
            winners.append("Draw (Mutual Annihilation)")

        if winners:
            self.stop_simulation()
            win_msg = f"Winner: {', '.join(winners)}"
            print(f"\n--- {win_msg} ---")
            if self.control_panel:
                self.control_panel.update_status(win_msg)

    def update_params(self, params: dict):
        """Update simulation parameters from control panel."""
        # Update internal config
        sim_config = self.config.get('simulation', {})
        sim_config['grid_size'] = params.get('grid_size', sim_config.get('grid_size', 50))
        sim_config['cell_size'] = params.get('cell_size', sim_config.get('cell_size', 12))
        sim_config['simulation_speed'] = params.get('simulation_speed', 0.1)
        
        self.config['terrain']['preset'] = params.get('terrain_preset', 'valley')
        
        # Update teams config
        teams_params = params.get('teams', {})
        for team_id, t_params in teams_params.items():
            if team_id in self.config['teams']:
                # Note: 'units' param from panel acts as simple scalar, 
                # but for CA we use density. We can map 'units' (1-500) to density roughly?
                # Or just ignore it if panel isn't updated.
                # Let's map units count (approx) to density for now to keep panel working.
                # Assuming 50x50=2500 cells. 500 units = 20%.
                desired_units = t_params.get('units', 50)
                grid_cells = sim_config['grid_size'] ** 2
                density = min(1.0, desired_units / grid_cells) if grid_cells > 0 else 0.1
                self.config['teams'][team_id]['initial_pop_percent'] = density

        self.timer.setInterval(int(sim_config['simulation_speed'] * 1000))
        self.reset_simulation()

    def handle_control(self, command: str):
        cp = self.control_panel
        if command == "start":
            self.start_simulation()
            if cp: cp.update_status("Running")
        elif command == "pause":
            self.pause_simulation()
            if cp: cp.update_status("Paused")
        elif command == "reset":
            self.reset_simulation()
        elif command == "end":
            self.end_simulation()

    def start_simulation(self):
        if not self.running:
            self.running = True
            if self.visualizer is None:
                 self.init_simulation()
            self.timer.start(int(self.config['simulation']['simulation_speed'] * 1000))

    def pause_simulation(self):
        if self.running:
            self.running = False
            self.timer.stop()

    def stop_simulation(self):
        self.running = False
        self.timer.stop()

    def reset_simulation(self):
        self.stop_simulation()
        self.init_simulation()

    def end_simulation(self):
        self.stop_simulation()
        if self.visualizer:
             self.visualizer.quit_pygame()
        if self.control_panel:
             self.control_panel.close()
        QApplication.quit()

def main():
    pygame.init()
    app = QApplication(sys.argv)
    
    simulator = WarSimulator()
    
    control_panel = ControlPanel()
    control_panel.show()
    simulator.control_panel = control_panel
    
    control_panel.params_changed.connect(simulator.update_params)
    control_panel.simulation_control.connect(simulator.handle_control)
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()