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
            "cuadrado": Image.open("assets/square.png").resize((50, 50), Image.LANCZOS)
        }
        self.grid_paths = []
        self.fatherFrame = fatherFrame  # Guarda fatherFrame como atributo
        self.MapFrame = ctk.CTkFrame(self.fatherFrame)  # Aquí se pasa el fatherFrame
        self.background_label = None  # Para almacenar la etiqueta de fondo
        self.setup_ui()

    def setup_ui(self):
        """Configura el marco y la interfaz de usuario."""
        self.MapFrame.grid_rowconfigure(0, weight=1)
        self.MapFrame.grid_columnconfigure(0, weight=1)
        self.MapFrame.grid_columnconfigure(1, weight=3)

        self.control_panel = ctk.CTkFrame(self.MapFrame, width=200)
        self.control_panel.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        self.add_buttons()

        self.map_widget = TkinterMapView(self.MapFrame, width=900, height=600, corner_radius=0)
        self.map_widget.grid(row=0, column=1, padx=10, pady=10)

        self.map_widget.set_tile_server(None)
        self.map_widget.set_position(41.276430, 1.988686)  # Ajustar a tu ubicación inicial
        self.map_widget.set_zoom(20)

        self.draw_grid()
        self.map_widget.bind("<Configure>", self.on_resize)

    def buildFrame(self):
        """Construye y devuelve el marco del mapa."""
        self.MapFrame.pack(expand=True, fill='both')
        return self.MapFrame

    def add_buttons(self):
        """Añade los botones de la interfaz."""
        ctk.CTkButton(self.control_panel, text="Dibujar Mapa", command=self.draw_map_mode).pack(pady=10)
        ctk.CTkButton(self.control_panel, text="Obstáculos", command=self.select_obstacle).pack(pady=10)
        ctk.CTkButton(self.control_panel, text="Añadir Fondo", command=self.add_background).pack(pady=10)

    def draw_grid(self):
        """Dibuja la cuadrícula sobre el mapa."""
        # Limpiar las rutas de la cuadrícula anterior
        for path in self.grid_paths:
            self.map_widget.remove_path(path)
        self.grid_paths = []

        center_lat, center_lon = self.map_widget.get_position()
        grid_size = 20  # Número de líneas en la cuadrícula
        grid_step = 0.0001  # Espaciado entre líneas de la cuadrícula

        for i in range(grid_size + 1):
            # Dibujar líneas verticales
            lat1 = center_lat - (grid_size / 2) * grid_step
            lat2 = center_lat + (grid_size / 2) * grid_step
            lon = center_lon - (grid_size / 2) * grid_step + i * grid_step
            path = self.map_widget.set_path([(lat1, lon), (lat2, lon)])  # Solo coordenadas
            self.grid_paths.append(path)

        for j in range(grid_size + 1):
            # Dibujar líneas horizontales
            lon1 = center_lon - (grid_size / 2) * grid_step
            lon2 = center_lon + (grid_size / 2) * grid_step
            lat = center_lat - (grid_size / 2) * grid_step + j * grid_step
            path = self.map_widget.set_path([(lat, lon1), (lat, lon2)])  # Solo coordenadas
            self.grid_paths.append(path)

    def on_resize(self, event):
        """Redibuja la cuadrícula y ajusta el tamaño del mapa al cambiar el tamaño de la ventana."""
        self.map_widget.config(width=event.width - 220, height=event.height - 20)  # Ajustar ancho y alto
        self.draw_grid()  # Redibujar la cuadrícula al cambiar el tamaño

        # Redimensionar la etiqueta de fondo
        if self.background_label:
            self.background_label.config(width=event.width - 220, height=event.height)

    def draw_map_mode(self):
        """Activa el modo de dibujo del mapa."""
        messagebox.showinfo("Modo de Dibujo", "Haz clic derecho en el mapa para crear los vértices del geo fence.")
        self.map_widget.add_right_click_menu_command(label="Add Marker", command=self.add_marker_event, pass_coords=True)

    def add_marker_event(self, coords):
        """Agrega un marcador al mapa en las coordenadas especificadas."""
        marker_text = f"Vertex {len(self.geofencePoints) + 1}"
        marker = self.map_widget.set_marker(coords[0], coords[1], text=marker_text)
        self.geofenceElements.append(marker)
        self.geofencePoints.append({'lat': coords[0], 'lon': coords[1]})

        if len(self.geofencePoints) > 1:
            last_two_points = [self.geofencePoints[-2], self.geofencePoints[-1]]
            path = self.map_widget.set_path([(point['lat'], point['lon']) for point in last_two_points])
            self.geofenceElements.append(path)

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
            coords = self.map_widget.get_position()  # Obtener posición actual del dron
            icon = ImageTk.PhotoImage(self.obstacle_images[obstacle_name])
            self.map_widget.set_marker(coords[0], coords[1], icon=icon)
            self.geofenceElements.append({'type': obstacle_name, 'lat': coords[0], 'lon': coords[1]})

    def add_background(self):
        """Método para añadir un fondo personalizado al mapa."""
        image_path = filedialog.askopenfilename(title="Seleccionar Imagen de Fondo",
                                                filetypes=[("Image Files", "*.png;*.jpg;*.jpeg")])
        if image_path:
            self.set_background_image(image_path)

    def set_background_image(self, image_path):
        """Establece la imagen de fondo del mapa."""
        if self.background_label:
            self.background_label.destroy()  # Destruir la etiqueta anterior si existe

        self.background_image = Image.open(image_path)
        self.background_image = self.background_image.resize((900, 600), Image.LANCZOS)  # Ajustar al tamaño del mapa
        self.background_image_tk = ImageTk.PhotoImage(self.background_image)

        # Crear un label para mostrar la imagen de fondo
        self.background_label = ctk.CTkLabel(self.MapFrame, image=self.background_image_tk)
        self.background_label.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")  # Asegurarse de que se ajuste al mapa

        # Colocar la etiqueta de fondo detrás del widget del mapa
        self.background_label.lower()

# Aquí puedes crear la instancia de tu aplicación y ejecutar el bucle principal
if __name__ == "__main__":
    root = ctk.CTk()  # Cambiar a CTk para usar el tema personalizado
    editor = MapFrameClass(None, root)  # Pasar 'root' como el marco padre
    editor.buildFrame()  # Llama al método buildFrame para empaquetar el marco
    root.mainloop()
