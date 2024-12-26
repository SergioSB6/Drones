import os
import customtkinter as ctk
from tkinter import filedialog, messagebox, Toplevel
import json
from PIL import Image, ImageTk
from modules.map_processing import calculate_coordinates, get_geofence_polygons

class CheckpointScreen:
    def __init__(self, dron, parent_frame):
        # Frame principal
        self.dron = dron
        self.map_data = None
        self.connected_drones = []  # Lista de drones conectados
        self.frame = parent_frame  # Contenedor principal

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
            global dron
            connection_string = "tcp:127.0.0.1:5762"
            baud = 115200
            try:
                print(f"Intentando conectar a {connection_string} con baud {baud}...")

                if self.dron.connect(connection_string, baud):
                    print("Conexión exitosa al dron.")
                    self.connected_drones.append(self.dron)
                    self.update_player_list()
                    dron= self.dron
                    messagebox.showinfo("Conexión Exitosa", "Jugador conectado correctamente.")
                else:
                    messagebox.showerror("Error", "No se pudo conectar al dron.")
            except Exception as e:
                print(f"Error inesperado: {e}")
                messagebox.showerror("Error", f"Ocurrió un error inesperado: {e}")

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

    def start_telemetry_update(self):
        """
        Inicia una actualización periódica para mostrar la telemetría del dron.
        """
        if not self.dron.is_connected:
            messagebox.showwarning("Advertencia", "El dron no está conectado.")
            return

        def update_telemetry():
            telemetry = self.dron.get_local_telemetry()
            if telemetry:
                position = f"Posición: Lat {telemetry['lat']}, Lon {telemetry['lon']}, Alt {telemetry['alt']}"
                velocity = f"Velocidad: {telemetry['vel']} m/s"
                mode = f"Modo: {telemetry['mode']}"
                self.telemetry_label.configure(text=f"{position}\n{velocity}\n{mode}")
            self.frame.after(1000, update_telemetry)

        update_telemetry()

        # Añade esta etiqueta a tu interfaz
        self.telemetry_label = ctk.CTkLabel(self.frame, text="Telemetría: No disponible", font=("Arial", 12))
        self.telemetry_label.place(relx=0.05, rely=0.1, anchor="nw")

    def link_controls_to_map(self, control_window):
        """
        Vincula los controles de administración con el mapa.
        """

        def move_dron_on_map(direction):
            # Movemos el dron físicamente
            self.dron.go(direction)

            # Obtenemos la posición actualizada
            telemetry = self.dron.get_local_telemetry()
            if telemetry:
                lat, lon = telemetry["lat"], telemetry["lon"]

                # Convertimos la posición geográfica a coordenadas del canvas
                cell = self.get_canvas_coordinates_from_gps(lat, lon)
                if cell:
                    x, y = cell
                    self.game_canvas.coords("player_drone_1", x, y)

        # Vinculamos los botones de navegación
        for direction in ["NorthWest", "North", "NorthEast", "West", "Stop", "East", "SouthWest", "South", "SouthEast"]:
            control_window.link_button_to_direction(direction, move_dron_on_map)

    def get_canvas_coordinates_from_gps(self, lat, lon):
        """
        Convierte coordenadas GPS a coordenadas del canvas.
        """
        if not self.map_data or not self.map_data.get("cell_coordinates"):
            return None

        for idx, cell in enumerate(self.map_data["cell_coordinates"]):
            if abs(cell["lat"] - lat) < 0.0001 and abs(cell["lon"] - lon) < 0.0001:
                row = idx // self.map_data["map_size"]["width"]
                col = idx % self.map_data["map_size"]["width"]
                x = col * self.map_data["map_size"]["cell_size"]
                y = row * self.map_data["map_size"]["cell_size"]
                return x, y
        return None

    def start_game(self):
        if not self.map_data:
            messagebox.showwarning("Advertencia", "Selecciona un mapa antes de jugar.")
            return

        if not self.connected_drones:
            messagebox.showwarning("Advertencia", "Conecta al menos un jugador antes de iniciar el juego.")
            return

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

        # Dibujar drones para jugadores conectados
        try:
            drone_image_path = "assets/dron.png"
            drone_image = Image.open(drone_image_path).resize((cell_size, cell_size), Image.LANCZOS)
            self.drone_image_full = ImageTk.PhotoImage(drone_image)

            # Tamaño del mapa en celdas
            map_width_cells = self.map_data["map_size"]["width"] // self.map_data["map_size"]["cell_size"]
            map_height_cells = self.map_data["map_size"]["height"] // self.map_data["map_size"]["cell_size"]

            # Obtener celdas fuera del geofence
            geofence_cells = {(cell["row"], cell["col"]) for cell in self.map_data["geofence"]}
            positions = []

            # Jugador 1: Columna central en la mitad izquierda
            left_center_col = map_width_cells // 4
            for row in reversed(range(map_height_cells)):
                if (row, left_center_col) not in geofence_cells:
                    positions.append((left_center_col * cell_size, row * cell_size))
                    break

            # Jugador 2: Columna central en la mitad derecha
            right_center_col = (map_width_cells // 4) * 3
            for row in reversed(range(map_height_cells)):
                if (row, right_center_col) not in geofence_cells:
                    positions.append((right_center_col * cell_size, row * cell_size))
                    break

            # Posicionar drones en las celdas calculadas
            for idx, dron in enumerate(self.connected_drones):
                if idx < len(positions):
                    x, y = positions[idx]
                    game_canvas.create_image(x, y, anchor="nw", image=self.drone_image_full,
                                             tag=f"player_drone_{idx + 1}")

        except Exception as e:
            print(f"Error cargando la imagen del dron: {e}")


        messagebox.showinfo("Juego Iniciado", "¡Comenzando la carrera con los jugadores conectados!")

    def callback_volver(self):
        # Función para volver al menú principal
        self.frame.tkraise()
