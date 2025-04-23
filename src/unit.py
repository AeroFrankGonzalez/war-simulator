from dataclasses import dataclass
from typing import Tuple, Optional
import numpy as np

@dataclass
class Unit:
    team_id: int
    position: Tuple[float, float]
    health: int = 5  # Initial contact resistance as per REQ-COMBAT-2
    movement_speed: float = 1.0
    kills: int = 0
    distance_moved: float = 0.0
    target: Optional[Tuple[float, float]] = None
    last_direction: Optional[Tuple[float, float]] = None

    def move(self, target: Tuple[float, float], terrain_modifier: float = 1.0, terrain_bounds: Tuple[float, float] = None) -> None:
        """
        Move the unit towards the target position considering terrain effects and boundaries
        """
        direction = np.array(target) - np.array(self.position)
        distance = np.linalg.norm(direction)
        
        if distance > 0:
            normalized_direction = direction / distance
            actual_speed = self.movement_speed * terrain_modifier
            movement = normalized_direction * actual_speed
            new_position = np.array(self.position) + movement
            
            # Check if new position would be out of bounds
            if terrain_bounds:
                width, height = terrain_bounds
                if (new_position[0] < 0 or new_position[0] >= width or 
                    new_position[1] < 0 or new_position[1] >= height):
                    # Reverse direction if hitting a boundary
                    if self.last_direction is not None:
                        # Use the last valid direction but reversed
                        movement = -np.array(self.last_direction) * actual_speed
                    else:
                        # Random perpendicular direction
                        perp_direction = np.array([-normalized_direction[1], normalized_direction[0]])
                        movement = perp_direction * actual_speed
                    new_position = np.array(self.position) + movement
                    
                    # Ensure position stays within bounds
                    new_position[0] = np.clip(new_position[0], 0, width - 1)
                    new_position[1] = np.clip(new_position[1], 0, height - 1)
                    
                    # Set new random target
                    self.target = (
                        np.random.uniform(width * 0.2, width * 0.8),
                        np.random.uniform(height * 0.2, height * 0.8)
                    )
            
            self.last_direction = tuple(movement / actual_speed)
            self.distance_moved += actual_speed
            self.position = tuple(new_position)

    def take_damage(self) -> bool:
        """
        Unit takes 1 point of damage
        Returns True if unit dies, False otherwise
        """
        self.health -= 1
        return self.health <= 0

    def is_in_contact_range(self, other_unit: 'Unit', contact_radius: float) -> bool:
        """Check if another unit is within contact range"""
        distance = np.linalg.norm(
            np.array(self.position) - np.array(other_unit.position)
        )
        return distance <= contact_radius