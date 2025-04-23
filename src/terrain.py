import numpy as np # Asegúrate de tener numpy instalado (pip install numpy)
from typing import Dict, Tuple # Importa Dict y Tuple desde typing

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
        TerrainType.WATER: {'base_movement_modifier': 0.2, 'base_density': 0.8, 'base_height': 0.0},
        TerrainType.FOREST: {'base_movement_modifier': 0.6, 'base_density': 0.7, 'base_height': 0.2},
        TerrainType.SAND: {'base_movement_modifier': 0.8, 'base_density': 0.3, 'base_height': 0.0},
        TerrainType.MOUNTAIN: {'base_movement_modifier': 0.3, 'base_density': 0.9, 'base_height': 0.8},
    }

    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.terrain_type_map = np.full((height, width), TerrainType.GRASS, dtype=int)
        self.height_map = np.zeros((height, width))
        self.density_map = np.zeros((height, width))

        self.conquest_map = np.zeros((height, width), dtype=int)  # 0 = neutral, 1 = team1, 2 = team2
        self.conquest_progress = np.zeros((height, width))  # Progress towards conquest (0-1)
        self.control_points = np.zeros((height, width), dtype=int)  # Current controlling team for visualization
        self.last_controlling_team = np.zeros((height, width), dtype=int)  # Track last team that had control for logic

        # Initialize height_map and density_map based on the initial terrain type
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
            # Update base height and density when changing type
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
            properties = self.TERRAIN_PROPERTIES.get(terrain_type, self.TERRAIN_PROPERTIES[TerrainType.GRASS])
            base_modifier = properties['base_movement_modifier']

            height_factor = 1.0 - (self.height_map[y, x] * 0.7)
            density_factor = 1.0 - (self.density_map[y, x] * 0.5)

            total_modifier = base_modifier * height_factor * density_factor

            return max(0.1, total_modifier)

        return 1.0

    def update_conquest(self, unit_positions: Dict[int, list[Tuple[float, float]]], conquest_rate: float = 0.1) -> None:
        """Update terrain conquest based on unit positions with dynamic control using majority influence."""

        # Mapa temporal para contar cuántas unidades de cada equipo influyen en cada celda en este paso.
        # Dimension 0: Sin usar (podría ser para neutral, pero no contamos influencia neutral aquí)
        # Dimension 1: Conteo de unidades del Equipo 1 en el área de influencia de la celda
        # Dimension 2: Conteo de unidades del Equipo 2 en el área de influencia de la celda
        team_influence_counts = np.zeros((self.height, self.width, 3), dtype=int)

        # Rellenar el mapa de conteo de influencia basado en la posición de las unidades.
        # Cada unidad influye en un área de 3x3 celdas a su alrededor.
        for team_id, positions in unit_positions.items():
            # Solo consideramos la influencia de los equipos 1 y 2.
            if team_id > 0:
                for pos in positions:
                    # Obtener las coordenadas enteras de la unidad.
                    x_unit, y_unit = int(pos[0]), int(pos[1])

                    # Asegurarse de que la posición de la unidad esté dentro de los límites del terreno.
                    if 0 <= x_unit < self.width and 0 <= y_unit < self.height:
                        # Definir el área de influencia de 3x3 alrededor de la unidad, dentro de los límites del mapa.
                        x_min, x_max = max(0, x_unit - 1), min(self.width, x_unit + 2)
                        y_min, y_max = max(0, y_unit - 1), min(self.height, y_unit + 2)

                        # Incrementar el contador de influencia para el equipo de esta unidad en todas las celdas de su área de 3x3.
                        for y_inf in range(y_min, y_max):
                            for x_inf in range(x_min, x_max):
                                # Usamos x_inf, y_inf para evitar confusión con los bucles principales x, y
                                team_influence_counts[y_inf, x_inf, team_id] += 1

        # Determinar el controlador actual de cada celda para ESTE paso basado en la mayoría de la influencia.
        # Usaremos un mapa temporal para almacenar este controlador determinado antes de actualizar self.last_controlling_team.
        new_current_controllers = np.zeros((self.height, self.width), dtype=int)

        # Iterar por cada celda del terreno para actualizar su estado de conquista.
        for y in range(self.height):
            for x in range(self.width):
                # Obtener el conteo de influencia de cada equipo en esta celda.
                team1_influence = team_influence_counts[y, x, 1]
                team2_influence = team_influence_counts[y, x, 2]

                # Determinar qué equipo tiene la mayoría de la influencia en ESTA celda para ESTE paso.
                if team1_influence > team2_influence:
                    current_controller_this_step = 1
                elif team2_influence > team1_influence:
                    current_controller_this_step = 2
                else:
                    # Si la influencia es igual para ambos equipos (incluyendo cero), esta celda es neutral en términos de control en este paso.
                    current_controller_this_step = 0

                # Almacenar el controlador determinado para esta celda en el mapa temporal para este paso.
                new_current_controllers[y, x] = current_controller_this_step


                # --- Actualizar el progreso de conquista usando el current_controller_this_step ---
                # Esta lógica usa el controlador determinado para *this* paso comparado con el controlador del paso *previous* (last_controlling_team)
                previous_controller = self.last_controlling_team[y, x] # El controlador del paso ANTERIOR.

                # <<< Línea 107 podría estar por aquí, si el error es exactamente en la línea 107 >>>
                # <<< Asegúrate de que la indentación de los siguientes bloques if/else sea correcta >>>

                if current_controller_this_step > 0: # Si un equipo tiene la mayoría de la influencia en este paso...
                    if current_controller_this_step != previous_controller:
                        # Si el controlador de este paso es diferente al del paso anterior, reducir el progreso del equipo anterior.
                        self.conquest_progress[y, x] = max(0.0, self.conquest_progress[y, x] - conquest_rate * 2)
                        # Si el progreso llega a 0 o menos, la celda se vuelve neutral en el mapa de conquista oficial.
                        if self.conquest_progress[y, x] <= 0:
                            self.conquest_map[y, x] = 0
                            self.conquest_progress[y, x] = 0.0 # Asegurar que el progreso sea exactamente 0.0.
                    else:
                        # Si el controlador de este paso es el mismo que el del paso anterior, aumentar el progreso.
                        self.conquest_progress[y, x] = min(1.0, self.conquest_progress[y, x] + conquest_rate)
                        # Si el progreso llega a 1.0 o más, la celda es oficialmente conquistada por este equipo.
                        if self.conquest_progress[y, x] >= 1.0:
                            self.conquest_map[y, x] = current_controller_this_step
                            self.conquest_progress[y, x] = 1.0 # Asegurar que el progreso sea exactamente 1.0.

                else: # Si ningún equipo tiene la mayoría de la influencia en este paso (es neutral)...
                    # El progreso de conquista existente se desvanece lentamente.
                    self.conquest_progress[y, x] = max(0.0, self.conquest_progress[y, x] - conquest_rate * 0.5)
                    # Si el progreso se desvanece a 0 o menos, la celda se vuelve neutral en el mapa de conquista oficial.
                    if self.conquest_progress[y, x] <= 0:
                        self.conquest_map[y, x] = 0
                        self.conquest_progress[y, x] = 0.0 # Asegurar que el progreso sea exactamente 0.0.

                # <<< Asegúrate de que no haya código aquí con indentación incorrecta >>>
                # <<< Este es el final del bloque if/else que actualiza el progreso >>>
                # <<< Después de este bloque, el código debe estar indentado al mismo nivel que 'if current_controller_this_step > 0:' >>>
                # <<< si hay más código dentro del bucle for x, o al mismo nivel que 'for y...' si es el final del bucle for x >>>
                # <<< En este código, el bucle for x termina después de este bloque else. >>>


        # --- Actualizar self.last_controlling_team y self.control_points DESPUÉS de iterar por todas las celdas ---
        # Estas líneas deben estar FUERA de ambos bucles for y, for x.

        # El last_controlling_team para el *próximo* paso será el controlador determinado para *este* paso (basado en mayoría de influencia).
        self.last_controlling_team = new_current_controllers.copy()

        # El mapa control_points se utiliza principalmente para la visualización, para mostrar dónde hay unidades ejerciendo influencia.
        # Lo establecemos al controlador determinado por mayoría (new_current_controllers).
        self.control_points = new_current_controllers.copy()

        # Opcional: Si prefieres que control_points muestre *cualquier* área de 3x3 con unidades (no solo mayoría),
        # puedes descomentar y usar el bloque de código de abajo.
        # self.control_points.fill(0) # Limpiar el mapa de puntos de control visual.
        # for team_id, positions in unit_positions.items():
        #     if team_id > 0:
        #         for pos in positions:
        #             x_unit, y_unit = int(pos[0]), int(pos[1])
        #             if 0 <= x_unit < self.width and 0 <= y_unit < self.height:
        #                 x_min, x_max = max(0, x_unit - 1), min(self.width, x_unit + 2)
        #                 y_min, y_max = max(0, y_unit - 1), min(self.height, y_unit + 2)
        #                 # Marcar el área 3x3.
        #                 self.control_points[y_min:y_max, x_min:x_max] = team_id


    @classmethod
    def create_preset(cls, preset_name: str, width: int, height: int) -> 'Terrain':
        """Create a predefined terrain configuration including terrain types"""
        terrain = cls(width, height)

        # --- Implementación de presets (mantén o añade tus lógicas aquí) ---
        if preset_name == "valley":
            x_coords = np.linspace(0, 1, width)
            for x in range(width):
                mountain_height = 1.0 - 0.8 * np.exp(-(((x_coords[x] - 0.5) / 0.2) ** 2))
                for y in range(height):
                    variation = 0.2 * np.sin(y / 5.0)
                    h = mountain_height + variation
                    terrain.set_height(x, y, h)
                    terrain.set_density(x, y, mountain_height * 0.3 + variation * 0.5)
                    if h > 0.7:
                        terrain.set_terrain_type(x, y, TerrainType.MOUNTAIN)
                    elif h < 0.1:
                        terrain.set_terrain_type(x, y, TerrainType.WATER)
                    else:
                        terrain.set_terrain_type(x, y, TerrainType.GRASS)

        elif preset_name == "hills":
            freq = 5.0
            for x in range(width):
                for y in range(height):
                    h = (np.sin(x/freq) + np.sin(y/freq) +
                         np.sin((x+y)/freq) + np.sin((x-y)/freq)) / 4.0
                    h = (h + 1) / 2
                    terrain.set_height(x, y, h)
                    terrain.set_density(x, y, h * 0.4)
                    if h > 0.6:
                        terrain.set_terrain_type(x, y, TerrainType.MOUNTAIN)
                    elif h < 0.2:
                         terrain.set_terrain_type(x, y, TerrainType.GRASS)
                    else:
                         terrain.set_terrain_type(x, y, TerrainType.GRASS)

        elif preset_name == "forest_map":
             for y in range(height):
                 for x in range(width):
                     if x % 10 < 4:
                         terrain.set_terrain_type(x, y, TerrainType.FOREST)
                     else:
                         terrain.set_terrain_type(x, y, TerrainType.GRASS)
             for y in range(height):
                  for x in range(width):
                      current_type = terrain.terrain_type_map[y, x]
                      if current_type in terrain.TERRAIN_PROPERTIES:
                           terrain.height_map[y, x] = terrain.TERRAIN_PROPERTIES[current_type]['base_height']
                           terrain.density_map[y, x] = terrain.TERRAIN_PROPERTIES[current_type]['base_density']

        elif preset_name == "rivers_and_lakes":
              center_x, center_y = width // 2, height // 2
              for y in range(height):
                  for x in range(width):
                      dist_to_center = np.sqrt((x - center_x)**2 + (y - center_y)**2)
                      if dist_to_center < min(width, height) / 6:
                          terrain.set_terrain_type(x, y, TerrainType.WATER)
                      elif dist_to_center < min(width, height) / 4 and np.random.rand() < 0.3:
                           terrain.set_terrain_type(x, y, TerrainType.WATER)
                      else:
                          terrain.set_terrain_type(x, y, TerrainType.GRASS)
              for y in range(height):
                   for x in range(width):
                       current_type = terrain.terrain_type_map[y, x]
                       if current_type in terrain.TERRAIN_PROPERTIES:
                            terrain.height_map[y, x] = terrain.TERRAIN_PROPERTIES[current_type]['base_height']
                            terrain.density_map[y, x] = terrain.TERRAIN_PROPERTIES[current_type]['base_density']
        # --- Fin de implementación de presets ---


        # Asegúrate de que los mapas de conquista y control estén limpios al inicio.
        terrain.last_controlling_team.fill(0)
        terrain.conquest_map.fill(0)
        terrain.conquest_progress.fill(0.0)
        terrain.control_points.fill(0)

        return terrain


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

    def get_terrain_type_map(self) -> np.ndarray:
        """Get current terrain type map"""
        return self.terrain_type_map