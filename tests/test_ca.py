import unittest
import sys
import os
import numpy as np

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from battle import Battle
from terrain import Terrain

class TestCellularAutomaton(unittest.TestCase):
    def setUp(self):
        self.config = {
            'automaton_rules': {
                'survival_threshold': [2, 3],
                'birth_threshold': [3],
                'enemy_tolerance': 3
            },
            'teams': {1: {}, 2: {}} 
        }
        self.terrain = Terrain(10, 10)
        self.battle = Battle(self.terrain, self.config)
        # Manually clear grid to ensure clean slate (using zeros for int grid)
        self.battle.grid = np.zeros((10, 10), dtype=int)

    def test_underpopulation(self):
        """Test that a unit dies with < 2 neighbors."""
        # Place one Team 1 unit at 5,5
        self.battle.grid[5, 5] = 1
        # Place one neighbor at 5,6
        self.battle.grid[5, 6] = 1
        
        self.battle.step()
        
        # Both should die (become 0) because each has only 1 neighbor
        self.assertEqual(self.battle.grid[5, 5], 0, "Unit should die from underpopulation")
        self.assertEqual(self.battle.grid[5, 6], 0, "Unit should die from underpopulation")

    def test_survival(self):
        """Test that a unit survives with 2 or 3 neighbors."""
        # Create a block (2x2 square), static life
        self.battle.grid[1, 1] = 1
        self.battle.grid[1, 2] = 1
        self.battle.grid[2, 1] = 1
        self.battle.grid[2, 2] = 1
        
        self.battle.step()
        
        self.assertEqual(self.battle.grid[1, 1], 1, "Unit should survive (Block pattern)")
        self.assertEqual(self.battle.grid[1, 2], 1, "Unit should survive (Block pattern)")
        self.assertEqual(self.battle.grid[2, 1], 1, "Unit should survive (Block pattern)")
        self.assertEqual(self.battle.grid[2, 2], 1, "Unit should survive (Block pattern)")

    def test_birth(self):
        """Test that a unit is born with 3 neighbors."""
        # Place 3 neighbors around 5,5
        self.battle.grid[4, 5] = 1
        self.battle.grid[5, 4] = 1
        self.battle.grid[5, 6] = 1
        
        # 5,5 is empty initially
        self.assertEqual(self.battle.grid[5, 5], 0)
        
        self.battle.step()
        
        # 5,5 should now have a unit (1)
        self.assertEqual(self.battle.grid[5, 5], 1, "Unit should be born")

    def test_combat_overwhelming(self):
        """Test that a unit dies if overwhelmed by enemies."""
        # Place 1 Team 1 unit
        self.battle.grid[5, 5] = 1
        
        # Place 4 Team 2 neighbors (Enemy tolerance is 3)
        self.battle.grid[4, 5] = 2
        self.battle.grid[5, 4] = 2
        self.battle.grid[5, 6] = 2
        self.battle.grid[6, 5] = 2
        
        self.battle.step()
        
        self.assertEqual(self.battle.grid[5, 5], 0, "Unit should die from enemy overwhelming")

if __name__ == '__main__':
    unittest.main()
