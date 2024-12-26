import json
from pymavlink import mavutil
import pymavlink.dialects.v20.all as dialect


def _setGEOFence(self, polygons):
    """
    Configura geofences en forma de múltiples polígonos.
    :param polygons: Lista de polígonos, donde cada polígono es una lista de coordenadas.
    """
    try:
        # Habilitar geofence
        self.vehicle.mav.param_set_send(
            self.vehicle.target_system,
            self.vehicle.target_component,
            b"FENCE_ENABLE",
            float(1),  # Activar geofence
            mavutil.mavlink.MAV_PARAM_TYPE_REAL32,
        )

        # Configurar la acción (mantener dentro)
        self.vehicle.mav.param_set_send(
            self.vehicle.target_system,
            self.vehicle.target_component,
            b"FENCE_ACTION",
            float(4),  # Acción: Mantener dentro
            mavutil.mavlink.MAV_PARAM_TYPE_REAL32,
        )

        for polygon in polygons:
            # Validar que el polígono tiene al menos 3 puntos
            if len(polygon) < 3:
                raise ValueError("Cada polígono debe tener al menos 3 puntos.")

            # Número total de puntos en el polígono (incluyendo cierre)
            fence_points = len(polygon) + 1

            # Enviar número de puntos del geofence
            self.vehicle.mav.param_set_send(
                self.vehicle.target_system,
                self.vehicle.target_component,
                b"FENCE_TOTAL",
                float(fence_points),
                mavutil.mavlink.MAV_PARAM_TYPE_REAL32,
            )

            # Enviar los puntos del polígono
            for idx, point in enumerate(polygon):
                self.vehicle.mav.send(
                    mavutil.mavlink.MAVLink_fence_point_message(
                        self.vehicle.target_system,
                        self.vehicle.target_component,
                        idx % 256,  # Índice del punto (dentro del rango 0-255)
                        fence_points,
                        float(point["lat"]),
                        float(point["lon"]),
                    )
                )

            # Cerrar el polígono enviando el primer punto nuevamente
            first_point = polygon[0]
            self.vehicle.mav.send(
                mavutil.mavlink.MAVLink_fence_point_message(
                    self.vehicle.target_system,
                    self.vehicle.target_component,
                    len(polygon) % 256,
                    fence_points,
                    float(first_point["lat"]),
                    float(first_point["lon"]),
                )
            )
        print("Geofence aplicado correctamente.")
    except Exception as e:
        raise RuntimeError(f"Error al configurar el geofence: {e}")


def setGEOFence(self, polygons):
    """
    Configura un geofence basado en múltiples polígonos.
    :param polygons: Lista de polígonos, donde cada polígono es una lista de coordenadas.
    """
    try:
        print("Configurando geofence con los polígonos proporcionados...")
        _setGEOFence(self, polygons)
    except Exception as e:
        raise RuntimeError(f"Error al aplicar el geofence: {e}")
