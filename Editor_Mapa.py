import json
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
        self.MapFrame = ctk.CTkFrame(self.fatherFrame)
        self.background_label = None
        self.obstacles = []  # Guardamos cada obstáculo con su GeoFence y área verde
        self.current_obstacle_size = 27  # Tamaño inicial del obstáculo en píxeles

        # Mantener las referencias de imágenes redimensionadas para que no se recojan por el recolector de basura
        self.resized_images = {}

        # Inicializar las imágenes de los obstáculos
        self.obstacle_images = {}
        self.load_obstacle_images()

        # Ajuste de la escala para que la cuadrícula sea proporcional
        self.cell_size = 27  # Cada celda representa 1 metro aproximadamente (27.4 píxeles)
        self.ancho_terreno_metros = 32.84
        self.largo_terreno_metros = 74.5

        self.ancho_terreno_pixels = int(self.ancho_terreno_metros * self.cell_size)
        self.largo_terreno_pixels = int(self.largo_terreno_metros * self.cell_size)

        self.setup_ui()

        # Añadimos los límites de geo fence automáticamente
        self.auto_create_geofence()

    def load_obstacle_images(self):
        """Carga las imágenes de los obstáculos y maneja cualquier error."""
        try:
            self.obstacle_images["cuadrado"] = Image.open("assets/square.png").resize((self.current_obstacle_size, self.current_obstacle_size), Image.LANCZOS)
        except FileNotFoundError:
            messagebox.showerror("Error", "No se encontró la imagen del obstáculo en 'assets/square.png'.")
            self.obstacle_images["cuadrado"] = Image.new("RGB", (self.current_obstacle_size, self.current_obstacle_size), "red")  # Crear una imagen de reserva

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

        self.MapFrame.grid_columnconfigure(1, weight=1)

        self.draw_grid()

        # Ajustamos la vista del canvas para que comience desde la parte superior
        self.map_widget.xview_moveto(0)
        self.map_widget.yview_moveto(0)

    def buildFrame(self):
        """Construye y devuelve el marco del mapa."""
        self.MapFrame.pack(expand=True, fill='both')
        return self.MapFrame

    def add_buttons(self):
        """Añade los botones de la interfaz."""
        ctk.CTkButton(self.control_panel, text="Dibujar Obstáculo", command=self.draw_map_mode).pack(pady=10)
        ctk.CTkButton(self.control_panel, text="Añadir Fondo", command=self.add_background).pack(pady=10)
        ctk.CTkButton(self.control_panel, text="Aumentar tamaño", command=self.increase_obstacle_size).pack(pady=10)
        ctk.CTkButton(self.control_panel, text="Disminuir tamaño", command=self.decrease_obstacle_size).pack(pady=10)
        ctk.CTkButton(self.control_panel, text="Borrar Obstáculo", command=self.delete_obstacle).pack(pady=10)

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

    def add_marker_event(self, event):
        """Agrega un obstáculo con GeoFence en la zona activa y lo duplica en la otra zona."""
        x = self.map_widget.canvasx(event.x)
        y = self.map_widget.canvasy(event.y)

        mid_x = (self.ancho_terreno_pixels // 2) // self.cell_size * self.cell_size

        # Ajustar las coordenadas del obstáculo a la celda seleccionada
        col = int(x // self.cell_size)
        row = int(y // self.cell_size)
        x = col * self.cell_size
        y = row * self.cell_size

        # Cálculo de cuántas celdas ocupa el obstáculo
        cols_occupied = self.current_obstacle_size // self.cell_size
        rows_occupied = self.current_obstacle_size // self.cell_size

        if x <= mid_x:
            # Si el obstáculo está en la primera mitad del mapa
            obstacle_pair = self.add_obstacle_with_geofence((x, y), cols_occupied, rows_occupied)

            # Duplicar el obstáculo en la segunda mitad del mapa
            mirrored_x = mid_x + (mid_x - x)
            mirror_obstacle = self.add_obstacle_with_geofence((mirrored_x, y), cols_occupied, rows_occupied)

            # Guardar ambos obstáculos como un par
            self.obstacles.append((obstacle_pair, mirror_obstacle))
        else:
            # Si el obstáculo está en la segunda mitad del mapa
            obstacle_pair = self.add_obstacle_with_geofence((x, y), cols_occupied, rows_occupied)

            # Duplicar el obstáculo en la primera mitad del mapa
            mirrored_x = mid_x - (x - mid_x)
            mirror_obstacle = self.add_obstacle_with_geofence((mirrored_x, y), cols_occupied, rows_occupied)

            # Guardar ambos obstáculos como un par
            self.obstacles.append((obstacle_pair, mirror_obstacle))

        # Mostrar mensaje de coordenadas
        messagebox.showinfo("Coordenada", f"Obstáculo añadido en la celda ({col}, {row}), ocupando celdas de "
                                          f"({col}, {row}) a ({col + cols_occupied - 1}, {row + rows_occupied - 1})")

    def add_obstacle_with_geofence(self, coords, cols_occupied, rows_occupied):
        """Añade un obstáculo en las coordenadas especificadas y dibuja su GeoFence."""
        obstacle_name = "cuadrado"
        if obstacle_name in self.obstacle_images:
            resized_icon = self.resize_image(self.obstacle_images[obstacle_name], self.current_obstacle_size)
            obstacle = self.map_widget.create_image(coords[0], coords[1], image=resized_icon, anchor='nw',
                                                    tags="obstacle")

            # Aquí es donde almacenamos las referencias de las imágenes redimensionadas
            self.resized_images[obstacle] = resized_icon

            # Asociamos cada obstáculo con su propio GeoFence
            size = self.current_obstacle_size
            top_left = (coords[0], coords[1])
            bottom_right = (coords[0] + size, coords[1] + size)
            geofence = self.map_widget.create_rectangle(top_left[0], top_left[1], bottom_right[0], bottom_right[1],
                                                        outline="red", width=2, tags="geofence_obstacle")

            # Pintar todas las celdas ocupadas de verde
            col_start = int(coords[0] // self.cell_size)
            row_start = int(coords[1] // self.cell_size)
            area_green = []
            for i in range(cols_occupied):
                for j in range(rows_occupied):
                    green_area = self.map_widget.create_rectangle(
                        (col_start + i) * self.cell_size, (row_start + j) * self.cell_size,
                        (col_start + i + 1) * self.cell_size, (row_start + j + 1) * self.cell_size,
                        outline="green", width=2
                    )
                    area_green.append(green_area)

            self.geofenceElements.append(geofence)  # Guardamos el GeoFence para ese obstáculo
            return (obstacle, geofence, area_green)  # Devolvemos ambos elementos (obstáculo, GeoFence, y área verde)

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
        # Asegúrate de que obstacles tenga coordenadas correctas.
        for obstacle in self.obstacles:
            # Obtener las coordenadas actuales del obstáculo.
            coords = self.map_widget.coords(obstacle)

            if len(coords) == 4:  # Verificar que hay exactamente 4 coordenadas
                x1, y1, x2, y2 = coords
                # Calcular nuevas coordenadas
                width = self.current_obstacle_size
                height = self.current_obstacle_size

                # Actualizar las coordenadas del obstáculo
                new_coords = (x1, y1, x1 + width, y1 + height)
                self.map_widget.coords(obstacle, *new_coords)
            else:
                print(f"Error: el obstáculo tiene un número inesperado de coordenadas: {coords}")

    def delete_obstacle(self):
        """Elimina el último par de obstáculos (original y su espejo) junto con sus GeoFences y área verde."""
        if self.obstacles:
            # Eliminamos el último par de obstáculos y sus GeoFences correspondientes
            obstacle_pair = self.obstacles.pop()

            for obstacle, geofence, area_green in obstacle_pair:
                self.map_widget.delete(obstacle)  # Elimina el obstáculo
                self.map_widget.delete(geofence)  # Elimina su GeoFence
                for area in area_green:
                    self.map_widget.delete(area)  # Elimina el área verde
                self.resized_images.pop(obstacle, None)  # Eliminar referencia de la imagen redimensionada

    def add_background(self):
        """Añade una imagen de fondo al mapa escalada correctamente."""
        filename = filedialog.askopenfilename(title="Seleccionar imagen de fondo")
        if filename:
            # Abrir y redimensionar la imagen
            background_image = Image.open(filename).resize((self.ancho_terreno_pixels, self.largo_terreno_pixels),
                                                           Image.LANCZOS)
            self.background_image = ImageTk.PhotoImage(background_image)

            # Agregar la imagen al canvas
            if self.background_label:
                self.map_widget.delete(self.background_label)  # Eliminar el fondo anterior si existe

            self.background_label = self.map_widget.create_image(0, 0, anchor="nw", image=self.background_image)

            # Enviar la imagen al fondo del canvas
            self.map_widget.tag_lower(self.background_label)


if __name__ == "_main_":
    root = ctk.CTk()
    editor = MapFrameClass(None, root)
    editor.buildFrame()
    root.mainloop()