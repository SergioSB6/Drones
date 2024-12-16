import os
import customtkinter as ctk
from tkinter import filedialog, messagebox, Toplevel
import json

class CheckpointScreen:
    def __init__(self, dron, parent_frame):
        # Frame principal
        self.dron = dron
        self.map_data = None
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

        # Botón Jugar
        self.boton_jugar = ctk.CTkButton(master=self.frame, text="Jugar", command=self.start_game)
        self.boton_jugar.place(relx=0.5, rely=0.9, anchor="center")

        # Botón Volver
        self.boton_volver = ctk.CTkButton(master=self.frame, text="Return", font=("M04_FATAL FURY", 30),
                                          fg_color="transparent", hover=False, command=self.callback_volver)
        self.boton_volver.place(relx=0.05, rely=0.95, anchor="sw")

    def select_map(self):
        # Selección de archivo
        file_path = filedialog.askopenfilename(filetypes=[("JSON Files", "*.json")])
        if not file_path:
            return

        # Cargar el archivo JSON del mapa
        try:
            with open(file_path, "r") as file:
                self.map_data = json.load(file)

            # Dibujar una vista previa del mapa
            self.render_map_preview()
            messagebox.showinfo("Mapa Cargado", "Mapa cargado correctamente.")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo cargar el mapa: {e}")

    def render_map_preview(self):
        # Limpiar el canvas antes de redibujar
        self.map_canvas.delete("all")

        if not self.map_data:
            return

        # Dibujar geofence
        for fence in self.map_data.get("geofence", []):
            x, y = fence["x"], fence["y"]
            self.map_canvas.create_rectangle(x, y, x + 2, y + 2, fill="red")  # Puntos del geofence

        # Dibujar obstáculos
        for obstacle in self.map_data.get("obstacles", []):
            x, y = obstacle["x"], obstacle["y"]
            scale_x = x / 6  # Escalar las coordenadas para la preview
            scale_y = y / 6
            self.map_canvas.create_rectangle(scale_x, scale_y, scale_x + 10, scale_y + 10, fill="yellow")

    def start_game(self):
        if not self.map_data:
            messagebox.showwarning("Advertencia", "Selecciona un mapa antes de jugar.")
            return

        # Crear ventana emergente para mostrar el mapa completo
        game_window = Toplevel()
        game_window.title("Checkpoint Race - Mapa")
        game_window.geometry("1280x720")

        # Canvas para el mapa completo
        game_canvas = ctk.CTkCanvas(game_window, width=1280, height=720, bg="gray")
        game_canvas.pack(fill="both", expand=True)

        # Dibujar geofence
        for fence in self.map_data.get("geofence", []):
            x, y = fence["x"], fence["y"]
            game_canvas.create_rectangle(x, y, x + 2, y + 2, fill="red")

        # Dibujar cada obstáculo en el mapa completo
        for obstacle in self.map_data.get("obstacles", []):
            x, y = obstacle["x"], obstacle["y"]
            game_canvas.create_rectangle(x, y, x + 20, y + 20, fill="yellow")

        # Dibujar checkpoints si están definidos
        for checkpoint in self.map_data.get("checkpoints", []):
            x, y = checkpoint["x"], checkpoint["y"]
            game_canvas.create_oval(x, y, x + 15, y + 15, fill="blue")

        messagebox.showinfo("Juego Iniciado", "¡Comenzando la carrera con el mapa seleccionado!")

    def callback_volver(self):
        # Función para volver al menú principal
        self.frame.tkraise()
