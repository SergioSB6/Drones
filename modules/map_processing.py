import math
import json
from pymavlink import mavutil
from shapely.geometry import Polygon

GEO_ORIGIN_LAT = 41.2763696
GEO_ORIGIN_LON = 1.9884235

def calculate_coordinates(map_data):
    """
    Calcula las coordenadas geográficas para cada celda del mapa.
    :param map_data: Diccionario con datos del mapa.
    :return: Diccionario actualizado con coordenadas geográficas.
    """
    cell_size = map_data["map_size"]["cell_size"]
    map_width_cells = map_data["map_size"]["width"] // cell_size
    map_height_cells = map_data["map_size"]["height"] // cell_size

    METERS_PER_DEGREE_LAT = 111320
    METERS_PER_DEGREE_LON = METERS_PER_DEGREE_LAT * math.cos(math.radians(GEO_ORIGIN_LAT))

    map_data["cell_coordinates"] = []
    for row in range(map_height_cells):
        for col in range(map_width_cells):
            lat = GEO_ORIGIN_LAT - (row * cell_size / METERS_PER_DEGREE_LAT)
            lon = GEO_ORIGIN_LON + (col * cell_size / METERS_PER_DEGREE_LON)

            map_data["cell_coordinates"].append({"lat": lat, "lon": lon})

    return map_data

def prepare_geofence(map_data):
    """
    Convierte las celdas del geofence a coordenadas geográficas y las simplifica.
    :param map_data: Datos del mapa.
    :return: Lista de puntos geográficos simplificados.
    """
    if "geofence" not in map_data or "cell_coordinates" not in map_data:
        raise ValueError("El mapa no contiene geofence o coordenadas calculadas.")

    geofence_points = []
    cell_size = map_data["map_size"]["cell_size"]
    map_width_cells = map_data["map_size"]["width"] // cell_size

    # Convertir celdas a coordenadas geográficas
    for cell in map_data["geofence"]:
        row, col = cell["row"], cell["col"]
        cell_index = row * map_width_cells + col
        geofence_points.append(map_data["cell_coordinates"][cell_index])

    # Simplificar los puntos si exceden 255
    if len(geofence_points) > 255:
        geofence_points = simplify_geofence(geofence_points)

    return geofence_points

def simplify_geofence(geofence_points, tolerance=0.0001):
    """
    Simplifica el geofence utilizando el algoritmo de Douglas-Peucker.
    :param geofence_points: Lista de puntos geográficos (lat, lon).
    :param tolerance: Tolerancia para la simplificación.
    :return: Lista de puntos simplificados.
    """
    polygon = Polygon([(point["lon"], point["lat"]) for point in geofence_points])
    simplified_polygon = polygon.simplify(tolerance, preserve_topology=True)
    return [{"lat": coord[1], "lon": coord[0]} for coord in simplified_polygon.exterior.coords]

def get_geofence_polygons(map_data):
    """
    Calcula las esquinas interiores de los dos rectángulos del geofence (izquierda y derecha).
    :param map_data: Datos del mapa.
    :return: Lista de polígonos con coordenadas.
    """
    if "geofence" not in map_data or "cell_coordinates" not in map_data:
        raise ValueError("El mapa no contiene geofence o coordenadas calculadas.")

    geofence_cells = map_data["geofence"]
    cell_coordinates = map_data["cell_coordinates"]
    map_width_cells = map_data["map_size"]["width"] // map_data["map_size"]["cell_size"]

    def get_corner(row, col):
        return cell_coordinates[row * map_width_cells + col]

    # Filtrar celdas por regiones (izquierda y derecha)
    left_cells = [cell for cell in geofence_cells if cell["region"] == "left"]
    right_cells = [cell for cell in geofence_cells if cell["region"] == "right"]

    if not left_cells or not right_cells:
        raise ValueError("Faltan celdas en una de las regiones del geofence.")

    # Obtener las esquinas para los polígonos
    left_top = min(left_cells, key=lambda c: (c["row"], c["col"]))
    left_bottom = max(left_cells, key=lambda c: (c["row"], c["col"]))
    right_top = min(right_cells, key=lambda c: (c["row"], c["col"]))
    right_bottom = max(right_cells, key=lambda c: (c["row"], c["col"]))

    polygons = [
        [
            get_corner(left_top["row"], left_top["col"]),  # Superior izquierda
            get_corner(left_top["row"], left_bottom["col"]),  # Superior derecha
            get_corner(left_bottom["row"], left_bottom["col"]),  # Inferior derecha
            get_corner(left_bottom["row"], left_top["col"]),  # Inferior izquierda
        ],
        [
            get_corner(right_top["row"], right_top["col"]),  # Superior izquierda
            get_corner(right_top["row"], right_bottom["col"]),  # Superior derecha
            get_corner(right_bottom["row"], right_bottom["col"]),  # Inferior derecha
            get_corner(right_bottom["row"], right_top["col"]),  # Inferior izquierda
        ],
    ]

    return polygons

