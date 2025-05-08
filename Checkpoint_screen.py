import os
import customtkinter as ctk
from tkinter import filedialog, messagebox, Toplevel
import json
import math
from PIL import Image, ImageTk
from Dron import Dron
import time
from playsound import playsound
import threading
import winsound
import pywinstyles
# Módulos de dron
from modules.dron_setGeofence import setGEOFence
from modules.dron_local_telemetry import send_local_telemetry_info
from modules.dron_nav import go, changeHeading


class CheckpointScreen:
    def __init__(self, dron, parent_frame):
        self.dron = dron
        self.second_dron = Dron()
        self.map_data = None
        self.connected_drones = []
        self.player_positions = {}
        self.frame = parent_frame
        self.is_on_obstacle = False
<<<<<<< HEAD
        self.drone_image_full = None

        # Título
=======
        self.is_on_obstacle2 = False
        self.drone1_image_full = None
        self.drone2_image_full = None
        # Vida de cada dron (0.0 .. 1.0)
        self.life1 = 1.0
        self.life2 = 1.0
        # “facil” resta un 5%, “medio” 10%, “dificil” 25% al chocar.
        self.difficulty = "medio"
        self.damage_map = {"facil": 0.05, "medio": 0.1, "dificil": 0.25}
        self.hitbox_map = {"facil": 2, "medio": 1, "dificil": 0.5}
        self.raw_checkpoints = []  # lista completa de {id, original:{col,row}, mirror:{col,row}}
        self.queue_j1 = []  # checkpoints pendientes para jugador 1 (original)
        self.queue_j2 = []  # idem para jugador 2 (mirror)
        self.current_cp_j1 = None  # {col,row, item_id}
        self.current_cp_j2 = None
        self.cp1_count = 0  # recogidos por J1
        self.cp2_count = 0
        self.cp1_label = None
        self.cp2_label = None
        # ---------------- CONFIGURAR GRID PRINCIPAL ----------------
        # Dividimos el frame en filas y columnas para acomodar widgets.
        self.frame.rowconfigure(0, weight=1)  # Para el título
        self.frame.rowconfigure(1, weight=1)  # Para la fila de "LISTA" vs "PREVIEW"
        self.frame.rowconfigure(2, weight=1)  # Para la fila donde pueden ir los botones
        self.frame.columnconfigure(0, weight=1)
        self.frame.columnconfigure(1, weight=1)

        # ---------------- TÍTULO ----------------
>>>>>>> 2013fb8 (Juego funcional)
        label_title = ctk.CTkLabel(self.frame, text="CHECKPOINT RACE MODE", font=("M04_FATAL FURY", 50))
        label_title.place(relx=0.5, rely=0.05, anchor="n")

        # Lista de jugadores
        self.player_listbox = ctk.CTkTextbox(self.frame, width=300, height=300)
        self.player_listbox.place(relx=0.2, rely=0.4, anchor="center")
        label_players = ctk.CTkLabel(self.frame, text="LISTA DE JUGADORES", font=("M04_FATAL FURY", 20))
        label_players.place(relx=0.2, rely=0.25, anchor="center")

        # Vista previa del mapa
        self.preview_label = ctk.CTkLabel(self.frame, text="PREVIEW MAPA", font=("M04_FATAL FURY", 20))
        self.preview_label.place(relx=0.7, rely=0.25, anchor="center")

        self.map_canvas = ctk.CTkCanvas(self.frame, width=300, height=300, bg="gray")
        self.map_canvas.place(relx=0.7, rely=0.45, anchor="center")

<<<<<<< HEAD
        # Botones
        self.boton_select_map = ctk.CTkButton(self.frame, text="Seleccionar Mapa", command=self.select_map)
        self.boton_select_map.place(relx=0.7, rely=0.8, anchor="center")

        self.boton_connect = ctk.CTkButton(self.frame, text="Conectar Jugador", command=self.connect_player)
        self.boton_connect.place(relx=0.5, rely=0.8, anchor="center")

        self.boton_jugar = ctk.CTkButton(self.frame, text="Jugar", command=self.start_game)
        self.boton_jugar.place(relx=0.5, rely=0.9, anchor="center")
=======
        # ---------------- FILA DE BOTONES AL FINAL ----------------
        botones_frame = ctk.CTkFrame(self.frame)
        botones_frame.grid(row=3, column=0, columnspan=2, pady=(20, 10))

        # Selector de dificultad
        self.difficulty_var = ctk.StringVar(value=self.difficulty.capitalize())
        ctk.CTkLabel(botones_frame, text="Dificultad:", font=("M04_FATAL FURY", 18)).pack(side="left", padx=(10, 5))
        self.diff_menu = ctk.CTkOptionMenu(
            botones_frame,
            values=["Facil", "Medio", "Dificil"],
            variable=self.difficulty_var,
            command=self.on_difficulty_change
        )
        self.diff_menu.pack(side="left", padx=(0, 20))

        # Botones de acción
        self.boton_select_map = ctk.CTkButton(botones_frame, text="Seleccionar Mapa", command=self.select_map)
        self.boton_select_map.pack(side="left", padx=10)

        self.boton_connect = ctk.CTkButton(botones_frame, text="Conectar Jugador", command=self.connect_player)
        self.boton_connect.pack(side="left", padx=10)

        self.boton_jugar = ctk.CTkButton(botones_frame, text="Jugar", command=self.start_game)
        self.boton_jugar.pack(side="left", padx=10)
>>>>>>> 2013fb8 (Juego funcional)

        self.boton_volver = ctk.CTkButton(self.frame, text="Return", font=("M04_FATAL FURY", 30),
                                          fg_color="transparent", hover=False, command=self.callback_volver)
        self.boton_volver.place(relx=0.05, rely=0.95, anchor="sw")

        # ─── Variables para el temporizador ────────────────────────────────────
        # Para evitar varios finales de partida
        self.game_over = False

        # Dentro de botones_frame, justo tras self.diff_menu.pack(...)
        ctk.CTkLabel(botones_frame, text="Tiempo (min):", font=("M04_FATAL FURY", 18)) \
            .pack(side="left", padx=(10, 5))
        self.time_entry = ctk.CTkEntry(botones_frame, width=50)
        self.time_entry.insert(0, "2")  # valor por defecto (minutos)
        self.time_entry.pack(side="left", padx=(0, 20))

    # ─── Método para formatear segundos a M:SS ──────────────────────────────


    def _format_time(self, total_seconds):
        """
        Devuelve 'M:SS' donde M es minutos (sin cero inicial) y SS segundos con dos dígitos.
        """
        mins = total_seconds // 60
        secs = total_seconds % 60
        return f"{mins}:{secs:02d}"

        # ─── Método para mostrar la ventana de fin de partida ───────────────────


    def _show_game_over(self):
        """
        Se ejecuta una sola vez al acabar tiempo o al recoger todos los checkpoints.
        Muestra puntos, tiempo empleado y ganador.
        """
        if self.game_over:
            return
        self.game_over = True

        threading.Thread(target=self.dron.stopGo, daemon=True).start()
        threading.Thread(target=self.dron2.stopGo, daemon=True).start()

        total = len(self.raw_checkpoints)
        elapsed = self.timer_duration - self.remaining_time
        time_str = self._format_time(elapsed)

        # Determinar ganador
        if self.cp1_count == total and self.cp2_count == total:
            winner = "Empate"
        elif self.cp1_count == total:
            winner = "Jugador 1"
        elif self.cp2_count == total:
            winner = "Jugador 2"
        else:
            # fin por tiempo: el que más checkpoints tenga
            if self.cp1_count > self.cp2_count:
                winner = "Jugador 1"
            elif self.cp2_count > self.cp1_count:
                winner = "Jugador 2"
            else:
                winner = "Empate"

        # Crear ventana de resumen
        self.over = ctk.CTkToplevel(self.game_window)
        self.over.title("Fin de la Partida")
        self.over.geometry("400x300")

        # Contenedor interior para centrar y ajustar márgenes
        frame = ctk.CTkFrame(self.over, fg_color="transparent")
        frame.pack(expand=True, fill="both", padx=20, pady=20)

        # --- Encabezados de tabla ---
        header_font = ("M04_FATAL FURY", 18, "bold")
        ctk.CTkLabel(frame, text="Jugador", font=header_font).grid(row=0, column=0, padx=10, pady=(0, 5))
        ctk.CTkLabel(frame, text="Puntos", font=header_font).grid(row=0, column=1, padx=10, pady=(0, 5))
        ctk.CTkLabel(frame, text="Tiempo", font=header_font).grid(row=0, column=2, padx=10, pady=(0, 5))

        # --- Fila Jugador 1 ---
        body_font = ("M04_FATAL FURY", 16)
        ctk.CTkLabel(frame, text="Jugador 1", font=body_font).grid(row=1, column=0, padx=10, pady=2)
        ctk.CTkLabel(frame, text=f"{self.cp1_count}/{total}", font=body_font).grid(row=1, column=1, padx=10, pady=2)
        ctk.CTkLabel(frame, text=time_str, font=body_font).grid(row=1, column=2, padx=10, pady=2)

        # --- Fila Jugador 2 ---
        ctk.CTkLabel(frame, text="Jugador 2", font=body_font).grid(row=2, column=0, padx=10, pady=2)
        ctk.CTkLabel(frame, text=f"{self.cp2_count}/{total}", font=body_font).grid(row=2, column=1, padx=10, pady=2)
        ctk.CTkLabel(frame, text=time_str, font=body_font).grid(row=2, column=2, padx=10, pady=2)

        # --- Mensaje de ganador ---
        winner_font = ("M04_FATAL FURY", 20)
        ctk.CTkLabel(self.over, text=f"Ganador: {winner}", font=winner_font, text_color="blue") \
            .pack(pady=(0, 10))

        # --- Botón de cierre ---
        def on_finalize():
            # 2) RTL en hilos separados
            threading.Thread(target=self.dron.RTL, daemon=True).start()
            threading.Thread(target=self.dron2.RTL, daemon=True).start()
            # 3) cerrar ventanas
            self.over.destroy()
            self.game_window.destroy()

        ctk.CTkButton(
            self.over,
            text="Finalizar",
            command=on_finalize
        ).pack(pady=10)

    def stop_drones(self):
        """
        Para ambos drones en un hilo para no bloquear la UI.
        """
        try:
            self.dron.stopGo()
        except Exception as e:
            print(f"Error al parar dron1: {e}")
        try:
            self.dron2.stopGo()
        except Exception as e:
            print(f"Error al parar dron2: {e}")

    def rtl_drones(self):
        """
        Envía RTL a ambos drones en un hilo.
        """
        try:
            self.dron.RTL()
        except Exception as e:
            print(f"Error enviando RTL dron1: {e}")
        try:
            self.dron2.RTL()
        except Exception as e:
            print(f"Error enviando RTL dron2: {e}")

    def _spawn_next_checkpoint(self, canvas, queue, which):
        if not queue:
            setattr(self, f"current_cp_{which}", None)
            self._show_game_over()
            return
        cell = queue.pop(0)
        size = self.map_data["map_size"]["cell_size"]
        x = cell["col"] * size + size / 2
        y = cell["row"] * size + size / 2

        # si usas imagen:
        item = canvas.create_image(x, y, image=self.checkpoint_img, tag=f"cp_{which}")

        # o si prefieres óvalo:
        # r = size*0.4
        # item = canvas.create_oval(x-r, y-r, x+r, y+r, fill="yellow", outline="black", tag=f"cp_{which}")

        setattr(self, f"current_cp_{which}", {
            "col": cell["col"],
            "row": cell["row"],
            "item": item,
            "x": x,
            "y": y
        })

    def on_difficulty_change(self, selection):
        # convierte a minúsculas para usar el damage_map
        key = selection.lower()
        if key in self.damage_map:
            self.difficulty = key
        print(f"Dificultad → {self.difficulty}, daño por obstáculo = {self.damage_map[self.difficulty] * 100:.0f}%")

    # ----------------------------------------------------------------------
    # Seleccionar Mapa y mostrar preview
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
    # Conectar Jugador y activar telemetría
    # ----------------------------------------------------------------------
    def connect_player(self):

        baud = 115200
        try:
            connection_string = "tcp:127.0.0.1:5762"
            print(f"🔌 Intentando conectar a {connection_string} con baud {baud}...")
            self.dron.connect(connection_string, baud, blocking=True)
            if self.dron.state == "connected":
                print("✅ Conexión exitosa al dron.")
                self.connected_drones.append(self.dron)
                # Iniciar telemetría
                self.dron.send_telemetry_info(self.process_telemetry_info)
                print("📡 Enviando datos de telemetría al juego.")
                self.update_player_list()
                messagebox.showinfo("Conexión Exitosa", "Jugador conectado correctamente.")
            else:
                messagebox.showerror("Error", "El dron no está en estado 'connected'.")
        except Exception as e:
            print(f"❌ Error en connect_player: {e}")
            messagebox.showerror("Error", f"Ocurrió un error inesperado: {e}")
            # Conexión del segundo dron (jugador 2)
        try:
            connection_string2 = "tcp:127.0.0.1:5772"
            print(f"Conectando jugador 2 a {connection_string2}...")
            self.second_dron.connect(connection_string2, baud, blocking=True)
            if self.second_dron.state == "connected":
                print("✅✅Jugador 2 conectado.")
                self.connected_drones.append(self.second_dron)
                # Se puede usar un callback distinto si querés diferenciarlos
                self.second_dron.send_telemetry_info(self.process_telemetry_info_second)
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
            x_old = x
            y_old = y
            angulo = math.radians(-72)
            x = x_old * math.cos(angulo) - y_old * math.sin(angulo)
            y = x_old * math.sin(angulo) + y_old * math.cos(angulo)
            print(f"📌 GPS → Canvas: lat={lat}, lon={lon} → x={x:.2f}, y={y:.2f}")
            return x, y
        except Exception as e:
            print(f"❌ Error en get_canvas_coordinates_from_gps: {e}")
            return None, None

    def check_if_on_obstacle_cell(self, x, y):
        cell_size = self.map_data["map_size"]["cell_size"]
        col = int(x / cell_size)
        row = int(y / cell_size)
        print("Dron 1 en celda:", (col, row))

        obstacle_cells = set()
        for obs in self.map_data.get("obstacles", []):
            obstacle_cells.add((obs["original"]["col"], obs["original"]["row"]))
            obstacle_cells.add((obs["mirror"]["col"], obs["mirror"]["row"]))
        print("Celdas de obstáculo:", obstacle_cells)

        if (col, row) in obstacle_cells:
            if not self.is_on_obstacle:
                damage = self.damage_map[self.difficulty]
                self.life1 = max(0.0, self.life1 - damage)
                self.hp1_bar.set(self.life1)
                print(f"J1 choca: vida ahora {self.life1:.2f}")
                print("¡Alerta! Dron 1 sobre obstáculo en celda", (col, row))
                winsound.PlaySound("assets/Bite.wav", winsound.SND_FILENAME | winsound.SND_ASYNC)
            self.is_on_obstacle = True
            return True
        self.is_on_obstacle=False
        return False

    def check_if_on_checkpoint_j1(self, x, y, canvas):
        size = self.map_data["map_size"]["cell_size"]
        cp = self.current_cp_j1
        if not cp:
            return False

        # hitbox en celdas → hitbox en píxeles
        hb_cells = self.hitbox_map.get(self.difficulty, 0)
        # tomamos la mitad de la celda + las celdas extra de tolerancia
        radius = size * (0.5 + hb_cells)

        # si estamos dentro del cuadrado de detección:
        if abs(x - cp["x"]) <= radius and abs(y - cp["y"]) <= radius:
            winsound.PlaySound("assets/ring.wav", winsound.SND_FILENAME | winsound.SND_ASYNC)
            canvas.delete(cp["item"])
            self.cp1_count += 1
            self.cp1_label.configure(text=f"Checkpoints: {self.cp1_count}")
            self._spawn_next_checkpoint(canvas, self.queue_j1, "j1")

            return True
        if self.cp1_count == len(self.raw_checkpoints): self._show_game_over()
        return False

    def check_if_on_obstacle_cell_2(self, x, y):
        cell_size = self.map_data["map_size"]["cell_size"]
        col = int(x / cell_size)
        row = int(y / cell_size)
        print("Dron 2 en celda:", (col, row))

        obstacle_cells = set()
        for obs in self.map_data.get("obstacles", []):
            obstacle_cells.add((obs["original"]["col"], obs["original"]["row"]))
            obstacle_cells.add((obs["mirror"]["col"], obs["mirror"]["row"]))
        print("Celdas de obstáculo:", obstacle_cells)

        if (col, row) in obstacle_cells:

<<<<<<< HEAD
            if not self.is_on_obstacle:
=======
            if not self.is_on_obstacle2:
                damage = self.damage_map[self.difficulty]
                self.life2 = max(0.0, self.life2 - damage)
                self.hp2_bar.set(self.life2)
                print(f"J2 choca: vida ahora {self.life2:.2f}")
>>>>>>> 2013fb8 (Juego funcional)
                print("¡Alerta! Dron 2 sobre obstáculo en celda", (col, row))
                winsound.PlaySound("assets/Bite.wav", winsound.SND_FILENAME | winsound.SND_ASYNC)
            self.is_on_obstacle = True
            return True
        self.is_on_obstacle = False
        return False

<<<<<<< HEAD
=======
    def check_if_on_checkpoint_j2(self, x, y, canvas):
        size = self.map_data["map_size"]["cell_size"]
        cp = self.current_cp_j2
        if not cp:
            return False

        # hitbox en celdas → hitbox en píxeles
        hb_cells = self.hitbox_map.get(self.difficulty, 0)
        # tomamos la mitad de la celda + las celdas extra de tolerancia
        radius = size * (0.5 + hb_cells)

        # si estamos dentro del cuadrado de detección:
        if abs(x - cp["x"]) <= radius and abs(y - cp["y"]) <= radius:
            winsound.PlaySound("assets/ring.wav", winsound.SND_FILENAME | winsound.SND_ASYNC)
            canvas.delete(cp["item"])
            self.cp2_count += 1
            self.cp2_label.configure(text=f"Checkpoints: {self.cp2_count}")
            self._spawn_next_checkpoint(canvas, self.queue_j2, "j2")

            return True
        if self.cp2_count == len(self.raw_checkpoints): self._show_game_over()
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



>>>>>>> 2013fb8 (Juego funcional)
    def start_game(self):
        if not self.map_data:
            messagebox.showwarning("Advertencia", "Selecciona un mapa antes de jugar.")
            return

        # ─── Leer y validar tiempo en minutos (mínimo 2) ───────────────────────
        try:
            mins = int(self.time_entry.get())
        except ValueError:
            mins = 2
        if mins < 2:
            mins = 2
        self.timer_duration = mins * 60   # en segundos

        self.raw_checkpoints = self.map_data.get("checkpoints", [])
        self.queue_j1 = [{"col": cp["original"]["col"], "row": cp["original"]["row"], "id": cp["id"]}
                         for cp in self.raw_checkpoints]
        self.queue_j2 = [{"col": cp["mirror"]["col"], "row": cp["mirror"]["row"], "id": cp["id"]}
                         for cp in self.raw_checkpoints]
        map_width = self.map_data["map_size"]["width"]
        map_height = self.map_data["map_size"]["height"]
        cell_size = self.map_data["map_size"]["cell_size"]

            # --- ventana en fullscreen ---
        def end_fullscreen(event=None):
            self.game_window.attributes("-fullscreen", False)

        self.game_window = ctk.CTkToplevel(fg_color="white")
        self.game_window.title("Checkpoint Race - Mapa")
        self.game_window.attributes("-fullscreen", True)
        self.game_window.bind("<Escape>", end_fullscreen)
        self.game_window.grid_rowconfigure(0, weight=1)
        self.game_window.grid_columnconfigure(0, weight=0)
        self.game_window.grid_columnconfigure(1, weight=1)
        self.game_window.grid_columnconfigure(2, weight=0)

        # --- Barra de vida horizontal J1 ---

        life_frame1 = ctk.CTkFrame(self.game_window, fg_color="transparent")
        life_frame1.grid(row=0, column=0, sticky="nw", padx=20, pady=10)
        life_frame1.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(life_frame1, text="PLAYER 1", font=("M04_FATAL FURY", 20), bg_color="transparent", text_color="black") \
            .grid(row=0, column=0, pady=(0, 5))

        self.hp1_bar = ctk.CTkProgressBar(
            life_frame1,
            orientation="horizontal",
            width=200,
            height=20,
            progress_color="green",
            fg_color="white"
            )
        self.hp1_bar.set(self.life1)
        self.hp1_bar.grid(row=1, column=0, sticky="ew", pady=(20, 0))

        #label de recuento de checkpoints J1
        self.cp1_label = ctk.CTkLabel(life_frame1,
                                      text=f"Checkpoints: {self.cp1_count}",
                                      font=("M04_FATAL FURY", 16),
                                      text_color="black")
        self.cp1_label.grid(row=2, column=0, pady=(5, 10), sticky="n")

        # Temporizador Para Jugador 1
        self.timer1_label = ctk.CTkLabel(life_frame1,
                                         text=self._format_time(self.timer_duration),
                                         font=("M04_FATAL FURY", 16),
                                         text_color="black")
        self.timer1_label.grid(row=3, column=0, pady=(0, 10), sticky="n")



        # --- contenedor central expandible ---
        center_container = ctk.CTkFrame(self.game_window, fg_color="transparent")
        center_container.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        center_container.grid_rowconfigure(0, weight=1)
        center_container.grid_columnconfigure(0, weight=1)

        # --- canvas central TAMAÑO FIJO y centrado ---
        # usa map_width/map_height tal como ya los calculas un poco más arriba
        game_canvas = ctk.CTkCanvas(
            center_container,
            width=map_width,
            height=map_height,
            bg="gray"
        )
        # en lugar de grid, lo colocamos en el medio:
        game_canvas.place(relx=0.5, rely=0.5, anchor="center")

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


<<<<<<< HEAD
        for poligono in lista_geo:
            for coordenada in poligono:
                lata, longanisa = self.get_gps_from_canvas_coordinates(coordenada[0],coordenada[1])
                coordenada[0] = lata
                coordenada[1] = longanisa
        self.dron.setGEOFence(lista_geo)
        self.second_dron.setGEOFence(lista_geo)
        print(lista_geo)
=======
        #lista_geo = [[[0, 0], [0, 0], [0, 980], [224, 980], [224, 0]], [[224, 0], [224, 980], [448, 980], [448, 0]]]
        # lista_geo = [[[14,14], [14, 14], [14, 966], [210, 966], [210, 14]], [[238,14],[238,966],[434,966],[434,14]]]
        # for poligono in lista_geo:
        #     for coordenada in poligono:
        #         lata, longanisa = self.get_gps_from_canvas_coordinates(coordenada[0],coordenada[1])
        #         coordenada[0] = lata
        #         coordenada[1] = longanisa
        #         print(self.get_canvas_coordinates_from_gps(lata, longanisa))
        # self.dron.setGEOFence(lista_geo)
        # self.dron2.setGEOFence(lista_geo)
        # print(lista_geo)
        # lista original en píxeles
        pixel_polygons = [
            [[14, 14], [14, 14], [14, 966], [210, 966], [210, 14]],
            [[238, 14], [238, 966], [434, 966], [434, 14]]
        ]

        # convierte cada (x,y) en [lat, lon]
        lista_geo = []
        for poly in pixel_polygons:
            geo_poly = []
            for x_px, y_px in poly:
                lat, lon = self.get_gps_from_canvas_coordinates(x_px, y_px)
                geo_poly.append([lat, lon])
            lista_geo.append(geo_poly)

        # aplica el geofence
        self.dron.setGEOFence(lista_geo, 0.5)
        self.dron2.setGEOFence(lista_geo, 0.5)

        print("Geofence enviado:", lista_geo)
>>>>>>> 2013fb8 (Juego funcional)

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
            drone1_image_path = "assets/dron.png"
            if not os.path.exists(drone1_image_path):
                raise FileNotFoundError(f"No se encontró la imagen del dron en {drone1_image_path}")
            drone1_image = Image.open(drone1_image_path).resize((cell_size, cell_size), Image.LANCZOS)
            self.drone1_image_full = ImageTk.PhotoImage(drone1_image)
        except Exception as e:
            print(f"Error al cargar la imagen del dron: {e}")

            # --- Barra de vida horizontal J2 ---
        life_frame2 = ctk.CTkFrame(self.game_window, fg_color="transparent")
        life_frame2.grid(row=0, column=2, sticky="ne", padx=20, pady=10)
        life_frame2.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(life_frame2, text="PLAYER 2", font=("M04_FATAL FURY", 20), fg_color="transparent", text_color="black") \
            .grid(row=0, column=0, pady=(0, 5))

        self.hp2_bar = ctk.CTkProgressBar(
            life_frame2,
            orientation="horizontal",
            width=200,
            height=20,
            progress_color="green",
            fg_color="white"
        )
        self.hp2_bar.set(self.life2)
        self.hp2_bar.grid(row=1, column=0, sticky="ew", pady=(20, 0))

        # label de recuento de checkpoints J1
        self.cp2_label = ctk.CTkLabel(life_frame2,
                                      text=f"Checkpoints: {self.cp2_count}",
                                      font=("M04_FATAL FURY", 16),
                                      text_color="black")
        self.cp2_label.grid(row=2, column=0, pady=(5, 10), sticky="n")
        # timer j2
        self.timer2_label = ctk.CTkLabel(life_frame2,
                                         text=self._format_time(self.timer_duration),
                                         font=("M04_FATAL FURY", 16),
                                         text_color="black")
        self.timer2_label.grid(row=3, column=0, pady=(0, 10), sticky="n")

        messagebox.showinfo("Juego Iniciado", "¡Comenzando la carrera con los jugadores conectados!")

        self.checkpoint_img = ImageTk.PhotoImage(
            Image.open("assets/checkpoint.png")
            .resize((cell_size, cell_size), Image.LANCZOS)
        )
        self._spawn_next_checkpoint(game_canvas, self.queue_j1, "j1")
        self._spawn_next_checkpoint(game_canvas, self.queue_j2, "j2")
        # ─── Iniciar temporizador ────────────────────────────────────────────
        self.remaining_time = self.timer_duration

        def update_timer():
            texto = self._format_time(self.remaining_time)
            self.timer1_label.configure(text=texto)
            self.timer2_label.configure(text=texto)

            if self.remaining_time > 0:
                self.remaining_time -= 1
                self.game_window.after(1000, update_timer)
            else:
                # tiempo agotado
                self._show_game_over()

        update_timer()

        self.start_telemetry_sync(game_canvas)
        self.start_telemetry_sync_second(game_canvas)
<<<<<<< HEAD
        print(self.get_gps_from_canvas_coordinates(0,0))

=======
        threading.Thread(target=self.arm_and_takeoff, args=(self.dron,)).start()
        threading.Thread(target=self.arm_and_takeoff, args=(self.dron2,)).start()
>>>>>>> 2013fb8 (Juego funcional)

    # ----------------------------------------------------------------------
    # 4) Telemetría y coordenadas
    # ----------------------------------------------------------------------
    def process_telemetry_info(self, telemetry_info):
        """
        Callback de telemetría.
        Aquí solo mostramos o guardamos info, sin offset ni desplazamiento.
        """
        print(f"📡 Telemetría recibida: {telemetry_info}")

    def process_telemetry_info_second(self, telemetry_info):
        print(f"📡 Telemetría Jugador 2: {telemetry_info}")

<<<<<<< HEAD
    def get_canvas_coordinates_from_gps(self, lat, lon):
        """
        Convierte lat/lon a coords de canvas, sin offset.
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
=======
    def start_telemetry_sync(self, canvas):
        def update():
            lat, lon = self.dron.lat, self.dron.lon
            if lat != 0.0 or lon != 0.0:
                # 1) coords LÓGICAS (sin clamp, ya rotadas por get_canvas_coordinates_from_gps)
                x_logic, y_logic = self.get_canvas_coordinates_from_gps(lat, lon)

                # 2) detecciones en coords LÓGICAS
                self.check_if_on_checkpoint_j1(x_logic, y_logic, canvas)
                self.check_if_on_obstacle_cell(x_logic, y_logic)

                # 3) coords PARA DIBUJAR (clamp + centrar)
                map_w = self.map_data["map_size"]["width"]
                map_h = self.map_data["map_size"]["height"]
                hw = self.drone1_image_full.width() / 2
                hh = self.drone1_image_full.height() / 2

                x_draw = min(max(x_logic, hw), map_w - hw)
                y_draw = min(max(y_logic, hh), map_h - hh)

                # 4) dibujar con anchor="center"
                tag = "player_drone"
                canvas.delete(tag)
                canvas.create_image(
                    x_draw, y_draw,
                    anchor="center",  
                    image=self.drone1_image_full,
                    tag=tag
                )
>>>>>>> 2013fb8 (Juego funcional)

                print(f"✅ Dron 1 en canvas: lógico=({x_logic:.1f},{y_logic:.1f})  dibujado=({x_draw:.1f},{y_draw:.1f})")

            canvas.after(35, update)

        update()

    def start_telemetry_sync_second(self, canvas):
        """
        Dibuja el dron 2 cada ~35 ms, separando lógica de detección de dibujo.
        """

        def update():
            lat, lon = self.dron2.lat, self.dron2.lon
            if lat != 0.0 or lon != 0.0:
                # 1) coords LÓGICAS (sin clamp ni rotación extra)
                x_logic, y_logic = self.get_canvas_coordinates_from_gps(lat, lon)

                # 2) detecciones en coords LÓGICAS
                self.check_if_on_checkpoint_j2(x_logic, y_logic, canvas)
                self.check_if_on_obstacle_cell_2(x_logic, y_logic)

                # 3) coords PARA DIBUJAR (clamp + centrar el sprite)
                map_w = self.map_data["map_size"]["width"]
                map_h = self.map_data["map_size"]["height"]
                hw = self.drone1_image_full.width() / 2
                hh = self.drone1_image_full.height() / 2

                x_draw = min(max(x_logic, hw), map_w - hw)
                y_draw = min(max(y_logic, hh), map_h - hh)

                # 4) dibujar con anchor="center" y tag propio
                tag = "player_drone_2"
                canvas.delete(tag)
                canvas.create_image(
                    x_draw, y_draw,
                    anchor="center",
                    image=self.drone1_image_full,
                    tag=tag
                )

                print(f"✅ Dron 2 en canvas: lógico=({x_logic:.1f},{y_logic:.1f})  dibujado=({x_draw:.1f},{y_draw:.1f})")

<<<<<<< HEAD
    def start_telemetry_sync_second(self, canvas):
        def update():
            try:
                if not self.second_dron:
                    return
                lat = self.second_dron.lat
                lon = self.second_dron.lon
                if lat == 0.0 and lon == 0.0:
                    print("⚠ Dron 2 sin coordenadas GPS válidas.")
                else:
                    # Para el segundo dron, podés aplicar un offset para diferenciar su visualización.
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
                        # Aplicar un offset para que se dibuje en la mitad derecha, por ejemplo:
                        x += map_width / 2
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
=======
>>>>>>> 2013fb8 (Juego funcional)
            canvas.after(35, update)

        update()

    # ----------------------------------------------------------------------
    # 5) Utilidades de la interfaz
    # ----------------------------------------------------------------------
    def update_player_list(self):
        self.player_listbox.delete("1.0", "end")
        for idx, dron in enumerate(self.connected_drones, start=1):
            self.player_listbox.insert("end", f"Jugador {idx}: {dron.state}\n")


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

        scale_x = 300 / map_width_cells if map_width_cells else 1
        scale_y = 300 / map_height_cells if map_height_cells else 1
        scale = min(scale_x, scale_y)
        offset_x = (300 - (map_width_cells * scale)) / 2
        offset_y = (300 - (map_height_cells * scale)) / 2

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
