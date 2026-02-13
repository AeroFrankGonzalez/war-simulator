# unit.py

from dataclasses import dataclass
from typing import Optional

@dataclass
class Unit:
    """
    Represents a unit in a specific cell for the Cellular Automaton simulation.
    In this model, a Unit is effectively a state marker for a grid cell.
    """
    team_id: int # The ID of the team the unit belongs to (e.g., 1 or 2).
    health: int = 1 # Simplified health: 1 = Alive/Present. Could be >1 for "fortified" units later.
    
    # Movement related attributes (position, speed, target) are removed 
    # as position is determined by grid coordinates in the Battle matrix.