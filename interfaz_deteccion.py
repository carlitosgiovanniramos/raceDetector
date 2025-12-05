#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Interfaz de Detección en Vivo - Race Detector
Panel de control para la Fase 2: Durante la Carrera

Integra el pipeline de detección con una interfaz gráfica completa que incluye:
- Pantalla Principal: Muestra el último corredor detectado en grande
- Vista de Cámara: Feed en vivo con detecciones
- Panel de Control: Iniciar/Pausar/Detener carrera
- Estadísticas en tiempo real
"""

import tkinter as tk
from tkinter import ttk, messagebox
import cv2
import numpy as np
from PIL import Image, ImageTk
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path
import json
import pandas as pd

# Importar componentes del pipeline
from gestor_participantes import GestorParticipantes


class Config:
    """Configuración cargada desde config_calibracion.json"""
    CONFIG_FILE = Path(__file__).parent / "config_calibracion.json"
    
    DEFAULTS = {
        "camara_index": 0,
        "resolucion": "1280x720",
        "conf_rbnr": 0.3,
        "conf_svhn": 0.25,
        "conf_svhn_min_digit": 0.80,
        "conf_svhn_avg_min": 0.90,
        "min_digits_count": 3,
        "max_digits_count": 4,
        "debounce_seconds": 2.0
    }
    
    @classmethod
    def cargar(cls):
        if cls.CONFIG_FILE.exists():
            try:
                with open(cls.CONFIG_FILE, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    for key, value in cls.DEFAULTS.items():
                        if key not in config:
                            config[key] = value
                    return config
            except:
                pass
        return cls.DEFAULTS.copy()


class DetectorDorsales:
    """Clase que encapsula la lógica de detección del pipeline"""
    
    def __init__(self):
        self.config = Config.cargar()
        self.net_bib = None
        self.net_svhn = None
        self.layers_bib = None
        self.layers_svhn = None
        self.names_bib = []
        self.names_svhn = []
        self.cargado = False
        
        # Rutas de modelos
        self.RBNR_CFG = "weights-classes/RBNR_custom-yolov4-tiny-detector.cfg"
        self.RBNR_WEIGHTS = "weights-classes/RBNR_custom-yolov4-tiny-detector_best.weights"
        self.RBNR_NAMES = "weights-classes/RBRN_obj.names"
        self.SVHN_CFG = "weights-classes/SVHN_custom-yolov4-tiny-detector.cfg"
        self.SVHN_WEIGHTS = "weights-classes/SVHN_custom-yolov4-tiny-detector_best.weights"
        self.SVHN_NAMES = "weights-classes/SVHN_obj.names"
        
        # Parámetros
        self.INPUT_SIZE = 416
        self.NMS_THRESHOLD = 0.4
        
    def cargar_modelos(self):
        """Carga los modelos YOLO"""
        try:
            # Cargar modelo RBNR (detección de dorsales)
            self.net_bib = cv2.dnn.readNetFromDarknet(self.RBNR_CFG, self.RBNR_WEIGHTS)
            self.net_bib.setPreferableBackend(cv2.dnn.DNN_BACKEND_OPENCV)
            self.net_bib.setPreferableTarget(cv2.dnn.DNN_TARGET_CPU)
            
            layer_names = self.net_bib.getLayerNames()
            unconnected = self.net_bib.getUnconnectedOutLayers()
            if isinstance(unconnected, np.ndarray):
                if unconnected.ndim == 1:
                    self.layers_bib = [layer_names[i - 1] for i in unconnected]
                else:
                    self.layers_bib = [layer_names[i[0] - 1] for i in unconnected]
            else:
                self.layers_bib = [layer_names[unconnected - 1]]
            
            with open(self.RBNR_NAMES, 'r') as f:
                self.names_bib = [line.strip() for line in f.readlines()]
            
            # Cargar modelo SVHN (detección de dígitos)
            self.net_svhn = cv2.dnn.readNetFromDarknet(self.SVHN_CFG, self.SVHN_WEIGHTS)
            self.net_svhn.setPreferableBackend(cv2.dnn.DNN_BACKEND_OPENCV)
            self.net_svhn.setPreferableTarget(cv2.dnn.DNN_TARGET_CPU)
            
            layer_names = self.net_svhn.getLayerNames()
            unconnected = self.net_svhn.getUnconnectedOutLayers()
            if isinstance(unconnected, np.ndarray):
                if unconnected.ndim == 1:
                    self.layers_svhn = [layer_names[i - 1] for i in unconnected]
                else:
                    self.layers_svhn = [layer_names[i[0] - 1] for i in unconnected]
            else:
                self.layers_svhn = [layer_names[unconnected - 1]]
            
            with open(self.SVHN_NAMES, 'r') as f:
                self.names_svhn = [line.strip() for line in f.readlines()]
            
            self.cargado = True
            return True
        except Exception as e:
            print(f"Error cargando modelos: {e}")
            return False
    
    def detectar(self, frame, conf_threshold):
        """Detecta objetos en un frame"""
        height, width = frame.shape[:2]
        blob = cv2.dnn.blobFromImage(frame, 1/255.0, (self.INPUT_SIZE, self.INPUT_SIZE), 
                                      swapRB=True, crop=False)
        self.net_bib.setInput(blob)
        outputs = self.net_bib.forward(self.layers_bib)
        
        boxes = []
        confidences = []
        class_ids = []
        
        for output in outputs:
            for detection in output:
                scores = detection[5:]
                class_id = np.argmax(scores)
                confidence = float(scores[class_id]) * float(detection[4])
                
                if confidence > conf_threshold:
                    center_x = int(detection[0] * width)
                    center_y = int(detection[1] * height)
                    w = int(detection[2] * width)
                    h = int(detection[3] * height)
                    x = center_x - w // 2
                    y = center_y - h // 2
                    
                    boxes.append([x, y, w, h])
                    confidences.append(confidence)
                    class_ids.append(class_id)
        
        indices = cv2.dnn.NMSBoxes(boxes, confidences, conf_threshold, self.NMS_THRESHOLD)
        
        results = []
        if len(indices) > 0:
            for i in indices.flatten():
                results.append({
                    'bbox': boxes[i],
                    'confidence': confidences[i],
                    'class_id': class_ids[i]
                })
        
        return results
    
    def detectar_digitos(self, roi, conf_threshold):
        """Detecta dígitos en una ROI"""
        height, width = roi.shape[:2]
        blob = cv2.dnn.blobFromImage(roi, 1/255.0, (self.INPUT_SIZE, self.INPUT_SIZE),
                                      swapRB=True, crop=False)
        self.net_svhn.setInput(blob)
        outputs = self.net_svhn.forward(self.layers_svhn)
        
        boxes = []
        confidences = []
        class_ids = []
        
        for output in outputs:
            for detection in output:
                scores = detection[5:]
                class_id = np.argmax(scores)
                confidence = float(scores[class_id]) * float(detection[4])
                
                if confidence > conf_threshold:
                    center_x = int(detection[0] * width)
                    center_y = int(detection[1] * height)
                    w = int(detection[2] * width)
                    h = int(detection[3] * height)
                    x = center_x - w // 2
                    y = center_y - h // 2
                    
                    boxes.append([x, y, w, h])
                    confidences.append(confidence)
                    class_ids.append(class_id)
        
        indices = cv2.dnn.NMSBoxes(boxes, confidences, conf_threshold, self.NMS_THRESHOLD)
        
        results = []
        if len(indices) > 0:
            for i in indices.flatten():
                results.append({
                    'bbox': boxes[i],
                    'confidence': confidences[i],
                    'class_id': class_ids[i]
                })
        
        return results


class InterfazDeteccion:
    """Interfaz principal de detección en vivo"""
    
    def __init__(self, root, modo_independiente=True):
        self.root = root
        self.modo_independiente = modo_independiente
        self.root.title("🏃 Detección en Vivo - Race Detector")
        self.root.geometry("1400x800")
        self.root.configure(bg="#2b2d30")
        self.root.minsize(1200, 700)
        
        # Estado de la carrera
        self.carrera_activa = False
        self.carrera_pausada = False
        self.tiempo_inicio = None
        self.tiempo_pausado_total = timedelta(0)
        self.ultimo_pause = None
        
        # Detección
        self.detector = DetectorDorsales()
        self.gestor = GestorParticipantes()
        self.config = Config.cargar()
        
        # Cámara
        self.cap = None
        self.captura_activa = False
        self.hilo_captura = None
        
        # Estadísticas
        self.total_detectados = 0
        self.dorsales_registrados = set()
        self.ultimo_dorsal = None
        self.ultimo_participante = None
        self.ultimo_tiempo = None
        
        # Debounce
        self.cache_debounce = {}  # dorsal -> timestamp
        
        # FPS
        self.fps_buffer = []
        self.fps_actual = 0
        
        # Frame actual para mostrar
        self.frame_actual = None
        self.lock_frame = threading.Lock()
        
        self.crear_widgets()
        self.cargar_modelos_async()
        
    def crear_widgets(self):
        """Crea todos los widgets de la interfaz"""
        
        # ===== HEADER =====
        self.crear_header()
        
        # ===== CONTENIDO PRINCIPAL =====
        frame_principal = tk.Frame(self.root, bg="#2b2d30")
        frame_principal.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)
        
        # Configurar grid
        frame_principal.grid_columnconfigure(0, weight=2)  # Pantalla corredor
        frame_principal.grid_columnconfigure(1, weight=3)  # Vista cámara
        frame_principal.grid_columnconfigure(2, weight=1)  # Panel control
        frame_principal.grid_rowconfigure(0, weight=1)
        
        # Columna 1: Pantalla del corredor (grande)
        self.crear_pantalla_corredor(frame_principal)
        
        # Columna 2: Vista de cámara
        self.crear_vista_camara(frame_principal)
        
        # Columna 3: Panel de control
        self.crear_panel_control(frame_principal)
        
        # ===== BARRA INFERIOR =====
        self.crear_barra_estado()
    
    def crear_header(self):
        """Header con título y cronómetro"""
        frame_header = tk.Frame(self.root, bg="#1e1f22", height=60)
        frame_header.pack(fill=tk.X)
        frame_header.pack_propagate(False)
        
        # Título
        tk.Label(frame_header, text="🏃 DETECCIÓN EN VIVO", 
                font=('Segoe UI', 20, 'bold'),
                bg="#1e1f22", fg="#5a9fd4").pack(side=tk.LEFT, padx=20, pady=10)
        
        # Cronómetro grande
        frame_crono = tk.Frame(frame_header, bg="#1e1f22")
        frame_crono.pack(side=tk.RIGHT, padx=20)
        
        tk.Label(frame_crono, text="⏱️", font=('Segoe UI', 16),
                bg="#1e1f22", fg="#e8e8e8").pack(side=tk.LEFT)
        
        self.label_cronometro = tk.Label(frame_crono, text="00:00:00", 
                                         font=('Consolas', 28, 'bold'),
                                         bg="#1e1f22", fg="#5a9fd4")
        self.label_cronometro.pack(side=tk.LEFT, padx=10)
        
        # Estado
        self.label_estado_carrera = tk.Label(frame_header, text="⏸️ ESPERANDO", 
                                             font=('Segoe UI', 14, 'bold'),
                                             bg="#1e1f22", fg="#d4a373")
        self.label_estado_carrera.pack(side=tk.RIGHT, padx=20)
    
    def crear_pantalla_corredor(self, parent):
        """Pantalla grande que muestra el último corredor detectado"""
        frame = tk.Frame(parent, bg="#3c3f41", highlightbackground="#5a9fd4", 
                        highlightthickness=2)
        frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10), pady=5)
        
        # Título
        tk.Label(frame, text="📢 ÚLTIMO CORREDOR", 
                font=('Segoe UI', 14, 'bold'),
                bg="#3c3f41", fg="#e8e8e8").pack(pady=(15, 5))
        
        # Frame para el contenido del corredor
        self.frame_corredor = tk.Frame(frame, bg="#3c3f41")
        self.frame_corredor.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Color base para la pantalla del corredor
        self.color_corredor_base = "#3c3f41"
        
        # Posición
        self.label_posicion = tk.Label(self.frame_corredor, text="--", 
                                       font=('Segoe UI', 48, 'bold'),
                                       bg="#3c3f41", fg="#d4a373")
        self.label_posicion.pack(pady=(20, 5))
        
        tk.Label(self.frame_corredor, text="POSICIÓN", 
                font=('Segoe UI', 12),
                bg="#3c3f41", fg="#9ca3af").pack()
        
        # Dorsal grande
        self.label_dorsal_grande = tk.Label(self.frame_corredor, text="----", 
                                            font=('Consolas', 72, 'bold'),
                                            bg="#3c3f41", fg="#5a9fd4")
        self.label_dorsal_grande.pack(pady=20)
        
        # Nombre
        self.label_nombre_grande = tk.Label(self.frame_corredor, text="Esperando corredor...", 
                                            font=('Segoe UI', 24, 'bold'),
                                            bg="#3c3f41", fg="#e8e8e8")
        self.label_nombre_grande.pack(pady=10)
        
        # Tiempo
        self.label_tiempo_corredor = tk.Label(self.frame_corredor, text="--:--:--", 
                                              font=('Consolas', 36, 'bold'),
                                              bg="#3c3f41", fg="#6ba8dc")
        self.label_tiempo_corredor.pack(pady=20)
        
        # Estado (REGISTRADO / NO ENCONTRADO)
        self.label_estado_registro = tk.Label(self.frame_corredor, text="", 
                                              font=('Segoe UI', 12, 'bold'),
                                              bg="#3c3f41", fg="#28a745")
        self.label_estado_registro.pack(pady=10)
    
    def crear_vista_camara(self, parent):
        """Vista de la cámara con detecciones"""
        frame = tk.Frame(parent, bg="#3c3f41", highlightbackground="#4c5052", 
                        highlightthickness=1)
        frame.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
        
        # Título
        tk.Label(frame, text="📹 VISTA DE CÁMARA", 
                font=('Segoe UI', 12, 'bold'),
                bg="#3c3f41", fg="#e8e8e8").pack(pady=(10, 5))
        
        # Canvas para la cámara
        self.canvas_camara = tk.Canvas(frame, bg="#1e1f22", highlightthickness=0)
        self.canvas_camara.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Texto inicial
        self.canvas_camara.create_text(300, 200, 
                                       text="Presiona 'Iniciar Cámara' para comenzar",
                                       fill="#666666", font=('Segoe UI', 14),
                                       tags="placeholder")
        
        # Info de FPS
        frame_info = tk.Frame(frame, bg="#3c3f41")
        frame_info.pack(fill=tk.X, padx=10, pady=5)
        
        self.label_fps = tk.Label(frame_info, text="FPS: --", 
                                  font=('Consolas', 10),
                                  bg="#3c3f41", fg="#5a9fd4")
        self.label_fps.pack(side=tk.LEFT)
        
        self.label_resolucion = tk.Label(frame_info, text="", 
                                         font=('Consolas', 10),
                                         bg="#3c3f41", fg="#888888")
        self.label_resolucion.pack(side=tk.RIGHT)
    
    def crear_panel_control(self, parent):
        """Panel de control de la carrera"""
        frame = tk.Frame(parent, bg="#3c3f41", highlightbackground="#4c5052", 
                        highlightthickness=1)
        frame.grid(row=0, column=2, sticky="nsew", padx=(10, 0), pady=5)
        
        # Título
        tk.Label(frame, text="🎮 PANEL DE CONTROL", 
                font=('Segoe UI', 11, 'bold'),
                bg="#3c3f41", fg="#e8e8e8").pack(pady=(15, 10))
        
        # === Botones de Cámara ===
        frame_camara = tk.LabelFrame(frame, text="Cámara", 
                                     bg="#3c3f41", fg="#9ca3af",
                                     font=('Segoe UI', 9))
        frame_camara.pack(fill=tk.X, padx=10, pady=5)
        
        self.btn_iniciar_camara = tk.Button(frame_camara, text="📷 Iniciar Cámara",
                                           command=self.iniciar_camara,
                                           bg="#5a9fd4", fg="white",
                                           font=('Segoe UI', 10, 'bold'),
                                           pady=8, cursor="hand2", relief=tk.FLAT)
        self.btn_iniciar_camara.pack(fill=tk.X, padx=10, pady=5)
        
        self.btn_detener_camara = tk.Button(frame_camara, text="⏹️ Detener Cámara",
                                           command=self.detener_camara,
                                           bg="#6c757d", fg="white",
                                           font=('Segoe UI', 10),
                                           pady=8, cursor="hand2", relief=tk.FLAT,
                                           state=tk.DISABLED)
        self.btn_detener_camara.pack(fill=tk.X, padx=10, pady=5)
        
        # === Botones de Carrera ===
        frame_carrera = tk.LabelFrame(frame, text="Carrera", 
                                      bg="#3c3f41", fg="#9ca3af",
                                      font=('Segoe UI', 9))
        frame_carrera.pack(fill=tk.X, padx=10, pady=10)
        
        self.btn_iniciar_carrera = tk.Button(frame_carrera, text="🏁 INICIAR CARRERA",
                                            command=self.iniciar_carrera,
                                            bg="#5a9fd4", fg="white",
                                            font=('Segoe UI', 11, 'bold'),
                                            pady=12, cursor="hand2", relief=tk.FLAT)
        self.btn_iniciar_carrera.pack(fill=tk.X, padx=10, pady=5)
        
        self.btn_pausar = tk.Button(frame_carrera, text="⏸️ Pausar",
                                   command=self.pausar_carrera,
                                   bg="#d4a373", fg="white",
                                   font=('Segoe UI', 10),
                                   pady=8, cursor="hand2", relief=tk.FLAT,
                                   state=tk.DISABLED)
        self.btn_pausar.pack(fill=tk.X, padx=10, pady=5)
        
        self.btn_detener_carrera = tk.Button(frame_carrera, text="🛑 Finalizar Carrera",
                                            command=self.detener_carrera,
                                            bg="#a85858", fg="white",
                                            font=('Segoe UI', 10),
                                            pady=8, cursor="hand2", relief=tk.FLAT,
                                            state=tk.DISABLED)
        self.btn_detener_carrera.pack(fill=tk.X, padx=10, pady=5)
        
        # === Estadísticas ===
        frame_stats = tk.LabelFrame(frame, text="Estadísticas", 
                                    bg="#3c3f41", fg="#9ca3af",
                                    font=('Segoe UI', 9))
        frame_stats.pack(fill=tk.X, padx=10, pady=10)
        
        # Total detectados
        frame_stat1 = tk.Frame(frame_stats, bg="#3c3f41")
        frame_stat1.pack(fill=tk.X, padx=10, pady=3)
        tk.Label(frame_stat1, text="Corredores:", bg="#3c3f41", fg="#9ca3af",
                font=('Segoe UI', 9)).pack(side=tk.LEFT)
        self.label_total = tk.Label(frame_stat1, text="0", bg="#3c3f41", 
                                    fg="#5a9fd4", font=('Segoe UI', 11, 'bold'))
        self.label_total.pack(side=tk.RIGHT)
        
        # Último dorsal
        frame_stat2 = tk.Frame(frame_stats, bg="#3c3f41")
        frame_stat2.pack(fill=tk.X, padx=10, pady=3)
        tk.Label(frame_stat2, text="Último dorsal:", bg="#3c3f41", fg="#9ca3af",
                font=('Segoe UI', 9)).pack(side=tk.LEFT)
        self.label_ultimo = tk.Label(frame_stat2, text="--", bg="#3c3f41", 
                                     fg="#d4a373", font=('Segoe UI', 11, 'bold'))
        self.label_ultimo.pack(side=tk.RIGHT)
        
        # === Botón Volver (siempre visible) ===
        tk.Button(frame, text="◀️ Volver al Menú",
                 command=self.cerrar,
                 bg="#6c757d", fg="white",
                 font=('Segoe UI', 10),
                 pady=8, cursor="hand2", relief=tk.FLAT).pack(fill=tk.X, padx=10, pady=20)
    
    def crear_barra_estado(self):
        """Barra de estado inferior"""
        frame = tk.Frame(self.root, bg="#1e1f22", height=35)
        frame.pack(fill=tk.X, side=tk.BOTTOM)
        frame.pack_propagate(False)
        
        self.label_estado = tk.Label(frame, text="⏳ Cargando modelos de detección...", 
                                     font=('Segoe UI', 9),
                                     bg="#1e1f22", fg="#9ca3af")
        self.label_estado.pack(side=tk.LEFT, padx=15, pady=8)
        
        # Info de configuración
        config = self.config
        info = f"Cámara: {config.get('camara_index', 0)} | Res: {config.get('resolucion', '1280x720')}"
        tk.Label(frame, text=info, font=('Segoe UI', 9),
                bg="#1e1f22", fg="#666666").pack(side=tk.RIGHT, padx=15)
    
    def cargar_modelos_async(self):
        """Carga los modelos en un hilo separado"""
        def cargar():
            exito = self.detector.cargar_modelos()
            self.root.after(0, lambda: self.modelos_cargados(exito))
        
        threading.Thread(target=cargar, daemon=True).start()
    
    def modelos_cargados(self, exito):
        """Callback cuando los modelos terminan de cargar"""
        if exito:
            self.label_estado.config(text="✅ Modelos cargados correctamente. Listo para detectar.",
                                     fg="#28a745")
        else:
            self.label_estado.config(text="❌ Error cargando modelos. Verifica los archivos.",
                                     fg="#dc3545")
            messagebox.showerror("Error", "No se pudieron cargar los modelos de detección.\n"
                                         "Verifica que existan los archivos en weights-classes/")
    
    def iniciar_camara(self):
        """Inicia la captura de la cámara"""
        if self.captura_activa:
            return
        
        config = self.config
        camara_idx = config.get("camara_index", 0)
        resolucion = config.get("resolucion", "1280x720")
        
        try:
            res_w, res_h = map(int, resolucion.split('x'))
        except:
            res_w, res_h = 1280, 720
        
        self.cap = cv2.VideoCapture(camara_idx)
        if not self.cap.isOpened():
            messagebox.showerror("Error", f"No se pudo abrir la cámara {camara_idx}")
            return
        
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, res_w)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, res_h)
        
        self.captura_activa = True
        self.btn_iniciar_camara.config(state=tk.DISABLED)
        self.btn_detener_camara.config(state=tk.NORMAL)
        
        # Actualizar info de resolución
        real_w = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        real_h = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.label_resolucion.config(text=f"{real_w}x{real_h}")
        
        # Iniciar hilo de captura
        self.hilo_captura = threading.Thread(target=self.loop_captura, daemon=True)
        self.hilo_captura.start()
        
        # Iniciar actualización de UI
        self.actualizar_vista_camara()
        
        self.label_estado.config(text=f"📷 Cámara {camara_idx} activa a {real_w}x{real_h}")
    
    def detener_camara(self):
        """Detiene la captura de la cámara"""
        self.captura_activa = False
        
        if self.cap:
            self.cap.release()
            self.cap = None
        
        self.btn_iniciar_camara.config(state=tk.NORMAL)
        self.btn_detener_camara.config(state=tk.DISABLED)
        
        # Limpiar canvas
        self.canvas_camara.delete("all")
        self.canvas_camara.create_text(300, 200, 
                                       text="Cámara detenida",
                                       fill="#666666", font=('Segoe UI', 14))
        
        self.label_estado.config(text="⏹️ Cámara detenida")
    
    def loop_captura(self):
        """Loop de captura en hilo separado"""
        while self.captura_activa and self.cap and self.cap.isOpened():
            t0 = time.time()
            
            ret, frame = self.cap.read()
            if not ret:
                continue
            
            # Procesar detección solo si la carrera está activa y no pausada
            if self.carrera_activa and not self.carrera_pausada and self.detector.cargado:
                frame = self.procesar_frame(frame)
            
            # Calcular FPS
            elapsed = time.time() - t0
            fps = 1 / elapsed if elapsed > 0 else 0
            self.fps_buffer.append(fps)
            if len(self.fps_buffer) > 30:
                self.fps_buffer.pop(0)
            self.fps_actual = sum(self.fps_buffer) / len(self.fps_buffer)
            
            # Guardar frame para mostrar
            with self.lock_frame:
                self.frame_actual = frame.copy()
            
            # Limitar a ~30 FPS
            time.sleep(max(0, 0.033 - elapsed))
    
    def procesar_frame(self, frame):
        """Procesa un frame para detectar dorsales"""
        config = self.config
        conf_rbnr = config.get("conf_rbnr", 0.3)
        conf_svhn = config.get("conf_svhn", 0.25)
        conf_min_digit = config.get("conf_svhn_min_digit", 0.80)
        conf_avg_min = config.get("conf_svhn_avg_min", 0.90)
        min_digits = config.get("min_digits_count", 3)
        max_digits = config.get("max_digits_count", 4)
        
        # Detectar dorsales
        detections = self.detector.detectar(frame, conf_rbnr)
        
        for det in detections:
            x, y, w, h = det['bbox']
            x1 = max(0, x)
            y1 = max(0, y)
            x2 = min(frame.shape[1], x + w)
            y2 = min(frame.shape[0], y + h)
            
            # Padding
            pad_x = int(0.04 * (x2 - x1))
            pad_y = int(0.05 * (y2 - y1))
            x1p = max(0, x1 - pad_x)
            y1p = max(0, y1 - pad_y)
            x2p = min(frame.shape[1], x2 + pad_x)
            y2p = min(frame.shape[0], y2 + pad_y)
            
            roi = frame[y1p:y2p, x1p:x2p]
            if roi.size == 0:
                continue
            
            # Detectar dígitos
            digitos = self.detector.detectar_digitos(roi, conf_svhn)
            
            # Filtrar y procesar dígitos
            digitos_filtrados = [d for d in digitos if d['confidence'] >= conf_min_digit]
            
            numero = ""
            aceptado = False
            
            if len(digitos_filtrados) > 0:
                # Calcular centros y ordenar
                for d in digitos_filtrados:
                    bx, by, bw, bh = d['bbox']
                    d['center_x'] = bx + bw / 2
                
                digitos_ordenados = sorted(digitos_filtrados, key=lambda d: d['center_x'])
                
                # Clustering simple
                if len(digitos_ordenados) >= min_digits and len(digitos_ordenados) <= max_digits:
                    confs = [d['confidence'] for d in digitos_ordenados]
                    avg_conf = np.mean(confs)
                    
                    if avg_conf >= conf_avg_min:
                        chars = []
                        for d in digitos_ordenados:
                            cls_id = d['class_id']
                            cls = self.detector.names_svhn[cls_id] if cls_id < len(self.detector.names_svhn) else str(cls_id)
                            chars.append(cls)
                        numero = ''.join(chars)
                        aceptado = True
            
            # Dibujar bounding box del dorsal
            color = (0, 255, 0) if aceptado else (0, 165, 255)
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 3)
            
            if numero and aceptado:
                # Buscar participante
                participante = self.gestor.buscar_por_dorsal(numero)
                
                # Registrar si pasa debounce
                if self.puede_registrar(numero):
                    self.registrar_deteccion(numero, participante)
                
                # Dibujar info
                if participante:
                    nombre = f"{participante.get('nombre', '')} {participante.get('apellido', '')}"
                    texto = f"{numero} - {nombre}"
                    (tw, th), _ = cv2.getTextSize(texto, cv2.FONT_HERSHEY_SIMPLEX, 0.8, 2)
                    cv2.rectangle(frame, (x1, max(0, y1 - 45)), (x1 + tw + 10, y1 - 5), (0, 180, 0), -1)
                    cv2.putText(frame, texto, (x1 + 5, max(20, y1 - 18)), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
                else:
                    cv2.putText(frame, numero, (x1, max(20, y1 - 10)), 
                               cv2.FONT_HERSHEY_SIMPLEX, 1.0, color, 3)
            
            # Dibujar dígitos individuales
            for d in digitos:
                dx, dy, dw, dh = d['bbox']
                abs_x = x1p + dx
                abs_y = y1p + dy
                cv2.rectangle(frame, (abs_x, abs_y), (abs_x + dw, abs_y + dh), (0, 165, 255), 1)
        
        return frame
    
    def puede_registrar(self, dorsal):
        """Verifica si un dorsal puede registrarse.
        
        Un dorsal solo se registra UNA VEZ por carrera.
        El debounce solo se usa para evitar múltiples detecciones del mismo frame.
        """
        # PRIMERO: Verificar si ya fue registrado en esta carrera
        if dorsal in self.dorsales_registrados:
            return False
        
        # SEGUNDO: Debounce para evitar registros del mismo dorsal en detecciones rápidas
        debounce = self.config.get("debounce_seconds", 2.0)
        now = time.time()
        
        if dorsal in self.cache_debounce:
            if now - self.cache_debounce[dorsal] < debounce:
                return False
        
        self.cache_debounce[dorsal] = now
        return True
    
    def registrar_deteccion(self, dorsal, participante):
        """Registra una detección"""
        self.total_detectados += 1
        self.dorsales_registrados.add(dorsal)
        self.ultimo_dorsal = dorsal
        self.ultimo_participante = participante
        self.ultimo_tiempo = self.obtener_tiempo_carrera()
        
        # Guardar en Excel
        self.guardar_registro(dorsal, participante)
        
        # Actualizar UI (en hilo principal)
        self.root.after(0, self.actualizar_pantalla_corredor)
    
    def guardar_registro(self, dorsal, participante):
        """Guarda el registro en Excel"""
        excel_path = Path("registros_dorsales.xlsx")
        
        tiempo = self.obtener_tiempo_carrera()
        posicion = self.total_detectados
        
        nuevo_registro = {
            "Posición": posicion,
            "Dorsal": dorsal,
            "Nombre": participante.get("nombre", "") if participante else "",
            "Apellido": participante.get("apellido", "") if participante else "",
            "HoraLlegada": tiempo,
            "Estado": "Registrado" if participante else "No encontrado"
        }
        
        try:
            if excel_path.exists():
                df = pd.read_excel(excel_path)
                df = pd.concat([df, pd.DataFrame([nuevo_registro])], ignore_index=True)
            else:
                df = pd.DataFrame([nuevo_registro])
            
            df.to_excel(excel_path, index=False)
        except Exception as e:
            print(f"Error guardando en Excel: {e}")
    
    def actualizar_pantalla_corredor(self):
        """Actualiza la pantalla del corredor"""
        if self.ultimo_dorsal:
            self.label_posicion.config(text=f"#{self.total_detectados}")
            self.label_dorsal_grande.config(text=self.ultimo_dorsal)
            
            if self.ultimo_participante:
                nombre = f"{self.ultimo_participante.get('nombre', '')} {self.ultimo_participante.get('apellido', '')}"
                self.label_nombre_grande.config(text=nombre, fg="#5a9fd4")
                self.label_estado_registro.config(text="✅ REGISTRADO", fg="#28a745")
                self.frame_corredor.config(bg="#2a4a3a")  # Verde oscuro sobrio
                for widget in self.frame_corredor.winfo_children():
                    widget.config(bg="#2a4a3a")
            else:
                self.label_nombre_grande.config(text="Participante no encontrado", fg="#d4a373")
                self.label_estado_registro.config(text="⚠️ NO EN BASE DE DATOS", fg="#d4a373")
                self.frame_corredor.config(bg="#4a3a2a")  # Naranja oscuro sobrio
                for widget in self.frame_corredor.winfo_children():
                    widget.config(bg="#4a3a2a")
            
            self.label_tiempo_corredor.config(text=self.ultimo_tiempo or "--:--:--")
            self.label_ultimo.config(text=self.ultimo_dorsal)
            self.label_total.config(text=str(self.total_detectados))
            
            # Volver al color normal después de 3 segundos
            self.root.after(3000, self.restaurar_color_corredor)
    
    def restaurar_color_corredor(self):
        """Restaura el color de fondo de la pantalla del corredor"""
        self.frame_corredor.config(bg="#3c3f41")
        for widget in self.frame_corredor.winfo_children():
            widget.config(bg="#3c3f41")
    
    def actualizar_vista_camara(self):
        """Actualiza la vista de la cámara en el canvas"""
        if not self.captura_activa:
            return
        
        with self.lock_frame:
            frame = self.frame_actual.copy() if self.frame_actual is not None else None
        
        if frame is not None:
            # Obtener tamaño del canvas
            canvas_w = self.canvas_camara.winfo_width()
            canvas_h = self.canvas_camara.winfo_height()
            
            if canvas_w > 1 and canvas_h > 1:
                # Redimensionar manteniendo aspecto
                h, w = frame.shape[:2]
                ratio = min(canvas_w / w, canvas_h / h)
                new_w = int(w * ratio)
                new_h = int(h * ratio)
                
                frame_resized = cv2.resize(frame, (new_w, new_h))
                frame_rgb = cv2.cvtColor(frame_resized, cv2.COLOR_BGR2RGB)
                
                img = Image.fromarray(frame_rgb)
                self.photo = ImageTk.PhotoImage(img)
                
                # Centrar en canvas
                x = (canvas_w - new_w) // 2
                y = (canvas_h - new_h) // 2
                
                self.canvas_camara.delete("all")
                self.canvas_camara.create_image(x, y, anchor=tk.NW, image=self.photo)
        
        # Actualizar FPS
        self.label_fps.config(text=f"FPS: {self.fps_actual:.1f}")
        
        # Programar siguiente actualización
        if self.captura_activa:
            self.root.after(33, self.actualizar_vista_camara)
    
    def iniciar_carrera(self):
        """Inicia la carrera y el cronómetro"""
        if not self.captura_activa:
            if not messagebox.askyesno("Iniciar Carrera", 
                                       "La cámara no está activa. ¿Desea iniciar la cámara también?"):
                return
            self.iniciar_camara()
        
        self.carrera_activa = True
        self.carrera_pausada = False
        self.tiempo_inicio = datetime.now()
        self.tiempo_pausado_total = timedelta(0)
        
        # Resetear estadísticas
        self.total_detectados = 0
        self.dorsales_registrados.clear()
        self.cache_debounce.clear()
        
        # Actualizar UI
        self.btn_iniciar_carrera.config(state=tk.DISABLED)
        self.btn_pausar.config(state=tk.NORMAL)
        self.btn_detener_carrera.config(state=tk.NORMAL)
        self.label_estado_carrera.config(text="🏃 EN CURSO", fg="#5a9fd4")
        
        # Iniciar cronómetro
        self.actualizar_cronometro()
        
        self.label_estado.config(text="🏁 ¡CARRERA INICIADA! Detectando dorsales...")
    
    def pausar_carrera(self):
        """Pausa/Reanuda la carrera"""
        if self.carrera_pausada:
            # Reanudar
            self.carrera_pausada = False
            if self.ultimo_pause:
                self.tiempo_pausado_total += datetime.now() - self.ultimo_pause
            self.btn_pausar.config(text="⏸️ Pausar", bg="#d4a373")
            self.label_estado_carrera.config(text="🏃 EN CURSO", fg="#5a9fd4")
            self.label_estado.config(text="▶️ Carrera reanudada")
        else:
            # Pausar
            self.carrera_pausada = True
            self.ultimo_pause = datetime.now()
            self.btn_pausar.config(text="▶️ Reanudar", bg="#5a9fd4")
            self.label_estado_carrera.config(text="⏸️ PAUSADA", fg="#d4a373")
            self.label_estado.config(text="⏸️ Carrera pausada - Detección detenida")
    
    def detener_carrera(self):
        """Finaliza la carrera"""
        if not messagebox.askyesno("Finalizar Carrera", 
                                   f"¿Finalizar la carrera?\n\n"
                                   f"Corredores registrados: {self.total_detectados}"):
            return
        
        self.carrera_activa = False
        self.carrera_pausada = False
        
        # Actualizar UI
        self.btn_iniciar_carrera.config(state=tk.NORMAL)
        self.btn_pausar.config(state=tk.DISABLED, text="⏸️ Pausar", bg="#d4a373")
        self.btn_detener_carrera.config(state=tk.DISABLED)
        self.label_estado_carrera.config(text="🏁 FINALIZADA", fg="#a85858")
        
        tiempo_final = self.obtener_tiempo_carrera()
        self.label_estado.config(text=f"🏁 Carrera finalizada. Tiempo: {tiempo_final} | Corredores: {self.total_detectados}")
        
        messagebox.showinfo("Carrera Finalizada", 
                           f"¡Carrera completada!\n\n"
                           f"⏱️ Tiempo total: {tiempo_final}\n"
                           f"🏃 Corredores: {self.total_detectados}\n\n"
                           f"Los resultados se guardaron en 'registros_dorsales.xlsx'")
    
    def obtener_tiempo_carrera(self):
        """Obtiene el tiempo transcurrido de la carrera"""
        if not self.tiempo_inicio:
            return "00:00:00"
        
        ahora = datetime.now()
        if self.carrera_pausada and self.ultimo_pause:
            ahora = self.ultimo_pause
        
        transcurrido = ahora - self.tiempo_inicio - self.tiempo_pausado_total
        
        total_seconds = int(transcurrido.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    
    def actualizar_cronometro(self):
        """Actualiza el cronómetro"""
        if self.carrera_activa:
            tiempo = self.obtener_tiempo_carrera()
            self.label_cronometro.config(text=tiempo)
            self.root.after(100, self.actualizar_cronometro)
    
    def cerrar(self):
        """Cierra la interfaz"""
        if self.carrera_activa:
            if not messagebox.askyesno("Cerrar", "Hay una carrera en curso. ¿Desea cerrar de todos modos?"):
                return
        
        self.captura_activa = False
        if self.cap:
            self.cap.release()
        
        if self.modo_independiente:
            self.root.destroy()
        else:
            self.root.destroy()


def main():
    root = tk.Tk()
    app = InterfazDeteccion(root, modo_independiente=True)
    root.protocol("WM_DELETE_WINDOW", app.cerrar)
    root.mainloop()


if __name__ == "__main__":
    main()
