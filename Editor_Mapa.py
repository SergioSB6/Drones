import customtkinter as ctk
from tkinter import messagebox, filedialog
from PIL import Image, ImageTk
import os
import json
import math


class MapFrameClass:
    def __init__(self, dron, fatherFrame):
        self.map_canvas = None  # Se inicializa en setup_ui
        self.obstacles = []  # Lista de obstáculos
        self.geofence_cells = set()  # Celdas para el geofence
        self.dron = dron
        self.fatherFrame = fatherFrame
        self.obstacle_positions = []
        self.selected_obstacle = None
        self.occupied_cells = set()
        self.resized_images = {}
        self.obstacle_images = {}

        self.ancho_terreno_metros = 32.00
        self.largo_terreno_metros = 70.00
        self.cell_size = 0
        self.calculate_cell_size()
        self.current_obstacle_size = self.cell_size
        # Referencia geográfica: esquina superior izquierda del terreno real
        self.top_left_lat = 41.2766126
        self.top_left_lon = 1.9890216
        self.ancho_terreno_pixels = int(self.ancho_terreno_metros * self.cell_size)
        self.largo_terreno_pixels = int(self.largo_terreno_metros * self.cell_size)

        self.load_obstacle_images()
        self.obstacle_counter = 0
        self.setup_ui()
        self.create_geofence_cells()

    def calculate_cell_size(self):
        max_width = 448
        max_height = 980
        cell_width = max_width / self.ancho_terreno_metros
        cell_height = max_height / self.largo_terreno_metros
        self.cell_size = int(min(cell_width, cell_height))

    def generate_obstacle_id(self):
        self.obstacle_counter += 1
        return self.obstacle_counter

    def load_obstacle_images(self):
        try:
            self.obstacle_images["cuadrado"] = Image.open("assets/square.png").resize(
                (self.cell_size, self.cell_size), Image.LANCZOS)
        except FileNotFoundError:
            self.obstacle_images["cuadrado"] = Image.new("RGB", (self.cell_size, self.cell_size), "red")

    def setup_ui(self):
        self.fatherFrame.grid_rowconfigure(0, weight=1)
        self.fatherFrame.grid_columnconfigure(1, weight=1)

        self.control_panel = ctk.CTkFrame(self.fatherFrame, width=200)
        self.control_panel.grid(row=0, column=0, sticky="ns")
        self.add_buttons()

        self.map_canvas = ctk.CTkCanvas(self.fatherFrame, width=1685, height=1009, bg="white")
        self.map_canvas.grid(row=0, column=1, sticky="nsew")
        self.draw_grid()
        self.map_canvas.bind("<Button-1>", self.select_obstacle)
        self.map_canvas.bind("<Button-3>", self.add_marker_event)

    def add_buttons(self):
        self.add_background_button = ctk.CTkButton(self.control_panel, text="Añadir Fondo", command=self.add_background)
        self.add_background_button.pack(pady=10)

        self.add_obstacle_button = ctk.CTkButton(self.control_panel, text="Añadir Obstáculo",
                                                 command=self.add_marker_mode)
        self.add_obstacle_button.pack(pady=10)

        self.delete_button = ctk.CTkButton(self.control_panel, text="Borrar Obstáculo Seleccionado",
                                           command=self.delete_selected_obstacle)
        self.delete_button.pack(pady=10)

        self.save_button = ctk.CTkButton(self.control_panel, text="Guardar Mapa", command=self.save_map)
        self.save_button.pack(pady=10)

    def draw_grid(self):
        for i in range(0, self.ancho_terreno_pixels, self.cell_size):
            self.map_canvas.create_line(i, 0, i, self.largo_terreno_pixels, fill="blue", tag="grid")
        for j in range(0, self.largo_terreno_pixels, self.cell_size):
            self.map_canvas.create_line(0, j, self.ancho_terreno_pixels, j, fill="blue", tag="grid")
        self.create_geofence_cells()
        # Pintar las celdas del geofence en rojo
        for col, row in self.geofence_cells:
            x1 = col * self.cell_size
            y1 = row * self.cell_size
            x2 = x1 + self.cell_size
            y2 = y1 + self.cell_size
            self.map_canvas.create_rectangle(x1, y1, x2, y2, fill="red", outline="red", tag="geofence")

    def create_geofence_cells(self):
        self.geofence_cells = set()
        num_cols = self.ancho_terreno_pixels // self.cell_size
        num_rows = self.largo_terreno_pixels // self.cell_size

        # Asegurar que el número de columnas sea par (para dividir en dos zonas)
        if num_cols % 2 != 0:
            num_cols -= 1

        # Bordes del terreno
        for col in range(num_cols):
            self.geofence_cells.add((col, 0))  # Borde superior
            self.geofence_cells.add((col, num_rows - 1))  # Borde inferior
        for row in range(num_rows):
            self.geofence_cells.add((0, row))  # Borde izquierdo
            self.geofence_cells.add((num_cols - 1, row))  # Borde derecho

        # Línea central: para separar zona de jugador 1 y 2
        mid_col_left = (num_cols // 2) - 1
        mid_col_right = num_cols // 2
        for row in range(num_rows):
            self.geofence_cells.add((mid_col_left, row))
            self.geofence_cells.add((mid_col_right, row))

    # --- Funciones para convertir celdas a coordenadas GPS y construir el polígono de geofence ---

    def cell_to_latlon(self, col, row):
        """
        Convierte una celda (col, row) en coordenadas GPS (lat, lon)
        usando self.top_left_lat y self.top_left_lon como referencia.
        Se asume que self.cell_size representa metros por celda.
        """
        delta_lat_m = row * self.cell_size
        delta_lon_m = col * self.cell_size
        dlat_deg = delta_lat_m / 111320.0
        dlon_deg = delta_lon_m / (111320.0 * math.cos(math.radians(self.top_left_lat)))
        lat = self.top_left_lat - dlat_deg
        lon = self.top_left_lon + dlon_deg
        return lat, lon

    def build_geofence_polygon(self):
        """
        Construye un polígono (lista de diccionarios con lat y lon) que encierra
        todas las celdas definidas en self.geofence_cells.
        Se genera un rectángulo mínimo que cubre todas las celdas.
        """
        if not self.geofence_cells:
            return []
        cols = [col for col, row in self.geofence_cells]
        rows = [row for col, row in self.geofence_cells]
        min_col, max_col = min(cols), max(cols)
        min_row, max_row = min(rows), max(rows)
        # Para cubrir completamente las celdas, usamos max+1
        lat1, lon1 = self.cell_to_latlon(min_col, min_row)
        lat2, lon2 = self.cell_to_latlon(max_col + 1, min_row)
        lat3, lon3 = self.cell_to_latlon(max_col + 1, max_row + 1)
        lat4, lon4 = self.cell_to_latlon(min_col, max_row + 1)
        polygon = [
            {"lat": lat1, "lon": lon1},
            {"lat": lat2, "lon": lon2},
            {"lat": lat3, "lon": lon3},
            {"lat": lat4, "lon": lon4},
        ]
        return polygon

    # --- Resto de métodos del editor de mapas ---

    def add_marker_mode(self):
        self.map_canvas.bind("<Button-3>", self.add_marker_event)
        messagebox.showinfo("Modo de Añadir", "Haz clic derecho en el mapa para añadir un obstáculo.")

    def add_marker_event(self, event):
        x = self.map_canvas.canvasx(event.x)
        y = self.map_canvas.canvasy(event.y)

        col, row = int(x // self.cell_size), int(y // self.cell_size)
        new_cells = {(col, row)}

        if any(cell in self.occupied_cells or cell in self.geofence_cells for cell in new_cells):
            messagebox.showerror("Error", "No se puede colocar el obstáculo sobre otra celda ocupada o en el geofence.")
            return

        x = col * self.cell_size
        y = row * self.cell_size
        obstacle_id = self.generate_obstacle_id()
        obstacle = self.add_obstacle((x, y), obstacle_id)

        mid_col = self.ancho_terreno_pixels // (2 * self.cell_size)
        mirrored_col = mid_col + (mid_col - col) - 1
        mirrored_cells = {(mirrored_col, row)}

        if any(cell in self.occupied_cells or cell in self.geofence_cells for cell in mirrored_cells):
            messagebox.showerror("Error",
                                 "No se puede colocar el obstáculo espejo sobre otra celda ocupada o en el geofence.")
            return

        mirrored_x = mirrored_col * self.cell_size
        mirror_obstacle = self.add_obstacle((mirrored_x, y), obstacle_id)

        self.obstacles.append({
            "id": obstacle_id,
            "original": (obstacle, new_cells),
            "mirror": (mirror_obstacle, mirrored_cells)
        })
        print(f"Obstáculo añadido: ID={obstacle_id}, Original=({col}, {row}), Espejo=({mirrored_col}, {row})")
        self.occupied_cells.update(new_cells | mirrored_cells)

    def add_obstacle(self, coords, obstacle_id):
        resized_icon = ImageTk.PhotoImage(self.obstacle_images["cuadrado"].resize((self.cell_size, self.cell_size)))
        obstacle = self.map_canvas.create_image(coords[0], coords[1], image=resized_icon, anchor='nw', tags="obstacle")
        self.resized_images[obstacle] = resized_icon
        return obstacle

    def delete_selected_obstacle(self):
        if self.selected_obstacle:
            self.map_canvas.delete(self.selected_obstacle["original"][0])
            self.occupied_cells.difference_update(self.selected_obstacle["original"][1])
            self.map_canvas.delete(self.selected_obstacle["mirror"][0])
            self.occupied_cells.difference_update(self.selected_obstacle["mirror"][1])
            self.obstacles.remove(self.selected_obstacle)
            self.selected_obstacle = None
            print("Obstáculo y su espejo eliminados correctamente.")
        else:
            messagebox.showwarning("Advertencia", "No hay obstáculo seleccionado para eliminar.")

    def save_map(self):
        maps_folder = os.path.join(os.path.dirname(__file__), "maps")
        os.makedirs(maps_folder, exist_ok=True)
        file_name = filedialog.asksaveasfilename(
            initialdir=maps_folder,
            defaultextension=".json",
            filetypes=[("Archivos JSON", "*.json")],
            title="Guardar Mapa"
        )
        if not file_name:
            return
        try:
            obstacles = []
            for obs in self.obstacles:
                original_coords = list(obs["original"][1])[0]
                mirror_coords = list(obs["mirror"][1])[0]
                obstacles.append({
                    "id": obs["id"],
                    "original": {"col": original_coords[0], "row": original_coords[1]},
                    "mirror": {"col": mirror_coords[0], "row": mirror_coords[1]},
                    "size": self.cell_size
                })

            geofence_cells = [{"col": col, "row": row} for col, row in self.geofence_cells]
            occupied_cells = [{"col": col, "row": row} for col, row in self.occupied_cells]

            map_data = {
                "map_size": {
                    "width": self.ancho_terreno_pixels,
                    "height": self.largo_terreno_pixels,
                    "cell_size": self.cell_size
                },
                "top_left": {
                    "lat": self.top_left_lat,
                    "lon": self.top_left_lon
                },
                "background": getattr(self, "background_image_path", None),
                "obstacles": obstacles,
                "obstacle_image": "assets/square.png",
                "geofence": geofence_cells,
                "occupied_cells": occupied_cells
            }

            with open(file_name, "w") as file:
                json.dump(map_data, file, indent=4)

            messagebox.showinfo("Guardado", f"Mapa guardado correctamente en: {file_name}")
        except Exception as e:
            messagebox.showerror("Error", f"Ocurrió un error al guardar el mapa: {e}")

    def add_background(self):
        background_folder = os.path.join(os.path.dirname(__file__), "Background")
        os.makedirs(background_folder, exist_ok=True)
        filename = filedialog.askopenfilename(
            initialdir=background_folder,
            title="Seleccionar imagen de fondo",
            filetypes=[("Imágenes", "*.png;*.jpg;*.jpeg;*.bmp")]
        )
        if filename:
            try:
                background_image = Image.open(filename).resize((self.ancho_terreno_pixels, self.largo_terreno_pixels),
                                                               Image.LANCZOS)
                self.background_image = ImageTk.PhotoImage(background_image)
                if hasattr(self, 'background_label'):
                    self.map_canvas.delete(self.background_label)
                self.background_label = self.map_canvas.create_image(0, 0, anchor="nw", image=self.background_image)
                self.map_canvas.tag_lower(self.background_label)
                destination_path = os.path.join(background_folder, os.path.basename(filename))
                if not os.path.exists(destination_path):
                    with open(filename, "rb") as src, open(destination_path, "wb") as dst:
                        dst.write(src.read())
                self.background_image_path = destination_path
                messagebox.showinfo("Éxito", "Imagen de fondo añadida correctamente.")
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo cargar la imagen de fondo: {e}")

    def select_obstacle(self, event):
        x, y = self.map_canvas.canvasx(event.x), self.map_canvas.canvasy(event.y)
        item = next((obj for obj in self.map_canvas.find_overlapping(x, y, x, y)
                     if "obstacle" in self.map_canvas.gettags(obj)), None)
        if item:
            for obstacle in self.obstacles:
                if obstacle["original"][0] == item or obstacle["mirror"][0] == item:
                    self.selected_obstacle = obstacle
                    print(
                        f"Obstáculo seleccionado: ID {obstacle['id']} - Celdas Originales: {obstacle['original'][1]} - Celdas Espejo: {obstacle['mirror'][1]}")
                    return

    def buildFrame(self):
        return self.fatherFrame


if __name__ == "__main__":
    root = ctk.CTk()
    root.geometry("1685x1009")
    editor = MapFrameClass(None, root)
    root.mainloop()
