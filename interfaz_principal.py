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
        self.root.geometry("950x680")
        self.root.configure(bg="#2b2d30")
        self.root.resizable(True, True)
        self.root.minsize(850, 620)
        
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
        
        # ===== HEADER =====
        frame_header = tk.Frame(self.root, bg="#1e1f22", height=100)
        frame_header.pack(fill=tk.X)
        frame_header.pack_propagate(False)
        
        header_content = tk.Frame(frame_header, bg="#1e1f22")
        header_content.pack(expand=True)
        
        # Logo y título
        tk.Label(header_content, text="⏱️  Race Detector", 
                font=('Segoe UI', 32, 'bold'), 
                bg="#1e1f22", fg="#e8e8e8").pack(pady=(20, 5))
        
        tk.Label(header_content, text="Sistema de Cronometraje Profesional", 
                font=('Segoe UI', 11), 
                bg="#1e1f22", fg="#9ca3af").pack()
        
        # ===== CONTENIDO PRINCIPAL =====
        frame_contenido = tk.Frame(self.root, bg="#2b2d30")
        frame_contenido.pack(fill=tk.BOTH, expand=True, padx=50, pady=30)
        
        # Centrar contenido verticalmente
        frame_contenido.grid_rowconfigure(0, weight=1)
        frame_contenido.grid_rowconfigure(1, weight=0)
        frame_contenido.grid_rowconfigure(2, weight=1)
        frame_contenido.grid_columnconfigure(0, weight=1)
        
        # ===== BOTÓN PRINCIPAL DE INICIO =====
        frame_boton_central = tk.Frame(frame_contenido, bg="#2b2d30")
        frame_boton_central.grid(row=0, column=0, sticky="s", pady=(0, 20))
        
        # Tarjeta del botón principal
        card_principal = tk.Frame(frame_boton_central, bg="#3c3f41", 
                                 highlightbackground="#5a9fd4", highlightthickness=2)
        card_principal.pack()
        
        # Canvas para el botón de play
        canvas_size = 140
        self.canvas = tk.Canvas(card_principal, 
                               width=canvas_size, 
                               height=canvas_size,
                               bg="#3c3f41", 
                               highlightthickness=0,
                               cursor="hand2")
        self.canvas.pack(padx=50, pady=(30, 15))
        
        # Círculo exterior
        self.circulo_exterior = self.canvas.create_oval(10, 10, 130, 130, 
                                                        fill="#5a9fd4", 
                                                        outline="#6ba8dc", 
                                                        width=3)
        
        # Círculo interior
        self.circulo_interior = self.canvas.create_oval(22, 22, 118, 118, 
                                                        fill="#3c3f41", 
                                                        outline="")
        
        # Triángulo de play (centrado correctamente)
        cx, cy = 70, 70  # Centro del canvas
        self.triangulo = self.canvas.create_polygon(
            cx - 15, cy - 25,   # Punto superior izquierdo
            cx - 15, cy + 25,   # Punto inferior izquierdo
            cx + 25, cy,        # Punto derecho
            fill="#5a9fd4",
            outline="")
        
        # Textos
        tk.Label(card_principal, 
                text="INICIAR CRONOMETRAJE", 
                font=('Segoe UI', 14, 'bold'),
                bg="#3c3f41", fg="#e8e8e8").pack(pady=(0, 5))
        
        tk.Label(card_principal, 
                text="Clic para comenzar la detección en vivo", 
                font=('Segoe UI', 9),
                bg="#3c3f41", fg="#9ca3af").pack(pady=(0, 25))
        
        # Eventos del botón principal
        self.canvas.bind("<Enter>", self.on_hover_principal)
        self.canvas.bind("<Leave>", self.on_leave_principal)
        self.canvas.bind("<Button-1>", self.iniciar_cronometraje)
        card_principal.bind("<Enter>", self.on_hover_principal)
        card_principal.bind("<Leave>", self.on_leave_principal)
        card_principal.bind("<Button-1>", self.iniciar_cronometraje)
        
        # ===== SECCIÓN DE TARJETAS =====
        frame_tarjetas = tk.Frame(frame_contenido, bg="#2b2d30")
        frame_tarjetas.grid(row=1, column=0, sticky="n", pady=(10, 0))
        
        # Título de sección
        tk.Label(frame_tarjetas, 
                text="— Panel de Configuración —", 
                font=('Segoe UI', 11),
                bg="#2b2d30", fg="#6c727a").pack(pady=(0, 20))
        
        # Contenedor de tarjetas
        frame_cards = tk.Frame(frame_tarjetas, bg="#2b2d30")
        frame_cards.pack()
        
        # ===== TARJETA 1: GESTIONAR PARTICIPANTES =====
        self.card_participantes = tk.Frame(frame_cards, bg="#3c3f41", cursor="hand2",
                                          highlightbackground="#4c5052", highlightthickness=1,
                                          width=280, height=150)
        self.card_participantes.pack(side=tk.LEFT, padx=15)
        self.card_participantes.pack_propagate(False)
        
        content_part = tk.Frame(self.card_participantes, bg="#3c3f41")
        content_part.pack(expand=True)
        
        tk.Label(content_part, text="👥", 
                font=('Segoe UI', 32), bg="#3c3f41", fg="#6ba8dc").pack(pady=(10, 5))
        
        tk.Label(content_part, text="Gestionar Participantes", 
                font=('Segoe UI', 12, 'bold'), bg="#3c3f41", fg="#e8e8e8").pack(pady=(0, 5))
        
        tk.Label(content_part, text="Administra corredores y dorsales", 
                font=('Segoe UI', 9), bg="#3c3f41", fg="#9ca3af").pack()
        
        # Eventos
        for widget in [self.card_participantes, content_part] + content_part.winfo_children():
            widget.bind("<Enter>", lambda e: self.on_hover_card(self.card_participantes, "#484b4d"))
            widget.bind("<Leave>", lambda e: self.on_leave_card(self.card_participantes, "#3c3f41"))
            widget.bind("<Button-1>", lambda e: self.abrir_gestion_participantes())
        
        # ===== TARJETA 2: CALIBRAR DISPOSITIVOS =====
        self.card_calibrar = tk.Frame(frame_cards, bg="#3c3f41", cursor="hand2",
                                     highlightbackground="#4c5052", highlightthickness=1,
                                     width=280, height=150)
        self.card_calibrar.pack(side=tk.LEFT, padx=15)
        self.card_calibrar.pack_propagate(False)
        
        content_calib = tk.Frame(self.card_calibrar, bg="#3c3f41")
        content_calib.pack(expand=True)
        
        tk.Label(content_calib, text="⚙️", 
                font=('Segoe UI', 32), bg="#3c3f41", fg="#d4a373").pack(pady=(10, 5))
        
        tk.Label(content_calib, text="Calibrar Dispositivos", 
                font=('Segoe UI', 12, 'bold'), bg="#3c3f41", fg="#e8e8e8").pack(pady=(0, 5))
        
        tk.Label(content_calib, text="Configura cámaras y sensores", 
                font=('Segoe UI', 9), bg="#3c3f41", fg="#9ca3af").pack()
        
        # Eventos
        for widget in [self.card_calibrar, content_calib] + content_calib.winfo_children():
            widget.bind("<Enter>", lambda e: self.on_hover_card(self.card_calibrar, "#484b4d"))
            widget.bind("<Leave>", lambda e: self.on_leave_card(self.card_calibrar, "#3c3f41"))
            widget.bind("<Button-1>", lambda e: self.calibrar_dispositivos())
        
        # ===== FOOTER =====
        frame_footer = tk.Frame(self.root, bg="#1e1f22", height=40)
        frame_footer.pack(fill=tk.X, side=tk.BOTTOM)
        frame_footer.pack_propagate(False)
        
        tk.Label(frame_footer, 
                text="© 2025 Race Detector  •  v1.0  •  Sistema Profesional de Cronometraje", 
                font=('Segoe UI', 9),
                bg="#1e1f22", fg="#6c727a").pack(expand=True)
    
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
