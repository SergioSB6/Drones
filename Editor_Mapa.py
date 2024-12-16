import customtkinter as ctk
from tkinter import messagebox, filedialog
from PIL import Image, ImageTk
import os
import json

class MapFrameClass:
    def __init__(self, dron, fatherFrame):
        self.dron = dron
        self.geofencePoints = []
        self.geofenceElements = []
        self.grid_paths = []
        self.fatherFrame = fatherFrame
        self.obstacle_positions = []
        self.selected_obstacle = None
        self.occupied_cells = set()
        self.obstacles = []
        self.resized_images = {}
        self.obstacle_images = {}

        # Ajustar dinámicamente el tamaño de las celdas
        self.ancho_terreno_metros = 32.00
        self.largo_terreno_metros = 74.00
        self.cell_size = 0  # Se calculará dinámicamente

        self.calculate_cell_size()
        self.current_obstacle_size = self.cell_size

        self.ancho_terreno_pixels = int(self.ancho_terreno_metros * self.cell_size)
        self.largo_terreno_pixels = int(self.largo_terreno_metros * self.cell_size)

        self.load_obstacle_images()
        self.obstacle_counter = 0
        self.setup_ui()
        self.auto_create_geofence()

    def calculate_cell_size(self):
        # Tamaño fijo del mapa especificado por el usuario
        max_width = 1685
        max_height = 1009

        cell_width = max_width / self.ancho_terreno_metros
        cell_height = max_height / self.largo_terreno_metros

        # Tomar el tamaño mínimo para evitar distorsión
        self.cell_size = int(min(cell_width, cell_height))

    def generate_obstacle_id(self):
        self.obstacle_counter += 1
        return self.obstacle_counter

    def load_obstacle_images(self):
        try:
            self.obstacle_images["cuadrado"] = Image.open("assets/square.png").resize(
                (self.cell_size, self.cell_size), Image.LANCZOS)
        except FileNotFoundError:
            self.obstacle_images["cuadrado"] = Image.new("RGB",
                                                         (self.cell_size, self.cell_size), "red")

    def setup_ui(self):
        # Configurar el layout principal
        self.fatherFrame.grid_rowconfigure(0, weight=1)
        self.fatherFrame.grid_columnconfigure(1, weight=1)

        # Crear panel de control (fijo a la izquierda)
        self.control_panel = ctk.CTkFrame(self.fatherFrame, width=200)
        self.control_panel.grid(row=0, column=0, sticky="ns")
        self.add_buttons()

        # Crear el mapa centrado
        self.map_canvas = ctk.CTkCanvas(self.fatherFrame, width=1685, height=1009, bg="white")
        self.map_canvas.grid(row=0, column=1, sticky="nsew")

        self.draw_grid()
        self.map_canvas.bind("<Button-1>", self.select_obstacle)
        self.map_canvas.bind("<Button-3>", self.add_marker_event)

    def add_buttons(self):
        self.add_background_button = ctk.CTkButton(self.control_panel, text="Añadir Fondo", command=self.add_background)
        self.add_background_button.pack(pady=10)

        self.add_obstacle_button = ctk.CTkButton(self.control_panel, text="Añadir Obstáculo", command=self.add_marker_mode)
        self.add_obstacle_button.pack(pady=10)

        self.delete_button = ctk.CTkButton(self.control_panel, text="Borrar Obstáculo Seleccionado",
                                           command=self.delete_selected_obstacle)
        self.delete_button.pack(pady=10)

        self.save_button = ctk.CTkButton(self.control_panel, text="Guardar Mapa", command=self.save_map)
        self.save_button.pack(pady=10)

        self.load_button = ctk.CTkButton(self.control_panel, text="Cargar Mapa", command=self.load_map)
        self.load_button.pack(pady=10)

    def draw_grid(self):
        for i in range(0, self.ancho_terreno_pixels, self.cell_size):
            self.map_canvas.create_line(i, 0, i, self.largo_terreno_pixels, fill="blue", tag="grid")
        for j in range(0, self.largo_terreno_pixels, self.cell_size):
            self.map_canvas.create_line(0, j, self.ancho_terreno_pixels, j, fill="blue", tag="grid")

        # Línea roja central
        mid_x = self.ancho_terreno_pixels // 2
        self.map_canvas.create_line(mid_x, 0, mid_x, self.largo_terreno_pixels, fill="red", width=3, tag="grid")
        self.auto_create_geofence()

    def auto_create_geofence(self):
        offset = 1  # Margen adicional para asegurar que las líneas sean visibles
        self.map_canvas.create_line(offset, offset, self.ancho_terreno_pixels, offset, fill="red", width=3)
        self.map_canvas.create_line(self.ancho_terreno_pixels - offset, offset, self.ancho_terreno_pixels - offset, self.largo_terreno_pixels, fill="red", width=3)
        self.map_canvas.create_line(self.ancho_terreno_pixels - offset, self.largo_terreno_pixels - offset, offset, self.largo_terreno_pixels - offset, fill="red", width=3)
        self.map_canvas.create_line(offset, self.largo_terreno_pixels - offset, offset, offset, fill="red", width=3)

    def add_marker_mode(self):
        self.map_canvas.bind("<Button-3>", self.add_marker_event)
        messagebox.showinfo("Modo de Añadir", "Haz clic derecho en el mapa para añadir un obstáculo.")

    def add_marker_event(self, event):
        x = self.map_canvas.canvasx(event.x)
        y = self.map_canvas.canvasy(event.y)

        col, row = int(x // self.cell_size), int(y // self.cell_size)
        new_cells = {(col, row)}

        # Verificar si las celdas ya están ocupadas
        if any(cell in self.occupied_cells for cell in new_cells):
            messagebox.showerror("Error", "No se puede colocar el obstáculo sobre otro obstáculo.")
            return

        # Añadir obstáculo original
        x = col * self.cell_size
        y = row * self.cell_size
        obstacle_id = self.generate_obstacle_id()
        obstacle = self.add_obstacle((x, y), obstacle_id)

        # Calcular posición espejo
        mid_x = self.ancho_terreno_pixels // 2
        mirrored_x = mid_x + (mid_x - x) - self.cell_size
        mirrored_col = int(mirrored_x // self.cell_size)
        mirrored_cells = {(mirrored_col, row)}

        # Verificar si las celdas espejo están ocupadas
        if any(cell in self.occupied_cells for cell in mirrored_cells):
            messagebox.showerror("Error", "No se puede colocar el obstáculo espejo sobre otro obstáculo.")
            return

        # Añadir espejo
        mirror_obstacle = self.add_obstacle((mirrored_x, y), obstacle_id)

        # Guardar obstáculos con celdas ocupadas
        self.obstacles.append({
            "id": obstacle_id,
            "original": (obstacle, new_cells),
            "mirror": (mirror_obstacle, mirrored_cells)
        })
        self.occupied_cells.update(new_cells | mirrored_cells)

    def place_obstacle(self, x, y, mirrored):
        col, row = int(x // self.cell_size), int(y // self.cell_size)
        new_cells = {(col, row)}

        if any(cell in self.occupied_cells for cell in new_cells):
            return False

        x, y = col * self.cell_size, row * self.cell_size
        obstacle_id = self.generate_obstacle_id()
        obstacle = self.add_obstacle((x, y), obstacle_id)
        self.obstacles.append({"id": obstacle_id, "item": obstacle, "cells": new_cells, "mirrored": mirrored})
        self.occupied_cells.update(new_cells)
        return True


    def add_obstacle(self, coords, obstacle_id):
        resized_icon = ImageTk.PhotoImage(self.obstacle_images["cuadrado"].resize((self.cell_size, self.cell_size)))
        obstacle = self.map_canvas.create_image(coords[0], coords[1], image=resized_icon, anchor='nw', tags="obstacle")
        self.resized_images[obstacle] = resized_icon
        return obstacle

    def select_obstacle(self, event):
        x, y = self.map_canvas.canvasx(event.x), self.map_canvas.canvasy(event.y)
        item = next((obj for obj in self.map_canvas.find_overlapping(x, y, x, y)
                     if "obstacle" in self.map_canvas.gettags(obj)), None)

        if item:
            for obstacle in self.obstacles:
                if obstacle["original"][0] == item or obstacle["mirror"][0] == item:
                    self.selected_obstacle = obstacle
                    print(f"Obstáculo seleccionado: ID {obstacle['id']} - "
                          f"Celdas Originales: {obstacle['original'][1]} - "
                          f"Celdas Espejo: {obstacle['mirror'][1]}")
                    return

    def delete_selected_obstacle(self):
        if self.selected_obstacle:
            # Eliminar el obstáculo original
            self.map_canvas.delete(self.selected_obstacle["original"][0])
            self.occupied_cells.difference_update(self.selected_obstacle["original"][1])

            # Eliminar el obstáculo espejo
            self.map_canvas.delete(self.selected_obstacle["mirror"][0])
            self.occupied_cells.difference_update(self.selected_obstacle["mirror"][1])

            # Eliminar el obstáculo de la lista
            self.obstacles.remove(self.selected_obstacle)
            self.selected_obstacle = None
            print("Obstáculo y su espejo eliminados correctamente.")
        else:
            messagebox.showwarning("Advertencia", "No hay obstáculo seleccionado para eliminar.")

    def add_background(self):
        filename = filedialog.askopenfilename(title="Seleccionar imagen de fondo")
        if filename:
            background_image = Image.open(filename).resize((self.ancho_terreno_pixels, self.largo_terreno_pixels), Image.LANCZOS)
            self.background_image = ImageTk.PhotoImage(background_image)
            if hasattr(self, 'background_label'):
                self.map_canvas.delete(self.background_label)
            self.background_label = self.map_canvas.create_image(0, 0, anchor="nw", image=self.background_image)
            self.map_canvas.tag_lower(self.background_label)

    def save_map(self):
        folder_path = "Drones/maps"
        os.makedirs(folder_path, exist_ok=True)

        file_name = filedialog.asksaveasfilename(
            initialdir=folder_path,
            title="Guardar Mapa",
            defaultextension=".json",
            filetypes=[("Archivos JSON", "*.json")]
        )

        if not file_name:
            messagebox.showwarning("Cancelado", "El guardado del mapa fue cancelado.")
            return

        try:
            obstacles = []
            for obs in self.obstacles:
                if "original" in obs and "mirror" in obs:
                    obstacles.append({
                        "id": obs["id"],
                        "original": {"x": obs["original"]["coords"][0], "y": obs["original"]["coords"][1]},
                        "mirror": {"x": obs["mirror"]["coords"][0], "y": obs["mirror"]["coords"][1]}
                    })

            geofence = []
            for element in self.geofenceElements:
                coords = self.map_canvas.coords(element)
                if coords:
                    geofence.append({"x": coords[0], "y": coords[1]})

            map_data = {
                "map_size": {
                    "width": self.map_canvas.winfo_width(),
                    "height": self.map_canvas.winfo_height()
                },
                "obstacles": obstacles,
                "geofence": geofence
            }

            with open(file_name, "w") as file:
                json.dump(map_data, file, indent=4)

            messagebox.showinfo("Guardado", f"Mapa guardado correctamente como: {os.path.basename(file_name)}")
        except Exception as e:
            messagebox.showerror("Error", f"Ocurrió un error al guardar el mapa: {str(e)}")

    def load_map(self):
        folder_path = "Drones/maps"
        file_path = filedialog.askopenfilename(
            initialdir=folder_path,
            title="Cargar Mapa",
            filetypes=[("Archivos JSON", "*.json")]
        )

        if not file_path:
            messagebox.showwarning("Cancelado", "La carga del mapa fue cancelada.")
            return

        try:
            with open(file_path, "r") as file:
                map_data = json.load(file)

            # Limpiar canvas y variables
            self.map_canvas.delete("all")
            self.occupied_cells.clear()
            self.obstacles.clear()
            self.selected_obstacle = None

            # Dibujar la cuadrícula y el geofence
            self.draw_grid()
            self.auto_create_geofence()

            # Cargar el fondo
            if map_data.get("background"):
                self.add_background_from_path(map_data["background"])

            # Cargar los obstáculos
            for obs in map_data["obstacles"]:
                original_x = obs["original"]["x"]
                original_y = obs["original"]["y"]

                # Reconstruir obstáculo original y espejo
                self.load_obstacle(original_x, original_y)

            messagebox.showinfo("Cargado", f"Mapa cargado correctamente desde: {file_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Ocurrió un error al cargar el mapa: {str(e)}")

    def load_obstacle(self, x, y):
        # Añadir obstáculo original
        col, row = int(x // self.cell_size), int(y // self.cell_size)
        new_cells = {(col, row)}

        # Calcular posición espejo
        mid_x = self.ancho_terreno_pixels // 2
        mirrored_x = mid_x + (mid_x - x) - self.cell_size
        mirrored_col = int(mirrored_x // self.cell_size)
        mirrored_cells = {(mirrored_col, row)}

        # Añadir obstáculo y espejo al mapa
        obstacle_id = self.generate_obstacle_id()
        obstacle = self.add_obstacle((x, y), obstacle_id)
        mirror_obstacle = self.add_obstacle((mirrored_x, y), obstacle_id)

        # Actualizar variables
        self.obstacles.append({
            "id": obstacle_id,
            "original": (obstacle, new_cells),
            "mirror": (mirror_obstacle, mirrored_cells)
        })
        self.occupied_cells.update(new_cells | mirrored_cells)

    def add_background_from_path(self, path):
        try:
            background_image = Image.open(path).resize((self.ancho_terreno_pixels, self.largo_terreno_pixels),
                                                       Image.LANCZOS)
            self.background_image = ImageTk.PhotoImage(background_image)
            if hasattr(self, 'background_label'):
                self.map_canvas.delete(self.background_label)
            self.background_label = self.map_canvas.create_image(0, 0, anchor="nw", image=self.background_image)
            self.map_canvas.tag_lower(self.background_label)
            self.background_image_path = path
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo cargar el fondo: {str(e)}")


    def buildFrame(self):
        return self.fatherFrame


if __name__ == "__main__":
    root = ctk.CTk()
    root.geometry("1685x1009")
    root.grid_rowconfigure(0, weight=1)
    root.grid_columnconfigure(1, weight=1)
    editor = MapFrameClass(None, root)
    root.mainloop()
