# dron_setGeofence.py
import json
from pymavlink import mavutil
import pymavlink.dialects.v20.all as dialect

def _setGEOFence(self, polygons):
    """
    Configura geofences en forma de múltiples polígonos en ArduPilot.
    :param polygons: Lista de polígonos, donde cada polígono es una lista de diccionarios
                     con {"lat": float, "lon": float}.
    """
    try:
        # Activar el geofence
        self.vehicle.mav.param_set_send(
            self.vehicle.target_system,
            self.vehicle.target_component,
            b"FENCE_ENABLE",
            float(1),  # Activa geofence
            mavutil.mavlink.MAV_PARAM_TYPE_REAL32,
        )
        # Configurar la acción (por ejemplo, mantener dentro)
        self.vehicle.mav.param_set_send(
            self.vehicle.target_system,
            self.vehicle.target_component,
            b"FENCE_ACTION",
            float(4),  # Acción: Mantener dentro (verifica según tu firmware)
            mavutil.mavlink.MAV_PARAM_TYPE_REAL32,
        )
        self.vehicle.mav.param_set_send(
            self.vehicle.target_system,
            self.vehicle.target_component,
            b"FENCE_TYPE",
            float(7),  # 7 = Inclusion
            mavutil.mavlink.MAV_PARAM_TYPE_REAL32,
        )

        # Unificar todos los polígonos en una lista de puntos (cerrando cada polígono)
        all_points = []
        for polygon in polygons:
            if len(polygon) < 3:
                raise ValueError("Cada polígono debe tener al menos 3 puntos.")
            closed_polygon = polygon + [polygon[0]]  # Cierra el polígono
            all_points.extend(closed_polygon)

        fence_total = len(all_points)
        if fence_total > 255:
            raise ValueError("El número total de puntos no puede exceder 255.")

        # Enviar FENCE_TOTAL (una sola vez)
        self.vehicle.mav.param_set_send(
            self.vehicle.target_system,
            self.vehicle.target_component,
            b"FENCE_TOTAL",
            float(fence_total),
            mavutil.mavlink.MAV_PARAM_TYPE_REAL32,
        )

        # Enviar cada punto
        for idx, point in enumerate(all_points):
            self.vehicle.mav.send(
                mavutil.mavlink.MAVLink_fence_point_message(
                    self.vehicle.target_system,
                    self.vehicle.target_component,
                    idx,
                    fence_total,
                    float(point[0]),
                    float(point[1]),
                )
            )
        print("Geofence aplicado correctamente con", fence_total, "puntos.")
    except Exception as e:
        raise RuntimeError(f"Error al configurar el geofence: {e}")

def setGEOFence(self, polygons):
    """
    Configura un geofence basado en múltiples polígonos.
    :param polygons: Lista de polígonos, donde cada polígono es una lista de diccionarios
                     con {"lat": float, "lon": float}.
    """
    try:
        print("Configurando geofence con los polígonos proporcionados...")
        _setGEOFence(self, polygons)
    except Exception as e:
        raise RuntimeError(f"Error al aplicar el geofence: {e}")
