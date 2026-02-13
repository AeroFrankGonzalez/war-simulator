import sys
import yaml
import os
import pygame
from terrain import Terrain
from battle import Battle
from visualizer import Visualizer
from ui import Button, Slider

class Game:
    def __init__(self):
        self.load_config()
        self.init_simulation()
        
        self.paused = True
        self.game_over = False # New State
        self.clock = pygame.time.Clock()
        self.target_fps = 60
        self.update_speed_ms = 100
        self.last_step_time = 0
        
        self.init_ui()

    def load_config(self):
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.yaml')
        with open(path, 'r') as f:
            self.config = yaml.safe_load(f)

    def init_simulation(self):
        self.game_over = False # Reset state
        grid_size = self.config['simulation']['grid_size']
        cell_size = self.config['simulation']['cell_size']
        preset = self.config['terrain']['preset']
        
        self.terrain = Terrain.create_preset(preset, grid_size, grid_size)
        self.battle = Battle(self.terrain, self.config)
        
        if not hasattr(self, 'visualizer'):
            self.visualizer = Visualizer(grid_size, grid_size, cell_size)

    def init_ui(self):
        x_base = self.visualizer.width + 15
        y_base = 300
        w = 220
        h = 30
        gap = 10
        
        self.btn_pause = Button(x_base, y_base, w, h, "START / PAUSE", self.toggle_pause)
        y_base += h + gap
        self.btn_reset = Button(x_base, y_base, w, h, "RESET SIMULATION", self.reset_sim, color=(100, 40, 40))
        y_base += h + gap * 2
        self.slider_speed = Slider(x_base, y_base, w, 20, 10, 1000, 100, "Update Delay (ms)", self.set_speed)
        y_base += 40
        self.slider_d1 = Slider(x_base, y_base, w, 20, 0.05, 0.9, 0.2, "Cyan Density", lambda v: self.set_density(1, v))
        y_base += 40
        self.slider_d2 = Slider(x_base, y_base, w, 20, 0.05, 0.9, 0.2, "Neon Density", lambda v: self.set_density(2, v))
        
        self.visualizer.ui_elements = [self.btn_pause, self.btn_reset, self.slider_speed, self.slider_d1, self.slider_d2]

    def toggle_pause(self):
        self.paused = not self.paused

    def reset_sim(self):
        self.init_simulation()
        self.battle.initialize_grid()
        self.paused = True # Auto-pause on reset to let user see setup? Or keep running. Let's Auto-Pause.

    def set_speed(self, val):
        self.update_speed_ms = int(val)

    def set_density(self, team_id, val):
        self.config['teams'][team_id]['initial_pop_percent'] = val
    
    def run(self):
        running = True
        while running:
            current_time = pygame.time.get_ticks()
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                for element in self.visualizer.ui_elements:
                    element.handle_event(event)

            # Simulation Step
            if not self.paused and not self.game_over:
                if current_time - self.last_step_time > self.update_speed_ms:
                    stats = self.battle.step()
                    self.last_step_time = current_time
                    
                    # VICTORY CHECK (Annihilation)
                    pop1 = stats['units_remaining'][1]
                    pop2 = stats['units_remaining'][2]
                    
                    if pop1 == 0 and pop2 > 0:
                        self.game_over = True
                        self.visualizer.draw_game_over("NEON FACTION")
                    elif pop2 == 0 and pop1 > 0:
                        self.game_over = True
                        self.visualizer.draw_game_over("CYAN FACTION")
                    elif pop1 == 0 and pop2 == 0:
                        self.game_over = True
                        self.visualizer.draw_game_over("DRAW (MUTUAL DEATH)")

            # Render (only if not game over overlay, to preserve distinct state, or render behind?)
            if not self.game_over:
                self.visualizer.update(self.battle)
            else:
                # Just flip to keep the overlay visible and responsive to quit events
                # We do NOT call update which would redraw the frame without the overlay
                # But we might need to handle UI events?
                # Actually, if Game Over, we wait for Reset.
                # So we simply don't update the simulation, but we SHOULD update the screen? 
                # Re-drawing OVERLAY every frame is fine.
                self.visualizer.update(self.battle) # Draw base
                
                # Draw Overlay
                if stats['units_remaining'][1] == 0: win = "NEON"
                else: win = "CYAN"
                if stats['units_remaining'][1] == 0 and stats['units_remaining'][2] == 0: win = "DRAW"
                
                self.visualizer.draw_game_over(win)
            
            self.clock.tick(self.target_fps)
            
        self.visualizer.quit_pygame()
        sys.exit()

if __name__ == "__main__":
    pygame.init()
    game = Game()
    game.run()