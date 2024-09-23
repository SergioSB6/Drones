import customtkinter as ctk


# ================= DASHBOARD INICIAL =================

ctk.set_appearance_mode("dark")  # Modo oscuro
ctk.set_default_color_theme("blue")  # Tema por defecto

# Función para cambiar de marco
def mostrar_frame(frame):
    frame.tkraise()  # Mueve el marco especificado al frente, ocultando los otros

# Crear la ventana principal
ventana = ctk.CTk()  # Crear la ventana
ventana.geometry("1280x720")  # Tamaño de la ventana
ventana.title("Ventana principal")

# =================== MARCOS (PANTALLAS) ===================

# Crear dos marcos (pantallas) que se alternarán
frame_titulo = ctk.CTkFrame(master=ventana)  # Primer marco (titulo)
frame_titulo.place(relx=0, rely=0, relwidth=1, relheight=1)  # Ocupa toda la ventana

frame_menu = ctk.CTkFrame(master=ventana)  # Segundo marco (Juego)
frame_menu.place(relx=0, rely=0, relwidth=1, relheight=1)  # Ocupa toda la ventana

frame_tag= ctk.CTkFrame(master=ventana)  # Segundo marco (Juego)
frame_tag.place(relx=0, rely=0, relwidth=1, relheight=1)  # Ocupa toda la ventana

frame_CheckPoint= ctk.CTkFrame(master=ventana)  # Segundo marco (Juego)
frame_CheckPoint.place(relx=0, rely=0, relwidth=1, relheight=1)  # Ocupa toda la ventana

frame_Editor_mapas= ctk.CTkFrame(master=ventana)  # Segundo marco (Juego)
frame_Editor_mapas.place(relx=0, rely=0, relwidth=1, relheight=1)  # Ocupa toda la ventana
# ================== CONTENIDO DEL TITULO ==================
mostrar_frame(frame_titulo)
# Agregar una etiqueta de texto
label = ctk.CTkLabel(master=frame_titulo, text="DroneLab",  font=("M04_FATAL FURY", 80))
label.pack(pady=20)
# Agregar un botón a la ventana
def boton_click():
    mostrar_frame(frame_menu)

boton_play = ctk.CTkButton(master=frame_titulo, text="Play!", font=("M04_FATAL FURY", 50), fg_color="transparent", hover=False, command=boton_click, width=300, height=50)
boton_play.pack(pady=100, padx=0, side="bottom")

# ================== EFECTO DE REBOTE (AMPLIAR Y DESAMPLIAR) ==================
# Variables de control para el tamaño del botón
increase = True  # Indica si estamos ampliando o reduciendo el botón
current_size = 50  # Tamaño inicial del texto

# Función para hacer el efecto de rebote
def bounce_button():
    global increase, current_size

    # Incrementa o reduce el tamaño
    if increase:
        current_size += 1  # Aumenta el tamaño del texto
        if current_size >= 60:  # Tamaño máximo
            increase = False  # Cambia la dirección para reducir
    else:
        current_size -= 1  # Reduce el tamaño del texto
        if current_size <= 50:  # Tamaño mínimo
            increase = True  # Cambia la dirección para aumentar

    # Aplica el nuevo tamaño al botón
    boton_play.configure(font=("M04_FATAL FURY", current_size))

    # Llama a la función de nuevo después de 50 milisegundos
    ventana.after(50, bounce_button)

# Inicia el efecto de rebote en el botón de Play
bounce_button()

# ================== CONTENIDO DEL MENÚ PRINCIPAL ==================

# Agregar una etiqueta y botón en el marco del juego
label_select = ctk.CTkLabel(master=frame_menu, text="Select game", font=("M04_FATAL FURY", 70))
label_select.pack(pady=20, side="top")

#Seleccionar juegos
def tag():
    mostrar_frame(frame_tag)

boton_tag = ctk.CTkButton(master=frame_menu, text="Tag", font=("M04_FATAL FURY", 35), fg_color="transparent",hover=False, command=tag)
boton_tag.place(relx=0.3, rely=0.4, anchor="center")

def CheckPoint():
    mostrar_frame(frame_CheckPoint)

boton_tag = ctk.CTkButton(master=frame_menu, text="CheckPoints race", font=("M04_FATAL FURY", 35), fg_color="transparent",hover=False, command=CheckPoint)
boton_tag.place(relx=0.7, rely=0.4, anchor="center")
boton_tag._text_label.configure(wraplength=400)

#Editor de mapas
def Editor_mapas():
    mostrar_frame(frame_Editor_mapas)

boton_editorMap = ctk.CTkButton(master=frame_menu, text="Map Editor", font=("M04_FATAL FURY", 35), fg_color="transparent",hover=False, command=Editor_mapas)
boton_editorMap.place(relx=0.85, rely=0.95, anchor="s")
boton_editorMap._text_label.configure(wraplength=400)

# volver al titulo
def volver_titulo():
    mostrar_frame(frame_titulo)

boton_volver = ctk.CTkButton(master=frame_menu, text="Return", font=("M04_FATAL FURY", 30), fg_color="transparent", hover=False, command=volver_titulo)
boton_volver.place(relx=0.01, rely=0.95, anchor="sw")

# ================== CONTENIDO DEL TAG ==================
label_tag = ctk.CTkLabel(master=frame_tag, text="Welcome to Tag mode!", font=("M04_FATAL FURY", 35))
label_tag.pack(pady=20)

# volver al titulo
def volver_menu():
    mostrar_frame(frame_menu)

boton_volver1 = ctk.CTkButton(master=frame_tag, text="Return", font=("M04_FATAL FURY", 30), fg_color="transparent", hover=False, command=volver_menu)
boton_volver1.place(relx=0.01, rely=0.95, anchor="sw")

# ================== CONTENIDO DEL CHECKPOINT==================
label_tag = ctk.CTkLabel(master=frame_CheckPoint, text="Welcome to CheckPoint Race mode!", font=("M04_FATAL FURY", 35))
label_tag.pack(pady=20)

boton_volver2 = ctk.CTkButton(master=frame_CheckPoint, text="Return", font=("M04_FATAL FURY", 30), fg_color="transparent", hover=False, command=volver_menu)
boton_volver2.place(relx=0.01, rely=0.95, anchor="sw")

# ================== CONTENIDO DEL EDITOR DE MAPAS==================
label_tag = ctk.CTkLabel(master=frame_Editor_mapas, text="Welcome to Map Editor!", font=("M04_FATAL FURY", 35))
label_tag.pack(pady=20)

boton_volver3 = ctk.CTkButton(master=frame_Editor_mapas, text="Return", font=("M04_FATAL FURY", 30), fg_color="transparent", hover=False, command=volver_menu)
boton_volver3.place(relx=0.01, rely=0.95, anchor="sw")
# Ejecutar la ventana principal
ventana.mainloop()
