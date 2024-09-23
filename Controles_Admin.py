import customtkinter as ctk
from Dron import Dron
from tkinter import messagebox

ctk.set_appearance_mode("System")  # Opciones: "System", "Light", "Dark"
ctk.set_default_color_theme("blue")  # Opciones de color


def connect():
    global dron, connectBtn
    connection_string = 'tcp:127.0.0.1:5763'
    baud = 115200
    dron.connect(connection_string, baud)

    connectBtn.configure(text='Conectado', fg_color="green", text_color="white")


def arm(button):
    global dron, armBtn
    dron.arm()
    armBtn.configure(text="Armado", fg_color="green", text_color="white")


def takeoff():
    global dron, takeOffBtn, alt_entry
    try:
        alt = float(alt_entry.get())
        dron.takeOff(alt, blocking=False, callback=informar, params='VOLANDO')
        takeOffBtn.configure(text="Despegando....", fg_color="yellow")
    except:
        messagebox.showerror("error", "Introduce la altura para el despegue")


def informar(mensaje):
    global takeOffBtn, RTLBtn, connectBtn, armBtn, landBtn, dron
    messagebox.showinfo("showinfo", "Mensaje del dron:--->  " + mensaje)

    if mensaje == 'VOLANDO':
        takeOffBtn.configure(text="En el aire", fg_color="green", text_color="white")

    if mensaje == "EN CASA":
        RTLBtn.configure(text="En casa", fg_color="green", text_color="white")
        dron.disconnect()
        reset_buttons()

    if mensaje == "EN TIERRA":
        landBtn.configure(text="En tierra", fg_color="green", text_color="white")
        dron.disconnect()
        reset_buttons()


def reset_buttons():
    connectBtn.configure(text="Conectar", fg_color="dark orange", text_color="black")
    armBtn.configure(text="Armar", fg_color="dark orange", text_color="black")
    takeOffBtn.configure(text="Despegar", fg_color="dark orange", text_color="black")
    RTLBtn.configure(text="RTL", fg_color="dark orange", text_color="black")
    landBtn.configure(text="Aterrizar", fg_color="dark orange", text_color="black")


def RTL():
    global dron, RTLBtn
    if dron.going:
        dron.stopGo()
    dron.RTL(blocking=False, callback=informar, params='EN CASA')
    RTLBtn.configure(text="Retornando....", fg_color="yellow")


def aterrizar():
    global dron, landBtn
    if dron.going:
        dron.stopGo()
    dron.Land(blocking=False, callback=informar, params='EN TIERRA')
    landBtn.configure(text="Aterrizando....", fg_color="yellow")


def change_speed(speed):
    global dron
    dron.changeNavSpeed(float(speed))


def go(direction):
    global dron
    if not dron.going:
        dron.startGo()
    dron.go(direction)




def crear_ventana():
    global dron, alt_entry, connectBtn, armBtn, takeOffBtn, RTLBtn, landBtn, speedSldr

    dron = Dron()
    ventana = ctk.CTk()
    ventana.title("Ventana con botones y entradas")
    ventana.geometry("800x600")

    # Control Frame
    controlFrame = ctk.CTkFrame(ventana)
    controlFrame.pack(side="left", fill="y", padx=10, pady=10)

    connectBtn = ctk.CTkButton(controlFrame, text="Conectar", fg_color="dark orange", command=connect)
    connectBtn.pack(padx=5, pady=5)

    armBtn = ctk.CTkButton(controlFrame, text="Armar", fg_color="dark orange", command=lambda: arm(armBtn))
    armBtn.pack(padx=5, pady=5)

    # Takeoff Frame
    takeOffFrame = ctk.CTkFrame(controlFrame)
    takeOffFrame.pack(padx=5, pady=5)

    alt_entry = ctk.CTkEntry(takeOffFrame, placeholder_text="Altura de despegue")
    alt_entry.pack(side="left", padx=5, pady=5)

    takeOffBtn = ctk.CTkButton(takeOffFrame, text="Despegar", fg_color="dark orange", command=takeoff)
    takeOffBtn.pack(side="right", padx=5, pady=5)

    RTLBtn = ctk.CTkButton(controlFrame, text="RTL", fg_color="dark orange", command=RTL)
    RTLBtn.pack(padx=5, pady=5)

    # Speed Slider
    speedSldr = ctk.CTkSlider(controlFrame, from_=0, to=20, number_of_steps=20, command=change_speed)
    speedSldr.set(1)
    speedSldr.pack(padx=5, pady=5)

    navFrame = ctk.CTkFrame(controlFrame)
    navFrame.pack(padx=5, pady=5)

    NWBtn = ctk.CTkButton(navFrame, text="NW", fg_color="dark orange", command=lambda: go("NorthWest"))
    NWBtn.grid(row=0, column=0, padx=5, pady=5)

    NoBtn = ctk.CTkButton(navFrame, text="No", fg_color="dark orange", command=lambda: go("North"))
    NoBtn.grid(row=0, column=1, padx=5, pady=5)

    NEBtn = ctk.CTkButton(navFrame, text="NE", fg_color="dark orange", command=lambda: go("NorthEast"))
    NEBtn.grid(row=0, column=2, padx=5, pady=5)

    WeBtn = ctk.CTkButton(navFrame, text="We", fg_color="dark orange", command=lambda: go("West"))
    WeBtn.grid(row=1, column=0, padx=5, pady=5)

    StopBtn = ctk.CTkButton(navFrame, text="St", fg_color="dark orange", command=lambda: go("Stop"))
    StopBtn.grid(row=1, column=1, padx=5, pady=5)

    EaBtn = ctk.CTkButton(navFrame, text="Ea", fg_color="dark orange", command=lambda: go("East"))
    EaBtn.grid(row=1, column=2, padx=5, pady=5)


    userFrame = ctk.CTkFrame(ventana)
    userFrame.pack(side="right", fill="y", padx=10, pady=10)

    landBtn = ctk.CTkButton(userFrame, text="Aterrizar", fg_color="dark orange", command=aterrizar)
    landBtn.pack(padx=5, pady=5)

    return ventana

    if __name__ == "__main__":
    ventana = crear_ventana()
    ventana.mainloop()
