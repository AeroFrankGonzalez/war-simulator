import unittest
import sys
import os
import numpy as np

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from battle import Battle
from terrain import Terrain
from unit import Unit

class TestCellularAutomaton(unittest.TestCase):
    def setUp(self):
        self.config = {
            'automaton_rules': {
                'survival_threshold': [2, 3],
                'birth_threshold': [3],
                'enemy_tolerance': 3
            },
            'teams': {1: {}, 2: {}} # Empty config to avoid auto-population
        }
        # Use a small grid for testing
        self.terrain = Terrain(10, 10)
        # Mock battle initialization to avoid random population
        self.battle = Battle(self.terrain, self.config)
        # Clear the grid manually to be sure
        self.battle.grid = np.empty((10, 10), dtype=object)

    def test_underpopulation(self):
        """Test that a unit dies with < 2 neighbors."""
        # Place one unit at 5,5
        self.battle.grid[5, 5] = Unit(team_id=1)
        # Place one neighbor at 5,6
        self.battle.grid[5, 6] = Unit(team_id=1)
        
        self.battle.step()
        
        # Both should die because each has only 1 neighbor
        self.assertIsNone(self.battle.grid[5, 5], "Unit should die from underpopulation")
        self.assertIsNone(self.battle.grid[5, 6], "Unit should die from underpopulation")

    def test_survival(self):
        """Test that a unit survives with 2 or 3 neighbors."""
        # Create a block (2x2 square), static life
        # Top-left 1,1
        self.battle.grid[1, 1] = Unit(team_id=1)
        self.battle.grid[1, 2] = Unit(team_id=1)
        self.battle.grid[2, 1] = Unit(team_id=1)
        self.battle.grid[2, 2] = Unit(team_id=1)
        
        self.battle.step()
        
        self.assertIsNotNone(self.battle.grid[1, 1], "Unit should survive (Block pattern)")
        self.assertIsNotNone(self.battle.grid[1, 2], "Unit should survive (Block pattern)")
        self.assertIsNotNone(self.battle.grid[2, 1], "Unit should survive (Block pattern)")
        self.assertIsNotNone(self.battle.grid[2, 2], "Unit should survive (Block pattern)")

    def test_birth(self):
        """Test that a unit is born with 3 neighbors."""
        # Place 3 neighbors around 5,5
        self.battle.grid[4, 5] = Unit(team_id=1)
        self.battle.grid[5, 4] = Unit(team_id=1)
        self.battle.grid[5, 6] = Unit(team_id=1)
        
        # 5,5 is empty initially
        self.assertIsNone(self.battle.grid[5, 5])
        
        self.battle.step()
        
        # 5,5 should now have a unit
        new_unit = self.battle.grid[5, 5]
        self.assertIsNotNone(new_unit, "Unit should be born")
        self.assertEqual(new_unit.team_id, 1, "Born unit should belong to neighbors' team")

    def test_combat_overwhelming(self):
        """Test that a unit dies if overwhelmed by enemies."""
        # Place 1 Team 1 unit
        self.battle.grid[5, 5] = Unit(team_id=1)
        
        # Place 4 Team 2 neighbors (Enemy tolerance is 3)
        self.battle.grid[4, 5] = Unit(team_id=2)
        self.battle.grid[5, 4] = Unit(team_id=2)
        self.battle.grid[5, 6] = Unit(team_id=2)
        self.battle.grid[6, 5] = Unit(team_id=2)
        
        self.battle.step()
        
        self.assertIsNone(self.battle.grid[5, 5], "Unit should die from enemy overwhelming")

if __name__ == '__main__':
    unittest.main()
