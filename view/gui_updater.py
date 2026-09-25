import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import threading
from modules.updater import main


class GUIUpdater:

    def __init__(self):
        self.ventana = ttk.Window(
            title="TerPENEitor",
            themename="vapor"
        )
        self.ventana.iconbitmap("smile.ico")

        self.ventana.resizable(False, False)

        ancho = 400
        alto = 180
        pantalla_ancho = self.ventana.winfo_screenwidth()
        pantalla_alto = self.ventana.winfo_screenheight()
        x = int((pantalla_ancho / 2) - (ancho / 2))
        y = int((pantalla_alto / 2) - (alto / 2))
        self.ventana.geometry(f"{ancho}x{alto}+{x}+{y}")

        self.titulo = ttk.Label(
            self.ventana,
            text="TerPENEitor",
            font=("Segoe UI", 18, "bold")
        )
        self.titulo.pack(pady=(20, 5))

        self.estado = ttk.Label(
            self.ventana,
            text="Comprobando actualizaciones..."
        )
        self.estado.pack(pady=5)

        self.progreso = ttk.Progressbar(
            self.ventana,
            length=320,
            mode="indeterminate"
        )
        self.progreso.pack(pady=10)

        self.progreso.start(10)

        self.respuesta_usuario = None
        self.evento_respuesta = threading.Event()

    def cambiar_estado(self, texto):
        self.ventana.after(
            0,
            lambda: self._aplicar_estado(texto)
        )

    def _aplicar_estado(self, texto):
        self.estado.config(text=texto)

    def mostrar_progreso(self, porcentaje):
        self.ventana.after(
            0,
            lambda: self._aplicar_progreso(porcentaje)
        )

    def _aplicar_progreso(self, porcentaje):
        self.progreso.stop()
        self.progreso.config(
            mode="determinate",
            value=porcentaje
        )

    def mostrar_progreso_indeterminado(self):
        self.ventana.after(
            0,
            self._aplicar_progreso_indeterminado
        )

    def _aplicar_progreso_indeterminado(self):
        self.progreso.stop()
        self.progreso.config(mode="indeterminate")
        self.progreso.start(10)

    def actualizar_progreso(self, porcentaje):
        self.mostrar_progreso(porcentaje)

    def mostrar_confirmacion(self, version):
        self.ventana.after(
            0,
            lambda: self._crear_confirmacion(version)
        )

    def _crear_confirmacion(self, version):
        self.progreso.stop()
        self.progreso.config(value=0)

        self.estado.config(
            text=f"Nueva versión disponible: {version}"
        )

        ventana = ttk.Toplevel(self.ventana)
        ventana.title("Actualización")
        ventana.iconbitmap("smile.ico")
        ventana.resizable(False, False)

        ancho = 360
        alto = 160
        pantalla_ancho = self.ventana.winfo_screenwidth()
        pantalla_alto = self.ventana.winfo_screenheight()
        x = int((pantalla_ancho / 2) - (ancho / 2))
        y = int((pantalla_alto / 2) - (alto / 2))
        ventana.geometry(f"{ancho}x{alto}+{x}+{y}")

        ventana.grab_set()

        mensaje = ttk.Label(
            ventana,
            text="¿Deseas actualizar el pene de TerPENEitor?",
            font=("Segoe UI", 11),
            wraplength=320,
            justify="center"
        )
        mensaje.pack(pady=(25, 15))

        botones = ttk.Frame(ventana)
        botones.pack()

        ttk.Button(
            botones,
            text="Sí",
            bootstyle="success",
            command=lambda: self.responder(
                ventana,
                True
            )
        ).pack(side=LEFT, padx=5)

        ttk.Button(
            botones,
            text="No",
            bootstyle="danger",
            command=lambda: self.responder(
                ventana,
                False
            )
        ).pack(side=LEFT, padx=5)

    def responder(self, ventana, respuesta):
        self.respuesta_usuario = respuesta
        ventana.destroy()
        self.evento_respuesta.set()

    def _ejecutar_flujo(self):
        main(gui=self)
        self.ventana.after(0, self.ventana.destroy)

    def iniciar(self):
        hilo = threading.Thread(
            target=self._ejecutar_flujo,
            daemon=True
        )
        hilo.start()
        self.ventana.mainloop()