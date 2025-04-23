# visualizer.py

import pygame
import numpy as np
from battle import Battle
from terrain import Terrain, TerrainType
from typing import Dict, Tuple

class Visualizer:
    def __init__(self, width: int, height: int, cell_size: int = 10):
        pygame.init()
        self.cell_size = cell_size
        self.grid_width = width
        self.grid_height = height
        self.width = self.grid_width * self.cell_size
        self.height = self.grid_height * self.cell_size
        self.screen = pygame.display.set_mode((self.width + 200, self.height))
        pygame.display.set_caption("War Simulator")

        # Color definitions
        self.colors = {
            'terrain_types': {
                TerrainType.GRASS: pygame.Color(124, 252, 0),   # Lawn Green
                TerrainType.WATER: pygame.Color(0, 191, 255),   # Deep Sky Blue
                TerrainType.FOREST: pygame.Color(34, 139, 34), # Forest Green
                TerrainType.SAND: pygame.Color(245, 222, 179),  # Wheat
                TerrainType.MOUNTAIN: pygame.Color(139, 69, 19), # Saddle Brown
                # Añade colores para otros tipos de terreno aquí
            },
            'variation': {
                # Ajusta estos factores para controlar la influencia de altura y densidad
                'height_shade_factor': 0.25, # Ligeramente más influencia de la altura
                'density_factor': 0.4     # Ligeramente más influencia de la densidad
            },
            'units': {
                1: pygame.Color(255, 0, 0),    # Team 1 (Red)
                2: pygame.Color(0, 0, 255)     # Team 2 (Blue)
            },
            'territory': {
                # Colores más sólidos para el territorio conquistado
                1: pygame.Color(255, 150, 150),  # Medium Light Red
                2: pygame.Color(150, 150, 255)   # Medium Light Blue
            },
            'control': {
                # Indicador sutil de control actual/contienda (usado para el overlay)
                1: pygame.Color(255, 50, 50),  # Red (Alpha will be applied dynamically)
                2: pygame.Color(50, 50, 255)   # Blue (Alpha will be applied dynamically)
            }
        }
        pygame.font.init()
        self.font = pygame.font.SysFont(None, 24)


    def draw_terrain(self, terrain: Terrain) -> None:
        """Draw terrain features including type, height, density, and territory control"""
        terrain_type_map = terrain.get_terrain_type_map()
        conquest_map = terrain.conquest_map
        conquest_progress = terrain.conquest_progress
        control_points = terrain.control_points

        for y in range(terrain.height):
            for x in range(terrain.width):
                rect = pygame.Rect(
                    x * self.cell_size,
                    y * self.cell_size,
                    self.cell_size,
                    self.cell_size
                )

                # --- Draw Base Terrain (with height/density variation) ---
                terrain_type = terrain_type_map[y, x]
                base_color = self.colors['terrain_types'].get(terrain_type, self.colors['terrain_types'][TerrainType.GRASS])

                height_value = terrain.height_map[y, x]
                shade_factor = height_value * self.colors['variation']['height_shade_factor']
                shaded_color = (
                    int(base_color[0] * (1 - shade_factor)),
                    int(base_color[1] * (1 - shade_factor)),
                    int(base_color[2] * (1 - shade_factor))
                )
                shaded_color = tuple(max(0, min(255, c)) for c in shaded_color)

                density_value = terrain.density_map[y, x]
                density_color_effect = (0, 0, 0)
                if terrain_type == TerrainType.FOREST:
                     # Add green tint based on density in forests
                     density_tint = int(density_value * 150 * self.colors['variation']['density_factor'])
                     density_color_effect = (0, density_tint, 0)
                elif terrain_type == TerrainType.MOUNTAIN:
                     # Darken based on density in mountains/rocky areas
                     darken_amount = int(density_value * 80 * self.colors['variation']['density_factor'])
                     density_color_effect = (-darken_amount, -darken_amount, -darken_amount)
                # Add effects for other terrain types if needed (e.g., lighter sand in high density areas?)


                final_terrain_color = (
                     max(0, min(255, shaded_color[0] + density_color_effect[0])),
                     max(0, min(255, shaded_color[1] + density_color_effect[1])),
                     max(0, min(255, shaded_color[2] + density_color_effect[2]))
                )
                pygame.draw.rect(self.screen, final_terrain_color, rect)


                # --- Draw Conquest Status ---
                cell_conquest_map = conquest_map[y, x]
                cell_conquest_progress = conquest_progress[y, x]
                cell_control_points = control_points[y, x] # Team ID currently controlling this cell (from units nearby)


                # Layer 1: Draw the base conquered territory color with high opacity
                # This layer shows who officially controls the cell (from conquest_map)
                if cell_conquest_map > 0:
                    territory_color = self.colors['territory'][cell_conquest_map]
                    territory_surface = pygame.Surface((self.cell_size, self.cell_size), pygame.SRCALPHA)
                    # Use opacity based on progress even for controlled cells to show recent activity/reinforcement
                    # Or keep it mostly solid for controlled territory
                    opacity = 180 # Opacity for officially controlled territory
                    territory_surface.fill((territory_color.r, territory_color.g, territory_color.b, opacity))
                    self.screen.blit(territory_surface, rect)


                # Layer 2: Draw an indicator for active influence/contention (where units are)
                # This layer shows where units are currently asserting control (from control_points)
                if cell_control_points > 0:
                    # Color based on the team currently asserting control
                    control_color = self.colors['control'][cell_control_points] # Use control color (already has alpha defined or apply here)

                    # Determine opacity: Higher where contested, lower where already controlled by same team
                    # Let's make it visible over the base conquest layer
                    opacity = 80 # Base opacity for the control indicator
                    if cell_conquest_map == 0:
                        # Higher opacity on neutral ground being influenced
                         opacity = int(80 + cell_conquest_progress * 100) # More visible as progress increases on neutral
                    elif cell_conquest_map != cell_control_points:
                         # Highest opacity on enemy territory being contested
                         opacity = int(120 + cell_conquest_progress * 100) # Very visible when taking enemy land
                    # If cell_conquest_map == cell_control_points, use base opacity (80)

                    opacity = min(opacity, 255) # Cap opacity at 255

                    control_indicator_surface = pygame.Surface((self.cell_size, self.cell_size), pygame.SRCALPHA)
                    control_indicator_surface.fill((control_color.r, control_color.g, control_color.b, opacity))
                    self.screen.blit(control_indicator_surface, rect)

                # Optional: Draw a border around contested cells for clarity
                # A cell is contested if different teams have control points on it,
                # or if a team has control points on neutral or enemy territory.
                # This requires checking control_points from *both* teams, which
                # isn't directly available per cell in the loop here without pre-calculating.
                # The current control_points map only stores the *last* team to mark control there in a step.
                # A simpler contested indicator could be based on control_points > 0 on neutral/enemy land.
                if cell_control_points > 0 and cell_conquest_map != cell_control_points:
                     border_color = (255, 255, 0) # Yellow border
                     pygame.draw.rect(self.screen, border_color, rect, 1) # Draw a 1px border


    def draw_units(self, battle: Battle) -> None:
        """Draw all units in the battle"""
        # Units are drawn on top of terrain and conquest layers
        for team_id, units in battle.units.items():
            color = self.colors['units'][team_id]
            for unit in units:
                if unit.health > 0:
                    x = int(unit.position[0] * self.cell_size)
                    y = int(unit.position[1] * self.cell_size)

                    # Draw unit body
                    pygame.draw.circle(self.screen, color, (x, y), self.cell_size // 2)

                    # Draw health bar
                    max_health = 5 # Asumimos salud máxima de 5
                    health_width = (self.cell_size * unit.health) // max_health
                    health_height = 2
                    health_rect = pygame.Rect(
                        x - self.cell_size//2,
                        y - self.cell_size//2 - 4,
                        health_width,
                        health_height
                    )
                    if unit.health > max_health * 0.6:
                         health_color = (0, 255, 0)
                    elif unit.health > max_health * 0.2:
                         health_color = (255, 165, 0)
                    else:
                         health_color = (255, 0, 0)

                    pygame.draw.rect(self.screen, health_color, health_rect)


    def draw_stats_panel(self, battle: Battle) -> None:
        """Draw detailed statistics panel"""
        stats = battle.get_battle_stats()
        panel_rect = pygame.Rect(self.width, 0, 200, self.height)
        pygame.draw.rect(self.screen, (50, 50, 50), panel_rect)

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

            # Team Header
            self._draw_text(f"Team {team_id}", (self.width + 10, y_pos), color=team_color)
            y_pos += padding

            # Units
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
        text_surface = self.font.render(text, True, color)
        self.screen.blit(text_surface, position)

    def update(self, battle: Battle) -> bool:
        """Update the display. Returns False if the window was closed."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.quit_pygame()
                return False

        self.screen.fill((0, 0, 0))  # Clear screen
        self.draw_terrain(battle.terrain)
        self.draw_units(battle) # Units are drawn last so they appear on top
        self.draw_stats_panel(battle)
        pygame.display.flip()
        return True

    def quit_pygame(self):
        """Quit pygame."""
        pygame.quit()

    def reset_display(self, width: int, height: int, cell_size: int):
        """Reset or re-initialize the display."""
        self.grid_width = width
        self.grid_height = height
        self.cell_size = cell_size
        self.width = self.grid_width * self.cell_size
        self.height = self.grid_height * self.cell_size
        try:
            self.screen = pygame.display.set_mode((self.width + 200, self.height))
            pygame.display.set_caption("War Simulator")
        except pygame.error as e:
            print(f"Could not set display mode: {e}")
            self.screen = pygame.display.set_mode((200, 200)) # Fallback
            pygame.display.set_caption("Error")