import os
import customtkinter as ctk
from tkinter import filedialog, messagebox, Toplevel
import json
import math
from PIL import Image, ImageTk
from Dron import Dron
import time
import threading
import winsound

# Módulos de dron
from modules.dron_setGeofence import setGEOFence
from modules.dron_local_telemetry import send_local_telemetry_info
from modules.dron_nav import go, changeHeading

class CheckpointScreen:
    def __init__(self, dron, dron2, parent_frame):
        self.dron = dron
        self.dron2 = dron2
        self.map_data = None
        self.connected_drones = []
        self.player_positions = {}
        self.frame = parent_frame
        self.is_on_obstacle = False
        self.is_on_obstacle2 = False
        self.drone_image_full = None

        # ---------------- CONFIGURAR GRID PRINCIPAL ----------------
        # Dividimos el frame en filas y columnas para acomodar widgets.
        self.frame.rowconfigure(0, weight=1)  # Para el título
        self.frame.rowconfigure(1, weight=1)  # Para la fila de "LISTA" vs "PREVIEW"
        self.frame.rowconfigure(2, weight=1)  # Para la fila donde pueden ir los botones
        self.frame.columnconfigure(0, weight=1)
        self.frame.columnconfigure(1, weight=1)

        # ---------------- TÍTULO ----------------
        label_title = ctk.CTkLabel(self.frame, text="CHECKPOINT RACE MODE", font=("M04_FATAL FURY", 50))
        # Lo ponemos en la primera fila, ocupando 2 columnas
        label_title.grid(row=0, column=0, columnspan=2, pady=20, sticky="n")

        # ---------------- LISTA DE JUGADORES (Columna 0) ----------------
        label_players = ctk.CTkLabel(self.frame, text="LISTA DE JUGADORES", font=("M04_FATAL FURY", 20))
        label_players.grid(row=1, column=0, padx=10, pady=(0, 5), sticky="n")

        self.player_listbox = ctk.CTkTextbox(self.frame, width=300, height=300)
        self.player_listbox.grid(row=2, column=0, padx=10, pady=5, sticky="n")

        # ---------------- PREVIEW MAPA (Columna 1) ----------------
        self.preview_label = ctk.CTkLabel(self.frame, text="PREVIEW MAPA", font=("M04_FATAL FURY", 20))
        self.preview_label.grid(row=1, column=1, padx=10, pady=(0, 5), sticky="n")

        self.map_canvas = ctk.CTkCanvas(self.frame, width=500, height=500, bg="gray")
        self.map_canvas.grid(row=2, column=1, padx=10, pady=5, sticky="n")

        # ---------------- FILA DE BOTONES AL FINAL ----------------
        # Creamos un frame para agrupar los botones en la parte inferior
        botones_frame = ctk.CTkFrame(self.frame)
        botones_frame.grid(row=3, column=0, columnspan=2, pady=(20, 10))

        self.boton_select_map = ctk.CTkButton(botones_frame, text="Seleccionar Mapa", command=self.select_map)
        self.boton_select_map.pack(side="left", padx=20)

        self.boton_connect = ctk.CTkButton(botones_frame, text="Conectar Jugador", command=self.connect_player)
        self.boton_connect.pack(side="left", padx=20)

        self.boton_jugar = ctk.CTkButton(botones_frame, text="Jugar", command=self.start_game)
        self.boton_jugar.pack(side="left", padx=20)

        self.boton_volver = ctk.CTkButton(self.frame, text="Return", font=("M04_FATAL FURY", 30),
                                          fg_color="transparent", hover=False, command=self.callback_volver)

    # ----------------------------------------------------------------------
    # 1) Seleccionar Mapa y mostrar preview
    # ----------------------------------------------------------------------
    def select_map(self):
        file_path = filedialog.askopenfilename(filetypes=[("JSON Files", "*.json")])
        if not file_path:
            return
        try:
            with open(file_path, "r") as file:
                self.map_data = json.load(file)
            self.render_map_preview()
            messagebox.showinfo("Mapa Cargado", "Mapa cargado correctamente.")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo cargar el mapa: {e}")

    # ----------------------------------------------------------------------
    # 2) Conectar Jugador (Dron) y activar telemetría
    # ----------------------------------------------------------------------
    def connect_player(self):

        baud = 115200
        try:
            connection_string = "tcp:127.0.0.1:5762"
            print(f"🔌 Intentando conectar a {connection_string} con baud {baud}...")
            self.dron.connect(connection_string, baud, blocking=True)
            if self.dron.state == "connected":
                print("✅Jugador 1 conectado.")
                self.connected_drones.append(self.dron)
                # Iniciar telemetría
                self.dron.send_telemetry_info(self.process_telemetry_info)
                self.update_player_list()
            else:
                messagebox.showerror("Error", "El dron no está en estado 'connected'.")
        except Exception as e:
            print(f"❌ Error en connect_player: {e}")
            messagebox.showerror("Error", f"Ocurrió un error inesperado: {e}")
            # Conexión del segundo dron (jugador 2)
        try:
            connection_string2 = "tcp:127.0.0.1:5772"
            print(f"Conectando jugador 2 a {connection_string2}...")
            self.dron2.connect(connection_string2, baud, blocking=True)
            if self.dron2.state == "connected":
                print("✅✅Jugador 2 conectado.")
                self.connected_drones.append(self.dron2)
                # Se puede usar un callback distinto si querés diferenciarlos
                self.dron2.send_telemetry_info(self.process_telemetry_info_second)
                self.update_player_list()
            else:
                messagebox.showerror("Error", "El dron del jugador 2 no está en estado 'connected'.")
        except Exception as e:
            messagebox.showerror("Error", f"Error conectando jugador 2: {e}")
    # ----------------------------------------------------------------------
    def get_gps_from_canvas_coordinates(self, x, y):
            """
            Converts canvas coordinates (x, y) back to GPS coordinates (lat, lon).
            Uses 'top_left' as a reference and 'cell_size' as px/m.
            """
            x_old = x
            y_old = y
            angulo = math.radians(72)
            x = x_old * math.cos(angulo) - y_old * math.sin(angulo)
            y = x_old * math.sin(angulo) + y_old * math.cos(angulo)

            if not self.map_data or "top_left" not in self.map_data:
                print("🚨 Mapa sin 'top_left'.")
                return None, None

            top_left_lat = self.map_data["top_left"]["lat"]
            top_left_lon = self.map_data["top_left"]["lon"]
            scale = self.map_data["map_size"]["cell_size"]

            # Convert back from pixels to meters
            delta_lon_m = x / scale
            delta_lat_m = y / scale

            # Convert back from meters to degrees
            lat = top_left_lat - (delta_lat_m / 111320.0)
            lon = top_left_lon + (delta_lon_m / (111320.0 * math.cos(math.radians(top_left_lat))))

            print(f"📌 Canvas → GPS: x={x:.2f}, y={y:.2f} → lat={lat:.6f}, lon={lon:.6f}")
            return lat, lon

    def check_if_on_obstacle_cell(self, x, y):
        cell_size = self.map_data["map_size"]["cell_size"]
        col = int(x / cell_size)+1
        row = int(y / cell_size)+1
        print("Dron en celda:", (col, row))

        obstacle_cells = set()
        for obs in self.map_data.get("obstacles", []):
            obstacle_cells.add((obs["original"]["col"], obs["original"]["row"]))
            obstacle_cells.add((obs["mirror"]["col"], obs["mirror"]["row"]))
        print("Celdas de obstáculo:", obstacle_cells)

        if (col, row) in obstacle_cells:

            if not self.is_on_obstacle:
                print("¡Alerta! Dron sobre obstáculo en celda", (col, row))
                winsound.PlaySound("assets/Bite.wav", winsound.SND_FILENAME | winsound.SND_ASYNC)
            self.is_on_obstacle = True
            return True
        self.is_on_obstacle=False
        return False

    def check_if_on_obstacle_cell_2(self, x, y):
        cell_size = self.map_data["map_size"]["cell_size"]
        col = int(x / cell_size) + 1
        row = int(y / cell_size) + 1
        print("Dron 2 en celda:", (col, row))

        obstacle_cells = set()
        for obs in self.map_data.get("obstacles", []):
            obstacle_cells.add((obs["original"]["col"], obs["original"]["row"]))
            obstacle_cells.add((obs["mirror"]["col"], obs["mirror"]["row"]))
        print("Celdas de obstáculo:", obstacle_cells)

        if (col, row) in obstacle_cells:

            if not self.is_on_obstacle2:
                print("¡Alerta! Dron 2 sobre obstáculo en celda", (col, row))
                winsound.PlaySound("assets/Bite.wav", winsound.SND_FILENAME | winsound.SND_ASYNC)
            self.is_on_obstacle2 = True
            return True
        self.is_on_obstacle2 = False
        return False

    def arm_and_takeoff(self, drone):
        try:
            print(f"Iniciando armado para {drone}")
            drone.arm()  # Comando para armar
            time.sleep(1)  # Espera para dar tiempo a que se procese el armado
            drone.takeOff(5)  # Comando para despegar a 5 metros
            print(f"Comando de despegue enviado para {drone}")
        except Exception as e:
            print(f"Error al armar/despegar {drone}: {e}")


    def start_game(self):
        if not self.map_data:
            messagebox.showwarning("Advertencia", "Selecciona un mapa antes de jugar.")
            return

        game_window = Toplevel()
        game_window.title("Checkpoint Race - Mapa")

        map_width = self.map_data["map_size"]["width"]
        map_height = self.map_data["map_size"]["height"]
        cell_size = self.map_data["map_size"]["cell_size"]

        game_window.geometry(f"{map_width}x{map_height}")
        game_canvas = ctk.CTkCanvas(game_window, width=map_width, height=map_height, bg="gray")
        game_canvas.pack(fill="both", expand=True)

        # Fondo
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

        lista_geo = [[[0,0], [0, 0], [0, 966], [210, 966], [210, 0]], [[224,0],[224,966],[434,966],[434,0]]]

        for poligono in lista_geo:
            for coordenada in poligono:
                lata, longanisa = self.get_gps_from_canvas_coordinates(coordenada[0],coordenada[1])
                coordenada[0] = lata
                coordenada[1] = longanisa
        self.dron.setGEOFence(lista_geo)
        self.dron2.setGEOFence(lista_geo)
        print(lista_geo)

        # Dibujar obstáculos
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

        # Cargar la imagen del dron
        try:
            drone_image_path = "assets/dron.png"
            if not os.path.exists(drone_image_path):
                raise FileNotFoundError(f"No se encontró la imagen del dron en {drone_image_path}")
            drone_image = Image.open(drone_image_path).resize((30, 30), Image.LANCZOS)
            self.drone_image_full = ImageTk.PhotoImage(drone_image)
        except Exception as e:
            print(f"Error al cargar la imagen del dron: {e}")

        messagebox.showinfo("Juego Iniciado", "¡Comenzando la carrera con los jugadores conectados!")
        self.start_telemetry_sync(game_canvas)
        self.start_telemetry_sync_second(game_canvas)
        print(self.get_gps_from_canvas_coordinates(0,0))

        threading.Thread(target=self.arm_and_takeoff, args=(self.dron,)).start()
        threading.Thread(target=self.arm_and_takeoff, args=(self.dron2,)).start()

    # ----------------------------------------------------------------------
    # 4) Telemetría y coordenadas
    # ----------------------------------------------------------------------
    def process_telemetry_info(self, telemetry_info):
        print(f"📡 Telemetría Jugador 1: {telemetry_info}")

    def process_telemetry_info_second(self, telemetry_info):
        print(f"📡 Telemetría Jugador 2: {telemetry_info}")

    def get_canvas_coordinates_from_gps(self, lat, lon):
        """
        Usa 'top_left' como referencia y 'cell_size' como px/m.
        """
        try:
            if not self.map_data or "top_left" not in self.map_data:
                print("🚨 Mapa sin 'top_left'.")
                return None, None

            top_left_lat = self.map_data["top_left"]["lat"]
            top_left_lon = self.map_data["top_left"]["lon"]
            scale = self.map_data["map_size"]["cell_size"]

            delta_lat_m = (top_left_lat - lat) * 111320.0
            delta_lon_m = (lon - top_left_lon) * (111320.0 * math.cos(math.radians(top_left_lat)))
            x = delta_lon_m * scale
            y = delta_lat_m * scale

            print(f"📌 GPS → Canvas: lat={lat}, lon={lon} → x={x:.2f}, y={y:.2f}")
            return x, y
        except Exception as e:
            print(f"❌ Error en get_canvas_coordinates_from_gps: {e}")
            return None, None



    def start_telemetry_sync(self, canvas):
        """
        Dibuja el dron cada 100ms según la lat/lon real.
        """

        def update():
            try:
                lat = self.dron.lat
                lon = self.dron.lon
                if lat == 0.0 and lon == 0.0:
                    print("⚠ Dron sin coordenadas GPS válidas.")
                else:
                    x, y = self.get_canvas_coordinates_from_gps(lat, lon)
                    if x is not None and y is not None and self.drone_image_full:
                        tag = "player_drone"
                        canvas.delete(tag)
                        # Clamping opcional
                        map_width = self.map_data["map_size"]["width"]
                        map_height = self.map_data["map_size"]["height"]
                        x_old=x
                        y_old=y
                        angulo=math.radians(-72)
                        x = x_old * math.cos(angulo) - y_old * math.sin(angulo)
                        y = x_old * math.sin(angulo) + y_old * math.cos(angulo)
                        x = max(0, min(map_width - 30, x))
                        y = max(0, min(map_height - 30, y))
                        if self.check_if_on_obstacle_cell(x, y):
                            print("Alerta: Dron sobre obstáculo.")
                        canvas.create_image(x, y, anchor="nw", image=self.drone_image_full, tag=tag)
                        print(f"✅ Dron en canvas: x={x:.1f}, y={y:.1f}")
                    else:
                        print("❌ No se pudo dibujar el dron (coords o imagen nulas).")
            except Exception as e:
                print(f"❌ Error en start_telemetry_sync: {e}")

            canvas.after(35, update)

        update()

    def start_telemetry_sync_second(self, canvas):
        def update():
            try:
                if not self.dron2:
                    return
                lat = self.dron2.lat
                lon = self.dron2.lon
                if lat == 0.0 and lon == 0.0:
                    print("⚠ Dron 2 sin coordenadas GPS válidas.")
                else:
                    x, y = self.get_canvas_coordinates_from_gps(lat, lon)
                    if x is not None and y is not None and self.drone_image_full:
                        tag = "player_drone_2"
                        canvas.delete(tag)
                        map_width = self.map_data["map_size"]["width"]
                        map_height = self.map_data["map_size"]["height"]
                        x_old = x
                        y_old = y
                        angulo = math.radians(-72)
                        x = x_old * math.cos(angulo) - y_old * math.sin(angulo)
                        y = x_old * math.sin(angulo) + y_old * math.cos(angulo)

                        x = max(0, min(map_width - 30, x))
                        y = max(0, min(map_height - 30, y))
                        if self.check_if_on_obstacle_cell_2(x, y):
                            print("Alerta: Dron 2 sobre obstáculo.")
                        canvas.create_image(x, y, anchor="nw", image=self.drone_image_full, tag=tag)
                        print(f"✅ Dron 2 en canvas: x={x:.1f}, y={y:.1f}")
                    else:
                        print("❌ No se pudo dibujar el dron 2 (coords o imagen nulas).")
            except Exception as e:
                print(f"❌ Error en start_telemetry_sync_second: {e}")
            canvas.after(35, update)

        update()

    # ----------------------------------------------------------------------
    # 5) Utilidades de la interfaz
    # ----------------------------------------------------------------------
    def update_player_list(self):
        self.player_listbox.delete("1.0", "end")

        # Comprueba el estado del primer dron
        if hasattr(self, "dron") and self.dron:
            self.player_listbox.insert("end", f"Jugador 1: {self.dron.state}\n")
        else:
            self.player_listbox.insert("end", "Jugador 1: No conectado\n")

        # Comprueba el estado del segundo dron
        if hasattr(self, "dron2") and self.dron2:
            self.player_listbox.insert("end", f"Jugador 2: {self.dron2.state}\n")
        else:
            self.player_listbox.insert("end", "Jugador 2: No conectado\n")

    def render_map_preview(self):
        """
        Muestra un preview de 300x300 del mapa en self.map_canvas.
        """
        self.map_canvas.delete("all")
        if not self.map_data:
            return

        map_width = self.map_data["map_size"]["width"]
        map_height = self.map_data["map_size"]["height"]
        cell_size = self.map_data["map_size"]["cell_size"]

        if cell_size <= 0:
            print("⚠ cell_size inválido en map_data.")
            return
        map_width_cells = map_width // cell_size
        map_height_cells = map_height // cell_size
        scale_x = 500 / map_width_cells if map_width_cells else 1
        scale_y = 500 / map_height_cells if map_height_cells else 1
        scale = min(scale_x, scale_y)
        offset_x = (500 - (map_width_cells * scale)) / 2
        offset_y = (500 - (map_height_cells * scale)) / 2

        background_path = self.map_data.get("background")
        if background_path and os.path.exists(background_path):
            try:
                background_image = Image.open(background_path)
                resized_image = background_image.resize(
                    (int(map_width_cells * scale), int(map_height_cells * scale)), Image.LANCZOS
                )
                self.background_image_preview = ImageTk.PhotoImage(resized_image)
                self.map_canvas.create_image(offset_x, offset_y, anchor="nw", image=self.background_image_preview)
            except Exception as e:
                print(f"Error cargando el fondo: {e}")

        # Pintar geofence
        for fence in self.map_data.get("geofence", []):
            col, row = fence["col"], fence["row"]
            x1 = offset_x + col * scale
            y1 = offset_y + row * scale
            x2 = x1 + scale
            y2 = y1 + scale
            self.map_canvas.create_rectangle(x1, y1, x2, y2, fill="red", outline="red")

        # Pintar obstáculos
        obstacle_image_path = self.map_data.get("obstacle_image")
        obstacle_image = None
        if obstacle_image_path and os.path.exists(obstacle_image_path):
            try:
                obstacle_image = Image.open(obstacle_image_path).resize((int(scale), int(scale)), Image.LANCZOS)
                self.obstacle_image_preview = ImageTk.PhotoImage(obstacle_image)
            except Exception as e:
                print(f"Error cargando la imagen del obstáculo: {e}")

        for obstacle in self.map_data.get("obstacles", []):
            col, row = obstacle["original"]["col"], obstacle["original"]["row"]
            x = offset_x + col * scale
            y = offset_y + row * scale
            if obstacle_image:
                self.map_canvas.create_image(x, y, anchor="nw", image=self.obstacle_image_preview)
            else:
                self.map_canvas.create_rectangle(x, y, x + scale, y + scale, fill="yellow", outline="yellow")

            mirror_col, mirror_row = obstacle["mirror"]["col"], obstacle["mirror"]["row"]
            mx = offset_x + mirror_col * scale
            my = offset_y + mirror_row * scale
            if obstacle_image:
                self.map_canvas.create_image(mx, my, anchor="nw", image=self.obstacle_image_preview)
            else:
                self.map_canvas.create_rectangle(mx, my, mx + scale, my + scale, fill="yellow", outline="yellow")

    def callback_volver(self):
        self.frame.tkraise()
