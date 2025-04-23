import numpy as np
from typing import Dict, Tuple

class Terrain:
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.height_map = np.zeros((height, width))
        self.density_map = np.zeros((height, width))
        self.conquest_map = np.zeros((height, width), dtype=int)  # 0 = neutral, 1 = team1, 2 = team2
        self.conquest_progress = np.zeros((height, width))  # Progress towards conquest (0-1)
        self.control_points = np.zeros((height, width), dtype=int)  # Current controlling team
        self.last_controlling_team = np.zeros((height, width), dtype=int)  # Track last team that had control

    def set_height(self, x: int, y: int, value: float) -> None:
        """Set height value at position (x,y)"""
        self.height_map[y, x] = max(0.0, min(1.0, value))

    def set_density(self, x: int, y: int, value: float) -> None:
        """Set density value at position (x,y)"""
        self.density_map[y, x] = max(0.0, min(1.0, value))

    def get_movement_modifier(self, x: int, y: int) -> float:
        """Calculate movement speed modifier based on terrain properties"""
        if 0 <= x < self.width and 0 <= y < self.height:
            height_factor = 1.0 - (self.height_map[y, x] * 0.7)  # Height reduces speed up to 70%
            density_factor = 1.0 - (self.density_map[y, x] * 0.5)  # Density reduces speed up to 50%
            return max(0.1, height_factor * density_factor)  # Ensure minimum speed of 10%
        return 1.0

    def update_conquest(self, unit_positions: Dict[int, list[Tuple[float, float]]], conquest_rate: float = 0.1) -> None:
        """Update terrain conquest based on unit positions with dynamic control"""
        # Reset current control points
        self.control_points.fill(0)
        
        # Mark control points for each team
        for team_id, positions in unit_positions.items():
            for pos in positions:
                x, y = int(pos[0]), int(pos[1])
                if 0 <= x < self.width and 0 <= y < self.height:
                    # Mark control in 3x3 area around unit
                    x_min, x_max = max(0, x-1), min(self.width, x+2)
                    y_min, y_max = max(0, y-1), min(self.height, y+2)
                    self.control_points[y_min:y_max, x_min:x_max] = team_id

        # Update conquest progress
        for y in range(self.height):
            for x in range(self.width):
                current_controller = self.control_points[y, x]
                if current_controller > 0:
                    if current_controller != self.last_controlling_team[y, x]:
                        # Different team is now controlling - start reducing progress
                        self.conquest_progress[y, x] = max(0.0, self.conquest_progress[y, x] - conquest_rate * 2)
                        if self.conquest_progress[y, x] == 0:
                            # Territory lost - reset conquest
                            self.conquest_map[y, x] = 0
                    else:
                        # Same team still controlling - increase progress
                        self.conquest_progress[y, x] = min(1.0, self.conquest_progress[y, x] + conquest_rate)
                        if self.conquest_progress[y, x] >= 1.0:
                            self.conquest_map[y, x] = current_controller
                else:
                    # No team controlling - slowly decay progress
                    self.conquest_progress[y, x] = max(0.0, self.conquest_progress[y, x] - conquest_rate * 0.5)
                    if self.conquest_progress[y, x] == 0:
                        self.conquest_map[y, x] = 0

                # Update last controlling team
                self.last_controlling_team[y, x] = current_controller

    def get_conquest_percentage(self, team_id: int) -> float:
        """Calculate the percentage of terrain conquered by a team"""
        total_cells = self.width * self.height
        conquered_cells = np.sum(self.conquest_map == team_id)
        return (conquered_cells / total_cells) * 100

    def get_control_points(self) -> np.ndarray:
        """Get current control points map"""
        return self.control_points

    def get_conquest_progress(self) -> np.ndarray:
        """Get current conquest progress map"""
        return self.conquest_progress

    @classmethod
    def create_preset(cls, preset_name: str, width: int, height: int) -> 'Terrain':
        """Create a predefined terrain configuration"""
        terrain = cls(width, height)
        
        if preset_name == "valley":
            # Create a valley with mountains on the sides
            x_coords = np.linspace(0, 1, width)
            for x in range(width):
                mountain_height = 1.0 - 0.8 * np.exp(-(((x_coords[x] - 0.5) / 0.2) ** 2))
                for y in range(height):
                    variation = 0.2 * np.sin(y / 5.0)
                    terrain.set_height(x, y, mountain_height + variation)
                    terrain.set_density(x, y, mountain_height * 0.3 + variation * 0.5)
        
        elif preset_name == "hills":
            # Create random rolling hills using Perlin-like noise
            freq = 5.0
            for x in range(width):
                for y in range(height):
                    h = (np.sin(x/freq) + np.sin(y/freq) + 
                         np.sin((x+y)/freq) + np.sin((x-y)/freq)) / 4.0
                    h = (h + 1) / 2  # Normalize to 0-1
                    terrain.set_height(x, y, h)
                    terrain.set_density(x, y, h * 0.4)

        return terrain