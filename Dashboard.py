import customtkinter as ctk

# ================= DASHBOARD INICIAL =================

ctk.set_appearance_mode("dark")  # Modo oscuro
ctk.set_default_color_theme("blue")  # Tema por defecto (colores)

# Función para cambiar de marco
def mostrar_frame(frame):
    frame.tkraise()  # Mueve el marco especificado al frente, ocultando los otros

# Crear la ventana principal
ventana = ctk.CTk()  # Crear la ventana usando customtkinter
ventana.geometry("1280x720")  # Tamaño de la ventana
ventana.title("Ventana principal")

# =================== MARCOS (PANTALLAS) ===================

# Crear dos marcos (pantallas) que se alternarán
frame_titulo = ctk.CTkFrame(master=ventana)  # Primer marco (titulo)
frame_titulo.place(relx=0, rely=0, relwidth=1, relheight=1)  # Ocupa toda la ventana

frame_juego = ctk.CTkFrame(master=ventana)  # Segundo marco (Juego)
frame_juego.place(relx=0, rely=0, relwidth=1, relheight=1)  # Ocupa toda la ventana

# ================== CONTENIDO DEL TITULO ==================

# Agregar una etiqueta de texto
label = ctk.CTkLabel(master=ventana, text="DroneLab",  font=("M04_FATAL FURY", 80))
label.pack(pady=20)

# Función para aumentar el tamaño del botón al pasar el ratón
def on_enter(event):
    event.widget.configure(font=("M04_FATAL FURY", 60))  # Cambia el tamaño del texto o botón

# Función para restaurar el tamaño original al salir el ratón
def on_leave(event):
    event.widget.configure(font=("M04_FATAL FURY", 50))  # Vuelve al tamaño normal

# Agregar un botón a la ventana
def boton_click():
    mostrar_frame(frame_juego)

boton = ctk.CTkButton(master=ventana, text="Play!",  font=("M04_FATAL FURY", 50), fg_color="transparent",hover_color="none", command=boton_click, width=300, height=50)
boton.pack(pady=100, padx=100, side="bottom")  # Agregar margen alrededor del botón

# Asignar eventos al botón
boton.bind("<Enter>", on_enter)  # Evento al pasar el ratón
boton.bind("<Leave>", on_leave)  # Evento al salir el ratón

# ================== CONTENIDO DEL MENÚ PRINCIPAL ==================

# Ejecutar la ventana principal
ventana.mainloop()
