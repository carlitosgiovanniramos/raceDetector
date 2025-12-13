"""
Sistema de Cronometraje - Race Detector
Interfaz de Calibración de Dispositivos
Autor: Sistema de Gestión de Carreras
Fecha: Diciembre 2025
"""

import tkinter as tk
import tkinter.ttk as ttk
import tkinter.messagebox as messagebox
import cv2
import json
import os
import sys
from pathlib import Path
from PIL import Image, ImageTk
import threading


def obtener_ruta_base():
    """Obtiene la ruta base correcta tanto en desarrollo como en .exe PyInstaller."""
    if getattr(sys, 'frozen', False):
        # Ejecutando como .exe empaquetado
        return sys._MEIPASS
    else:
        # Ejecutando como script Python normal
        return os.path.dirname(os.path.abspath(__file__))


class InterfazCalibracion:
    """Interfaz para calibrar cámaras y ajustar parámetros de detección"""
    
    # Archivo de configuración (ruta absoluta)
    CONFIG_FILE = os.path.join(obtener_ruta_base(), "config_calibracion.json")
    
    # Valores por defecto
    DEFAULTS = {
        "camara_index": 0,
        "resolucion": "1280x720",
        "conf_rbnr": 0.3,
        "conf_svhn": 0.25,
        "conf_svhn_min_digit": 0.80,
        "conf_svhn_avg_min": 0.90,
        "min_digits_count": 3,
        "max_digits_count": 4,
        "debounce_seconds": 2.0  # Tiempo mínimo entre registros del MISMO dorsal
    }
    
    RESOLUCIONES = ["640x480", "800x600", "1280x720", "1920x1080"]
    
    def __init__(self, root):
        self.root = root
        self.root.title("⚙️ Calibración de Dispositivos - Race Detector")
        self.root.geometry("900x650")
        self.root.configure(bg="#2b2d30")
        self.root.resizable(True, True)
        self.root.minsize(750, 500)
        
        # Variables
        self.config = self.cargar_configuracion()
        self.cap = None
        self.preview_activa = False
        self.camaras_disponibles = []
        
        # Variables de tkinter
        self.var_camara = tk.StringVar(value=str(self.config.get("camara_index", 0)))
        self.var_resolucion = tk.StringVar(value=self.config.get("resolucion", "1280x720"))
        self.var_conf_rbnr = tk.DoubleVar(value=self.config.get("conf_rbnr", 0.3))
        self.var_conf_svhn = tk.DoubleVar(value=self.config.get("conf_svhn", 0.25))
        self.var_debounce = tk.DoubleVar(value=self.config.get("debounce_seconds", 2.0))
        self.var_min_digits = tk.IntVar(value=self.config.get("min_digits_count", 3))
        self.var_max_digits = tk.IntVar(value=self.config.get("max_digits_count", 4))
        
        # Detectar cámaras
        self.detectar_camaras()
        
        # Crear interfaz
        self.crear_widgets()
        
        # Centrar ventana
        self.centrar_ventana()
    
    def centrar_ventana(self):
        """Centra la ventana en la pantalla"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
    
    def cargar_configuracion(self):
        """Carga la configuración desde archivo JSON"""
        if os.path.exists(self.CONFIG_FILE):
            try:
                with open(self.CONFIG_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        return self.DEFAULTS.copy()
    
    def guardar_configuracion(self):
        """Guarda la configuración en archivo JSON"""
        config = {
            "camara_index": int(self.var_camara.get()),
            "resolucion": self.var_resolucion.get(),
            "conf_rbnr": self.var_conf_rbnr.get(),
            "conf_svhn": self.var_conf_svhn.get(),
            "conf_svhn_min_digit": self.config.get("conf_svhn_min_digit", 0.80),
            "conf_svhn_avg_min": self.config.get("conf_svhn_avg_min", 0.90),
            "min_digits_count": self.var_min_digits.get(),
            "max_digits_count": self.var_max_digits.get(),
            "debounce_seconds": self.var_debounce.get()
        }
        
        try:
            with open(self.CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar la configuración:\n{e}")
            return False
    
    def detectar_camaras(self):
        """Detecta las cámaras disponibles en el sistema"""
        self.camaras_disponibles = []
        for i in range(5):  # Probar índices 0-4
            cap = cv2.VideoCapture(i, cv2.CAP_DSHOW)
            if cap.isOpened():
                self.camaras_disponibles.append(i)
                cap.release()
        
        if not self.camaras_disponibles:
            self.camaras_disponibles = [0]  # Por defecto
    
    def crear_widgets(self):
        """Crea todos los widgets de la interfaz"""
        
        # ===== HEADER =====
        frame_header = tk.Frame(self.root, bg="#1e1f22", height=55)
        frame_header.pack(fill=tk.X)
        frame_header.pack_propagate(False)
        
        header_content = tk.Frame(frame_header, bg="#1e1f22")
        header_content.pack(expand=True)
        
        tk.Label(header_content, text="⚙️ Calibración de Dispositivos", 
                font=('Segoe UI', 20, 'bold'), 
                bg="#1e1f22", fg="#e8e8e8").pack(pady=(12, 0))
        
        # ===== CONTENIDO PRINCIPAL =====
        frame_contenido = tk.Frame(self.root, bg="#2b2d30")
        frame_contenido.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)
        
        # Dividir en dos columnas
        frame_contenido.grid_columnconfigure(0, weight=1)
        frame_contenido.grid_columnconfigure(1, weight=1)
        
        # ===== COLUMNA IZQUIERDA: VISTA PREVIA =====
        frame_preview = tk.Frame(frame_contenido, bg="#3c3f41", 
                                highlightbackground="#4c5052", highlightthickness=1)
        frame_preview.grid(row=0, column=0, sticky="nsew", padx=(0, 10), pady=5)
        
        tk.Label(frame_preview, text="📹 Vista Previa de Cámara", 
                font=('Segoe UI', 12, 'bold'), 
                bg="#3c3f41", fg="#e8e8e8").pack(pady=(15, 10))
        
        # Canvas para mostrar la vista previa
        self.canvas_preview = tk.Canvas(frame_preview, width=400, height=300, 
                                        bg="#1e1f22", highlightthickness=0)
        self.canvas_preview.pack(padx=15, pady=10)
        
        # Texto inicial en el canvas
        self.canvas_preview.create_text(200, 150, text="Presiona 'Iniciar Vista Previa'\npara ver la cámara",
                                        fill="#9ca3af", font=('Segoe UI', 11), justify=tk.CENTER)
        
        # Botones de control de preview
        frame_botones_preview = tk.Frame(frame_preview, bg="#3c3f41")
        frame_botones_preview.pack(pady=(5, 15))
        
        self.btn_preview = tk.Button(frame_botones_preview, text="▶️ Iniciar Vista Previa",
                                    command=self.toggle_preview,
                                    bg="#5a9fd4", fg="white", font=('Segoe UI', 10, 'bold'),
                                    padx=20, pady=8, cursor="hand2", relief=tk.FLAT)
        self.btn_preview.pack(side=tk.LEFT, padx=5)
        
        tk.Button(frame_botones_preview, text="🔄 Detectar Cámaras",
                 command=self.actualizar_camaras,
                 bg="#6c757d", fg="white", font=('Segoe UI', 10),
                 padx=15, pady=8, cursor="hand2", relief=tk.FLAT).pack(side=tk.LEFT, padx=5)
        
        # ===== COLUMNA DERECHA: CONFIGURACIÓN CON SCROLL =====
        frame_config_container = tk.Frame(frame_contenido, bg="#3c3f41",
                               highlightbackground="#4c5052", highlightthickness=1)
        frame_config_container.grid(row=0, column=1, sticky="nsew", padx=(10, 0), pady=5)
        
        tk.Label(frame_config_container, text="🎛️ Parámetros de Configuración", 
                font=('Segoe UI', 12, 'bold'), 
                bg="#3c3f41", fg="#e8e8e8").pack(pady=(15, 10))
        
        # Canvas con scrollbar para contenido scrolleable
        canvas_config = tk.Canvas(frame_config_container, bg="#3c3f41", 
                                  highlightthickness=0, bd=0)
        scrollbar = tk.Scrollbar(frame_config_container, orient="vertical", 
                                 command=canvas_config.yview)
        
        # Frame interno que contendrá los controles
        frame_controles = tk.Frame(canvas_config, bg="#3c3f41")
        
        # Configurar scroll
        frame_controles.bind("<Configure>", 
            lambda e: canvas_config.configure(scrollregion=canvas_config.bbox("all")))
        
        canvas_config.create_window((0, 0), window=frame_controles, anchor="nw")
        canvas_config.configure(yscrollcommand=scrollbar.set)
        
        # Hacer scroll con rueda del mouse
        def on_mousewheel(event):
            canvas_config.yview_scroll(int(-1*(event.delta/120)), "units")
        
        canvas_config.bind_all("<MouseWheel>", on_mousewheel)
        
        # Empaquetar canvas y scrollbar
        canvas_config.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(15, 0))
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, padx=(0, 5), pady=5)
        
        # Ajustar ancho del frame interno cuando cambia el canvas
        def ajustar_ancho(event):
            canvas_config.itemconfig(canvas_config.find_withtag("all")[0], width=event.width - 10)
        canvas_config.bind("<Configure>", ajustar_ancho)
        
        # --- Selección de Cámara ---
        self.crear_seccion_control(frame_controles, "📷 Cámara:", 
                                   self.crear_selector_camara)
        
        # --- Resolución ---
        self.crear_seccion_control(frame_controles, "📐 Resolución:",
                                   self.crear_selector_resolucion)
        
        # --- Separador ---
        ttk.Separator(frame_controles, orient='horizontal').pack(fill=tk.X, pady=15)
        
        # --- Sensibilidad Detección Dorsal ---
        self.crear_seccion_slider(frame_controles, "🎯 Sensibilidad Dorsal:",
                                  self.var_conf_rbnr, 0.1, 0.6, 
                                  "Menor = más sensible, Mayor = más estricto")
        
        # --- Sensibilidad Detección Dígitos ---
        self.crear_seccion_slider(frame_controles, "🔢 Sensibilidad Dígitos:",
                                  self.var_conf_svhn, 0.1, 0.5,
                                  "Menor = más sensible, Mayor = más estricto")
        
        # --- Separador ---
        ttk.Separator(frame_controles, orient='horizontal').pack(fill=tk.X, pady=15)
        
        # --- Rango de Dígitos ---
        frame_digitos = tk.Frame(frame_controles, bg="#3c3f41")
        frame_digitos.pack(fill=tk.X, pady=5)
        
        tk.Label(frame_digitos, text="🔢 Dígitos del Dorsal:", 
                font=('Segoe UI', 10, 'bold'), bg="#3c3f41", fg="#e8e8e8").pack(anchor=tk.W)
        
        frame_rango = tk.Frame(frame_digitos, bg="#3c3f41")
        frame_rango.pack(fill=tk.X, pady=5)
        
        tk.Label(frame_rango, text="Mínimo:", bg="#3c3f41", fg="#9ca3af",
                font=('Segoe UI', 9)).pack(side=tk.LEFT)
        
        spin_min = tk.Spinbox(frame_rango, from_=1, to=5, width=5, 
                             textvariable=self.var_min_digits,
                             font=('Segoe UI', 10))
        spin_min.pack(side=tk.LEFT, padx=(5, 20))
        
        tk.Label(frame_rango, text="Máximo:", bg="#3c3f41", fg="#9ca3af",
                font=('Segoe UI', 9)).pack(side=tk.LEFT)
        
        spin_max = tk.Spinbox(frame_rango, from_=2, to=6, width=5,
                             textvariable=self.var_max_digits,
                             font=('Segoe UI', 10))
        spin_max.pack(side=tk.LEFT, padx=5)
        
        # --- Separador ---
        ttk.Separator(frame_controles, orient='horizontal').pack(fill=tk.X, pady=10)
        
        # --- Tiempo de Debounce ---
        frame_debounce = tk.Frame(frame_controles, bg="#3c3f41")
        frame_debounce.pack(fill=tk.X, pady=5)
        
        tk.Label(frame_debounce, text="⏱️ Tiempo entre registros del MISMO dorsal:", 
                font=('Segoe UI', 10, 'bold'), bg="#3c3f41", fg="#e8e8e8").pack(anchor=tk.W)
        tk.Label(frame_debounce, text="(Dorsales diferentes se detectan inmediatamente)", 
                font=('Segoe UI', 8), bg="#3c3f41", fg="#888888").pack(anchor=tk.W)
        
        frame_debounce_val = tk.Frame(frame_debounce, bg="#3c3f41")
        frame_debounce_val.pack(fill=tk.X, pady=5)
        
        scale_debounce = tk.Scale(frame_debounce_val, from_=0.5, to=10, resolution=0.5,
                                 orient=tk.HORIZONTAL, variable=self.var_debounce, 
                                 bg="#3c3f41", fg="#e8e8e8",
                                 highlightthickness=0, troughcolor="#1e1f22",
                                 activebackground="#5a9fd4", length=200)
        scale_debounce.pack(side=tk.LEFT)
        
        self.label_debounce = tk.Label(frame_debounce_val, text=f"{self.var_debounce.get():.1f}s",
                                       font=('Segoe UI', 11, 'bold'), bg="#3c3f41", fg="#5a9fd4")
        self.label_debounce.pack(side=tk.LEFT, padx=10)
        
        self.var_debounce.trace('w', lambda *args: self.label_debounce.config(
            text=f"{self.var_debounce.get():.1f}s"))
        
        # Espaciado final para scroll
        tk.Frame(frame_controles, bg="#3c3f41", height=20).pack(fill=tk.X)
        
        # ===== BARRA INFERIOR: BOTONES DE ACCIÓN =====
        frame_acciones = tk.Frame(self.root, bg="#1e1f22", height=60)
        frame_acciones.pack(fill=tk.X, side=tk.BOTTOM)
        frame_acciones.pack_propagate(False)
        
        frame_botones = tk.Frame(frame_acciones, bg="#1e1f22")
        frame_botones.pack(expand=True, pady=10)
        
        tk.Button(frame_botones, text="💾 Guardar Configuración",
                 command=self.guardar_y_aplicar,
                 bg="#28a745", fg="white", font=('Segoe UI', 10, 'bold'),
                 padx=15, pady=8, cursor="hand2", relief=tk.FLAT).pack(side=tk.LEFT, padx=8)
        
        tk.Button(frame_botones, text="🔄 Restaurar Valores",
                 command=self.restaurar_defaults,
                 bg="#6c757d", fg="white", font=('Segoe UI', 10),
                 padx=15, pady=8, cursor="hand2", relief=tk.FLAT).pack(side=tk.LEFT, padx=8)
        
        tk.Button(frame_botones, text="◀️ Volver",
                 command=self.cerrar,
                 bg="#dc3545", fg="white", font=('Segoe UI', 10),
                 padx=15, pady=8, cursor="hand2", relief=tk.FLAT).pack(side=tk.LEFT, padx=8)
    
    def crear_seccion_control(self, parent, titulo, crear_control_func):
        """Crea una sección con título y control"""
        frame = tk.Frame(parent, bg="#3c3f41")
        frame.pack(fill=tk.X, pady=6)
        
        tk.Label(frame, text=titulo, font=('Segoe UI', 10, 'bold'),
                bg="#3c3f41", fg="#e8e8e8").pack(anchor=tk.W)
        
        crear_control_func(frame)
    
    def crear_selector_camara(self, parent):
        """Crea el selector de cámara"""
        frame = tk.Frame(parent, bg="#3c3f41")
        frame.pack(fill=tk.X, pady=5)
        
        opciones = [f"Cámara {i}" for i in self.camaras_disponibles]
        self.combo_camara = ttk.Combobox(frame, values=opciones, state="readonly",
                                        font=('Segoe UI', 10), width=20)
        self.combo_camara.set(f"Cámara {self.var_camara.get()}")
        self.combo_camara.pack(side=tk.LEFT)
        self.combo_camara.bind("<<ComboboxSelected>>", self.on_camara_change)
    
    def crear_selector_resolucion(self, parent):
        """Crea el selector de resolución"""
        frame = tk.Frame(parent, bg="#3c3f41")
        frame.pack(fill=tk.X, pady=5)
        
        combo = ttk.Combobox(frame, values=self.RESOLUCIONES, state="readonly",
                            textvariable=self.var_resolucion,
                            font=('Segoe UI', 10), width=20)
        combo.pack(side=tk.LEFT)
    
    def crear_seccion_slider(self, parent, titulo, variable, min_val, max_val, descripcion):
        """Crea una sección con slider"""
        frame = tk.Frame(parent, bg="#3c3f41")
        frame.pack(fill=tk.X, pady=8)
        
        tk.Label(frame, text=titulo, font=('Segoe UI', 10, 'bold'),
                bg="#3c3f41", fg="#e8e8e8").pack(anchor=tk.W)
        
        tk.Label(frame, text=descripcion, font=('Segoe UI', 8),
                bg="#3c3f41", fg="#9ca3af").pack(anchor=tk.W)
        
        frame_slider = tk.Frame(frame, bg="#3c3f41")
        frame_slider.pack(fill=tk.X, pady=5)
        
        scale = tk.Scale(frame_slider, from_=min_val, to=max_val, orient=tk.HORIZONTAL,
                        variable=variable, resolution=0.05, bg="#3c3f41", fg="#e8e8e8",
                        highlightthickness=0, troughcolor="#1e1f22",
                        activebackground="#5a9fd4", length=200)
        scale.pack(side=tk.LEFT)
        
        label_valor = tk.Label(frame_slider, text=f"{variable.get():.2f}",
                              font=('Segoe UI', 11, 'bold'), bg="#3c3f41", fg="#5a9fd4")
        label_valor.pack(side=tk.LEFT, padx=10)
        
        variable.trace('w', lambda *args: label_valor.config(text=f"{variable.get():.2f}"))
    
    def on_camara_change(self, event):
        """Maneja el cambio de cámara"""
        seleccion = self.combo_camara.get()
        index = int(seleccion.replace("Cámara ", ""))
        self.var_camara.set(str(index))
        
        # Si hay preview activa, reiniciarla
        if self.preview_activa:
            self.detener_preview()
            self.iniciar_preview()
    
    def actualizar_camaras(self):
        """Actualiza la lista de cámaras disponibles"""
        self.detectar_camaras()
        opciones = [f"Cámara {i}" for i in self.camaras_disponibles]
        self.combo_camara['values'] = opciones
        messagebox.showinfo("Cámaras Detectadas", 
                           f"Se encontraron {len(self.camaras_disponibles)} cámara(s):\n" +
                           "\n".join(opciones))
    
    def toggle_preview(self):
        """Activa/desactiva la vista previa"""
        if self.preview_activa:
            self.detener_preview()
        else:
            self.iniciar_preview()
    
    def iniciar_preview(self):
        """Inicia la vista previa de la cámara"""
        cam_index = int(self.var_camara.get())
        self.cap = cv2.VideoCapture(cam_index)
        
        if not self.cap.isOpened():
            messagebox.showerror("Error", f"No se pudo abrir la cámara {cam_index}")
            return
        
        # Configurar resolución
        res = self.var_resolucion.get().split("x")
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, int(res[0]))
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, int(res[1]))
        
        self.preview_activa = True
        self.btn_preview.config(text="⏹️ Detener Vista Previa", bg="#dc3545")
        self.actualizar_preview()
    
    def detener_preview(self):
        """Detiene la vista previa"""
        self.preview_activa = False
        self.btn_preview.config(text="▶️ Iniciar Vista Previa", bg="#5a9fd4")
        
        if self.cap:
            self.cap.release()
            self.cap = None
        
        # Limpiar canvas
        self.canvas_preview.delete("all")
        self.canvas_preview.create_text(200, 150, text="Vista previa detenida",
                                        fill="#9ca3af", font=('Segoe UI', 11))
    
    def actualizar_preview(self):
        """Actualiza el frame de la vista previa"""
        if not self.preview_activa or not self.cap:
            return
        
        ret, frame = self.cap.read()
        if ret:
            # Redimensionar para el canvas
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame = cv2.resize(frame, (400, 300))
            
            # Convertir a imagen de tkinter
            img = Image.fromarray(frame)
            self.photo = ImageTk.PhotoImage(image=img)
            
            # Mostrar en canvas
            self.canvas_preview.delete("all")
            self.canvas_preview.create_image(0, 0, anchor=tk.NW, image=self.photo)
        
        # Continuar actualizando
        if self.preview_activa:
            self.root.after(30, self.actualizar_preview)
    
    def guardar_y_aplicar(self):
        """Guarda la configuración y la aplica al pipeline"""
        if self.guardar_configuracion():
            # Aplicar al pipeline
            self.aplicar_configuracion_pipeline()
            messagebox.showinfo("✅ Guardado", 
                               "Configuración guardada correctamente.\n"
                               "Los cambios se aplicarán en la próxima detección.")
    
    def aplicar_configuracion_pipeline(self):
        """Aplica la configuración al archivo pipeline_bib_svhn.py"""
        # Por ahora solo guarda en JSON
        # En el futuro se puede modificar el pipeline para leer de este archivo
        pass
    
    def restaurar_defaults(self):
        """Restaura los valores por defecto"""
        respuesta = messagebox.askyesno("Restaurar", 
                                        "¿Desea restaurar todos los valores por defecto?")
        if respuesta:
            self.var_camara.set(str(self.DEFAULTS["camara_index"]))
            self.var_resolucion.set(self.DEFAULTS["resolucion"])
            self.var_conf_rbnr.set(self.DEFAULTS["conf_rbnr"])
            self.var_conf_svhn.set(self.DEFAULTS["conf_svhn"])
            self.var_min_digits.set(self.DEFAULTS["min_digits_count"])
            self.var_max_digits.set(self.DEFAULTS["max_digits_count"])
            self.var_debounce.set(self.DEFAULTS["debounce_seconds"])
            
            self.combo_camara.set(f"Cámara {self.DEFAULTS['camara_index']}")
            
            messagebox.showinfo("Restaurado", "Valores restaurados a los valores por defecto")
    
    def cerrar(self):
        """Cierra la ventana de calibración"""
        self.detener_preview()
        self.root.destroy()


def main():
    """Función principal"""
    root = tk.Tk()
    app = InterfazCalibracion(root)
    root.mainloop()


if __name__ == "__main__":
    main()
