import pygame
import numpy as np
from battle import Battle
from terrain import Terrain
from typing import Dict, Tuple

class Visualizer:
    def __init__(self, width: int, height: int, cell_size: int = 10):
        pygame.init()
        self.cell_size = cell_size
        self.width = width * cell_size
        self.height = height * cell_size
        self.screen = pygame.display.set_mode((self.width + 200, self.height))  # Added 200px for stats panel
        pygame.display.set_caption("War Simulator")
        
        # Color definitions
        self.colors = {
            'terrain': {
                'height': pygame.Color(100, 100, 100),
                'density': pygame.Color(0, 100, 0)
            },
            'units': {
                1: pygame.Color(255, 0, 0),    # Team 1 (Red)
                2: pygame.Color(0, 0, 255)     # Team 2 (Blue)
            },
            'territory': {
                1: pygame.Color(255, 200, 200),  # Light red
                2: pygame.Color(200, 200, 255)   # Light blue
            },
            'control': {
                1: pygame.Color(255, 100, 100),  # Medium red
                2: pygame.Color(100, 100, 255)   # Medium blue
            }
        }

    def draw_terrain(self, terrain: Terrain) -> None:
        """Draw terrain features including height, density, and territory control"""
        for y in range(terrain.height):
            for x in range(terrain.width):
                rect = pygame.Rect(
                    x * self.cell_size,
                    y * self.cell_size,
                    self.cell_size,
                    self.cell_size
                )
                
                # Draw base terrain (height)
                height_value = int(terrain.height_map[y, x] * 255)
                base_color = (height_value, height_value, height_value)
                pygame.draw.rect(self.screen, base_color, rect)
                
                # Draw density (vegetation)
                if terrain.density_map[y, x] > 0:
                    density_surface = pygame.Surface((self.cell_size, self.cell_size))
                    density_surface.fill(self.colors['terrain']['density'])
                    density_surface.set_alpha(int(terrain.density_map[y, x] * 128))
                    self.screen.blit(density_surface, rect)

                # Draw territory control and progress
                control_team = terrain.conquest_map[y, x]
                if control_team > 0:
                    territory_surface = pygame.Surface((self.cell_size, self.cell_size))
                    territory_surface.fill(self.colors['territory'][control_team])
                    territory_surface.set_alpha(int(terrain.conquest_progress[y, x] * 128))
                    self.screen.blit(territory_surface, rect)
                
                # Draw current control points
                current_control = terrain.control_points[y, x]
                if current_control > 0:
                    control_surface = pygame.Surface((self.cell_size, self.cell_size))
                    control_surface.fill(self.colors['control'][current_control])
                    control_surface.set_alpha(64)  # Light indicator of current control
                    self.screen.blit(control_surface, rect)

    def draw_units(self, battle: Battle) -> None:
        """Draw all units in the battle"""
        for team_id, units in battle.units.items():
            color = self.colors['units'][team_id]
            for unit in units:
                x = int(unit.position[0] * self.cell_size)
                y = int(unit.position[1] * self.cell_size)
                
                # Draw unit body
                pygame.draw.circle(self.screen, color, (x, y), self.cell_size // 2)
                
                # Draw health bar
                health_width = (self.cell_size * unit.health) // 5  # 5 is max health
                health_height = 2
                health_rect = pygame.Rect(
                    x - self.cell_size//2,
                    y - self.cell_size//2 - 4,
                    health_width,
                    health_height
                )
                health_color = (0, 255, 0) if unit.health > 2 else (255, 165, 0) if unit.health > 1 else (255, 0, 0)
                pygame.draw.rect(self.screen, health_color, health_rect)

    def draw_stats_panel(self, battle: Battle) -> None:
        """Draw detailed statistics panel"""
        stats = battle.get_battle_stats()
        panel_rect = pygame.Rect(self.width, 0, 200, self.height)
        pygame.draw.rect(self.screen, (50, 50, 50), panel_rect)
        
        font = pygame.font.SysFont(None, 24)
        y_pos = 10
        padding = 20
        
        # Draw simulation step
        self._draw_text(f"Step: {stats['step']}", (self.width + 10, y_pos), color=(255, 255, 255))
        y_pos += padding

        # Draw separator
        pygame.draw.line(self.screen, (100, 100, 100), 
                        (self.width + 10, y_pos), 
                        (self.width + 190, y_pos))
        y_pos += padding

        # Draw team statistics
        for team_id in [1, 2]:
            team_color = self.colors['units'][team_id]
            
            # Units
            self._draw_text(f"Team {team_id}", (self.width + 10, y_pos), color=team_color)
            y_pos += padding
            units_remaining = stats['units_remaining'].get(team_id, 0)
            self._draw_text(f"Units: {units_remaining}", (self.width + 20, y_pos))
            y_pos += padding

            # Territory
            territory = stats['territory_control'].get(team_id, 0)
            self._draw_text(f"Territory: {territory:.1f}%", (self.width + 20, y_pos))
            y_pos += padding

            # Kills/Losses
            kills = stats['total_kills'].get(team_id, 0)
            losses = stats['casualties'].get(team_id, 0)
            self._draw_text(f"Kills: {kills}", (self.width + 20, y_pos))
            y_pos += padding
            self._draw_text(f"Losses: {losses}", (self.width + 20, y_pos))
            y_pos += padding * 1.5

    def _draw_text(self, text: str, position: Tuple[int, int], color=(200, 200, 200)):
        """Helper method to draw text"""
        font = pygame.font.SysFont(None, 24)
        text_surface = font.render(text, True, color)
        self.screen.blit(text_surface, position)

    def update(self, battle: Battle) -> bool:
        """Update the display. Returns False if the window was closed."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return False

        self.screen.fill((0, 0, 0))  # Clear screen
        self.draw_terrain(battle.terrain)
        self.draw_units(battle)
        self.draw_stats_panel(battle)
        pygame.display.flip()
        return True