import pygame
import numpy as np
from battle import Battle
from terrain import Terrain, TerrainType
from typing import Dict, Tuple

class Visualizer:
    def __init__(self, width: int, height: int, cell_size: int = 10):
        """
        Initializes the visualizer. Assumes pygame.init() has been called BEFOREHAND.
        """
        self.cell_size = cell_size
        self.grid_width = width
        self.grid_height = height
        self.width = self.grid_width * self.cell_size
        self.height = self.grid_height * self.cell_size

        try:
            self.screen = pygame.display.set_mode((self.width + 200, self.height))
            pygame.display.set_caption("War Simulator - Cellular Automaton")
        except pygame.error as e:
            print(f"Error initializing Pygame display: {e}")
            if pygame.get_init():
                 pygame.quit()
            raise

        self.colors = {
            'terrain_types': {
                TerrainType.GRASS: pygame.Color(124, 252, 0),
                TerrainType.WATER: pygame.Color(0, 191, 255),
                TerrainType.FOREST: pygame.Color(34, 139, 34),
                TerrainType.SAND: pygame.Color(245, 222, 179),
                TerrainType.MOUNTAIN: pygame.Color(139, 69, 19),
            },
            'variation': {
                'height_shade_factor': 0.25,
                'density_factor': 0.4
            },
            'units': {
                1: pygame.Color(255, 0, 0),    # Team 1 (Red)
                2: pygame.Color(0, 0, 255)     # Team 2 (Blue)
            },
            'territory': {
                1: pygame.Color(255, 150, 150),
                2: pygame.Color(150, 150, 255)
            }
        }
        pygame.font.init()
        self.font = pygame.font.SysFont(None, 24)

    def draw_terrain(self, terrain: Terrain) -> None:
        """Draw terrain features."""
        terrain_type_map = terrain.get_terrain_type_map()
        
        for y in range(terrain.height):
            for x in range(terrain.width):
                rect = pygame.Rect(
                    x * self.cell_size,
                    y * self.cell_size,
                    self.cell_size,
                    self.cell_size
                )
                
                terrain_type = terrain_type_map[y, x]
                base_color = self.colors['terrain_types'].get(terrain_type, self.colors['terrain_types'][TerrainType.GRASS])
                
                # Simplified rendering for CA speed: just base color + height shade
                height_value = terrain.height_map[y, x]
                shade_factor = height_value * self.colors['variation']['height_shade_factor']
                shaded_color = (
                    int(base_color[0] * (1 - shade_factor)),
                    int(base_color[1] * (1 - shade_factor)),
                    int(base_color[2] * (1 - shade_factor))
                )
                final_terrain_color = tuple(max(0, min(255, c)) for c in shaded_color)
                
                pygame.draw.rect(self.screen, final_terrain_color, rect)

    def draw_units(self, battle: Battle) -> None:
        """Draw all units in the battle from the grid."""
        # Iterate over the grid to find occupied cells
        # Since grid is numpy array, iterating by index is okay, 
        # or we could use np.argwhere for potentially faster sparse iteration if grid is sparse.
        # maintaining loop for simplicity and consistency with terrain drawing.
        for y in range(battle.height):
            for x in range(battle.width):
                team_id = battle.grid[y, x]
                if team_id > 0:
                    # Draw unit as a filled rectangle or circle in the cell
                    color = self.colors['units'].get(team_id, (255, 255, 255))
                    
                    # Calculate pixel position
                    px = x * self.cell_size
                    py = y * self.cell_size
                    
                    # Draw distinct shape for units
                    # Using a slightly smaller rect to show grid lines if needed
                    unit_rect = pygame.Rect(
                        px + 1, py + 1, 
                        self.cell_size - 2, self.cell_size - 2
                    )
                    pygame.draw.rect(self.screen, color, unit_rect)

    def draw_stats_panel(self, battle: Battle) -> None:
        """Draw detailed statistics panel."""
        stats = battle.get_battle_stats()
        panel_rect = pygame.Rect(self.width, 0, 200, self.height)
        pygame.draw.rect(self.screen, (50, 50, 50), panel_rect)

        y_pos = 10
        padding = 20

        self._draw_text(f"Step: {stats.get('step', 0)}", (self.width + 10, y_pos), color=(255, 255, 255))
        y_pos += padding
        
        pygame.draw.line(self.screen, (100, 100, 100), (self.width + 10, y_pos), (self.width + 190, y_pos))
        y_pos += padding

        for team_id in [1, 2]:
            team_color = self.colors['units'].get(team_id, (200, 200, 200))
            if isinstance(team_color, pygame.Color):
                 team_color = (team_color.r, team_color.g, team_color.b)

            self._draw_text(f"Team {team_id}", (self.width + 10, y_pos), color=team_color)
            y_pos += padding
            
            units_count = stats.get('units_remaining', {}).get(team_id, 0)
            self._draw_text(f"Live Cells: {units_count}", (self.width + 20, y_pos))
            y_pos += padding

            territory = stats.get('territory_control', {}).get(team_id, 0.0)
            self._draw_text(f"Coverage: {territory:.1f}%", (self.width + 20, y_pos))
            y_pos += padding * 1.5

    def _draw_text(self, text: str, position: Tuple[int, int], color=(200, 200, 200)):
        if not pygame.font.get_init():
             pygame.font.init()
             self.font = pygame.font.SysFont(None, 24)
        text_surface = self.font.render(text, True, color)
        self.screen.blit(text_surface, position)

    def update(self, battle: Battle) -> bool:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False

        if self.screen is None:
             return True

        self.screen.fill((0, 0, 0))
        self.draw_terrain(battle.terrain)
        self.draw_units(battle)
        self.draw_stats_panel(battle)
        pygame.display.flip()
        return True

    def quit_pygame(self):
        if pygame.get_init():
             pygame.quit()
             self.screen = None

    def reset_display(self, width: int, height: int, cell_size: int):
        self.grid_width = width
        self.grid_height = height
        self.cell_size = cell_size
        self.width = self.grid_width * self.cell_size
        self.height = self.grid_height * self.cell_size

        try:
            self.screen = pygame.display.set_mode((self.width + 200, self.height))
            pygame.display.set_caption("War Simulator - Cellular Automaton")
        except pygame.error:
            pass