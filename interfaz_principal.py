"""
Sistema de Cronometraje - Race Detector
Interfaz Principal Moderna y Responsiva
Autor: Sistema de Gestión de Carreras
Fecha: Octubre 2025
"""

import tkinter as tk
from tkinter import messagebox
import subprocess
import sys
import os

class InterfazPrincipal:
    def __init__(self, root):
        self.root = root
        self.root.title("🏁 Race Detector - Sistema de Cronometraje")
        self.root.geometry("1000x700")
        self.root.configure(bg="#2b2d30")
        self.root.resizable(True, True)
        self.root.minsize(900, 650)
        
        # Variables para animaciones y estados
        self.animacion_activa = False
        
        # Centrar ventana en la pantalla
        self.centrar_ventana()
        
        # Crear widgets
        self.crear_widgets()
    
    def centrar_ventana(self):
        """Centra la ventana en la pantalla"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
    
    def crear_widgets(self):
        """Crea todos los widgets de la interfaz moderna con colores sobrios"""
        
        # ===== HEADER: DISEÑO SOBRIO Y ELEGANTE =====
        frame_header = tk.Frame(self.root, bg="#1e1f22", height=90)
        frame_header.pack(fill=tk.X, padx=0, pady=0)
        frame_header.pack_propagate(False)
        
        # Contenedor del título con mejor espaciado
        header_content = tk.Frame(frame_header, bg="#1e1f22")
        header_content.pack(expand=True)
        
        # Título principal sobrio
        tk.Label(header_content, text="⏱️ Race Detector", 
                font=('Segoe UI', 36, 'bold'), 
                bg="#1e1f22", fg="#e8e8e8",
                pady=3).pack()
        
        tk.Label(header_content, text="Sistema de Cronometraje Profesional", 
                font=('Segoe UI', 10), 
                bg="#1e1f22", fg="#9ca3af").pack()
        
        # ===== SECCIÓN CENTRAL: BOTÓN PRINCIPAL SOBRIO =====
        frame_central = tk.Frame(self.root, bg="#2b2d30")
        frame_central.pack(fill=tk.BOTH, expand=True, padx=60, pady=25)
        
        # Tarjeta con diseño sobrio
        card_principal = tk.Frame(frame_central, bg="#3c3f41", relief=tk.FLAT, bd=0,
                                 highlightbackground="#4c5052", highlightthickness=1)
        card_principal.pack(expand=True)
        
        # Canvas para el botón de play
        canvas_size = 160
        self.canvas = tk.Canvas(card_principal, 
                               width=canvas_size, 
                               height=canvas_size,
                               bg="#3c3f41", 
                               highlightthickness=0)
        self.canvas.pack(padx=60, pady=(35, 18))
        
        # Círculo exterior con diseño minimalista
        self.circulo_exterior = self.canvas.create_oval(15, 15, 145, 145, 
                                                        fill="#5a9fd4", 
                                                        outline="#6ba8dc", 
                                                        width=3)
        
        # Círculo interior
        self.circulo_interior = self.canvas.create_oval(28, 28, 132, 132, 
                                                        fill="#3c3f41", 
                                                        outline="", 
                                                        width=0)
        
        # Triángulo de play
        self.triangulo = self.canvas.create_polygon(
            62, 50,   # Punto superior
            62, 110,  # Punto inferior
            110, 80,  # Punto derecho
            fill="#5a9fd4",
            outline="",
            width=0
        )
        
        # Textos con diseño sobrio
        tk.Label(card_principal, 
                text="INICIAR CRONOMETRAJE", 
                font=('Segoe UI', 15, 'bold'),
                bg="#3c3f41", 
                fg="#e8e8e8").pack(pady=(0, 4))
        
        tk.Label(card_principal, 
                text="Haz clic para comenzar", 
                font=('Segoe UI', 9),
                bg="#3c3f41", 
                fg="#9ca3af").pack(pady=(0, 25))
        
        # Eventos del botón principal
        self.canvas.bind("<Enter>", self.on_hover_principal)
        self.canvas.bind("<Leave>", self.on_leave_principal)
        self.canvas.bind("<Button-1>", self.iniciar_cronometraje)
        
        # ===== SECCIÓN INFERIOR: TARJETAS SOBRIAS =====
        frame_inferior = tk.Frame(self.root, bg="#2b2d30")
        frame_inferior.pack(fill=tk.X, padx=60, pady=(0, 25))
        
        # Título de la sección
        titulo_seccion = tk.Frame(frame_inferior, bg="#2b2d30")
        titulo_seccion.pack(pady=(0, 18))
        
        tk.Label(titulo_seccion, 
                text="Panel de Configuración", 
                font=('Segoe UI', 12, 'bold'),
                bg="#2b2d30", 
                fg="#9ca3af").pack()
        
        # Contenedor responsivo para las tarjetas
        frame_cards = tk.Frame(frame_inferior, bg="#2b2d30")
        frame_cards.pack(expand=True)
        
        # Grid configuration para responsividad mejorada
        frame_cards.grid_columnconfigure(0, weight=1, minsize=260)
        frame_cards.grid_columnconfigure(1, weight=0, minsize=25)
        frame_cards.grid_columnconfigure(2, weight=1, minsize=260)
        
        # ===== TARJETA 1: GESTIONAR PARTICIPANTES =====
        self.card_participantes = tk.Frame(frame_cards, bg="#3c3f41", 
                                          relief=tk.FLAT, bd=0, cursor="hand2",
                                          highlightbackground="#4c5052", 
                                          highlightthickness=1)
        self.card_participantes.grid(row=0, column=0, sticky="ew", padx=8)
        
        # Contenido de la tarjeta
        content_part = tk.Frame(self.card_participantes, bg="#3c3f41")
        content_part.pack(fill=tk.BOTH, expand=True, padx=22, pady=22)
        
        # Icono
        tk.Label(content_part, text="👥", 
                font=('Segoe UI', 36), bg="#3c3f41", fg="#6ba8dc").pack(pady=(0, 8))
        
        # Título
        tk.Label(content_part, text="Gestionar Participantes", 
                font=('Segoe UI', 13, 'bold'), bg="#3c3f41", fg="#e8e8e8").pack(pady=(0, 6))
        
        # Descripción
        tk.Label(content_part, text="Administra la base de datos\nde corredores y dorsales", 
                font=('Segoe UI', 9), bg="#3c3f41", fg="#9ca3af",
                justify=tk.CENTER).pack()
        
        # Eventos de la tarjeta de participantes
        self.card_participantes.bind("<Enter>", lambda e: self.on_hover_card(self.card_participantes, "#484b4d"))
        self.card_participantes.bind("<Leave>", lambda e: self.on_leave_card(self.card_participantes, "#3c3f41"))
        self.card_participantes.bind("<Button-1>", lambda e: self.abrir_gestion_participantes())
        
        # Hacer que todos los widgets internos también respondan al click
        for widget in content_part.winfo_children():
            widget.bind("<Button-1>", lambda e: self.abrir_gestion_participantes())
        content_part.bind("<Button-1>", lambda e: self.abrir_gestion_participantes())
        
        # ===== TARJETA 2: CALIBRAR DISPOSITIVOS =====
        self.card_calibrar = tk.Frame(frame_cards, bg="#3c3f41", 
                                     relief=tk.FLAT, bd=0, cursor="hand2",
                                     highlightbackground="#4c5052", 
                                     highlightthickness=1)
        self.card_calibrar.grid(row=0, column=2, sticky="ew", padx=8)
        
        # Contenido de la tarjeta
        content_calib = tk.Frame(self.card_calibrar, bg="#3c3f41")
        content_calib.pack(fill=tk.BOTH, expand=True, padx=22, pady=22)
        
        # Icono
        tk.Label(content_calib, text="⚙️", 
                font=('Segoe UI', 36), bg="#3c3f41", fg="#d4a373").pack(pady=(0, 8))
        
        # Título
        tk.Label(content_calib, text="Calibrar Dispositivos", 
                font=('Segoe UI', 13, 'bold'), bg="#3c3f41", fg="#e8e8e8").pack(pady=(0, 6))
        
        # Descripción
        tk.Label(content_calib, text="Configura cámaras\ny sensores del sistema", 
                font=('Segoe UI', 9), bg="#3c3f41", fg="#9ca3af",
                justify=tk.CENTER).pack()
        
        # Eventos de la tarjeta de calibración
        self.card_calibrar.bind("<Enter>", lambda e: self.on_hover_card(self.card_calibrar, "#484b4d"))
        self.card_calibrar.bind("<Leave>", lambda e: self.on_leave_card(self.card_calibrar, "#3c3f41"))
        self.card_calibrar.bind("<Button-1>", lambda e: self.calibrar_dispositivos())
        
        # Hacer que todos los widgets internos también respondan al click
        for widget in content_calib.winfo_children():
            widget.bind("<Button-1>", lambda e: self.calibrar_dispositivos())
        content_calib.bind("<Button-1>", lambda e: self.calibrar_dispositivos())
        
        # ===== FOOTER: DISEÑO SOBRIO =====
        frame_footer = tk.Frame(self.root, bg="#1e1f22", height=40)
        frame_footer.pack(fill=tk.X, side=tk.BOTTOM)
        frame_footer.pack_propagate(False)
        
        tk.Label(frame_footer, 
                text="© 2025 Race Detector • v1.0 • Sistema Profesional de Cronometraje", 
                font=('Segoe UI', 8),
                bg="#1e1f22", 
                fg="#6c727a").pack(pady=11)
    
    def on_hover_principal(self, event):
        """Efecto hover sobrio en el botón principal"""
        self.canvas.itemconfig(self.circulo_exterior, fill="#6ba8dc", outline="#7ab3e0", width=4)
        self.canvas.itemconfig(self.triangulo, fill="#6ba8dc")
        self.root.config(cursor="hand2")
    
    def on_leave_principal(self, event):
        """Quita el efecto hover del botón principal"""
        self.canvas.itemconfig(self.circulo_exterior, fill="#5a9fd4", outline="#6ba8dc", width=3)
        self.canvas.itemconfig(self.triangulo, fill="#5a9fd4")
        self.root.config(cursor="")
    
    def on_hover_card(self, card, color_hover):
        """Efecto hover sobrio en tarjetas"""
        card.configure(bg=color_hover, highlightbackground="#6ba8dc", highlightthickness=2)
        for widget in card.winfo_children():
            self.cambiar_color_recursivo(widget, color_hover)
    
    def on_leave_card(self, card, color_original):
        """Quita el efecto hover de tarjetas"""
        card.configure(bg=color_original, highlightbackground="#4c5052", highlightthickness=1)
        for widget in card.winfo_children():
            self.cambiar_color_recursivo(widget, color_original)
    
    def cambiar_color_recursivo(self, widget, color):
        """Cambia el color de fondo de un widget y sus hijos recursivamente"""
        try:
            widget.config(bg=color)
        except:
            pass
        for child in widget.winfo_children():
            self.cambiar_color_recursivo(child, color)
    
    def iniciar_cronometraje(self, event=None):
        """Abre la interfaz de detección en vivo"""
        try:
            # Ocultar ventana principal temporalmente
            self.root.withdraw()
            
            # Ejecutar la interfaz de detección
            ruta_interfaz = os.path.join(os.path.dirname(__file__), "interfaz_deteccion.py")
            
            # Crear una nueva ventana de tkinter para la interfaz de detección
            ventana_deteccion = tk.Toplevel(self.root)
            
            # Importar y ejecutar la interfaz de detección
            import importlib.util
            spec = importlib.util.spec_from_file_location("interfaz_deteccion", ruta_interfaz)
            modulo = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(modulo)
            
            # Crear instancia de la interfaz de detección
            app_deteccion = modulo.InterfazDeteccion(ventana_deteccion, modo_independiente=False)
            
            # Cuando se cierre la ventana de detección, mostrar la principal nuevamente
            def al_cerrar_deteccion():
                # Detener la cámara si está activa
                if hasattr(app_deteccion, 'captura_activa') and app_deteccion.captura_activa:
                    app_deteccion.captura_activa = False
                    if app_deteccion.cap:
                        app_deteccion.cap.release()
                ventana_deteccion.destroy()
                self.root.deiconify()  # Mostrar ventana principal
                self.root.lift()  # Traer al frente
                self.root.focus_force()  # Forzar el foco
            
            ventana_deteccion.protocol("WM_DELETE_WINDOW", al_cerrar_deteccion)
            
            # Esperar a que se cierre la ventana de detección
            self.root.wait_window(ventana_deteccion)
            
            # Asegurar que la ventana principal esté visible después
            self.root.deiconify()
            self.root.lift()
            self.root.focus_force()
            
        except Exception as e:
            self.root.deiconify()  # Asegurar que la ventana principal se muestre
            self.root.lift()
            messagebox.showerror("❌ Error", 
                               f"No se pudo abrir la detección en vivo:\n{str(e)}")
    
    def abrir_gestion_participantes(self):
        """Abre la interfaz de gestión de participantes"""
        try:
            # Ocultar ventana principal temporalmente
            self.root.withdraw()
            
            # Ejecutar la interfaz de participantes
            ruta_interfaz = os.path.join(os.path.dirname(__file__), "interfaz_participantes.py")
            
            # Crear una nueva ventana de tkinter para la interfaz de participantes
            ventana_participantes = tk.Toplevel(self.root)
            
            # Importar y ejecutar la interfaz de participantes
            import importlib.util
            spec = importlib.util.spec_from_file_location("interfaz_participantes", ruta_interfaz)
            modulo = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(modulo)
            
            # Crear instancia de la interfaz de participantes
            app_participantes = modulo.InterfazParticipantes(ventana_participantes)
            
            # Cuando se cierre la ventana de participantes, mostrar la principal nuevamente
            def al_cerrar_participantes():
                ventana_participantes.destroy()
                self.root.deiconify()  # Mostrar ventana principal
                self.root.lift()  # Traer al frente
                self.root.focus_force()  # Forzar el foco
            
            ventana_participantes.protocol("WM_DELETE_WINDOW", al_cerrar_participantes)
            
            # Esperar a que se cierre la ventana de participantes
            self.root.wait_window(ventana_participantes)
            
            # Asegurar que la ventana principal esté visible después
            self.root.deiconify()
            self.root.lift()
            self.root.focus_force()
            
        except Exception as e:
            self.root.deiconify()  # Asegurar que la ventana principal se muestre
            self.root.lift()
            messagebox.showerror("❌ Error", 
                               f"No se pudo abrir la gestión de participantes:\n{str(e)}")
    
    def calibrar_dispositivos(self):
        """Abre la interfaz de calibración de dispositivos"""
        try:
            # Ocultar ventana principal temporalmente
            self.root.withdraw()
            
            # Ejecutar la interfaz de calibración
            ruta_interfaz = os.path.join(os.path.dirname(__file__), "interfaz_calibracion.py")
            
            # Crear una nueva ventana de tkinter para la interfaz de calibración
            ventana_calibracion = tk.Toplevel(self.root)
            
            # Importar y ejecutar la interfaz de calibración
            import importlib.util
            spec = importlib.util.spec_from_file_location("interfaz_calibracion", ruta_interfaz)
            modulo = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(modulo)
            
            # Crear instancia de la interfaz de calibración
            app_calibracion = modulo.InterfazCalibracion(ventana_calibracion)
            
            # Cuando se cierre la ventana de calibración, mostrar la principal nuevamente
            def al_cerrar_calibracion():
                ventana_calibracion.destroy()
                self.root.deiconify()  # Mostrar ventana principal
                self.root.lift()  # Traer al frente
                self.root.focus_force()  # Forzar el foco
            
            ventana_calibracion.protocol("WM_DELETE_WINDOW", al_cerrar_calibracion)
            
            # Esperar a que se cierre la ventana de calibración
            self.root.wait_window(ventana_calibracion)
            
            # Asegurar que la ventana principal esté visible después
            self.root.deiconify()
            self.root.lift()
            self.root.focus_force()
            
        except Exception as e:
            self.root.deiconify()  # Asegurar que la ventana principal se muestre
            self.root.lift()
            messagebox.showerror("❌ Error", 
                               f"No se pudo abrir la calibración de dispositivos:\n{str(e)}")
    
    def run(self):
        """Inicia el loop principal de la aplicación"""
        self.root.mainloop()

def main():
    """Función principal"""
    root = tk.Tk()
    app = InterfazPrincipal(root)
    app.run()

if __name__ == "__main__":
    main()
