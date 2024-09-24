import time
import customtkinter as ctk
from Dron import Dron
from tkinter import messagebox

def connect():
    global dron, connectBtn
    # conectamos con el simulador
    connection_string = 'tcp:127.0.0.1:5763'
    baud = 115200
    dron.connect(connection_string, baud)

    # una vez conectado cambio en color de boton
    connectBtn.configure(fg_color='green', text='Conectado')


def arm(button):
    global dron, armBtn
    dron.arm()
    # una vez armado cambio en color de boton
    armBtn.configure(fg_color='green', text='Armado')


def takeoff():
    global dron, takeOffBtn
    try:
        # altura de despegue prefijada
        alt = 8
        # llamo en modo no bloqueante y le indico qué función debe activar al acabar la operación, y qué parámetro debe usar
        dron.takeOff(alt, blocking=False, callback=informar, params='VOLANDO')
        # mientras despego pongo el boton en amarillo
        takeOffBtn.configure(fg_color='yellow', text='Despegando....')
    except:
        # en el cuadro de texto no hay ningún numero
        messagebox.showerror("error", "Introduce la altura para el despegue")


# esta es la función que se activará cuando acaben las funciones no bloqueantes (despegue y RTL)
def informar(mensaje):
    global takeOffBtn, RTLBtn, connectBtn, armBtn, landBtn
    global dron
    messagebox.showinfo("showinfo", "Mensaje del dron:--->  " + mensaje)
    if mensaje == 'VOLANDO':
        # pongo el boton de despegue en verde
        takeOffBtn.configure(fg_color='green', text='En el aire')
    if mensaje == "EN CASA":
        # pongo el boton RTL en verde
        RTLBtn.configure(fg_color='green', text='En casa')
        # me desconecto del dron (eso tardará 5 segundos)
        dron.disconnect()
        # devuelvo los botones a la situación inicial
        connectBtn.configure(fg_color='dark orange', text='Conectar')
        armBtn.configure(fg_color='dark orange', text='Armar')
        takeOffBtn.configure(fg_color='dark orange', text='Despegar')
        RTLBtn.configure(fg_color='dark orange', text='RTL')


def RTL():
    global dron, RTLBtn
    # si esta navegando detengo el modo de navegación
    if dron.going:
        dron.stopGo()
    # llamo en modo no bloqueante y le indico qué función debe activar al acabar la operación, y qué parámetro debe usar
    dron.RTL(blocking=False, callback=informar, params='EN CASA')
    # mientras retorno pongo el boton en amarillo
    RTLBtn.configure(fg_color='yellow', text='Retornando....')


# ====== NAVIGATION FUNCTIONS ======
# Esta función se activa cada vez que cambiamos la velocidad de navegación con el slider
def change_speed(speed):
    global dron
    dron.changeNavSpeed(float(speed))


# función para dirigir el dron en una dirección
def go(direction):
    global dron
    # si empezamos a navegar, le indico al dron
    if not dron.going:
        dron.startGo()
    dron.go(direction)


# ================= DASHBOARD INICIAL =================
def crear_ventana():
    global dron
    global altShowLbl, headingShowLbl, speedSldr, gradesSldr, speedShowLbl
    global takeOffBtn, connectBtn, armBtn, RTLBtn
    global alt_entry

    dron = Dron()

    ventana = ctk.CTk()
    ventana.title("Ventana con botones y entradas")
    ventana.rowconfigure(0, weight=1)
    ventana.columnconfigure(0, weight=1)
    ventana.columnconfigure(1, weight=1)

    # Configuración del Frame de Control
    controlFrame = ctk.CTkFrame(ventana)
    controlFrame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

    controlFrame.rowconfigure(0, weight=1)
    controlFrame.rowconfigure(1, weight=1)
    controlFrame.rowconfigure(2, weight=1)
    controlFrame.rowconfigure(3, weight=1)
    controlFrame.rowconfigure(4, weight=1)
    controlFrame.rowconfigure(5, weight=1)

    controlFrame.columnconfigure(0, weight=1)

    connectBtn = ctk.CTkButton(controlFrame, text="Conectar", fg_color="dark orange", command=connect)
    connectBtn.grid(row=0, column=0, padx=3, pady=5, sticky="nsew")

    # A la función que activamos al clicar en este boton le pasamos el propio boton para
    # que le cambie el color
    armBtn = ctk.CTkButton(controlFrame, text="Armar", fg_color="dark orange", command=lambda: arm(armBtn))
    armBtn.grid(row=1, column=0, padx=5, pady=5, sticky="nsew")

    takeOffBtn = ctk.CTkButton(controlFrame, text="Despegar", fg_color="dark orange", command=takeoff)
    takeOffBtn.grid(row=2, column=0, padx=5, pady=5, sticky="nsew")

    RTLBtn = ctk.CTkButton(controlFrame, text="RTL", fg_color="dark orange", command=RTL)
    RTLBtn.grid(row=3, column=0, padx=5, pady=5, sticky="nsew")

    # ================= FRAME/BOTONES NAVEGACIÓN =================

    speedSldr = ctk.CTkSlider(controlFrame, from_=0, to=20, number_of_steps=20, command=change_speed)
    speedSldr.set(1)  # velocidad por defecto de 1 m/s
    speedSldr.grid(row=4, column=0, padx=5, pady=5, sticky="nsew")

    navFrame = ctk.CTkFrame(controlFrame)
    navFrame.grid(row=5, column=0, padx=50, pady=5, sticky="nsew")

    # Configuración del Frame de Navegación
    navFrame.rowconfigure(0, weight=1)
    navFrame.rowconfigure(1, weight=1)
    navFrame.rowconfigure(2, weight=1)

    navFrame.columnconfigure(0, weight=1)
    navFrame.columnconfigure(1, weight=1)
    navFrame.columnconfigure(2, weight=1)

    # todos los botones activan la misma función, pero pasándole como parametro
    # la dirección de navegación
    NWBtn = ctk.CTkButton(navFrame, text="NW", fg_color="dark orange", command=lambda: go("NorthWest"))
    NWBtn.grid(row=0, column=0, padx=2, pady=2, sticky="nsew")

    NoBtn = ctk.CTkButton(navFrame, text="No", fg_color="dark orange", command=lambda: go("North"))
    NoBtn.grid(row=0, column=1, padx=2, pady=2, sticky="nsew")

    NEBtn = ctk.CTkButton(navFrame, text="NE", fg_color="dark orange", command=lambda: go("NorthEast"))
    NEBtn.grid(row=0, column=2, padx=2, pady=2, sticky="nsew")

    WeBtn = ctk.CTkButton(navFrame, text="We", fg_color="dark orange", command=lambda: go("West"))
    WeBtn.grid(row=1, column=0, padx=2, pady=2, sticky="nsew")

    StopBtn = ctk.CTkButton(navFrame, text="St", fg_color="dark orange", command=lambda: go("Stop"))
    StopBtn.grid(row=1, column=1, padx=2, pady=2, sticky="nsew")

    EaBtn = ctk.CTkButton(navFrame, text="Ea", fg_color="dark orange", command=lambda: go("East"))
    EaBtn.grid(row=1, column=2, padx=2, pady=2, sticky="nsew")

    SWBtn = ctk.CTkButton(navFrame, text="SW", fg_color="dark orange", command=lambda: go("SouthWest"))
    SWBtn.grid(row=2, column=0, padx=2, pady=2, sticky="nsew")

    SoBtn = ctk.CTkButton(navFrame, text="So", fg_color="dark orange", command=lambda: go("South"))
    SoBtn.grid(row=2, column=1, padx=2, pady=2, sticky="nsew")

    SEBtn = ctk.CTkButton(navFrame, text="SE", fg_color="dark orange", command=lambda: go("SouthEast"))
    SEBtn.grid(row=2, column=2, padx=2, pady=2, sticky="nsew")

    return ventana

if __name__ == "__main__":
    ventana = crear_ventana()
    ventana.mainloop()
