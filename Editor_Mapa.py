import customtkinter as ctk
from tkinter import messagebox, filedialog
from PIL import Image, ImageTk


class MapFrameClass:
    def __init__(self, dron, fatherFrame):
        self.dron = dron
        self.geofencePoints = []
        self.geofenceElements = []  # Para guardar los GeoFence específicos de cada obstáculo
        self.grid_paths = []
        self.fatherFrame = fatherFrame
        self.obstacle_positions = []  # Lista para almacenar las posiciones de los obstáculos
        self.selected_obstacle = None  # Atributo para el obstáculo seleccionado
        self.selected_mirror_obstacle = None  # Atributo para el obstáculo reflejado seleccionado
        self.selected_mirror_obstacle = None  # Atributo para el obstáculo reflejado seleccionado
        self.occupied_cells = set()  # Conjunto para almacenar las celdas ocupadas (col, row)
        self.obstacles = []  # Lista de pares (obstacle_id, mirrored_obstacle_id)

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
        self.obstacles = []  # Guardamos cada obstáculo con su GeoFence
        self.current_obstacle_size = 27  # Tamaño inicial del obstáculo en píxeles

        # Mantener las referencias de imágenes redimensionadas para que no se recojan por el recolector de basura
        self.resized_images = {}

        # Inicializar las imágenes de los obstáculos
        self.obstacle_images = {}
        self.load_obstacle_images()

        # Ajuste de la escala para que la cuadrícula sea proporcional
        self.cell_size = 27  # Cada celda representa 1 metro aproximadamente (27.4 píxeles)
        self.ancho_terreno_metros = 32.00  # Ajustado a 32.00 metros para simetría en ancho
        self.largo_terreno_metros = 74.00  # Ajustado a 74.00 metros para evitar celdas cortadas

        # Ajustamos el número de columnas y filas para que sea simétrico
        self.ancho_terreno_pixels = int(self.ancho_terreno_metros * self.cell_size)
        self.largo_terreno_pixels = int(self.largo_terreno_metros * self.cell_size)

        self.setup_ui()

        # Añadimos los límites de geo fence automáticamente
        self.auto_create_geofence()

    def buildFrame(self):
        """Construye y devuelve el marco del mapa."""
        self.scrollbar_frame.pack(fill='both', expand=True)
        return self.scrollbar_frame

    def on_frame_configure(self, event):
        """Ajusta el scroll cuando se cambia el tamaño del frame"""
        self.canvas.config(scrollregion=self.canvas.bbox("all"))

    def load_obstacle_images(self):
        """Carga las imágenes de los obstáculos y maneja cualquier error."""
        try:
            self.obstacle_images["cuadrado"] = Image.open("assets/square.png").resize(
                (self.current_obstacle_size, self.current_obstacle_size), Image.LANCZOS)
            self.obstacle_images["Triangulo"] = Image.open("assets/triangle.png").resize(
                (self.current_obstacle_size, self.current_obstacle_size), Image.LANCZOS)
        except FileNotFoundError:

            messagebox.showerror("Error", "No se encontró la imagen del obstáculo en '/assets.")
            self.obstacle_images["cuadrado"] = Image.new("RGB",
                                                         (self.current_obstacle_size, self.current_obstacle_size),
                                                         "red")  # Crear una imagen de reserva

    def setup_ui(self):
        """Configura el marco y la interfaz de usuario."""
        self.MapFrame.grid_rowconfigure(0, weight=1)
        self.MapFrame.grid_columnconfigure(0, weight=1)
        self.MapFrame.grid_columnconfigure(1, weight=3)

        self.control_panel = ctk.CTkFrame(self.MapFrame, width=200)
        self.control_panel.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        self.add_buttons()

        # Ajuste del canvas para que tenga el tamaño adecuado en píxeles
        self.map_widget = ctk.CTkCanvas(self.MapFrame, width=self.ancho_terreno_pixels,
                                          height=self.largo_terreno_pixels)
        self.map_widget.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")

        self.draw_grid()

        # Ajustamos la vista del canvas para que comience desde la parte superior
        self.map_widget.xview_moveto(0)
        self.map_widget.yview_moveto(0)

    def add_buttons(self):
        """Añade los botones de la interfaz."""
        ctk.CTkButton(self.control_panel, text="Dibujar Obstáculo", command=self.draw_map_mode).pack(pady=10)
        ctk.CTkButton(self.control_panel, text="Añadir Fondo", command=self.add_background).pack(pady=10)
        ctk.CTkButton(self.control_panel, text="Aumentar tamaño", command=self.increase_obstacle_size).pack(pady=10)
        ctk.CTkButton(self.control_panel, text="Disminuir tamaño", command=self.decrease_obstacle_size).pack(pady=10)
        ctk.CTkButton(self.control_panel, text="Borrar Obstáculo Seleccionado", command=self.delete_selected_obstacle).pack(pady=10)

    def draw_grid(self):
        """Dibuja la cuadrícula sobre el mapa."""
        self.map_widget.delete("grid")  # Eliminar cualquier cuadrícula anterior

        cols = self.ancho_terreno_pixels // self.cell_size
        rows = self.largo_terreno_pixels // self.cell_size

        # Dibujar la cuadrícula ajustada al tamaño del terreno
        for i in range(cols + 1):
            self.map_widget.create_line(i * self.cell_size, 0, i * self.cell_size, self.largo_terreno_pixels,
                                        tag='grid', fill='blue')

        for j in range(rows + 1):
            self.map_widget.create_line(0, j * self.cell_size, self.ancho_terreno_pixels, j * self.cell_size,
                                        tag='grid', fill='blue')

        # Dibujar la línea que divide el mapa en dos, ajustada exactamente al borde de la celda
        mid_x = (self.ancho_terreno_pixels // 2) // self.cell_size * self.cell_size
        self.map_widget.create_line(mid_x, 0, mid_x, self.largo_terreno_pixels, tag='grid', fill='red', width=3)

        # Añadir la barra roja de GeoFence en la parte inferior del mapa
        self.map_widget.create_line(0, self.largo_terreno_pixels, self.ancho_terreno_pixels, self.largo_terreno_pixels,
                                    tag='grid', fill='red', width=3)

    def auto_create_geofence(self):
        """Crea automáticamente un geo fence que ocupa todo el borde del mapa."""
        top_left = (0, 0)
        top_right = (self.ancho_terreno_pixels, 0)
        bottom_left = (0, self.largo_terreno_pixels)
        bottom_right = (self.ancho_terreno_pixels, self.largo_terreno_pixels)

        # GeoFence alrededor de todo el mapa
        self.geofencePoints = [top_left, top_right, bottom_right, bottom_left]

        # Dibujar el geo fence en el mapa
        self.map_widget.create_line(top_left, top_right, fill="red", width=2, tags="geofence_line")
        self.map_widget.create_line(top_right, bottom_right, fill="red", width=2, tags="geofence_line")
        self.map_widget.create_line(bottom_right, bottom_left, fill="red", width=2, tags="geofence_line")
        self.map_widget.create_line(bottom_left, top_left, fill="red", width=2, tags="geofence_line")

    def draw_map_mode(self):
        """Activa el modo de dibujo de obstáculos con GeoFence."""
        messagebox.showinfo("Modo de Dibujo", "Haz clic derecho en el mapa para crear obstáculos con GeoFence.")
        self.map_widget.bind("<Button-3>", self.add_marker_event)
        self.map_widget.bind("<Button-1>", self.select_obstacle)


    def add_marker_event(self, event):
        """Agrega un obstáculo con GeoFence en la zona activa y lo duplica en la otra zona."""
        x = self.map_widget.canvasx(event.x)
        y = self.map_widget.canvasy(event.y)

        # Ajustar las coordenadas del obstáculo a la celda seleccionada
        col = int(x // self.cell_size)
        row = int(y // self.cell_size)

        # Comprobar si el obstáculo se coloca dentro de los límites
        if (col * self.cell_size + self.current_obstacle_size > self.ancho_terreno_pixels or
                row * self.cell_size + self.current_obstacle_size > self.largo_terreno_pixels):
            messagebox.showerror("Error", "No se puede colocar el obstáculo fuera de los límites del mapa.")
            return

        # Comprobar si el obstáculo se superpone con el geofence
        mid_x = self.ancho_terreno_pixels // 2
        if (col * self.cell_size < mid_x and col * self.cell_size + self.current_obstacle_size > mid_x) or \
                (col * self.cell_size >= mid_x and col * self.cell_size < mid_x + self.current_obstacle_size):
            messagebox.showerror("Error", "No se puede colocar el obstáculo sobre el geofence.")
            return

        # Comprobar si el obstáculo se superpone con otros obstáculos existentes
        for obstacle, _ in self.obstacles:
            print(f"Verificando obstáculo: {obstacle}")  # Depuración
            if isinstance(obstacle, int):  # Asegurar que es un ID válido de tkinter
                obstacle_coords = self.map_widget.coords(obstacle)
                if obstacle_coords:  # Verificar que el obstáculo tiene coordenadas
                    if self.is_overlapping(obstacle_coords, col * self.cell_size, row * self.cell_size):
                        messagebox.showerror("Error", "No se puede colocar el obstáculo sobre otro obstáculo.")
                        return
            else:
                print("Error: Obstáculo no tiene un ID válido.")

        # Ajustar las coordenadas a la celda más cercana
        x = col * self.cell_size
        y = row * self.cell_size

        # Cálculo de cuántas celdas ocupa el obstáculo
        cols_occupied = self.current_obstacle_size // self.cell_size
        rows_occupied = self.current_obstacle_size // self.cell_size

        # Generar las celdas que ocupará el nuevo obstáculo
        new_cells = {(col + i, row + j) for i in range(cols_occupied) for j in range(rows_occupied)}

        # Verificar si alguna de las celdas ya está ocupada por otro obstáculo
        if any(cell in self.occupied_cells for cell in new_cells):
            messagebox.showerror("Error", "No se puede colocar el obstáculo sobre otro obstáculo.")
            return

        # Agregar el obstáculo y reflejarlo en la otra mitad del mapa
        x = col * self.cell_size
        y = row * self.cell_size
        if x + self.current_obstacle_size <= self.ancho_terreno_pixels / 2:

            # Agregar obstáculo en la primera mitad del mapa
            obstacle_id = self.add_obstacle_with_geofence((x, y), cols_occupied, rows_occupied)

            # Duplicar en la segunda mitad del mapa
            mirrored_x = (self.ancho_terreno_pixels // 2) + (
                    (self.ancho_terreno_pixels // 2) - x) - self.current_obstacle_size
            mirror_obstacle_id = self.add_obstacle_with_geofence((mirrored_x, y), cols_occupied, rows_occupied)

            # Almacenar los IDs y actualizar las celdas ocupadas
            self.obstacles.append((obstacle_id, mirror_obstacle_id))
            mirror_col = int(mirrored_x // self.cell_size)
            mirror_cells = {(mirror_col + i, row + j) for i in range(cols_occupied) for j in range(rows_occupied)}
            self.occupied_cells.update(new_cells | mirror_cells)
            self.obstacle_positions.append(f"Obstáculo original: Celdas {sorted(new_cells)}")
            self.obstacle_positions.append(f"Obstáculo reflejado: Celdas {sorted(mirror_cells)}")

        else:
            # Agregar obstáculo en la segunda mitad
            obstacle_id = self.add_obstacle_with_geofence((x, y), cols_occupied, rows_occupied)

            # Duplicar en la primera mitad del mapa
            mirrored_x = (self.ancho_terreno_pixels // 2) - (
                    x - (self.ancho_terreno_pixels // 2)) - self.current_obstacle_size
            mirror_obstacle_id = self.add_obstacle_with_geofence((mirrored_x, y), cols_occupied, rows_occupied)

            # Almacenar los IDs y actualizar las celdas ocupadas
            self.obstacles.append((obstacle_id, mirror_obstacle_id))
            mirror_col = int(mirrored_x // self.cell_size)
            mirror_cells = {(mirror_col + i, row + j) for i in range(cols_occupied) for j in range(rows_occupied)}
            self.occupied_cells.update(new_cells | mirror_cells)
            self.obstacle_positions.append(f"Obstáculo original: Celdas {sorted(new_cells)}")
            self.obstacle_positions.append(f"Obstáculo reflejado: Celdas {sorted(mirror_cells)}")

            # Mostrar las coordenadas de todas las celdas ocupadas por el obstáculo
        messagebox.showinfo("Posiciones de los obstáculos",
                            f"{self.obstacle_positions[-2]}\n{self.obstacle_positions[-1]}")

    def add_obstacle_with_geofence(self, coords, cols_occupied, rows_occupied):
        """Añade un obstáculo en las coordenadas especificadas y dibuja su GeoFence."""
        obstacle_name = "cuadrado"
        if obstacle_name in self.obstacle_images:
            resized_icon = self.resize_image(self.obstacle_images[obstacle_name], self.current_obstacle_size)
            obstacle = self.map_widget.create_image(coords[0], coords[1], image=resized_icon, anchor='nw',
                                                    tags="obstacle")

            self.resized_images[obstacle] = resized_icon

            size = self.current_obstacle_size
            top_left = (coords[0], coords[1])
            bottom_right = (coords[0] + size, coords[1] + size)
            geofence = self.map_widget.create_rectangle(top_left[0], top_left[1], bottom_right[0], bottom_right[1],
                                                        outline="red", width=2, tags="geofence_obstacle")

            self.geofenceElements.append(geofence)
            return (obstacle, geofence)

    def is_overlapping(self, obstacle_coords, x, y):
        """Verifica si las coordenadas del nuevo obstáculo se superponen con el obstáculo existente."""
        new_obstacle_coords = (x, y, x + self.current_obstacle_size, y + self.current_obstacle_size)
        return (obstacle_coords[0] < new_obstacle_coords[2] and
                obstacle_coords[1] < new_obstacle_coords[3] and
                obstacle_coords[2] > new_obstacle_coords[0] and
                obstacle_coords[3] > new_obstacle_coords[1])

    def resize_image(self, image, size):
        """Redimensiona la imagen al tamaño especificado."""
        resized_image = image.resize((size, size), Image.LANCZOS)
        return ImageTk.PhotoImage(resized_image)

    def increase_obstacle_size(self):
        """Aumenta el tamaño del obstáculo."""
        self.current_obstacle_size += 10  # Aumenta el tamaño en 10 píxeles
        self.resize_obstacles()

    def decrease_obstacle_size(self):
        """Disminuye el tamaño del obstáculo."""
        if self.current_obstacle_size > 10:  # Asegura que no sea demasiado pequeño
            self.current_obstacle_size -= 10
            self.resize_obstacles()

    def resize_obstacles(self):
        for obstacle, resized_icon in self.obstacles:
            coords = self.map_widget.coords(obstacle)

            if coords:
                resized_icon = self.resize_image(self.obstacle_images["cuadrado"], self.current_obstacle_size)
                self.map_widget.itemconfig(obstacle, image=resized_icon)
                self.resized_images[obstacle] = resized_icon


    def select_obstacle(self, event):
        """Selecciona el obstáculo al hacer clic en él."""
        x = self.map_widget.canvasx(event.x)
        y = self.map_widget.canvasy(event.y)

        # Obtener el obstáculo más cercano a las coordenadas
        item = self.map_widget.find_closest(x, y)

        if item:  # Si encontramos un obstáculo
            obstacle_id = item[0]
            for obstacle_pair, mirror_pair in self.obstacles:
                # Comparar el ID del obstáculo con la lista de obstáculos guardados
                if obstacle_pair[0] == obstacle_id:
                    self.selected_obstacle = obstacle_pair
                    self.selected_mirror_obstacle = mirror_pair

                    # Cambiar el color de los obstáculos seleccionados
                    self.map_widget.itemconfig(self.selected_obstacle[0], outline="blue", width=3)
                    self.map_widget.itemconfig(self.selected_mirror_obstacle[0], outline="blue", width=3)

                    messagebox.showinfo("Selección",
                                        "Obstáculo seleccionado. Haz clic en 'Borrar Obstáculo Seleccionado' para eliminarlo.")
                    return
        else:
            messagebox.showwarning("Advertencia", "No se encontró ningún obstáculo en esa ubicación.")

    def delete_selected_obstacle(self):
        """Borra el obstáculo seleccionado y su reflejo, junto con sus geofences."""
        if self.selected_obstacle:
            # Borrar el obstáculo seleccionado
            self.map_widget.delete(self.selected_obstacle[0])  # Obstáculo
            self.map_widget.delete(self.selected_obstacle[1])  # GeoFence

            # Borrar el obstáculo reflejado
            self.map_widget.delete(self.selected_mirror_obstacle[0])  # Obstáculo reflejado
            self.map_widget.delete(self.selected_mirror_obstacle[1])  # GeoFence reflejado

            # Eliminar ambos del listado
            self.obstacles = [(o, m) for o, m in self.obstacles if
                              o != self.selected_obstacle and m != self.selected_mirror_obstacle]

            # Reiniciar selección
            self.selected_obstacle = None
            self.selected_mirror_obstacle = None

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


if __name__ == "_main_":
    root = ctk.CTk()
    editor = MapFrameClass(None, root)
    editor.buildFrame()
    root.mainloop()