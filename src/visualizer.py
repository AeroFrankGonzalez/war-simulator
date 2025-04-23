# visualizer.py

import pygame
import numpy as np
from battle import Battle
from terrain import Terrain, TerrainType # Importa TerrainType
from typing import Dict, Tuple

class Visualizer:
    def __init__(self, width: int, height: int, cell_size: int = 10):
        pygame.init()
        self.cell_size = cell_size
        self.grid_width = width # Store grid dimensions
        self.grid_height = height
        self.width = self.grid_width * self.cell_size
        self.height = self.grid_height * self.cell_size
        self.screen = pygame.display.set_mode((self.width + 200, self.height))  # Added 200px for stats panel
        pygame.display.set_caption("War Simulator")
        
        # Color definitions
        self.colors = {
            # --- INICIO DEL CAMBIO ---
            # Colores para los tipos de terreno
            'terrain_types': {
                TerrainType.GRASS: pygame.Color(124, 252, 0),   # Lawn Green
                TerrainType.WATER: pygame.Color(0, 191, 255),   # Deep Sky Blue
                TerrainType.FOREST: pygame.Color(34, 139, 34), # Forest Green
                TerrainType.SAND: pygame.Color(245, 222, 179),  # Wheat
                TerrainType.MOUNTAIN: pygame.Color(139, 69, 19), # Saddle Brown
                # Añade colores para otros tipos de terreno aquí
            },
            # Puedes mantener colores para añadir variación por altura/densidad
            'variation': {
                'height_darken_factor': 0.5, # Cuánto oscurecer por altura (0 a 1)
                'density_green_factor': 0.5  # Cuánto añadir de verde por densidad (0 a 1)
            },
            # --- FIN DEL CAMBIO ---
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
        # Inicializar fuente para el panel de estadísticas
        pygame.font.init()
        self.font = pygame.font.SysFont(None, 24)


    def draw_terrain(self, terrain: Terrain) -> None:
        """Draw terrain features including type, height, density, and territory control"""
        terrain_type_map = terrain.get_terrain_type_map() # Obtén el mapa de tipos de terreno

        for y in range(terrain.height):
            for x in range(terrain.width):
                rect = pygame.Rect(
                    x * self.cell_size,
                    y * self.cell_size,
                    self.cell_size,
                    self.cell_size
                )

                # --- INICIO DEL CAMBIO ---
                # Dibujar color base según el tipo de terreno
                terrain_type = terrain_type_map[y, x]
                # Usa un color por defecto si el tipo de terreno no está en el diccionario
                base_color = self.colors['terrain_types'].get(terrain_type, self.colors['terrain_types'][TerrainType.GRASS])
                
                # Aplica variación de color basada en altura
                height_value = terrain.height_map[y, x]
                # Interpolación lineal entre el color base y un color más oscuro (o más claro)
                # Cuanto mayor la altura, más oscuro/claro (ajusta la lógica según prefieras)
                interp_factor = height_value * self.colors['variation']['height_darken_factor']
                color_from_height = (
                    int(base_color[0] * (1 - interp_factor)),
                    int(base_color[1] * (1 - interp_factor)),
                    int(base_color[2] * (1 - interp_factor))
                )
                # Asegura que los valores de color estén dentro del rango 0-255
                color_from_height = tuple(max(0, min(255, c)) for c in color_from_height)

                # Aplica variación de color basada en densidad (ej. añadir un tinte verde para vegetación)
                density_value = terrain.density_map[y, x]
                density_green_amount = int(density_value * self.colors['variation']['density_green_factor'] * 255)
                final_color = (
                    max(0, min(255, color_from_height[0])),
                    max(0, min(255, color_from_height[1] + density_green_amount)), # Añadir verde
                    max(0, min(255, color_from_height[2]))
                )
                # Puedes ajustar cómo se aplica la densidad para diferentes tipos de terreno
                # Por ejemplo, la densidad podría no añadir verde en agua o arena.
                # if terrain_type not in [TerrainType.WATER, TerrainType.SAND]:
                #     final_color = (..., color_from_height[1] + density_green_amount, ...)


                pygame.draw.rect(self.screen, final_color, rect)
                # --- FIN DEL CAMBIO ---


                # Dibujar control de territorio y progreso (sin cambios)
                control_team = terrain.conquest_map[y, x]
                if control_team > 0:
                    territory_surface = pygame.Surface((self.cell_size, self.cell_size))
                    territory_surface.fill(self.colors['territory'][control_team])
                    territory_surface.set_alpha(int(terrain.conquest_progress[y, x] * 128))
                    self.screen.blit(territory_surface, rect)

                # Dibujar puntos de control actuales (sin cambios)
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
                # Asegurarse de que la unidad esté viva para dibujarla
                if unit.health > 0:
                    x = int(unit.position[0] * self.cell_size)
                    y = int(unit.position[1] * self.cell_size)

                    # Draw unit body
                    pygame.draw.circle(self.screen, color, (x, y), self.cell_size // 2)

                    # Draw health bar
                    max_health = 5 # Assuming max health is 5 based on config/unit class default
                    health_width = (self.cell_size * unit.health) // max_health
                    health_height = 2
                    health_rect = pygame.Rect(
                        x - self.cell_size//2,
                        y - self.cell_size//2 - 4,
                        health_width,
                        health_height
                    )
                    # Colores de la barra de vida
                    if unit.health > max_health * 0.6: # > 60%
                         health_color = (0, 255, 0) # Green
                    elif unit.health > max_health * 0.2: # > 20%
                         health_color = (255, 165, 0) # Orange
                    else: # <= 20%
                         health_color = (255, 0, 0) # Red

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
            y_pos += padding * 1.5 # Extra space between teams

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
        self.draw_units(battle)
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
        # Resize the window (requires re-setting the display mode)
        self.screen = pygame.display.set_mode((self.width + 200, self.height))
        pygame.display.set_caption("War Simulator")
        # You might need to re-initialize fonts or other assets if they were linked to the screen