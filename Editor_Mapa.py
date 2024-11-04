import customtkinter as ctk
from tkinter import messagebox, filedialog
from PIL import Image, ImageTk, ImageOps


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
        self.obstacle_type = "cuadrado"  # Tipo de obstáculo por defecto
        self.rotation_angles = {}  # Almacena el ángulo de rotación para cada obstáculo

        # Crear frame principal con scrollbar
        self.scrollbar_frame = ctk.CTkFrame(self.fatherFrame)
        self.scrollbar_frame.pack(fill='both', expand=True)

        # Crear scrollbar
        self.scrollbar_y = ctk.CTkScrollbar(self.scrollbar_frame, orientation="vertical")
        self.scrollbar_y.pack(side="right", fill="y")

        self.canvas = ctk.CTkCanvas(self.scrollbar_frame, yscrollcommand=self.scrollbar_y.set)
        self.canvas.pack(side="left", fill="both", expand=True)

        self.scrollbar_y.configure(command=self.canvas.yview)

        # Crear otro frame dentro del canvas
        self.MapFrame = ctk.CTkFrame(self.canvas)
        self.canvas.create_window((0, 0), window=self.MapFrame, anchor='nw')

        # Para que el canvas detecte el tamaño adecuado
        self.MapFrame.bind("<Configure>", self.on_frame_configure)

        self.background_label = None
        self.current_obstacle_size = 27  # Tamaño inicial del obstáculo en píxeles
        self.resized_images = {}

        # Inicializar las imágenes de los obstáculos
        self.obstacle_images = {}
        self.load_obstacle_images()

        # Ajuste de la escala para que la cuadrícula sea proporcional
        self.cell_size = 27
        self.ancho_terreno_metros = 32.00
        self.largo_terreno_metros = 74.00

        self.ancho_terreno_pixels = int(self.ancho_terreno_metros * self.cell_size)
        self.largo_terreno_pixels = int(self.largo_terreno_metros * self.cell_size)

        self.setup_ui()
        self.auto_create_geofence()

    def buildFrame(self):
        self.scrollbar_frame.pack(fill='both', expand=True)
        return self.scrollbar_frame

    def on_frame_configure(self, event):
        self.canvas.config(scrollregion=self.canvas.bbox("all"))

    def load_obstacle_images(self):
        try:
            self.obstacle_images["cuadrado"] = Image.open("assets/square.png").resize(
                (self.current_obstacle_size, self.current_obstacle_size), Image.LANCZOS)
            self.obstacle_images["Triangulo"] = Image.open("assets/triangle.png").resize(
                (self.current_obstacle_size, self.current_obstacle_size), Image.LANCZOS)
        except FileNotFoundError:
            messagebox.showerror("Error", "No se encontró la imagen del obstáculo en '/assets.")
            self.obstacle_images["cuadrado"] = Image.new("RGB",
                                                         (self.current_obstacle_size, self.current_obstacle_size),
                                                         "red")

    def setup_ui(self):
        self.MapFrame.grid_rowconfigure(0, weight=1)
        self.MapFrame.grid_columnconfigure(0, weight=1)
        self.MapFrame.grid_columnconfigure(1, weight=3)

        self.control_panel = ctk.CTkFrame(self.MapFrame, width=200)
        self.control_panel.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        # Añadir el desplegable para seleccionar el tipo de obstáculo
        self.obstacle_selector = ctk.CTkOptionMenu(self.control_panel, values=["cuadrado", "Triangulo"],
                                                   command=self.update_obstacle_type)
        self.obstacle_selector.pack(pady=10)
        self.obstacle_selector.set("cuadrado")  # Valor inicial del desplegable

        self.add_buttons()

        self.map_widget = ctk.CTkCanvas(self.MapFrame, width=self.ancho_terreno_pixels,
                                        height=self.largo_terreno_pixels)
        self.map_widget.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")

        self.draw_grid()
        self.map_widget.xview_moveto(0)
        self.map_widget.yview_moveto(0)

    def update_obstacle_type(self, selected_type):
        """Actualiza el tipo de obstáculo seleccionado."""
        self.obstacle_type = selected_type

    def add_buttons(self):
        ctk.CTkButton(self.control_panel, text="Dibujar Obstáculo", command=self.draw_map_mode).pack(pady=10)
        ctk.CTkButton(self.control_panel, text="Añadir Fondo", command=self.add_background).pack(pady=10)
        ctk.CTkButton(self.control_panel, text="Aumentar tamaño", command=self.increase_obstacle_size).pack(pady=10)
        ctk.CTkButton(self.control_panel, text="Disminuir tamaño", command=self.decrease_obstacle_size).pack(pady=10)
        ctk.CTkButton(self.control_panel, text="Borrar Obstáculo Seleccionado",
                      command=self.delete_selected_obstacle).pack(pady=10)
        ctk.CTkButton(self.control_panel, text="Rotar Obstáculo", command=self.rotate_obstacle).pack(pady=10)

    def draw_map_mode(self):
        """Activa el modo de dibujo de obstáculos con GeoFence."""
        messagebox.showinfo("Modo de Dibujo", "Haz clic derecho en el mapa para crear obstáculos con GeoFence.")
        self.map_widget.bind("<Button-3>", self.add_marker_event)
        self.map_widget.bind("<Button-1>", self.select_obstacle)

    def draw_grid(self):
        self.map_widget.delete("grid")

        cols = self.ancho_terreno_pixels // self.cell_size
        rows = self.largo_terreno_pixels // self.cell_size

        for i in range(cols + 1):
            self.map_widget.create_line(i * self.cell_size, 0, i * self.cell_size, self.largo_terreno_pixels,
                                        tag='grid', fill='blue')

        for j in range(rows + 1):
            self.map_widget.create_line(0, j * self.cell_size, self.ancho_terreno_pixels, j * self.cell_size,
                                        tag='grid', fill='blue')

        mid_x = (self.ancho_terreno_pixels // 2) // self.cell_size * self.cell_size
        self.map_widget.create_line(mid_x, 0, mid_x, self.largo_terreno_pixels, tag='grid', fill='red', width=3)

        self.map_widget.create_line(0, self.largo_terreno_pixels, self.ancho_terreno_pixels, self.largo_terreno_pixels,
                                    tag='grid', fill='red', width=3)

    def auto_create_geofence(self):
        top_left = (0, 0)
        top_right = (self.ancho_terreno_pixels, 0)
        bottom_left = (0, self.largo_terreno_pixels)
        bottom_right = (self.ancho_terreno_pixels, self.largo_terreno_pixels)

        self.geofencePoints = [top_left, top_right, bottom_right, bottom_left]

        self.map_widget.create_line(top_left, top_right, fill="red", width=2, tags="geofence_line")
        self.map_widget.create_line(top_right, bottom_right, fill="red", width=2, tags="geofence_line")
        self.map_widget.create_line(bottom_right, bottom_left, fill="red", width=2, tags="geofence_line")
        self.map_widget.create_line(bottom_left, top_left, fill="red", width=2, tags="geofence_line")

    def add_marker_event(self, event):
        x = self.map_widget.canvasx(event.x)
        y = self.map_widget.canvasy(event.y)

        col = int(x // self.cell_size)
        row = int(y // self.cell_size)

        # Cálculo de cuántas celdas ocupa el obstáculo
        cols_occupied = -(-self.current_obstacle_size // self.cell_size)  # Redondeo hacia arriba
        rows_occupied = -(-self.current_obstacle_size // self.cell_size)  # Redondeo hacia arriba

        # Generar las celdas que ocupará el nuevo obstáculo
        new_cells = {(col + i, row + j) for i in range(cols_occupied) for j in range(rows_occupied)}

        # Verificar si alguna de las celdas ya está ocupada por otro obstáculo
        if any(cell in self.occupied_cells for cell in new_cells):
            messagebox.showerror("Error", "No se puede colocar el obstáculo sobre otro obstáculo.")
            return

        # Verificar si el obstáculo se coloca dentro de los límites
        if (col * self.cell_size + self.current_obstacle_size > self.ancho_terreno_pixels or
                row * self.cell_size + self.current_obstacle_size > self.largo_terreno_pixels):
            messagebox.showerror("Error", "No se puede colocar el obstáculo fuera de los límites del mapa.")
            return

        mid_x = self.ancho_terreno_pixels // 2
        if (col * self.cell_size < mid_x and col * self.cell_size + self.current_obstacle_size > mid_x) or \
                (col * self.cell_size >= mid_x and col * self.cell_size < mid_x + self.current_obstacle_size):
            messagebox.showerror("Error", "No se puede colocar el obstáculo sobre el geofence.")
            return

        # Ajustar las coordenadas a la celda más cercana
        x = col * self.cell_size
        y = row * self.cell_size

        # Agregar el obstáculo y su reflejo
        obstacle_id = self.add_obstacle_with_geofence((x, y), cols_occupied, rows_occupied)
        mirrored_x = (self.ancho_terreno_pixels // 2) + (
                (self.ancho_terreno_pixels // 2) - x) - self.current_obstacle_size
        mirror_obstacle_id = self.add_obstacle_with_geofence((mirrored_x, y), cols_occupied, rows_occupied)
        self.obstacles.append((obstacle_id, mirror_obstacle_id, new_cells))
        self.occupied_cells.update(new_cells)
        print(f"Occupied cells updated after adding: {self.occupied_cells}")

    def add_obstacle_with_geofence(self, coords, cols_occupied, rows_occupied):
        """Añade un obstáculo en las coordenadas especificadas y dibuja su GeoFence adaptado a la forma."""
        if self.obstacle_type in self.obstacle_images:
            resized_icon = self.resize_image(self.obstacle_images[self.obstacle_type], self.current_obstacle_size)
            obstacle = self.map_widget.create_image(coords[0], coords[1], image=resized_icon, anchor='nw',
                                                    tags="obstacle")
            self.resized_images[obstacle] = resized_icon

            # Generar un geofence adaptado a la forma de la imagen del obstáculo, sin relleno
            geofence_points = self.get_shape_contour_points(coords)
            geofence = self.map_widget.create_polygon(geofence_points, outline="red", fill="", width=2,
                                                      tags="geofence_obstacle")
            self.geofenceElements.append(geofence)
            return (obstacle, geofence)

    def rotate_obstacle(self):
        """Rota el obstáculo seleccionado 90 grados cada vez que se presiona el botón."""
        if self.selected_obstacle:
            # Incrementar el ángulo de rotación
            current_angle = self.rotation_angles.get(self.selected_obstacle[0][0], 0)
            new_angle = (current_angle + 90) % 360
            self.rotation_angles[self.selected_obstacle[0][0]] = new_angle
            self.rotation_angles[self.selected_obstacle[1][0]] = new_angle  # Para el espejo también

            # Rotar la imagen del obstáculo seleccionado
            for obs, geo in [self.selected_obstacle[0], self.selected_obstacle[1]]:
                image = self.obstacle_images[self.obstacle_type]
                rotated_image = image.rotate(new_angle, expand=True)
                resized_icon = ImageTk.PhotoImage(rotated_image.resize((self.current_obstacle_size, self.current_obstacle_size)))
                self.map_widget.itemconfig(obs, image=resized_icon)
                self.resized_images[obs] = resized_icon

                # Rotar el geofence también
                coords = self.map_widget.coords(obs)
                if coords:
                    geofence_points = self.get_shape_contour_points((coords[0], coords[1]))
                    rotated_points = self.rotate_points(geofence_points, new_angle, coords)
                    self.map_widget.coords(geo, *sum(rotated_points, ()))

    def rotate_points(self, points, angle, center):
        """Rota una lista de puntos en torno a un centro dado."""
        from math import cos, sin, radians
        angle = radians(angle)
        cx, cy = center
        rotated_points = []
        for x, y in points:
            tx, ty = x - cx, y - cy
            x_rot = tx * cos(angle) - ty * sin(angle) + cx
            y_rot = tx * sin(angle) + ty * cos(angle) + cy
            rotated_points.append((x_rot, y_rot))
        return rotated_points

    def get_shape_contour_points(self, coords):
        """Obtiene los puntos del contorno de la forma del obstáculo en función de la geometría del tamaño."""
        x, y = coords
        size = self.current_obstacle_size

        if self.obstacle_type == "cuadrado":
            # Contorno de un cuadrado
            return [(x, y), (x + size, y), (x + size, y + size), (x, y + size)]
        elif self.obstacle_type == "Triangulo":
            # Contorno de un triángulo equilátero
            return [(x + size / 2, y), (x, y + size), (x + size, y + size)]
        else:
            return []

    def resize_image(self, image, size):
        resized_image = image.resize((size, size), Image.LANCZOS)
        return ImageTk.PhotoImage(resized_image)

    def increase_obstacle_size(self):
        self.current_obstacle_size += 10
        self.resize_obstacles()

    def decrease_obstacle_size(self):
        if self.current_obstacle_size > 10:
            self.current_obstacle_size -= 10
            self.resize_obstacles()

    def resize_obstacles(self):
        for obstacle_pair in self.obstacles:
            obstacle = obstacle_pair[0]  # Solo consideramos el obstáculo en sí, no el reflejo.
            if self.map_widget.coords(obstacle):  # Verificamos que el obstáculo aún existe en el mapa.
                coords = self.map_widget.coords(obstacle)
                if coords:  # Asegurarse de que se obtuvieron coordenadas válidas.
                    resized_icon = self.resize_image(self.obstacle_images[self.obstacle_type],
                                                     self.current_obstacle_size)
                    self.map_widget.itemconfig(obstacle, image=resized_icon)
                    self.resized_images[obstacle] = resized_icon

    def select_obstacle(self, event):
        """Selecciona el obstáculo al hacer clic en él."""
        x = self.map_widget.canvasx(event.x)
        y = self.map_widget.canvasy(event.y)

        # Filtrar los elementos que están en la posición clicada
        item = None
        for obj in self.map_widget.find_overlapping(x, y, x, y):
            if "obstacle" in self.map_widget.gettags(obj):
                item = obj
                break

        if item:
            obstacle_id = item
            for obstacle_pair in self.obstacles:
                if obstacle_pair[0][0] == obstacle_id or obstacle_pair[1][0] == obstacle_id:
                    self.selected_obstacle = obstacle_pair
                    break
            if self.selected_obstacle:
                # Marcar el obstáculo y su reflejo
                self.map_widget.itemconfig(self.selected_obstacle[1][1], outline="blue", width=3)  # Geofence
                messagebox.showinfo("Selección",
                                    "Obstáculo seleccionado. Usa 'Borrar Obstáculo Seleccionado' para eliminarlo.")
        else:
            messagebox.showwarning("Advertencia", "No se encontró ningún obstáculo en esa ubicación.")

    def delete_selected_obstacle(self):
        """Borra el obstáculo seleccionado y su reflejo, junto con sus geofences."""
        if self.selected_obstacle:
            self.map_widget.delete(self.selected_obstacle[0][0])  # Obstáculo
            self.map_widget.delete(self.selected_obstacle[0][1])  # Geofence
            self.map_widget.delete(self.selected_obstacle[1][0])  # Obstáculo reflejado
            self.map_widget.delete(self.selected_obstacle[1][1])  # Geofence reflejado

            # Eliminar las celdas ocupadas asociadas al obstáculo
            cells_to_remove = self.selected_obstacle[2]
            self.occupied_cells.difference_update(cells_to_remove)

            print(f"Cells to remove: {cells_to_remove}")
            print(f"Occupied cells after deletion: {self.occupied_cells}")

            # Actualizar la lista de obstáculos y reiniciar la selección
            self.obstacles = [obs for obs in self.obstacles if obs != self.selected_obstacle]
            self.selected_obstacle = None

            messagebox.showinfo("Eliminación", "Obstáculo y reflejo eliminados con éxito.")
        else:
            messagebox.showwarning("Advertencia", "No hay obstáculo seleccionado para eliminar.")

    def add_background(self):
        filename = filedialog.askopenfilename(title="Seleccionar imagen de fondo")
        if filename:
            background_image = Image.open(filename).resize((self.ancho_terreno_pixels, self.largo_terreno_pixels),
                                                           Image.LANCZOS)
            self.background_image = ImageTk.PhotoImage(background_image)

            if self.background_label:
                self.map_widget.delete(self.background_label)

            self.background_label = self.map_widget.create_image(0, 0, anchor="nw", image=self.background_image)
            self.map_widget.tag_lower(self.background_label)


if __name__ == "__main__":
    root = ctk.CTk()
    editor = MapFrameClass(None, root)
    editor.buildFrame()
    root.mainloop()
