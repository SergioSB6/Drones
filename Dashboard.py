import os
from tkinter import Menubutton
import customtkinter as ctk
from Dron import Dron
from Editor_Mapa import MapFrameClass
from Checkpoint_screen import CheckpointScreen
import platform
import subprocess
import sys
import shutil
from Controles_Admin import ControlesAdmin


def install_dependencies():
    # Instala las bibliotecas necesarias si no están instaladas
    try:
        import customtkinter
        import numpy
        import PIL
    except ImportError:
        print("Instalando dependencias necesarias...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "customtkinter", "numpy", "pillow","  shapely"])

    # Instala la fuente personalizada
    install_custom_font()

def install_custom_font():
    # Ruta a la fuente en la carpeta assets
    font_path = os.path.join(os.getcwd(), 'assets', 'm04fatal_fury', 'm04.ttf')

    if platform.system() == 'Windows':
        # Copia la fuente a la carpeta de fuentes de Windows
        try:
            windows_fonts_dir = os.path.join(os.environ['WINDIR'], 'Fonts')
            font_dest_path = os.path.join(windows_fonts_dir, 'm04.ttf')
            if not os.path.isfile(font_dest_path):  # Evita copiar si ya está instalada
                shutil.copy(font_path, font_dest_path)
                print("Fuente instalada correctamente en Windows.")
            else:
                print("La fuente ya está instalada.")
        except Exception as e:
            print(f"No se pudo instalar la fuente: {e}")

    else:
        # Para sistemas operativos diferentes a Windows, muestra un mensaje informativo
        print("Para otros sistemas, instala la fuente manualmente desde la carpeta assets/fonts.")

install_dependencies()

# ================= DASHBOARD INICIAL =================
global dron
dron = Dron()
ctk.set_appearance_mode("dark")  # Modo oscuro
ctk.set_default_color_theme("blue")  # Tema por defecto

# Función para cambiar de marco
def mostrar_frame(frame):
    frame.tkraise()  # Mueve el marco especificado al frente, ocultando los otros

# Función para activar/desactivar pantalla completa
def toggle_fullscreen(event=None):
    is_fullscreen = ventana.attributes("-fullscreen")
    ventana.attributes("-fullscreen", not is_fullscreen)

# Función para salir de pantalla completa
def end_fullscreen(event=None):
    ventana.attributes("-fullscreen", False)

# Crear la ventana principal
ventana = ctk.CTk()  # Crear la ventana
ventana.geometry("1280x720")  # Tamaño de la ventana
ventana.title("Ventana principal")


# Configurar para que la ventana comience en pantalla completa
ventana.attributes("-fullscreen", True)

# Vincular la tecla ESC para salir de pantalla completa
ventana.bind("<Escape>", end_fullscreen)

# =================== MARCOS (PANTALLAS) ===================

# Crear dos marcos (pantallas) que se alternarán
frame_titulo = ctk.CTkFrame(master=ventana)  # Primer marco (titulo)
frame_titulo.place(relx=0, rely=0, relwidth=1, relheight=1)  # Ocupa toda la ventana



frame_menu = ctk.CTkFrame(master=ventana)  # Segundo marco (Juego)
frame_menu.place(relx=0, rely=0, relwidth=1, relheight=1)  # Ocupa toda la ventana

frame_tag = ctk.CTkFrame(master=ventana)  # Segundo marco (Tag)
frame_tag.place(relx=0, rely=0, relwidth=1, relheight=1)  # Ocupa toda la ventana

frame_CheckPoint = ctk.CTkFrame(master=ventana)  # Segundo marco (CheckPoint)
frame_CheckPoint.place(relx=0, rely=0, relwidth=1, relheight=1)  # Ocupa toda la ventana

frame_Editor_mapas = ctk.CTkFrame(master=ventana)  # Segundo marco (Editor de mapas)
frame_Editor_mapas.place(relx=0, rely=0, relwidth=1, relheight=1)  # Ocupa toda la ventana

# ================== FUNCIONES DE NAVEGACIÓN ==================

# Función para volver al menú principal
def volver_menu():
    mostrar_frame(frame_menu)

# Función para volver al título principal
def volver_titulo():
    mostrar_frame(frame_titulo)

# ================== CONTENIDO DEL TITULO ==================
mostrar_frame(frame_titulo)
# Agregar una etiqueta de texto
label = ctk.CTkLabel(master=frame_titulo, text="DroneLab", font=("M04_FATAL FURY", 80))
label.pack(pady=20)

# Botón con efecto de rebote
increase = True
current_size = 50

def bounce_button():
    global increase, current_size

    if increase:
        current_size += 1
        if current_size >= 60:
            increase = False
    else:
        current_size -= 1
        if current_size <= 50:
            increase = True

    boton_play.configure(font=("M04_FATAL FURY", current_size))
    ventana.after(50, bounce_button)


# Agregar un botón a la ventana
def boton_click():
    mostrar_frame(frame_menu)

boton_play = ctk.CTkButton(master=frame_titulo, text="Play!", font=("M04_FATAL FURY", 50), fg_color="transparent", hover=False, command=boton_click, width=300, height=50)
boton_play.pack(pady=100, padx=0, side="bottom")

# Iniciar rebote
bounce_button()

# ================== CONTENIDO DEL MENÚ PRINCIPAL ==================

# Agregar una etiqueta y botón en el marco del juego
label_select = ctk.CTkLabel(master=frame_menu, text="Select game", font=("M04_FATAL FURY", 70))
label_select.pack(pady=20, side="top")

# Crear una función para mostrar el menú desplegable
def mostrar_menu():
    # Crear un frame para que actúe como menú desplegable
    menu_frame = ctk.CTkFrame(frame_menu, width=150, height=100, corner_radius=10)
    menu_frame.place(x=10, y=50)  # Posicionar debajo del botón de engranaje

    # Crear botones dentro del menú desplegable
    boton_configuracion = ctk.CTkButton(menu_frame, text="Configuración avanzada", command=abrir_configuracion_avanzada, width=130, height=30)
    boton_configuracion.pack(pady=5)

    boton_sonido = ctk.CTkButton(menu_frame, text="Sonido", command=ajustar_sonido, width=130, height=30)
    boton_sonido.pack(pady=5)

    # Ocultar el menú al hacer clic en cualquier parte de la pantalla
    def ocultar_menu(event):
        menu_frame.place_forget()

    frame_menu.bind("<Button-1>", ocultar_menu)

# Funciones para cada opción del menú
def abrir_configuracion_avanzada():
    global dron
    print("Abrir configuración avanzada")
    ca=ControlesAdmin(dron)
    ca.abrir_ventana()



def ajustar_sonido():
    print("Ajustar sonido")

# Crear el botón con forma de engranaje
icono_engrane = ctk.CTkButton(frame_menu, text="⚙", width=30, height=30, command=mostrar_menu)
icono_engrane.place(x=10, y=10)  # Posicionar en la esquina superior izquierda

# Seleccionar juegos
def tag():
    mostrar_frame(frame_tag)

boton_tag = ctk.CTkButton(master=frame_menu, text="Tag", font=("M04_FATAL FURY", 35), fg_color="transparent", hover=False, command=tag)
boton_tag.place(relx=0.3, rely=0.4, anchor="center")
def showcheckpoint():
    global dron

    # Limpiar frame actual
    for widget in frame_CheckPoint.winfo_children():
        widget.destroy()

    # Crear CheckpointScreen en frame_CheckPoint
    checkpoint_screen = CheckpointScreen(dron, frame_CheckPoint)
    boton_volver4 = ctk.CTkButton(master=frame_CheckPoint, text="Return", font=("M04_FATAL FURY", 30),
                                  fg_color="transparent", hover=False, command=volver_menu)
    boton_volver4.place(relx=0.01, rely=0.95, anchor="sw")
    # Mostrar el frame del checkpoint
    mostrar_frame(frame_CheckPoint)


    mostrar_frame(frame_CheckPoint)
def CheckPoint():
    mostrar_frame(frame_CheckPoint)

boton_tag = ctk.CTkButton(master=frame_menu, text="CheckPoints race", font=("M04_FATAL FURY", 35), fg_color="transparent", hover=False, command=showcheckpoint)
boton_tag.place(relx=0.7, rely=0.4, anchor="center")
boton_tag._text_label.configure(wraplength=400)


# Editor de mapas
# Abrimos el mapa
def showmap():
    global dron

    # ================== CONTENIDO DEL EDITOR DE MAPAS ==================
    # Inicializamos la clase del mapa con el dron y el frame_Editor_mapas como fatherFrame
    map_frame_class = MapFrameClass(dron, frame_Editor_mapas)

    # Construimos el frame del mapa dentro del frame_Editor_mapas
    map_frame = map_frame_class.buildFrame()

    # Lo ajustamos para que ocupe todo el espacio
    map_frame.pack(fill="both", expand=True)

    boton_volver3 = ctk.CTkButton(master=frame_Editor_mapas, text="Return", font=("M04_FATAL FURY", 30),
                                  fg_color="transparent", hover=False, command=volver_menu)
    boton_volver3.place(relx=0.01, rely=0.95, anchor="sw")

    # Mostrar el frame del editor de mapas
    mostrar_frame(frame_Editor_mapas)

def Editor_mapas():
    mostrar_frame(frame_Editor_mapas)

boton_editorMap = ctk.CTkButton(master=frame_menu, text="Map Editor", font=("M04_FATAL FURY", 35), fg_color="transparent", hover=False, command=showmap)
boton_editorMap.place(relx=0.85, rely=0.95, anchor="s")
boton_editorMap._text_label.configure(wraplength=400)

# Botón para volver al título
boton_volver = ctk.CTkButton(master=frame_menu, text="Return", font=("M04_FATAL FURY", 30), fg_color="transparent", hover=False, command=volver_titulo)
boton_volver.place(relx=0.01, rely=0.95, anchor="sw")

# ================== CONTENIDO DEL TAG ==================
label_tag = ctk.CTkLabel(master=frame_tag, text="Welcome to Tag mode!", font=("M04_FATAL FURY", 35))
label_tag.pack(pady=20)

boton_volver1 = ctk.CTkButton(master=frame_tag, text="Return", font=("M04_FATAL FURY", 30), fg_color="transparent", hover=False, command=volver_menu)
boton_volver1.place(relx=0.01, rely=0.95, anchor="sw")

# ================== CONTENIDO DEL CHECKPOINT ==================
label_tag = ctk.CTkLabel(master=frame_CheckPoint, text="Welcome to CheckPoint Race mode!", font=("M04_FATAL FURY", 35))
label_tag.pack(pady=20)

# Ejecutar la ventana principal
ventana.mainloop()