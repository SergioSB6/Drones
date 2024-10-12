import json
import customtkinter as ctk
from tkinter import messagebox, filedialog
from PIL import Image, ImageTk
from tkintermapview import TkinterMapView


class MapFrameClass:
    def __init__(self, dron, fatherFrame):
        self.dron = dron
        self.geofencePoints = []
        self.geofenceElements = []
        self.obstacle_images = {
            "cuadrado": Image.open("assets/square.png").resize((27, 27), Image.LANCZOS)  # Ajuste inicial
        }
        self.grid_paths = []
        self.fatherFrame = fatherFrame
        self.MapFrame = ctk.CTkFrame(self.fatherFrame)
        self.background_label = None
        self.obstacles = []
        self.current_obstacle_size = 27  # Tamaño inicial del obstáculo en píxeles

        # Mantener las referencias de imágenes redimensionadas para que no se recojan por el recolector de basura
        self.resized_images = {}

        # Ajuste de la escala para que la cuadrícula sea proporcional al laboratorio
        self.metros_por_pixel = 1 / 27.4  # Aproximadamente 1 metro por 27.4 píxeles
        self.largo_terreno_metros = 74.5
        self.ancho_terreno_metros = 32.84

        # Convertir las dimensiones del terreno a píxeles según la escala
        self.largo_terreno_pixels = int(self.largo_terreno_metros * 27.4)
        self.ancho_terreno_pixels = int(self.ancho_terreno_metros * 27.4)

        self.cell_size = 27  # Cada celda representa 1 metro aproximadamente (27.4 píxeles)
        self.setup_ui()

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

    def buildFrame(self):
        """Construye y devuelve el marco del mapa."""
        self.MapFrame.pack(expand=True, fill='both')
        return self.MapFrame

    def add_buttons(self):
        """Añade los botones de la interfaz."""
        ctk.CTkButton(self.control_panel, text="Dibujar Mapa", command=self.draw_map_mode).pack(pady=10)
        ctk.CTkButton(self.control_panel, text="Obstáculos", command=self.select_obstacle).pack(pady=10)
        ctk.CTkButton(self.control_panel, text="Añadir Fondo", command=self.add_background).pack(pady=10)
        ctk.CTkButton(self.control_panel, text="Aumentar tamaño", command=self.increase_obstacle_size).pack(pady=10)
        ctk.CTkButton(self.control_panel, text="Disminuir tamaño", command=self.decrease_obstacle_size).pack(pady=10)
        ctk.CTkButton(self.control_panel, text="Borrar Obstáculo", command=self.delete_obstacle).pack(
            pady=10)  # Nuevo botón

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

    def draw_map_mode(self):
        """Activa el modo de dibujo del mapa."""
        messagebox.showinfo("Modo de Dibujo", "Haz clic derecho en el mapa para crear los vértices del geo fence.")
        self.map_widget.bind("<Button-3>", self.add_marker_event)

    def add_marker_event(self, event):
        """Agrega un vértice al mapa en las coordenadas especificadas."""
        x = self.map_widget.canvasx(event.x)
        y = self.map_widget.canvasy(event.y)

        self.geofencePoints.append((x, y))

        if len(self.geofencePoints) > 1:
            last_two_points = [self.geofencePoints[-2], self.geofencePoints[-1]]
            self.map_widget.create_line(last_two_points[0], last_two_points[1], fill="black", tags="geofence_line")

    def select_obstacle(self):
        """Muestra una ventana para seleccionar el tipo de obstáculo."""
        self.obstacle_window = ctk.CTkToplevel()
        self.obstacle_window.title("Seleccionar Obstáculo")
        self.obstacle_window.geometry("300x200")

        for obstacle_name in self.obstacle_images.keys():
            button = ctk.CTkButton(self.obstacle_window, text=obstacle_name.capitalize(),
                                   command=lambda name=obstacle_name: self.add_obstacle(name))
            button.pack(pady=5)

    def add_obstacle(self, obstacle_name):
        """Añade un obstáculo al mapa."""
        if obstacle_name in self.obstacle_images:
            coords = (self.cell_size, self.cell_size)  # Coloca el obstáculo en la primera celda disponible
            resized_icon = self.resize_image(self.obstacle_images[obstacle_name], self.current_obstacle_size)
            obstacle = self.map_widget.create_image(coords[0], coords[1], image=resized_icon, anchor='nw',
                                                    tags="obstacle")
            self.obstacles.append((obstacle, resized_icon))  # Guardamos el obstáculo y su imagen

            self.resized_images[obstacle] = resized_icon  # Guardar referencia para evitar el recolector de basura

            self.map_widget.tag_bind(obstacle, "<B1-Motion>", lambda event, obs=obstacle: self.on_drag(event, obs))

    def resize_image(self, image, size):
        """Redimensiona la imagen al tamaño especificado."""
        resized_image = image.resize((size, size), Image.LANCZOS)
        return ImageTk.PhotoImage(resized_image)

    def on_drag(self, event, obstacle):
        """Permite arrastrar el marcador en el mapa."""
        x = self.map_widget.canvasx(event.x)
        y = self.map_widget.canvasy(event.y)

        # Encuentra la celda más cercana para alinear el obstáculo con la cuadrícula
        x = (x // self.cell_size) * self.cell_size
        y = (y // self.cell_size) * self.cell_size

        self.map_widget.coords(obstacle, x, y)

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
        """Redimensiona todos los obstáculos según el tamaño actual."""
        for obstacle, resized_icon in self.obstacles:
            # Obtener las coordenadas actuales del obstáculo
            coords = self.map_widget.coords(obstacle)

            if coords:  # Asegurarse de que existan coordenadas
                # Redimensionar la imagen y actualizar
                resized_icon = self.resize_image(self.obstacle_images["cuadrado"], self.current_obstacle_size)
                self.map_widget.itemconfig(obstacle, image=resized_icon)  # Actualizar la imagen del obstáculo

                # Mantener la referencia de la imagen redimensionada
                self.resized_images[obstacle] = resized_icon

    def delete_obstacle(self):
        """Elimina el obstáculo seleccionado."""
        if self.obstacles:  # Si hay obstáculos
            obstacle_to_remove = self.obstacles.pop()  # Eliminar el último obstáculo de la lista
            self.map_widget.delete(obstacle_to_remove[0])  # Eliminar el obstáculo del canvas
            self.resized_images.pop(obstacle_to_remove[0], None)  # Eliminar la referencia de la imagen

    def add_background(self):
        """Método para añadir un fondo personalizado al mapa."""
        image_path = filedialog.askopenfilename(title="Seleccionar Imagen de Fondo",
                                                filetypes=[("Image Files", ".png;.jpg;*.jpeg")])
        if image_path:
            self.set_background_image(image_path)

    def set_background_image(self, image_path):
        """Establece la imagen de fondo del mapa."""
        if self.background_label:
            self.background_label.destroy()  # Destruir la etiqueta anterior si existe

        self.background_image = Image.open(image_path)

        # Ajusta el tamaño de la imagen de fondo al tamaño del canvas
        self.background_image = self.background_image.resize((self.ancho_terreno_pixels, self.largo_terreno_pixels),
                                                             Image.LANCZOS)
        self.background_image_tk = ImageTk.PhotoImage(self.background_image)

        # Crear un label para mostrar la imagen de fondo
        self.background_label = ctk.CTkLabel(self.MapFrame, image=self.background_image_tk)
        self.background_label.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        self.background_label.lower()


# Aquí puedes crear la instancia de tu aplicación y ejecutar el bucle principal
if __name__ == "_main_":
    root = ctk.CTk()
    editor = MapFrameClass(None, root)
    editor.buildFrame()
    root.mainloop()