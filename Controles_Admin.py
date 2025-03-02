import time
import customtkinter as ctk
from Dron import Dron
from tkinter import messagebox
from modules import dron_nav

class ControlesAdmin:
    def __init__(self, dron):
        self.dron = dron

    def arm(self, button):
        """
        Arma el dron en modo no bloqueante.
        """
        global dron, armBtn
        # Llamada no bloqueante, con callback e identificador de mensaje 'ARMED'
        self.dron.arm(blocking=False, callback=self.informar, params='ARMED')
        # Mientras se arma, ponemos el botón en amarillo
        armBtn.configure(fg_color='yellow', text='Armando...')

    def takeoff(self):
        """
        Despega el dron en modo no bloqueante.
        """
        global dron, takeOffBtn
        try:
            alt = 8
            # Llamada no bloqueante, con callback e identificador 'VOLANDO'
            self.dron.takeOff(alt, blocking=False, callback=self.informar, params='VOLANDO')
            # Mientras despega, el botón en amarillo
            takeOffBtn.configure(fg_color='yellow', text='Despegando...')
        except:
            messagebox.showerror("error", "Introduce la altura para el despegue")

    def informar(self, mensaje):
        """
        Función de callback que se activa cuando acaban las funciones no bloqueantes
        (arm, takeOff, RTL). Actualiza los botones según el mensaje recibido.
        """
        global takeOffBtn, RTLBtn, armBtn, landBtn
        global dron

        messagebox.showinfo("showinfo", "Mensaje del dron:--->  " + mensaje)

        if mensaje == 'ARMED':
            # El dron ha terminado de armar
            armBtn.configure(fg_color='green', text='Armado')

        if mensaje == 'VOLANDO':
            # El dron ha terminado de despegar
            takeOffBtn.configure(fg_color='green', text='En el aire')

        if mensaje == "EN CASA":
            # El dron ha terminado de hacer RTL
            RTLBtn.configure(fg_color='green', text='En casa')
            dron.disconnect()
            # Devolver botones a la situación inicial
            armBtn.configure(fg_color='dark orange', text='Armar')
            takeOffBtn.configure(fg_color='dark orange', text='Despegar')
            RTLBtn.configure(fg_color='dark orange', text='RTL')

    def RTL(self):
        """
        Retorno a casa en modo no bloqueante.
        """
        global dron, RTLBtn
        if self.dron.going:
            self.dron.stopGo()
        self.dron.RTL(blocking=False, callback=self.informar, params='EN CASA')
        RTLBtn.configure(fg_color='yellow', text='Retornando...')

    # ====== NAVIGATION FUNCTIONS ======
    def change_speed(speed):
        global dron
        dron.changeNavSpeed(float(speed))

    def go(self, direction):
        global dron
        if not self.dron.going:
            self.dron.startGo()
        self.dron.go(direction)

    # ================= DASHBOARD INICIAL =================
    def crear_ventana(self):
        global dron
        global altShowLbl, headingShowLbl, speedSldr, gradesSldr, speedShowLbl
        global takeOffBtn, armBtn, RTLBtn
        global alt_entry

        ventana = ctk.CTkToplevel()
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

        # Botón Armar (modo no bloqueante)
        armBtn = ctk.CTkButton(controlFrame, text="Armar", fg_color="dark orange",
                               command=lambda: self.arm(armBtn))
        armBtn.grid(row=1, column=0, padx=5, pady=5, sticky="nsew")

        # Botón Despegar (modo no bloqueante)
        takeOffBtn = ctk.CTkButton(controlFrame, text="Despegar", fg_color="dark orange", command=self.takeoff)
        takeOffBtn.grid(row=2, column=0, padx=5, pady=5, sticky="nsew")

        # Botón RTL (modo no bloqueante)
        RTLBtn = ctk.CTkButton(controlFrame, text="RTL", fg_color="dark orange", command=self.RTL)
        RTLBtn.grid(row=3, column=0, padx=5, pady=5, sticky="nsew")

        # ================= FRAME/BOTONES NAVEGACIÓN =================
        speedSldr = ctk.CTkSlider(controlFrame, from_=0, to=20, number_of_steps=20, command=self.change_speed)
        speedSldr.set(1)  # velocidad por defecto de 1 m/s
        speedSldr.grid(row=4, column=0, padx=5, pady=5, sticky="nsew")

        navFrame = ctk.CTkFrame(controlFrame)
        navFrame.grid(row=5, column=0, padx=50, pady=5, sticky="nsew")

        navFrame.rowconfigure(0, weight=1)
        navFrame.rowconfigure(1, weight=1)
        navFrame.rowconfigure(2, weight=1)

        navFrame.columnconfigure(0, weight=1)
        navFrame.columnconfigure(1, weight=1)
        navFrame.columnconfigure(2, weight=1)

        NWBtn = ctk.CTkButton(navFrame, text="NW", fg_color="dark orange", command=lambda: self.go("NorthWest"))
        NWBtn.grid(row=0, column=0, padx=2, pady=2, sticky="nsew")

        NoBtn = ctk.CTkButton(navFrame, text="No", fg_color="dark orange", command=lambda: self.dron.go("North"))
        NoBtn.grid(row=0, column=1, padx=2, pady=2, sticky="nsew")

        NEBtn = ctk.CTkButton(navFrame, text="NE", fg_color="dark orange", command=lambda: self.go("NorthEast"))
        NEBtn.grid(row=0, column=2, padx=2, pady=2, sticky="nsew")

        WeBtn = ctk.CTkButton(navFrame, text="We", fg_color="dark orange", command=lambda: self.go("West"))
        WeBtn.grid(row=1, column=0, padx=2, pady=2, sticky="nsew")

        StopBtn = ctk.CTkButton(navFrame, text="St", fg_color="dark orange", command=lambda: self.go("Stop"))
        StopBtn.grid(row=1, column=1, padx=2, pady=2, sticky="nsew")

        EaBtn = ctk.CTkButton(navFrame, text="Ea", fg_color="dark orange", command=lambda: self.go("East"))
        EaBtn.grid(row=1, column=2, padx=2, pady=2, sticky="nsew")

        SWBtn = ctk.CTkButton(navFrame, text="SW", fg_color="dark orange", command=lambda: self.go("SouthWest"))
        SWBtn.grid(row=2, column=0, padx=2, pady=2, sticky="nsew")

        SoBtn = ctk.CTkButton(navFrame, text="So", fg_color="dark orange", command=lambda: self.go("South"))
        SoBtn.grid(row=2, column=1, padx=2, pady=2, sticky="nsew")

        SEBtn = ctk.CTkButton(navFrame, text="SE", fg_color="dark orange", command=lambda: self.go("SouthEast"))
        SEBtn.grid(row=2, column=2, padx=2, pady=2, sticky="nsew")

        return ventana

    def abrir_ventana(self):
        ventana = self.crear_ventana()
