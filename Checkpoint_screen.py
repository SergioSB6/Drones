import os
import customtkinter as ctk
from tkinter import filedialog, messagebox, Toplevel
import json
import time
from PIL import Image, ImageTk
from PIL.features import modules
from click import command

from modules.dron_setGeofence import setGEOFence
from modules.map_processing import calculate_coordinates
from modules.dron_local_telemetry import send_local_telemetry_info
import math
from modules.dron_nav import go, changeHeading
from modules.dron_mission import executeMission


class CheckpointScreen:
    def __init__(self, dron, parent_frame):
        # Frame principal
        self.dron = dron
        self.map_data = None
        self.connected_drones = []  # Lista de drones conectados
        self.player_positions = {}
        self.frame = parent_frame  # Contenedor principal
        self.reset_player_positions()

        # Título
        label_title = ctk.CTkLabel(master=self.frame, text="CHECKPOINT RACE MODE", font=("M04_FATAL FURY", 50))
        label_title.place(relx=0.5, rely=0.05, anchor="n")

        # Lista de jugadores
        self.player_listbox = ctk.CTkTextbox(master=self.frame, width=300, height=300)
        self.player_listbox.place(relx=0.2, rely=0.4, anchor="center")
        label_players = ctk.CTkLabel(master=self.frame, text="LISTA DE JUGADORES", font=("M04_FATAL FURY", 20))
        label_players.place(relx=0.2, rely=0.25, anchor="center")

        # Vista previa del mapa
        self.preview_label = ctk.CTkLabel(master=self.frame, text="PREVIEW MAPA", font=("M04_FATAL FURY", 20))
        self.preview_label.place(relx=0.7, rely=0.25, anchor="center")

        self.map_canvas = ctk.CTkCanvas(self.frame, width=300, height=300, bg="gray")
        self.map_canvas.place(relx=0.7, rely=0.45, anchor="center")

        # Botón Seleccionar Mapa
        self.boton_select_map = ctk.CTkButton(master=self.frame, text="Seleccionar Mapa", command=self.select_map)
        self.boton_select_map.place(relx=0.7, rely=0.8, anchor="center")

        # Botón Conectar Jugador
        self.boton_connect = ctk.CTkButton(master=self.frame, text="Conectar Jugador", command=self.connect_player)
        self.boton_connect.place(relx=0.5, rely=0.8, anchor="center")

        # Botón Jugar
        self.boton_jugar = ctk.CTkButton(master=self.frame, text="Jugar", command=self.start_game)
        self.boton_jugar.place(relx=0.5, rely=0.9, anchor="center")

        # Botón Volver
        self.boton_volver = ctk.CTkButton(master=self.frame, text="Return", font=("M04_FATAL FURY", 30),
                                          fg_color="transparent", hover=False, command=self.callback_volver)
        self.boton_volver.place(relx=0.05, rely=0.95, anchor="sw")
        self.player_id=0
    def select_map(self):
        # Selección de archivo
        file_path = filedialog.askopenfilename(filetypes=[("JSON Files", "*.json")])
        if not file_path:
            return

        # Cargar el archivo JSON del mapa
        try:
            with open(file_path, "r") as file:
                self.map_data = json.load(file)

            # Generar coordenadas geográficas para las celdas
            self.map_data = calculate_coordinates(self.map_data)

            # Dibujar una vista previa del mapa
            self.render_map_preview()
            messagebox.showinfo("Mapa Cargado", "Mapa cargado correctamente.")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo cargar el mapa: {e}")

    def connect_player(self):
        connection_string = "tcp:127.0.0.1:5762"
        baud = 115200
        try:
            print(f"Intentando conectar a {connection_string} con baud {baud}...")

            if self.dron.connect(connection_string, baud):
                print("Conexión exitosa al dron.")
                self.connected_drones.append(self.dron)

                # Inicia la telemetría después de conectar
                self.dron.send_telemetry_info(self.process_telemetry_info)

                self.update_player_list()
                messagebox.showinfo("Conexión Exitosa", "Jugador conectado correctamente.")
            else:
                messagebox.showerror("Error", "No se pudo conectar al dron.")
        except Exception as e:
            print(f"Error inesperado: {e}")
            messagebox.showerror("Error", f"Ocurrió un error inesperado: {e}")

    def process_telemetry_info(self, telemetry_info):
        """
        Procesa la información de telemetría recibida.
        """
        print(f"Telemetría recibida: {telemetry_info}")

        # Actualizar latitud y longitud iniciales
        if telemetry_info['lat'] != 0.0 and telemetry_info['lon'] != 0.0:
            self.initial_lat = telemetry_info['lat']
            self.initial_lon = telemetry_info['lon']
            print(f"Coordenadas iniciales asignadas: lat={self.initial_lat}, lon={self.initial_lon}")
        else:
            print("Las coordenadas recibidas no son válidas.")

    def reset_player_positions(self):
        """
        Reinicia las posiciones iniciales de los jugadores.
        """
        self.player_positions = {}  # Reiniciar las posiciones



    def update_player_list(self):
        self.player_listbox.delete("1.0", "end")
        for idx, dron in enumerate(self.connected_drones, start=1):
            self.player_listbox.insert("end", f"Jugador {idx}: {dron.state}\n")

    def render_map_preview(self):
        # Limpiar el canvas antes de redibujar
        self.map_canvas.delete("all")

        if not self.map_data:
            return

        # Tamaño del mapa en celdas
        map_width_cells = self.map_data["map_size"]["width"] // self.map_data["map_size"]["cell_size"]
        map_height_cells = self.map_data["map_size"]["height"] // self.map_data["map_size"]["cell_size"]

        # Escalar el mapa para que encaje en el canvas de vista previa (300x300)
        scale_x = 300 / map_width_cells
        scale_y = 300 / map_height_cells
        scale = min(scale_x, scale_y)

        # Calcular offset para centrar
        offset_x = (300 - (map_width_cells * scale)) / 2
        offset_y = (300 - (map_height_cells * scale)) / 2

        # Ajustar fondo
        background_path = self.map_data.get("background")
        if background_path and os.path.exists(background_path):
            try:
                background_image = Image.open(background_path)
                resized_image = background_image.resize((int(map_width_cells * scale), int(map_height_cells * scale)),
                                                        Image.LANCZOS)
                self.background_image_preview = ImageTk.PhotoImage(resized_image)
                self.map_canvas.create_image(offset_x, offset_y, anchor="nw", image=self.background_image_preview)
            except Exception as e:
                print(f"Error cargando el fondo: {e}")

        # Dibujar geofence
        for fence in self.map_data.get("geofence", []):
            col, row = fence["col"], fence["row"]
            x1 = offset_x + col * scale
            y1 = offset_y + row * scale
            x2 = x1 + scale
            y2 = y1 + scale
            self.map_canvas.create_rectangle(x1, y1, x2, y2, fill="red", outline="red")

        # Dibujar obstáculos
        obstacle_image_path = self.map_data.get("obstacle_image")
        obstacle_image = None
        if obstacle_image_path and os.path.exists(obstacle_image_path):
            try:
                obstacle_image = Image.open(obstacle_image_path).resize((int(scale), int(scale)), Image.LANCZOS)
                self.obstacle_image_preview = ImageTk.PhotoImage(obstacle_image)
            except Exception as e:
                print(f"Error cargando la imagen del obstáculo: {e}")

        for obstacle in self.map_data.get("obstacles", []):
            # Original
            col, row = obstacle["original"]["col"], obstacle["original"]["row"]
            x = offset_x + col * scale
            y = offset_y + row * scale
            if obstacle_image:
                self.map_canvas.create_image(x, y, anchor="nw", image=self.obstacle_image_preview)
            else:
                self.map_canvas.create_rectangle(x, y, x + scale, y + scale, fill="yellow", outline="yellow")

            # Espejo
            mirror_col, mirror_row = obstacle["mirror"]["col"], obstacle["mirror"]["row"]
            mx = offset_x + mirror_col * scale
            my = offset_y + mirror_row * scale
            if obstacle_image:
                self.map_canvas.create_image(mx, my, anchor="nw", image=self.obstacle_image_preview)
            else:
                self.map_canvas.create_rectangle(mx, my, mx + scale, my + scale, fill="yellow", outline="yellow")


    def start_game(self):
        if not self.map_data:
            messagebox.showwarning("Advertencia", "Selecciona un mapa antes de jugar.")
            return

        #if not self.connected_drones:
         #   messagebox.showwarning("Advertencia", "Conecta al menos un jugador antes de iniciar el juego.")
          #  return

        # Crear ventana emergente para mostrar el mapa completo
        game_window = Toplevel()
        game_window.title("Checkpoint Race - Mapa")

        map_width = self.map_data["map_size"]["width"]
        map_height = self.map_data["map_size"]["height"]
        cell_size = self.map_data["map_size"]["cell_size"]

        game_window.geometry(f"{map_width}x{map_height}")

        # Canvas para el mapa completo
        game_canvas = ctk.CTkCanvas(game_window, width=map_width, height=map_height, bg="gray")
        game_canvas.pack(fill="both", expand=True)

        # Dibujar el fondo del mapa si está definido
        background_path = self.map_data.get("background")
        if background_path and os.path.exists(background_path):
            try:
                background_image = Image.open(background_path).resize((map_width, map_height), Image.LANCZOS)
                self.background_image_full = ImageTk.PhotoImage(background_image)
                game_canvas.create_image(0, 0, anchor="nw", image=self.background_image_full)
            except Exception as e:
                print(f"Error cargando el fondo: {e}")

        # Dibujar geofence
        for cell in self.map_data.get("geofence", []):
            col, row = cell["col"], cell["row"]
            x1 = col * cell_size
            y1 = row * cell_size
            x2 = x1 + cell_size
            y2 = y1 + cell_size
            game_canvas.create_rectangle(x1, y1, x2, y2, fill="red", outline="red", tag="geofence")
            print(f"Dibujando celda de geofence: col={col}, row={row}, x1={x1}, y1={y1}")

        # Dibujar obstáculos (original y espejo)
        obstacle_image_path = self.map_data.get("obstacle_image")
        obstacle_image = None
        if obstacle_image_path and os.path.exists(obstacle_image_path):
            try:
                obstacle_image = Image.open(obstacle_image_path).resize((cell_size, cell_size), Image.LANCZOS)
                self.obstacle_image_full = ImageTk.PhotoImage(obstacle_image)
            except Exception as e:
                print(f"Error cargando la imagen del obstáculo: {e}")

        for obstacle in self.map_data.get("obstacles", []):
            col, row = obstacle["original"]["col"], obstacle["original"]["row"]
            x1 = col * cell_size
            y1 = row * cell_size
            if obstacle_image:
                game_canvas.create_image(x1, y1, anchor="nw", image=self.obstacle_image_full)
            else:
                x2 = x1 + cell_size
                y2 = y1 + cell_size
                game_canvas.create_rectangle(x1, y1, x2, y2, fill="yellow", outline="black", tag="obstacle")

            mirror_col, mirror_row = obstacle["mirror"]["col"], obstacle["mirror"]["row"]
            mx1 = mirror_col * cell_size
            my1 = mirror_row * cell_size
            if obstacle_image:
                game_canvas.create_image(mx1, my1, anchor="nw", image=self.obstacle_image_full)
            else:
                mx2 = mx1 + cell_size
                my2 = my1 + cell_size
                game_canvas.create_rectangle(mx1, my1, mx2, my2, fill="yellow", outline="black", tag="obstacle")

        try:
            drone_image_path = "assets/dron.png"
            if not os.path.exists(drone_image_path):
                raise FileNotFoundError(f"No se encontró la imagen del dron en {drone_image_path}")

            drone_image = Image.open(drone_image_path).resize((30, 30), Image.LANCZOS)
            self.drone_image_full = ImageTk.PhotoImage(drone_image)

            for idx, dron in enumerate(self.connected_drones):
                # Obtener las coordenadas actuales del dron
                lat, lon = dron.lat, dron.lon
                if lat == 0.0 and lon == 0.0:
                    print(f"Dron {idx + 1} no tiene coordenadas GPS válidas.")
                    continue

                # Convertir las coordenadas GPS a coordenadas del canvas
                x, y = self.get_canvas_coordinates_from_gps(lat, lon)
                if x is not None and y is not None:
                    print(f"Dibujando dron {idx + 1} en posición inicial: x={x}, y={y}")
                    game_canvas.create_image(x, y, anchor="nw", image=self.drone_image_full,
                                             tag=f"player_drone_{idx + 1}")
                else:
                    print(f"Error al calcular las coordenadas del canvas para el dron {idx + 1}.")
        except Exception as e:
            print(f"Error al dibujar el dron: {e}")

        messagebox.showinfo("Juego Iniciado", "¡Comenzando la carrera con los jugadores conectados!")

        self.start_telemetry_sync(game_canvas)

    def get_canvas_coordinates_from_gps(self, lat, lon):
        """
        Convierte coordenadas GPS (lat, lon) en coordenadas del canvas del juego.
        """
        try:
            if not self.map_data:
                print("Mapa no cargado.")
                return None, None

            cell_size = self.map_data["map_size"]["cell_size"]
            map_width = self.map_data["map_size"]["width"]
            map_height = self.map_data["map_size"]["height"]

            delta_lat = self.initial_lat - lat
            delta_lon = lon - self.initial_lon

            col = delta_lon * (111320 * math.cos(math.radians(self.initial_lat))) / cell_size
            row = delta_lat * 111320 / cell_size

            x = col * cell_size
            y = row * cell_size

            if 0 <= x <= map_width and 0 <= y <= map_height:
                return x, y
            else:
                print("Coordenadas fuera de los límites del mapa.")
                return None, None
        except Exception as e:
            print(f"Error en get_canvas_coordinates_from_gps: {e}")
            return None, None

    def start_telemetry_sync(self, canvas):
        """
        Sincroniza las coordenadas del dron en el canvas con base en la telemetría recibida.
        """

        def update():
            while True:
                try:
                    # Obtener las coordenadas GPS del dron
                    lat = self.dron.lat
                    lon = self.dron.lon

                    if lat == 0.0 and lon == 0.0:
                        print("Dron 1 no tiene coordenadas GPS válidas.")
                        continue

                    # Convertir coordenadas GPS a coordenadas del canvas
                    x, y = self.get_canvas_coordinates_from_gps(lat, lon)

                    if x is not None and y is not None:
                        tag = "player_drone"
                        canvas.delete(tag)  # Elimina la posición anterior
                        canvas.create_oval(
                            x - 5, y - 5, x + 5, y + 5, fill="blue", outline="white", tag=tag
                        )
                        print(f"Dron actualizado en canvas: x={x}, y={y}")
                    else:
                        print("Error: Coordenadas del canvas no válidas.")
                except Exception as e:
                    print(f"Error en la sincronización de telemetría: {e}")
                time.sleep(0.1)  # Frecuencia de actualización

        # Iniciar un hilo independiente para la actualización
        import threading
        threading.Thread(target=update, daemon=True).start()

    def callback_volver(self):
        # Función para volver al menú principal
        self.frame.tkraise()
