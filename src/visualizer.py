import pygame
import numpy as np
from battle import Battle
from terrain import Terrain
from typing import Dict, Tuple

class Visualizer:
    def __init__(self, width: int, height: int, cell_size: int = 10):
        self.cell_size = cell_size
        self.grid_width = width
        self.grid_height = height
        
        self.width = self.grid_width * self.cell_size
        self.height = self.grid_height * self.cell_size
        
        self.ui_width = 250
        self.total_width = self.width + self.ui_width

        try:
            self.screen = pygame.display.set_mode((self.total_width, self.height))
            pygame.display.set_caption("Neo-Warfare Simulator")
        except pygame.error as e:
            print(f"Error initializing Pygame: {e}")
            raise

        self.colors = {
            'background': (5, 5, 8),
            'grid_lines': (20, 25, 30),
            'ui_bg': (15, 15, 20),
            'text': (200, 220, 230),
            'team1': (0, 255, 200),     # Cyan
            'team2': (255, 0, 100),     # Neon Pink
            'team1_dark': (0, 80, 60),
            'team2_dark': (80, 0, 30),
            # Explicit Territory Colors (Alpha simulated via dark shades)
            't1_territory': (0, 40, 40), # Dark Cyan Background
            't2_territory': (40, 0, 20), # Dark Pink Background
            'contest_zone': (20, 20, 20) # Grey Neutral
        }
        
        pygame.font.init()
        self.font_header = pygame.font.SysFont("Arial", 18, bold=True)
        self.font_body = pygame.font.SysFont("Arial", 14)
        self.font_big = pygame.font.SysFont("Arial", 48, bold=True)
        
        self.ui_elements = []

    def draw_terrain_background(self, battle: Battle):
        self.screen.fill(self.colors['background'])
        
        # Draw Influence Map (Conquest Zones) - VISIBLE BLOCKS
        threshold = 2.0 # Lower threshold for visibility
        
        # Team 1 Territory
        # Draw explicit rects for territory
        # Optimization: Don't draw every single cell if not needed, but grid is small (50x50), so 2500 rects is fine.
        
        y_idxs, x_idxs = np.where(battle.influence > threshold)
        if len(y_idxs) > 0:
            c = self.colors['t1_territory']
            for y, x in zip(y_idxs, x_idxs):
                pygame.draw.rect(self.screen, c, 
                               (x * self.cell_size, y * self.cell_size, self.cell_size, self.cell_size))

        # Team 2 Territory
        y_idxs, x_idxs = np.where(battle.influence < -threshold)
        if len(y_idxs) > 0:
            c = self.colors['t2_territory']
            for y, x in zip(y_idxs, x_idxs):
                pygame.draw.rect(self.screen, c, 
                               (x * self.cell_size, y * self.cell_size, self.cell_size, self.cell_size))

    def draw_units(self, battle: Battle):
        rw, rh = self.cell_size - 1, self.cell_size - 1
        if rw < 1: rw = 1
        if rh < 1: rh = 1
        max_age = 60.0
        
        # Team 1
        y_idxs, x_idxs = np.where(battle.grid == 1)
        if len(y_idxs) > 0:
            ages = battle.ages[y_idxs, x_idxs]
            base_c = np.array(self.colors['team1'])
            dark_c = np.array(self.colors['team1_dark'])
            for y, x, age in zip(y_idxs, x_idxs, ages):
                ratio = min(1.0, age / max_age)
                final_c = base_c * (1 - ratio) + dark_c * ratio
                pygame.draw.rect(self.screen, final_c, (x * self.cell_size + 1, y * self.cell_size + 1, rw-2, rh-2))
            
        # Team 2
        y_idxs, x_idxs = np.where(battle.grid == 2)
        if len(y_idxs) > 0:
            ages = battle.ages[y_idxs, x_idxs]
            base_c = np.array(self.colors['team2'])
            dark_c = np.array(self.colors['team2_dark'])
            for y, x, age in zip(y_idxs, x_idxs, ages):
                ratio = min(1.0, age / max_age)
                final_c = base_c * (1 - ratio) + dark_c * ratio
                pygame.draw.rect(self.screen, final_c, (x * self.cell_size + 1, y * self.cell_size + 1, rw-2, rh-2))

    def draw_ui_panel(self, battle: Battle):
        ui_rect = pygame.Rect(self.width, 0, self.ui_width, self.height)
        pygame.draw.rect(self.screen, self.colors['ui_bg'], ui_rect)
        pygame.draw.line(self.screen, (50, 50, 60), (self.width, 0), (self.width, self.height))

        stats = battle.get_battle_stats()
        
        x_off = self.width + 15
        y_off = 20
        
        self._text("STATUS: OPS NORMAL", x_off, y_off, (100, 255, 100))
        y_off += 30
        
        self._text(f"Gen: {stats['step']}", x_off, y_off)
        y_off += 20
        fps = int(pygame.time.Clock().get_fps()) if 'clock' in globals() else 0
        self._text(f"FPS: {fps}", x_off, y_off)
        y_off += 30
        
        # Scores
        c1_score = stats['conquest_score'][1]
        c2_score = stats['conquest_score'][2]
        
        self._text("CYAN FACTION", x_off, y_off, self.colors['team1'])
        y_off += 20
        self._text(f"Units: {stats['units_remaining'][1]}", x_off + 10, y_off)
        y_off += 20
        self._text(f"Score: {c1_score}", x_off + 10, y_off)
        y_off += 30
        
        self._text("NEON FACTION", x_off, y_off, self.colors['team2'])
        y_off += 20
        self._text(f"Units: {stats['units_remaining'][2]}", x_off + 10, y_off)
        y_off += 20
        self._text(f"Score: {c2_score}", x_off + 10, y_off)
        y_off += 30
        
        # Draw UI Elements
        for element in self.ui_elements:
            element.draw(self.screen)

    def draw_game_over(self, winner: str):
        # Semi-transparent overlay
        s = pygame.Surface((self.width, self.height))
        s.set_alpha(180)
        s.fill((0, 0, 0))
        self.screen.blit(s, (0, 0))
        
        # Text
        text = self.font_big.render(f"{winner} WINS!", True, (255, 215, 0))
        text_rect = text.get_rect(center=(self.width // 2, self.height // 2))
        
        # Glow effect (simple shadow)
        shadow = self.font_big.render(f"{winner} WINS!", True, (100, 50, 0))
        shadow_rect = shadow.get_rect(center=(self.width // 2 + 2, self.height // 2 + 2))
        
        self.screen.blit(shadow, shadow_rect)
        self.screen.blit(text, text_rect)
        
        # Subtitle
        sub = self.font_header.render("Press RESET to play again", True, (200, 200, 200))
        sub_rect = sub.get_rect(center=(self.width // 2, self.height // 2 + 40))
        self.screen.blit(sub, sub_rect)
        
        pygame.display.flip()

    def _text(self, text, x, y, color=None):
        if color is None: color = self.colors['text']
        surf = self.font_body.render(text, True, color)
        self.screen.blit(surf, (x, y))

    def update(self, battle: Battle):
        self.draw_terrain_background(battle)
        self.draw_units(battle)
        self.draw_ui_panel(battle)
        pygame.display.flip()
        return True

    def quit_pygame(self):
        pygame.quit()