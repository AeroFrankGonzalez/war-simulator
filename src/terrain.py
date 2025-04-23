import numpy as np # Asegúrate de tener numpy instalado (pip install numpy)
from typing import Dict, Tuple # Importa Dict y Tuple desde typing

# Define los tipos de terreno como constantes para mayor legibilidad
class TerrainType:
    GRASS = 0
    WATER = 1
    FOREST = 2
    SAND = 3
    MOUNTAIN = 4
    # Puedes añadir más tipos según necesites. Asocia un número entero único a cada tipo.

class Terrain:
    # Define las propiedades base para cada tipo de terreno.
    # Estas propiedades incluyen un modificador de movimiento base, densidad base y altura base.
    TERRAIN_PROPERTIES: Dict[int, Dict[str, float]] = {
        TerrainType.GRASS: {'base_movement_modifier': 1.0, 'base_density': 0.1, 'base_height': 0.1},
        TerrainType.WATER: {'base_movement_modifier': 0.2, 'base_density': 0.8, 'base_height': 0.0}, # El agua suele ser un obstáculo, muy baja velocidad.
        TerrainType.FOREST: {'base_movement_modifier': 0.6, 'base_density': 0.7, 'base_height': 0.2}, # Los bosques ralentizan el movimiento y tienen alta densidad.
        TerrainType.SAND: {'base_movement_modifier': 0.8, 'base_density': 0.3, 'base_height': 0.0},   # La arena puede ser más lenta que el pasto, baja densidad.
        TerrainType.MOUNTAIN: {'base_movement_modifier': 0.3, 'base_density': 0.9, 'base_height': 0.8},# Las montañas son muy difíciles de transitar, alta densidad y altura.
        # Añade propiedades para otros tipos de terreno aquí, usando TerrainType.NOMBRE.
    }

    def __init__(self, width: int, height: int):
        # Inicializa las dimensiones del terreno.
        self.width = width
        self.height = height

        # Inicializa los mapas del terreno como matrices NumPy.
        # Mapa para almacenar el tipo de terreno en cada celda (ej. GRASS, WATER). Inicializado con GRASS por defecto.
        self.terrain_type_map = np.full((height, width), TerrainType.GRASS, dtype=int)
        # Mapa para almacenar el valor de altura en cada celda (0.0 a 1.0).
        self.height_map = np.zeros((height, width))
        # Mapa para almacenar el valor de densidad en cada celda (0.0 a 1.0).
        self.density_map = np.zeros((height, width))

        # Mapas para el sistema de conquista.
        # conquest_map: Equipo que oficialmente controla la celda (0=neutral, 1=equipo 1, 2=equipo 2).
        self.conquest_map = np.zeros((height, width), dtype=int)
        # conquest_progress: Progreso hacia la conquista de la celda (0.0 a 1.0).
        self.conquest_progress = np.zeros((height, width))
        # control_points: Equipo que tiene control inmediato sobre la celda en el paso actual (basado en proximidad de unidades). Usado para visualización.
        self.control_points = np.zeros((height, width), dtype=int)
        # last_controlling_team: Equipo que tuvo control inmediato sobre la celda en el paso ANTERIOR. Usado para la lógica de progreso de conquista.
        self.last_controlling_team = np.zeros((height, width), dtype=int)

        # Inicializar los mapas de altura y densidad con los valores base del tipo de terreno por defecto (GRASS).
        # Esto se hace al inicio. create_preset sobrescribirá esto.
        for y in range(height):
             for x in range(width):
                 initial_type = self.terrain_type_map[y, x] # Que es GRASS por defecto.
                 if initial_type in self.TERRAIN_PROPERTIES:
                    self.height_map[y, x] = self.TERRAIN_PROPERTIES[initial_type]['base_height']
                    self.density_map[y, x] = self.TERRAIN_PROPERTIES[initial_type]['base_density']


    def set_terrain_type(self, x: int, y: int, type_id: int) -> None:
        """
        Set terrain type value at position (x,y).
        Optionally updates base height and density according to the new type.
        """
        if 0 <= x < self.width and 0 <= y < self.height:
            # Asignar el nuevo tipo de terreno a la celda.
            self.terrain_type_map[y, x] = type_id
            # Si el nuevo tipo tiene propiedades definidas, actualizar la altura y densidad base de la celda.
            # Esto sobrescribe cualquier valor anterior y establece un punto de partida basado en el tipo.
            if type_id in self.TERRAIN_PROPERTIES:
                 self.height_map[y, x] = self.TERRAIN_PROPERTIES[type_id]['base_height']
                 self.density_map[y, x] = self.TERRAIN_PROPERTIES[type_id]['base_density']


    def set_height(self, x: int, y: int, value: float) -> None:
        """
        Set height value at position (x,y).
        Can be used for variation WITHIN a terrain type after its base height is set.
        Values are clamped between 0.0 and 1.0.
        """
        if 0 <= x < self.width and 0 <= y < self.height:
            # Establecer el valor de altura, asegurándose de que esté entre 0.0 y 1.0.
            self.height_map[y, x] = max(0.0, min(1.0, value))


    def set_density(self, x: int, y: int, value: float) -> None:
        """
        Set density value at position (x,y).
        Can be used for variation WITHIN a terrain type after its base density is set.
        Values are clamped between 0.0 and 1.0.
        """
        if 0 <= x < self.width and 0 <= y < self.height:
            # Establecer el valor de densidad, asegurándose de que esté entre 0.0 y 1.0.
            self.density_map[y, x] = max(0.0, min(1.0, value))


    def get_movement_modifier(self, x: int, y: int) -> float:
        """
        Calculate the movement speed modifier for a unit at position (x,y).
        The modifier is based on the terrain type, height, and density of the cell.
        Returns a factor between 0.1 and 1.0 (1.0 means velocidad normal, 0.1 significa 10% de velocidad).
        """
        # Asegurarse de que las coordenadas (x, y) estén dentro de los límites válidos de la cuadrícula.
        if 0 <= x < self.width and 0 <= y < self.height:
            # Obtener el tipo de terreno de la celda.
            terrain_type = self.terrain_type_map[y, x]
            # Obtener las propiedades base para este tipo de terreno. Usar propiedades de GRASS como fallback si el tipo no se encuentra.
            properties = self.TERRAIN_PROPERTIES.get(terrain_type, self.TERRAIN_PROPERTIES[TerrainType.GRASS])
            # Obtener el modificador de movimiento base para este tipo de terreno.
            base_modifier = properties['base_movement_modifier']

            # Calcular factores de reducción de velocidad basados en la altura y densidad actuales de la celda.
            # La altura reduce la velocidad (hasta un 70% si height_map es 1.0).
            height_factor = 1.0 - (self.height_map[y, x] * 0.7)
            # La densidad reduce la velocidad (hasta un 50% si density_map es 1.0).
            density_factor = 1.0 - (self.density_map[y, x] * 0.5)

            # Combinar el modificador base del tipo de terreno con los factores de altura y densidad.
            # La combinación multiplicativa significa que todos los factores contribuyen a la reducción.
            total_modifier = base_modifier * height_factor * density_factor

            # Asegurar que el modificador total no sea menor que un valor mínimo (ej. 0.1, 10% de la velocidad base).
            return max(0.1, total_modifier)

        # Si las coordenadas están fuera de los límites, aplicar un modificador neutro (sin efecto).
        return 1.0


    def update_conquest(self, unit_positions: Dict[int, list[Tuple[float, float]]], conquest_rate: float = 0.1) -> None:
        """
        Update terrain conquest state based on unit positions.
        Determines immediate control by majority influence and updates long-term progress.
        """

        # Mapa temporal para contar cuántas unidades de cada equipo influyen en cada celda en este paso.
        # Cada celda tiene un conteo para cada equipo (Team 1, Team 2).
        # Dimension 0: Sin usar (podría ser para influencia neutral, pero no la necesitamos).
        # Dimension 1: Conteo de unidades del Equipo 1 en el área de influencia de la celda (radio 3x3).
        # Dimension 2: Conteo de unidades del Equipo 2 en el área de influencia de la celda (radio 3x3).
        team_influence_counts = np.zeros((self.height, self.width, 3), dtype=int)

        # Rellenar el mapa de conteo de influencia basado en la posición actual de todas las unidades vivas.
        # Cada unidad influye en un área de 3x3 celdas a su alrededor (incluyendo la celda donde está).
        for team_id, positions in unit_positions.items():
            # Solo consideramos la influencia de los equipos 1 y 2.
            if team_id > 0:
                for pos in positions:
                    # Obtener las coordenadas enteras (índices de celda) de la unidad a partir de su posición flotante.
                    x_unit_cell, y_unit_cell = int(pos[0]), int(pos[1])

                    # Asegurarse de que la celda donde está la unidad esté dentro de los límites del terreno.
                    # Esto evita errores al calcular el área de influencia si una unidad está justo en el borde.
                    if 0 <= x_unit_cell < self.width and 0 <= y_unit_cell < self.height:
                        # Definir los límites del área de influencia de 3x3 alrededor de la celda de la unidad.
                        # Asegurarse de que estos límites también estén dentro de los límites del mapa global.
                        x_min_inf, x_max_inf = max(0, x_unit_cell - 1), min(self.width, x_unit_cell + 2)
                        y_min_inf, y_max_inf = max(0, y_unit_cell - 1), min(self.height, y_unit_cell + 2)

                        # Iterar sobre todas las celdas dentro del área de influencia calculada.
                        for y_inf in range(y_min_inf, y_max_inf):
                            for x_inf in range(x_min_inf, x_max_inf):
                                # Incrementar el contador de influencia para el equipo de esta unidad en la celda actual del área de influencia.
                                team_influence_counts[y_inf, x_inf, team_id] += 1

        # Determinar el controlador actual de cada celda para ESTE paso de simulación basándose en la mayoría de la influencia contada.
        # Usaremos un mapa temporal para almacenar este controlador determinado para el paso actual.
        new_current_controllers = np.zeros((self.height, self.width), dtype=int)

        # Iterar por cada celda de la cuadrícula del terreno.
        for y in range(self.height):
            for x in range(self.width):
                # Obtener el conteo de influencia del Equipo 1 y el Equipo 2 en esta celda.
                team1_influence = team_influence_counts[y, x, 1]
                team2_influence = team_influence_counts[y, x, 2]

                # Determinar qué equipo tiene la mayoría de la influencia en ESTA celda para ESTE paso.
                # Si la influencia es igual (incluyendo cero influencia de ambos), la celda es neutral en términos de control en este paso.
                if team1_influence > team2_influence:
                    current_controller_this_step = 1 # El Equipo 1 tiene mayoría de influencia.
                elif team2_influence > team1_influence:
                    current_controller_this_step = 2 # El Equipo 2 tiene mayoría de influencia.
                else:
                    current_controller_this_step = 0 # La influencia es igual o cero.

                # Almacenar el controlador determinado para esta celda en el mapa temporal para este paso.
                new_current_controllers[y, x] = current_controller_this_step


                # --- Actualizar el progreso de conquista usando el current_controller_this_step ---
                # Esta lógica actualiza el progreso de conquista (conquest_progress) y el mapa de conquista oficial (conquest_map).
                # Se basa en comparar el controlador determinado para *este* paso con el controlador del *paso anterior* (last_controlling_team).
                previous_controller = self.last_controlling_team[y, x] # Obtener el controlador de esta celda en el paso ANTERIOR.

                if current_controller_this_step > 0: # Si un equipo tiene la mayoría de la influencia en este paso (el controlador no es neutral)...
                    if current_controller_this_step != previous_controller:
                        # Caso 1: Un equipo diferente (o un equipo vs neutral anterior) tiene ahora la mayoría de control.
                        # Reducir rápidamente el progreso de conquista existente (si lo había).
                        self.conquest_progress[y, x] = max(0.0, self.conquest_progress[y, x] - conquest_rate * 2) # Reduce el doble de rápido.
                        # Si el progreso cae a 0 o menos, la celda se vuelve neutral oficialmente en el mapa de conquista.
                        if self.conquest_progress[y, x] <= 0:
                            self.conquest_map[y, x] = 0 # La celda vuelve a ser neutral.
                            self.conquest_progress[y, x] = 0.0 # Asegurar que el progreso sea exactamente 0.0.
                    else:
                        # Caso 2: El mismo equipo sigue teniendo la mayoría de control que en el paso anterior.
                        # Aumentar el progreso de conquista.
                        self.conquest_progress[y, x] = min(1.0, self.conquest_progress[y, x] + conquest_rate) # Aumenta con la tasa normal.
                        # Si el progreso alcanza 1.0 o más, la celda es oficialmente conquistada por este equipo.
                        if self.conquest_progress[y, x] >= 1.0:
                            self.conquest_map[y, x] = current_controller_this_step # La celda es conquistada por el controlador actual.
                            self.conquest_progress[y, x] = 1.0 # Asegurar que el progreso sea exactamente 1.0 una vez conquistada.

                else: # Si no hay mayoría de influencia de ningún equipo en este paso (current_controller_this_step es 0)...
                    # El progreso de conquista existente (si lo había de un equipo anterior) se desvanece lentamente.
                    self.conquest_progress[y, x] = max(0.0, self.conquest_progress[y, x] - conquest_rate * 0.5) # Desvanece a mitad de velocidad.
                    # Si el progreso se desvanece a 0 o menos, la celda se vuelve neutral oficialmente.
                    if self.conquest_progress[y, x] <= 0:
                        self.conquest_map[y, x] = 0 # La celda vuelve a ser neutral.
                        self.conquest_progress[y, x] = 0.0 # Asegurar que el progreso sea exactamente 0.0.


        # --- Actualizar self.last_controlling_team y self.control_points DESPUÉS de iterar por todas las celdas ---
        # Es crucial que estas actualizaciones ocurran *después* de que se haya calculado el controlador para *todas* las celdas en este paso.

        # self.last_controlling_team para el *próximo* paso será el controlador determinado por mayoría para *este* paso.
        self.last_controlling_team = new_current_controllers.copy()

        # self.control_points se utiliza principalmente para la visualización, para mostrar dónde hay unidades ejerciendo influencia ahora.
        # Lo establecemos al controlador determinado por mayoría (new_current_controllers) ya que representa quién "controla" localmente para fines visuales.
        self.control_points = new_current_controllers.copy()

        # Opcional: Si prefieres que control_points muestre *cualquier* área de 3x3 con unidades (no solo mayoría)
        # para la visualización, puedes descomentar y usar el bloque de código de abajo.
        # Esto haría que el indicador visual del área de unidades se parezca más al comportamiento original,
        # pero la lógica de conquista (conquest_progress, conquest_map) seguirá siendo la más estable basada en mayoría.
        # self.control_points.fill(0) # Limpiar el mapa de puntos de control visual.
        # for team_id, positions in unit_positions.items():
        #     if team_id > 0:
        #         for pos in positions:
        #             x_unit_cell, y_unit_cell = int(pos[0]), int(pos[1])
        #             if 0 <= x_unit_cell < self.width and 0 <= y_unit_cell < self.height:
        #                 x_min_inf, x_max_inf = max(0, x_unit_cell - 1), min(self.width, x_unit_cell + 2)
        #                 y_min_inf, y_max_inf = max(0, y_unit_cell - 1), min(self.height, y_unit_cell + 2)
        #                 # Marcar el área 3x3 con el team_id. En caso de superposición, la última unidad/equipo procesado gana visualmente en esta capa simple.
        #                 self.control_points[y_min_inf:y_max_inf, x_min_inf:x_max_inf] = team_id


    @classmethod
    def create_preset(cls, preset_name: str, width: int, height: int) -> 'Terrain':
        """
        Factory method to create a Terrain instance with a predefined configuration.
        Includes setting terrain types, height, and density for different map presets.
        """
        terrain = cls(width, height) # Crear una nueva instancia de Terrain.

        # --- Implementación de presets de mapa ---
        # Define la lógica para generar diferentes tipos de mapas (valley, hills, forest_map, etc.).
        # Cada preset debe configurar self.terrain_type_map, self.height_map, y self.density_map.
        # Asegúrate de que la lógica de cada preset sea consistente.

        if preset_name == "valley":
            # Crear un valle con montañas en los lados.
            x_coords = np.linspace(0, 1, width)
            for x in range(width):
                mountain_height = 1.0 - 0.8 * np.exp(-(((x_coords[x] - 0.5) / 0.2) ** 2))
                for y in range(height):
                    variation = 0.2 * np.sin(y / 5.0)
                    h = mountain_height + variation
                    # Establecer altura y densidad. set_terrain_type establecerá base height/density si se llama primero.
                    # Aquí, establecemos altura y densidad después, permitiendo que añadan variación sobre el tipo base.
                    terrain.set_height(x, y, h)
                    terrain.set_density(x, y, mountain_height * 0.3 + variation * 0.5)

                    # Asignar un tipo de terreno basado principalmente en la altura.
                    if h > 0.7:
                        terrain.set_terrain_type(x, y, TerrainType.MOUNTAIN)
                    elif h < 0.1:
                        terrain.set_terrain_type(x, y, TerrainType.WATER) # Las áreas bajas podrían ser agua.
                    else:
                        terrain.set_terrain_type(x, y, TerrainType.GRASS) # Las áreas intermedias son pasto.


        elif preset_name == "hills":
            # Crear colinas aleatorias usando una forma simple de ruido.
            freq = 5.0 # Frecuencia del ruido para las colinas.
            for x in range(width):
                for y in range(height):
                    # Generar un valor de altura basado en ruido sinusoidal.
                    h = (np.sin(x/freq) + np.sin(y/freq) +
                         np.sin((x+y)/freq) + np.sin((x-y)/freq)) / 4.0
                    h = (h + 1) / 2 # Normalizar a un rango de 0 a 1.

                    # Establecer altura y densidad.
                    terrain.set_height(x, y, h)
                    terrain.set_density(x, y, h * 0.4) # Densidad correlacionada con la altura.

                    # Asignar un tipo de terreno basado en la altura.
                    if h > 0.6:
                        terrain.set_terrain_type(x, y, TerrainType.MOUNTAIN) # Las colinas más altas son montañas.
                    elif h < 0.2:
                         terrain.set_terrain_type(x, y, TerrainType.GRASS) # Las áreas más bajas son pasto.
                    else:
                         terrain.set_terrain_type(x, y, TerrainType.GRASS) # La mayoría de las colinas son pasto.

        elif preset_name == "forest_map":
            # Crear un mapa con áreas de bosque y pasto en columnas simples.
            for y in range(height):
                for x in range(width):
                    if x % 10 < 4: # Columnas de 4 celdas de ancho cada 10 celdas.
                        terrain.set_terrain_type(x, y, TerrainType.FOREST) # Asignar tipo BOSQUE.
                    else:
                        terrain.set_terrain_type(x, y, TerrainType.GRASS) # Asignar tipo PASTO.

            # Después de asignar los tipos, asegurarse de que la altura y densidad base se establezcan según el tipo.
            # El método set_terrain_type ya hace esto si se llama primero. Si no, podemos asegurarlo aquí.
            for y in range(height):
                 for x in range(width):
                     current_type = terrain.terrain_type_map[y, x]
                     if current_type in terrain.TERRAIN_PROPERTIES:
                           # Asegurarse de que height_map y density_map reflejen los valores base del tipo final.
                           # Esto es importante si los valores base no se establecieron ya por set_terrain_type.
                           terrain.height_map[y, x] = terrain.TERRAIN_PROPERTIES[current_type]['base_height']
                           terrain.density_map[y, x] = terrain.TERRAIN_PROPERTIES[current_type]['base_density']


        elif preset_name == "rivers_and_lakes":
             # Crear un mapa con características de agua (ríos y lagos).
             center_x, center_y = width // 2, height // 2 # Centro del mapa.
             for y in range(height):
                 for x in range(width):
                     dist_to_center = np.sqrt((x - center_x)**2 + (y - center_y)**2) # Distancia al centro.
                     if dist_to_center < min(width, height) / 6: # Área circular grande en el centro (lago).
                         terrain.set_terrain_type(x, y, TerrainType.WATER) # Asignar tipo AGUA.
                     # Añadir áreas de agua más pequeñas aleatorias (ríos o lagos pequeños).
                     elif dist_to_center < min(width, height) / 4 and np.random.rand() < 0.3:
                          terrain.set_terrain_type(x, y, TerrainType.WATER) # Asignar tipo AGUA con cierta probabilidad.
                     else:
                         terrain.set_terrain_type(x, y, TerrainType.GRASS) # El resto es pasto.

             # Asegurarse de que la altura y densidad base se establezcan según el tipo después de asignar.
             for y in range(height):
                  for x in range(width):
                       current_type = terrain.terrain_type_map[y, x]
                       if current_type in terrain.TERRAIN_PROPERTIES:
                            terrain.height_map[y, x] = terrain.TERRAIN_PROPERTIES[current_type]['base_height']
                            terrain.density_map[y, x] = terrain.TERRAIN_PROPERTIES[current_type]['base_density']

        # Añade aquí bloques 'elif preset_name == "nombre_del_mapa":' para otros presets.
        # Por ejemplo: "arabia", "black_forest", "team_islands", etc.
        # Implementa la lógica para generar self.terrain_type_map, self.height_map, y self.density_map
        # de acuerdo al diseño visual de cada mapa de AoE II.

        # --- Fin de implementación de presets de mapa ---


        # Asegurarse de que los mapas relacionados con la conquista estén limpios al inicio de una nueva simulación o reset.
        terrain.last_controlling_team.fill(0) # Inicializar el último controlador a neutral para todas las celdas.
        terrain.conquest_map.fill(0) # Inicializar el mapa de conquista oficial a neutral para todas las celdas.
        terrain.conquest_progress.fill(0.0) # Inicializar el progreso de conquista a 0.0 para todas las celdas.
        terrain.control_points.fill(0) # Inicializar el mapa de control inmediato (visual) a neutral para todas las celdas.

        # Retornar la instancia de Terrain recién creada y configurada.
        return terrain


    def get_conquest_percentage(self, team_id: int) -> float:
        """
        Calculate the percentage of terrain officially conquered by a specific team.
        Returns a value between 0.0 and 100.0.
        """
        total_cells = self.width * self.height # Número total de celdas en el terreno.
        if total_cells == 0:
            return 0.0 # Evitar división por cero si el terreno no tiene dimensiones.

        # Contar el número de celdas donde el mapa de conquista oficial coincide con el team_id especificado.
        conquered_cells = np.sum(self.conquest_map == team_id)
        # Calcular el porcentaje y redondearlo para la presentación.
        return (conquered_cells / total_cells) * 100 # Puedes redondear aquí si lo necesitas, ej: round(..., 1)

    def get_control_points(self) -> np.ndarray:
        """
        Get the current control points map.
        This map indicates immediate control based on unit proximity in the last update step.
        Used primarily for visualization.
        """
        return self.control_points # Retorna la matriz de control_points.

    def get_conquest_progress(self) -> np.ndarray:
        """
        Get the current conquest progress map.
        This map shows the progress towards official conquest for each cell (0.0 to 1.0).
        """
        return self.conquest_progress # Retorna la matriz de progreso de conquista.

    def get_terrain_type_map(self) -> np.ndarray:
        """
        Get the current terrain type map.
        This map indicates the base type of terrain (GRASS, WATER, etc.) for each cell.
        """
        return self.terrain_type_map # Retorna la matriz de tipos de terreno.