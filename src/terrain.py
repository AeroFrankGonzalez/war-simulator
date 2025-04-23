import numpy as np
from typing import Dict, Tuple

# Define los tipos de terreno como constantes para mayor legibilidad
class TerrainType:
    GRASS = 0
    WATER = 1
    FOREST = 2
    SAND = 3
    MOUNTAIN = 4
    # Puedes añadir más tipos según necesites

class Terrain:
    # Define las propiedades base para cada tipo de terreno
    TERRAIN_PROPERTIES: Dict[int, Dict[str, float]] = {
        TerrainType.GRASS: {'base_movement_modifier': 1.0, 'base_density': 0.1, 'base_height': 0.1},
        TerrainType.WATER: {'base_movement_modifier': 0.2, 'base_density': 0.8, 'base_height': 0.0}, # El agua suele ser un obstáculo
        TerrainType.FOREST: {'base_movement_modifier': 0.6, 'base_density': 0.7, 'base_height': 0.2}, # Los bosques ralentizan
        TerrainType.SAND: {'base_movement_modifier': 0.8, 'base_density': 0.3, 'base_height': 0.0},   # La arena puede ser más lenta
        TerrainType.MOUNTAIN: {'base_movement_modifier': 0.3, 'base_density': 0.9, 'base_height': 0.8},# Las montañas son difíciles de transitar
        # Añade propiedades para otros tipos de terreno aquí
    }

    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        # Inicializa el mapa de tipos de terreno (por defecto, GRASS)
        self.terrain_type_map = np.full((height, width), TerrainType.GRASS, dtype=int)
        # Mantén los mapas de altura y densidad para variaciones dentro del tipo de terreno
        self.height_map = np.zeros((height, width))
        self.density_map = np.zeros((height, width))

        self.conquest_map = np.zeros((height, width), dtype=int)  # 0 = neutral, 1 = team1, 2 = team2
        self.conquest_progress = np.zeros((height, width))  # Progress towards conquest (0-1)
        self.control_points = np.zeros((height, width), dtype=int)  # Current controlling team
        self.last_controlling_team = np.zeros((height, width), dtype=int)  # Track last team that had control

        # Opcional: Inicializar height_map y density_map basados en el tipo de terreno inicial
        # Esto asegura que los valores iniciales de height y density reflejen el tipo de terreno base
        for y in range(height):
             for x in range(width):
                 initial_type = self.terrain_type_map[y, x]
                 if initial_type in self.TERRAIN_PROPERTIES:
                    self.height_map[y, x] = self.TERRAIN_PROPERTIES[initial_type]['base_height']
                    self.density_map[y, x] = self.TERRAIN_PROPERTIES[initial_type]['base_density']


    def set_terrain_type(self, x: int, y: int, type_id: int) -> None:
        """Set terrain type value at position (x,y) and optionally update base properties."""
        if 0 <= x < self.width and 0 <= y < self.height:
            self.terrain_type_map[y, x] = type_id
            # Opcional: Actualiza la altura y densidad base al cambiar el tipo
            # Si quieres que cambiar el tipo reinicie la altura/densidad a su valor base
            if type_id in self.TERRAIN_PROPERTIES:
                 self.height_map[y, x] = self.TERRAIN_PROPERTIES[type_id]['base_height']
                 self.density_map[y, x] = self.TERRAIN_PROPERTIES[type_id]['base_density']


    def set_height(self, x: int, y: int, value: float) -> None:
        """Set height value at position (x,y) - can be used for variation within a terrain type"""
        if 0 <= x < self.width and 0 <= y < self.height:
            self.height_map[y, x] = max(0.0, min(1.0, value))

    def set_density(self, x: int, y: int, value: float) -> None:
        """Set density value at position (x,y) - can be used for variation within a terrain type"""
        if 0 <= x < self.width and 0 <= y < self.height:
            self.density_map[y, x] = max(0.0, min(1.0, value))

    def get_movement_modifier(self, x: int, y: int) -> float:
        """Calculate movement speed modifier based on terrain type, height, and density"""
        if 0 <= x < self.width and 0 <= y < self.height:
            terrain_type = self.terrain_type_map[y, x]
            # Obtiene las propiedades del tipo de terreno, con GRASS como fallback
            properties = self.TERRAIN_PROPERTIES.get(terrain_type, self.TERRAIN_PROPERTIES[TerrainType.GRASS])
            base_modifier = properties['base_movement_modifier']

            # Mantén cómo la altura y la densidad afectan el modificador base
            # Estos factores ahora actúan *sobre* el modificador base del tipo de terreno.
            height_factor = 1.0 - (self.height_map[y, x] * 0.7)
            density_factor = 1.0 - (self.density_map[y, x] * 0.5)

            # Combina el modificador base del tipo de terreno con los factores de altura y densidad
            total_modifier = base_modifier * height_factor * density_factor

            return max(0.1, total_modifier) # Asegura una velocidad mínima

        return 1.0 # Default movement modifier for out of bounds

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

                    # Optional: Only mark control points on capturable terrain types
                    # capturable_types = [TerrainType.GRASS, TerrainType.FOREST, TerrainType.SAND, TerrainType.MOUNTAIN]
                    # for cy in range(y_min, y_max):
                    #     for cx in range(x_min, x_max):
                    #         if self.terrain_type_map[cy, cx] in capturable_types:
                    #              self.control_points[cy, cx] = team_id
                    # Si no usas la opción anterior, simplemente marca el área:
                    self.control_points[y_min:y_max, y_min:y_max] = team_id


        # Update conquest progress
        for y in range(self.height):
            for x in range(self.width):
                current_controller = self.control_points[y, x]
                # Optional: Do not update conquest on non-capturable terrain types
                # if self.terrain_type_map[y, x] in self.TERRAIN_PROPERTIES and self.TERRAIN_PROPERTIES[self.terrain_type_map[y, x]].get('capturable', True):

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

                # Update last controlling team AFTER updating progress for the current step
                # This is important for the logic in the next step
                self.last_controlling_team[y, x] = current_controller


    def get_conquest_percentage(self, team_id: int) -> float:
        """Calculate the percentage of terrain conquered by a team"""
        # Optional: Only count capturable terrain for percentage
        # capturable_mask = np.isin(self.terrain_type_map, [TerrainType.GRASS, TerrainType.FOREST, TerrainType.SAND, TerrainType.MOUNTAIN])
        # total_capturable_cells = np.sum(capturable_mask)
        # conquered_capturable_cells = np.sum((self.conquest_map == team_id) & capturable_mask)
        # return (conquered_capturable_cells / total_capturable_cells) * 100 if total_capturable_cells > 0 else 0.0

        total_cells = self.width * self.height
        conquered_cells = np.sum(self.conquest_map == team_id)
        return (conquered_cells / total_cells) * 100

    def get_control_points(self) -> np.ndarray:
        """Get current control points map"""
        return self.control_points

    def get_conquest_progress(self) -> np.ndarray:
        """Get current conquest progress map"""
        return self.conquest_progress

    def get_terrain_type_map(self) -> np.ndarray:
        """Get current terrain type map"""
        return self.terrain_type_map


    @classmethod
    def create_preset(cls, preset_name: str, width: int, height: int) -> 'Terrain':
        """Create a predefined terrain configuration including terrain types"""
        terrain = cls(width, height)

        if preset_name == "valley":
            # Reuse your existing valley logic for height and density
            x_coords = np.linspace(0, 1, width)
            for x in range(width):
                mountain_height = 1.0 - 0.8 * np.exp(-(((x_coords[x] - 0.5) / 0.2) ** 2))
                for y in range(height):
                    variation = 0.2 * np.sin(y / 5.0)
                    h = mountain_height + variation
                    terrain.set_height(x, y, h)
                    terrain.set_density(x, y, mountain_height * 0.3 + variation * 0.5)

                    # Based on height, assign a terrain type
                    if h > 0.7:
                        terrain.set_terrain_type(x, y, TerrainType.MOUNTAIN)
                    elif h < 0.1:
                        terrain.set_terrain_type(x, y, TerrainType.WATER) # Could represent a low-lying river or lake
                    else:
                        terrain.set_terrain_type(x, y, TerrainType.GRASS)


        elif preset_name == "hills":
            # Reuse your existing hills logic for height and density
            freq = 5.0
            for x in range(width):
                for y in range(height):
                    h = (np.sin(x/freq) + np.sin(y/freq) +
                         np.sin((x+y)/freq) + np.sin((x-y)/freq)) / 4.0
                    h = (h + 1) / 2  # Normalize to 0-1
                    terrain.set_height(x, y, h)
                    terrain.set_density(x, y, h * 0.4)

                    # Based on height, assign a terrain type for hills
                    if h > 0.6:
                        terrain.set_terrain_type(x, y, TerrainType.MOUNTAIN) # Higher hills might be mountainous
                    elif h < 0.2:
                         terrain.set_terrain_type(x, y, TerrainType.GRASS) # Lower areas are grassy
                    else:
                         terrain.set_terrain_type(x, y, TerrainType.GRASS) # Most hills are grassy

        elif preset_name == "forest_map":
            # Example: Create a map with areas of forest and grass
            for y in range(height):
                for x in range(width):
                    # Simple pattern: columns of forest
                    if x % 10 < 4:
                        terrain.set_terrain_type(x, y, TerrainType.FOREST)
                        # Al establecer el tipo, las propiedades base (densidad, altura) se actualizan
                        # Puedes añadir variaciones adicionales si lo deseas
                        # terrain.set_density(x, y, terrain.density_map[y, x] + np.random.rand() * 0.2)
                    else:
                        terrain.set_terrain_type(x, y, TerrainType.GRASS)
                        # terrain.set_density(x, y, terrain.density_map[y, x] + np.random.rand() * 0.1)


        elif preset_name == "rivers_and_lakes":
             # Example: Create a map with some water features
             center_x, center_y = width // 2, height // 2
             for y in range(height):
                 for x in range(width):
                     dist_to_center = np.sqrt((x - center_x)**2 + (y - center_y)**2)
                     if dist_to_center < min(width, height) / 6:
                         terrain.set_terrain_type(x, y, TerrainType.WATER)
                     elif dist_to_center < min(width, height) / 4 and np.random.rand() < 0.3:
                          terrain.set_terrain_type(x, y, TerrainType.WATER) # Smaller water patches/rivers
                     else:
                         terrain.set_terrain_type(x, y, TerrainType.GRASS)

        # Añade aquí más elif bloques para otros tipos de mapa de la imagen:
        # elif preset_name == "arabia":
        #     # Lógica para generar un mapa tipo desierto con algunas áreas de pasto/oasis
        #     for y in range(height):
        #         for x in range(width):
        #             # Ejemplo simple: la mayoría es arena
        #             terrain.set_terrain_type(x, y, TerrainType.SAND)
        #             # Añadir pequeñas áreas de pasto aleatorias
        #             if np.random.rand() < 0.05:
        #                  terrain.set_terrain_type(x, y, TerrainType.GRASS)
        #             # Podrías añadir algunas montañas o elevaciones rocosas
        #             if np.random.rand() < 0.01:
        #                 terrain.set_terrain_type(x, y, TerrainType.MOUNTAIN)
        #                 terrain.set_height(x, y, 0.9)
        #                 terrain.set_density(x, y, 0.9)

        # elif preset_name == "black_forest":
        #     # Lógica para generar un mapa denso con grandes áreas de bosque y quizás un camino central
        #     for y in range(height):
        #         for x in range(width):
        #             # La mayoría es bosque
        #             terrain.set_terrain_type(x, y, TerrainType.FOREST)
        #             # Crear un camino central (ejemplo simple)
        #             if abs(x - width // 2) < 3 or abs(y - height // 2) < 3:
        #                  terrain.set_terrain_type(x, y, TerrainType.GRASS)


        # Asegúrate de que los mapas de altura y densidad se inicialicen correctamente
        # después de establecer los tipos de terreno si no lo hiciste en set_terrain_type
        # (esto ya lo añadí opcionalmente en el __init__ y set_terrain_type)
        # for y in range(height):
        #     for x in range(width):
        #         current_type = terrain.terrain_type_map[y, x]
        #         if current_type in terrain.TERRAIN_PROPERTIES:
        #             # Si no quieres sobrescribir las variaciones, combina o solo usa base si no se ha tocado
        #             if terrain.height_map[y, x] == 0: # Suponiendo que 0 es el valor inicial/sin modificar
        #                  terrain.height_map[y, x] = terrain.TERRAIN_PROPERTIES[current_type]['base_height']
        #             if terrain.density_map[y, x] == 0: # Suponiendo que 0 es el valor inicial/sin modificar
        #                  terrain.density_map[y, x] = terrain.TERRAIN_PROPERTIES[current_type]['base_density']


        return terrain

# Example usage:
if __name__ == '__main__':
    map_width = 50
    map_height = 50

    # Crear un mapa de tipo "forest_map"
    forest_terrain = Terrain.create_preset("forest_map", map_width, map_height)
    print("Created Forest Map")
    # Puedes inspeccionar los mapas generados
    # print("Terrain Type Map:\n", forest_terrain.get_terrain_type_map())
    # print("Movement Modifier in Forest:", forest_terrain.get_movement_modifier(5, 10))
    # print("Movement Modifier in Grass:", forest_terrain.get_movement_modifier(15, 10))


    # Crear un mapa de tipo "rivers_and_lakes"
    water_terrain = Terrain.create_preset("rivers_and_lakes", map_width, map_height)
    print("\nCreated Rivers and Lakes Map")
    # print("Terrain Type Map:\n", water_terrain.get_terrain_type_map())
    # print("Movement Modifier at center (likely water):", water_terrain.get_movement_modifier(map_width//2, map_height//2))
    # print("Movement Modifier on edge (likely grass):", water_terrain.get_movement_modifier(5, 5))


    # Crear un mapa de tipo "valley" (con tipos de terreno asignados por altura)
    valley_terrain = Terrain.create_preset("valley", map_width, map_height)
    print("\nCreated Valley Map")
    # print("Height Map:\n", valley_terrain.height_map)
    # print("Terrain Type Map:\n", valley_terrain.get_terrain_type_map())


    # Example of updating conquest (requires a dictionary of unit positions)
    # Dummy unit positions: Team 1 at (5,5), Team 2 at (45,45)
    unit_positions_example = {
        1: [(5, 5)],
        2: [(45, 45)]
    }
    print("\nUpdating conquest on Valley Map...")
    for _ in range(20): # Simulate a few turns of conquest
        valley_terrain.update_conquest(unit_positions_example)

    print("Team 1 conquest percentage:", valley_terrain.get_conquest_percentage(1))
    print("Team 2 conquest percentage:", valley_terrain.get_conquest_percentage(2))
    # print("Conquest Map:\n", valley_terrain.conquest_map)
    # print("Conquest Progress Map:\n", valley_terrain.conquest_progress)