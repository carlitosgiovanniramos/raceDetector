#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pipeline: detectar bib (RBNR) -> recortar ROI -> detectar dígitos (SVHN)

Uso rápido:
  python pipeline_bib_svhn.py --modo imagen --archivo path\to\imagen.jpg

Este script carga dos modelos YOLOv4-tiny usando OpenCV DNN (CPU) y aplica
primero la detección de la caja del dorsal ('bib') y luego detecta dígitos
en la región recortada usando el detector SVHN disponible en `weights-classes`.
"""

import cv2
import numpy as np
from pathlib import Path
import argparse
import time
from datetime import datetime
import pandas as pd
import json
from gestor_participantes import GestorParticipantes

# Archivo de configuración de calibración
CONFIG_CALIBRACION_PATH = Path(__file__).parent / "config_calibracion.json"


def cargar_config_calibracion():
    """Carga la configuración desde el archivo JSON de calibración."""
    defaults = {
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
    if CONFIG_CALIBRACION_PATH.exists():
        try:
            with open(CONFIG_CALIBRACION_PATH, 'r', encoding='utf-8') as f:
                config = json.load(f)
                # Merge con defaults (por si faltan claves)
                for key, value in defaults.items():
                    if key not in config:
                        config[key] = value
                return config
        except Exception as e:
            print(f"[WARN] Error cargando config_calibracion.json: {e}")
    return defaults


class Config:
    # Cargar configuración desde archivo JSON
    _calibracion = cargar_config_calibracion()
    
    # Modelos
    RBNR_CFG = "weights-classes/RBNR_custom-yolov4-tiny-detector.cfg"
    RBNR_WEIGHTS = "weights-classes/RBNR_custom-yolov4-tiny-detector_best.weights"
    RBNR_NAMES = "weights-classes/RBRN_obj.names"

    SVHN_CFG = "weights-classes/SVHN_custom-yolov4-tiny-detector.cfg"
    SVHN_WEIGHTS = "weights-classes/SVHN_custom-yolov4-tiny-detector_best.weights"
    SVHN_NAMES = "weights-classes/SVHN_obj.names"

    # Tamaños de entrada
    INPUT_SIZE_RBNR = 416
    INPUT_SIZE_SVHN = 416

    # Umbrales (desde calibración o defaults)
    CONF_RBNR = _calibracion.get("conf_rbnr", 0.3)
    CONF_SVHN = _calibracion.get("conf_svhn", 0.25)
    NMS_THRESHOLD = 0.4

    # Parámetros para filtrado y aceptación de números
    # Confianza mínima por dígito (0..1) para considerarlo en el agrupamiento
    CONF_SVHN_MIN_DIGIT = _calibracion.get("conf_svhn_min_digit", 0.80)
    # Confianza promedio mínima del cluster aceptado
    CONF_SVHN_AVG_MIN = _calibracion.get("conf_svhn_avg_min", 0.90)
    # Proporción mínima del ancho del bib que debe cubrir el cluster de dígitos
    MIN_DIGITS_WIDTH_RATIO = 0.30
    # Proporción mínima de solapamiento vertical entre cluster de dígitos y el bib
    MIN_VERTICAL_OVERLAP_RATIO = 0.6
    # Número mínimo de dígitos que debe tener el dorsal para ser considerado válido
    MIN_DIGITS_COUNT = _calibracion.get("min_digits_count", 3)
    # Número máximo de dígitos (para filtrar ruido)
    MAX_DIGITS_COUNT = _calibracion.get("max_digits_count", 4)
    
    # Debounce: no registrar el mismo dorsal más de una vez en este número de segundos
    # NOTA: Dorsales DIFERENTES se detectan inmediatamente sin espera
    DEBOUNCE_SECONDS = _calibracion.get("debounce_seconds", 2.0)
    
    # Configuración de cámara
    CAMARA_INDEX = _calibracion.get("camara_index", 0)
    RESOLUCION = _calibracion.get("resolucion", "1280x720")

    # Colores
    COLOR_BIB = (0, 255, 0)
    COLOR_DIGIT = (0, 165, 255)
    
    @classmethod
    def recargar(cls):
        """Recarga la configuración desde el archivo JSON."""
        cls._calibracion = cargar_config_calibracion()
        cls.CONF_RBNR = cls._calibracion.get("conf_rbnr", 0.3)
        cls.CONF_SVHN = cls._calibracion.get("conf_svhn", 0.25)
        cls.CONF_SVHN_MIN_DIGIT = cls._calibracion.get("conf_svhn_min_digit", 0.80)
        cls.CONF_SVHN_AVG_MIN = cls._calibracion.get("conf_svhn_avg_min", 0.90)
        cls.MIN_DIGITS_COUNT = cls._calibracion.get("min_digits_count", 3)
        cls.MAX_DIGITS_COUNT = cls._calibracion.get("max_digits_count", 4)
        cls.DEBOUNCE_SECONDS = cls._calibracion.get("debounce_seconds", 2.0)
        cls.CAMARA_INDEX = cls._calibracion.get("camara_index", 0)
        cls.RESOLUCION = cls._calibracion.get("resolucion", "1280x720")
        print(f"[INFO] Configuración recargada: debounce={cls.DEBOUNCE_SECONDS}s, "
              f"conf_rbnr={cls.CONF_RBNR}, conf_svhn={cls.CONF_SVHN}")


def _load_net(cfg_path, weights_path):
    cfg = Path(cfg_path)
    weights = Path(weights_path)
    if not cfg.exists():
        raise FileNotFoundError(f"CFG no encontrado: {cfg}")
    if not weights.exists():
        raise FileNotFoundError(f"Weights no encontrado: {weights}")

    net = cv2.dnn.readNetFromDarknet(str(cfg), str(weights))
    net.setPreferableBackend(cv2.dnn.DNN_BACKEND_OPENCV)
    net.setPreferableTarget(cv2.dnn.DNN_TARGET_CPU)

    layer_names = net.getLayerNames()
    unconnected = net.getUnconnectedOutLayers()
    # Compatibilidad con diferentes formatos
    if isinstance(unconnected, np.ndarray):
        if len(unconnected.shape) == 1:
            output_layers = [layer_names[i - 1] for i in unconnected]
        else:
            output_layers = [layer_names[i[0] - 1] for i in unconnected]
    else:
        output_layers = [layer_names[i - 1] for i in unconnected]

    return net, output_layers


def _load_names(names_path):
    p = Path(names_path)
    if not p.exists():
        raise FileNotFoundError(f"Names no encontrado: {p}")
    with open(p, 'r', encoding='utf-8') as f:
        return [line.strip() for line in f.readlines() if line.strip()]


def detect_with_net(net, output_layers, frame, input_size, conf_threshold):
    h, w = frame.shape[:2]
    blob = cv2.dnn.blobFromImage(frame, 1/255.0, (input_size, input_size), swapRB=True, crop=False)
    net.setInput(blob)
    outputs = net.forward(output_layers)

    boxes = []
    confidences = []
    class_ids = []

    for output in outputs:
        for detection in output:
            objectness = float(detection[4])
            scores = detection[5:]
            if len(scores) == 0:
                continue
            class_id = int(np.argmax(scores))
            class_score = float(scores[class_id])
            confidence = objectness * class_score

            if confidence > conf_threshold:
                center_x = int(detection[0] * w)
                center_y = int(detection[1] * h)
                bw = int(detection[2] * w)
                bh = int(detection[3] * h)
                x = int(center_x - bw / 2)
                y = int(center_y - bh / 2)
                boxes.append([x, y, bw, bh])
                confidences.append(float(confidence))
                class_ids.append(class_id)

    indices = cv2.dnn.NMSBoxes(boxes, confidences, conf_threshold, Config.NMS_THRESHOLD)
    detections = []
    if len(indices) > 0:
        for i in indices.flatten():
            detections.append({
                'bbox': boxes[i],
                'confidence': confidences[i],
                'class_id': class_ids[i]
            })
    return detections


def clamp(x, a, b):
    return max(a, min(b, x))


# Cache de registros recientes para debounce: dorsal_str -> timestamp (seconds)
recent_registrations = {}

# Set de dorsales ya registrados en esta sesión (evita duplicados)
dorsales_registrados_sesion = set()


def should_register(dorsal_str: str) -> bool:
    """Devuelve True si el dorsal puede registrarse.
    
    Un dorsal solo se registra UNA VEZ por sesión/carrera.
    El debounce solo evita detecciones rápidas del mismo frame.
    """
    # PRIMERO: Verificar si ya fue registrado en esta sesión
    if dorsal_str in dorsales_registrados_sesion:
        return False
    
    # SEGUNDO: Debounce temporal para evitar múltiples detecciones rápidas
    now_ts = time.time()
    last = recent_registrations.get(dorsal_str)
    if last is None:
        recent_registrations[dorsal_str] = now_ts
        dorsales_registrados_sesion.add(dorsal_str)
        return True
    if now_ts - last >= Config.DEBOUNCE_SECONDS:
        recent_registrations[dorsal_str] = now_ts
        dorsales_registrados_sesion.add(dorsal_str)
        return True
    return False


def reset_registros():
    """Reinicia los registros para una nueva carrera/sesión."""
    global recent_registrations, dorsales_registrados_sesion
    recent_registrations = {}
    dorsales_registrados_sesion = set()


def process_image(image_path, net_bib, layers_bib, names_bib, net_svhn, layers_svhn, names_svhn, conf_bib, conf_svhn, show_window=True):
    img = cv2.imread(str(image_path))
    if img is None:
        raise FileNotFoundError(f"No se pudo leer la imagen: {image_path}")

    orig = img.copy()
    detections_bib = detect_with_net(net_bib, layers_bib, img, Config.INPUT_SIZE_RBNR, conf_bib)

    results = []

    for det in detections_bib:
        x, y, w, h = det['bbox']
        # ajustar límites
        x1 = clamp(x, 0, img.shape[1] - 1)
        y1 = clamp(y, 0, img.shape[0] - 1)
        x2 = clamp(x + w, 0, img.shape[1] - 1)
        y2 = clamp(y + h, 0, img.shape[0] - 1)

        # añadir pequeño padding
        pad_x = int(0.04 * (x2 - x1))
        pad_y = int(0.05 * (y2 - y1))
        x1p = clamp(x1 - pad_x, 0, img.shape[1] - 1)
        y1p = clamp(y1 - pad_y, 0, img.shape[0] - 1)
        x2p = clamp(x2 + pad_x, 0, img.shape[1] - 1)
        y2p = clamp(y2 + pad_y, 0, img.shape[0] - 1)

        roi = orig[y1p:y2p, x1p:x2p]
        if roi.size == 0:
            continue

        # Detectar dígitos en la ROI con el detector SVHN
        det_digits = detect_with_net(net_svhn, layers_svhn, roi, Config.INPUT_SIZE_SVHN, conf_svhn)

        digits = []
        for d in det_digits:
            dx, dy, dw, dh = d['bbox']
            # convertir coordenadas a las de la imagen original
            abs_x = x1p + dx
            abs_y = y1p + dy
            digits.append({
                'bbox': [abs_x, abs_y, dw, dh],
                'confidence': d['confidence'],
                'class_id': d['class_id']
            })

        # Filtrar dígitos por confianza individual
        digits_filtered = [d for d in digits if d['confidence'] >= Config.CONF_SVHN_MIN_DIGIT]

        numero = ''
        accepted = False
        if len(digits_filtered) > 0:
            # calcular centro x para clustering
            for d in digits_filtered:
                bx, by, bw, bh = d['bbox']
                d['center_x'] = bx + bw / 2

            digits_sorted = sorted(digits_filtered, key=lambda dd: dd['center_x'])
            widths = [d['bbox'][2] for d in digits_sorted]
            mean_w = float(np.mean(widths)) if len(widths) > 0 else 0

            # crear clusters simples por gap
            clusters = []
            current = [digits_sorted[0]]
            for i in range(1, len(digits_sorted)):
                gap = digits_sorted[i]['center_x'] - digits_sorted[i-1]['center_x']
                if gap > max(mean_w * 1.5, mean_w + 10):
                    clusters.append(current)
                    current = [digits_sorted[i]]
                else:
                    current.append(digits_sorted[i])
            clusters.append(current)

            # evaluar clusters y escoger mejor
            best_score = -1
            best_cluster = None
            bib_width = (x2 - x1) if (x2 - x1) > 0 else 1
            for cl in clusters:
                confidences = [c['confidence'] for c in cl]
                avg_conf = float(np.mean(confidences))
                minx = min([c['bbox'][0] for c in cl])
                maxx = max([c['bbox'][0] + c['bbox'][2] for c in cl])
                cluster_w = maxx - minx
                width_ratio = cluster_w / bib_width
                score = avg_conf * len(cl) * width_ratio
                if score > best_score:
                    best_score = score
                    best_cluster = {'cluster': cl, 'avg_conf': avg_conf, 'width_ratio': width_ratio}

            if best_cluster is not None:
                # Validar cantidad de dígitos en el cluster
                num_digits = len(best_cluster['cluster'])
                if (best_cluster['avg_conf'] >= Config.CONF_SVHN_AVG_MIN and 
                    best_cluster['width_ratio'] >= Config.MIN_DIGITS_WIDTH_RATIO and
                    Config.MIN_DIGITS_COUNT <= num_digits <= Config.MAX_DIGITS_COUNT):
                    # comprobar solapamiento vertical entre cluster y bib
                    miny = min([c['bbox'][1] for c in best_cluster['cluster']])
                    maxy = max([c['bbox'][1] + c['bbox'][3] for c in best_cluster['cluster']])
                    cluster_h = maxy - miny
                    bib_h = y2 - y1 if (y2 - y1) > 0 else 1
                    vert_overlap = cluster_h / bib_h
                    if vert_overlap >= Config.MIN_VERTICAL_OVERLAP_RATIO:
                        chars = []
                        for dd in sorted(best_cluster['cluster'], key=lambda dd: dd['bbox'][0]):
                            cls = names_svhn[dd['class_id']] if dd['class_id'] < len(names_svhn) else str(dd['class_id'])
                            chars.append(cls)
                        numero = ''.join(chars)
                        accepted = True

        # Dibujar bbox del bib
        cv2.rectangle(img, (x1, y1), (x2, y2), Config.COLOR_BIB, 2)
        # Dibujar número compuesto arriba del bbox (si existe)
        if numero:
            cv2.putText(img, numero, (x1, max(16, y1 - 20)), cv2.FONT_HERSHEY_SIMPLEX, 0.9, Config.COLOR_BIB, 3)
        else:
            cv2.putText(img, f"bib {det['confidence']:.2f}", (x1, y1 - 6), cv2.FONT_HERSHEY_SIMPLEX, 0.6, Config.COLOR_BIB, 2)

        # Dibujar dígitos detectados (opcional, mantiene los rectángulos individuales)
        for dd in digits:
            dx, dy, dw, dh = dd['bbox']
            cls = names_svhn[dd['class_id']] if dd['class_id'] < len(names_svhn) else str(dd['class_id'])
            cv2.rectangle(img, (dx, dy), (dx + dw, dy + dh), Config.COLOR_DIGIT, 2)
            cv2.putText(img, f"{cls}", (dx, dy - 6), cv2.FONT_HERSHEY_SIMPLEX, 0.7, Config.COLOR_DIGIT, 2)

        results.append({'bib_bbox': [x1, y1, x2 - x1, y2 - y1], 'digits': digits, 'number': numero if accepted else ''})
        # Registrar en Excel si hay número aceptado y pasa debounce
        if numero and accepted:
            dorsal_str = str(numero).strip()
            if should_register(dorsal_str):
                try:
                    # Buscar participante en la base de datos
                    participante = buscar_participante_por_dorsal(dorsal_str)
                    if participante:
                        nombre_completo = f"{participante.get('nombre', '')} {participante.get('apellido', '')}"
                        print(f"[✅ DETECTADO] Dorsal {dorsal_str} - {nombre_completo}")
                    else:
                        print(f"[⚠️ DETECTADO] Dorsal {dorsal_str} - No encontrado en base de datos")
                    
                    out_excel = Path('registros_dorsales.xlsx')
                    added_row = ensure_excel_and_append(dorsal_str, out_excel, participante)
                    if added_row is not None:
                        print(f"[REGISTRO] Añadida fila: {added_row}")
                except Exception as e:
                    print(f"[X] Error registrando en Excel: {e}")

    # Guardar resultado
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    out_path = output_dir / f"pipeline_result_{timestamp}.jpg"
    cv2.imwrite(str(out_path), img)

    if show_window:
        cv2.imshow('Bib + SVHN detections', img)
        print('\nPresiona cualquier tecla para cerrar...')
        cv2.waitKey(0)
        cv2.destroyAllWindows()

    return str(out_path), results


# Instancia global del gestor de participantes
gestor_participantes = GestorParticipantes()


def buscar_participante_por_dorsal(dorsal_str: str):
    """
    Busca un participante en la base de datos por su número de dorsal.
    
    Args:
        dorsal_str: Número de dorsal como string
        
    Returns:
        dict o None: Datos del participante si existe
    """
    try:
        participante = gestor_participantes.buscar_por_dorsal(dorsal_str)
        return participante
    except Exception as e:
        print(f"[!] Error buscando participante: {e}")
        return None


def ensure_excel_and_append(dorsal, excel_path: Path, participante_info: dict = None):
    """Asegura que el archivo Excel existe y añade una fila con datos del corredor.
    Si el dorsal ya está registrado, no lo duplica y devuelve None.
    Devuelve la fila añadida como dict si se añadió.
    
    Args:
        dorsal: Número de dorsal detectado
        excel_path: Ruta al archivo Excel de registros
        participante_info: Diccionario con datos del participante (opcional)
    """
    excel_path = Path(excel_path)
    columnas = ['Posición', 'Dorsal', 'Nombre', 'Apellido', 'HoraLlegada', 'Estado']
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    if excel_path.exists():
        # leer existing
        try:
            df = pd.read_excel(excel_path)
            # Asegurar que tiene todas las columnas necesarias
            for col in columnas:
                if col not in df.columns:
                    df[col] = ''
        except Exception:
            # si hay problema leyendo, crear nuevo
            df = pd.DataFrame(columns=columnas)
    else:
        df = pd.DataFrame(columns=columnas)

    # Comprobar duplicado por dorsal (comparar como str para normalizar)
    dorsal_str = str(dorsal).strip()
    if 'Dorsal' in df.columns and dorsal_str in df['Dorsal'].astype(str).str.strip().values:
        return None

    # Determinar posición
    if 'Posición' in df.columns and pd.api.types.is_numeric_dtype(df['Posición']):
        try:
            maxpos = int(pd.to_numeric(df['Posición'], errors='coerce').max())
            posicion = maxpos + 1 if not np.isnan(maxpos) else 1
        except Exception:
            posicion = len(df) + 1
    else:
        posicion = len(df) + 1

    # Construir fila con información del participante
    if participante_info:
        nueva = {
            'Posición': posicion, 
            'Dorsal': dorsal_str, 
            'Nombre': participante_info.get('nombre', 'Desconocido'),
            'Apellido': participante_info.get('apellido', ''),
            'HoraLlegada': now,
            'Estado': '✅ Registrado'
        }
    else:
        nueva = {
            'Posición': posicion, 
            'Dorsal': dorsal_str, 
            'Nombre': '⚠️ No encontrado',
            'Apellido': '',
            'HoraLlegada': now,
            'Estado': '⚠️ Sin datos'
        }

    # Añadir la fila usando pd.concat para compatibilidad con pandas 2.x
    new_row_df = pd.DataFrame([nueva])
    df = pd.concat([df, new_row_df], ignore_index=True)

    # Guardar
    df.to_excel(excel_path, index=False)
    return nueva


def main():
    parser = argparse.ArgumentParser(description='Pipeline: bib -> SVHN digits')
    parser.add_argument('--modo', choices=['imagen', 'camara'], default='imagen')
    parser.add_argument('--archivo', type=str, help='Ruta de imagen para modo imagen')
    parser.add_argument('--conf', type=float, default=None, help='Umbral/confianza para detección de bib (objectness*class_score)')
    parser.add_argument('--conf_svhn', type=float, default=None, help='Umbral/confianza para detección SVHN')
    parser.add_argument('--no-show', dest='show', action='store_false', help='No mostrar ventana interactiva')

    args = parser.parse_args()

    # Cargar modelos
    print('Cargando modelos...')
    net_bib, layers_bib = _load_net(Config.RBNR_CFG, Config.RBNR_WEIGHTS)
    names_bib = _load_names(Config.RBNR_NAMES)

    net_svhn, layers_svhn = _load_net(Config.SVHN_CFG, Config.SVHN_WEIGHTS)
    names_svhn = _load_names(Config.SVHN_NAMES)

    conf_bib = Config.CONF_RBNR if args.conf is None else float(args.conf)
    conf_svhn = Config.CONF_SVHN if args.conf_svhn is None else float(args.conf_svhn)

    if args.modo == 'imagen':
        if not args.archivo:
            print('[X] Modo imagen requiere --archivo')
            return
        image_path = Path(args.archivo)
        if not image_path.exists():
            print(f'[X] Imagen no encontrada: {image_path}')
            return

        print(f'Procesando imagen: {image_path}')
        out_path, results = process_image(image_path, net_bib, layers_bib, names_bib, net_svhn, layers_svhn, names_svhn, conf_bib, conf_svhn, args.show)
        print(f'Resultado guardado: {out_path}')
        print(f'Detecciones: {len(results)} bibs')
        for i, r in enumerate(results, 1):
            print(f' Bib {i}: {len(r["digits"])} dígitos')

    else:
        # Modo cámara: capturar frames y procesar en tiempo real
        print('Iniciando modo cámara. Presiona q o ESC para salir, c para capturar, espacio para pausar/reanudar.')
        
        # Usar configuración de calibración
        camara_index = Config.CAMARA_INDEX
        resolucion = Config.RESOLUCION
        try:
            res_w, res_h = map(int, resolucion.split('x'))
        except:
            res_w, res_h = 1280, 720
        
        print(f'[INFO] Usando cámara {camara_index} a {res_w}x{res_h}')
        print(f'[INFO] Debounce: {Config.DEBOUNCE_SECONDS}s (mismo dorsal), dorsales diferentes: inmediato')
        
        cap = cv2.VideoCapture(camara_index)
        if not cap.isOpened():
            print(f'[X] No se pudo abrir la cámara {camara_index}')
            return

        # configurar resolución desde calibración
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, res_w)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, res_h)

        pausado = False
        output_dir = Path('output')
        output_dir.mkdir(exist_ok=True)

        fps_buffer = []

        try:
            while True:
                if not pausado:
                    t0 = time.time()
                    ret, frame = cap.read()
                    if not ret:
                        print('[X] Error al leer frame de la cámara')
                        break

                    # detectar bibs en el frame
                    detections_bib = detect_with_net(net_bib, layers_bib, frame, Config.INPUT_SIZE_RBNR, conf_bib)

                    # para cada bib, recortar y detectar dígitos
                    for det in detections_bib:
                        x, y, w, h = det['bbox']
                        x1 = clamp(x, 0, frame.shape[1] - 1)
                        y1 = clamp(y, 0, frame.shape[0] - 1)
                        x2 = clamp(x + w, 0, frame.shape[1] - 1)
                        y2 = clamp(y + h, 0, frame.shape[0] - 1)

                        pad_x = int(0.04 * (x2 - x1))
                        pad_y = int(0.05 * (y2 - y1))
                        x1p = clamp(x1 - pad_x, 0, frame.shape[1] - 1)
                        y1p = clamp(y1 - pad_y, 0, frame.shape[0] - 1)
                        x2p = clamp(x2 + pad_x, 0, frame.shape[1] - 1)
                        y2p = clamp(y2 + pad_y, 0, frame.shape[0] - 1)

                        roi = frame[y1p:y2p, x1p:x2p]
                        if roi.size == 0:
                            continue

                        det_digits = detect_with_net(net_svhn, layers_svhn, roi, Config.INPUT_SIZE_SVHN, conf_svhn)

                        # preparar lista de dígitos absolutos
                        digits_cam = []
                        for d in det_digits:
                            dx, dy, dw, dh = d['bbox']
                            abs_x = x1p + dx
                            abs_y = y1p + dy
                            digits_cam.append({
                                'bbox': [abs_x, abs_y, dw, dh],
                                'confidence': d['confidence'],
                                'class_id': d['class_id']
                            })

                        # Filtrar por confianza y clusterizar como en el modo imagen
                        digits_cam_filtered = [d for d in digits_cam if d['confidence'] >= Config.CONF_SVHN_MIN_DIGIT]
                        numero_cam = ''
                        accepted_cam = False
                        if len(digits_cam_filtered) > 0:
                            for d in digits_cam_filtered:
                                bx, by, bw, bh = d['bbox']
                                d['center_x'] = bx + bw / 2
                            digits_sorted_cam = sorted(digits_cam_filtered, key=lambda dd: dd['center_x'])
                            widths_cam = [d['bbox'][2] for d in digits_sorted_cam]
                            mean_w_cam = float(np.mean(widths_cam)) if len(widths_cam) > 0 else 0

                            clusters_cam = []
                            current_cam = [digits_sorted_cam[0]]
                            for i in range(1, len(digits_sorted_cam)):
                                gap = digits_sorted_cam[i]['center_x'] - digits_sorted_cam[i-1]['center_x']
                                if gap > max(mean_w_cam * 1.5, mean_w_cam + 10):
                                    clusters_cam.append(current_cam)
                                    current_cam = [digits_sorted_cam[i]]
                                else:
                                    current_cam.append(digits_sorted_cam[i])
                            clusters_cam.append(current_cam)

                            best_score = -1
                            best_cluster = None
                            bib_width = (x2 - x1) if (x2 - x1) > 0 else 1
                            for cl in clusters_cam:
                                confidences = [c['confidence'] for c in cl]
                                avg_conf = float(np.mean(confidences))
                                minx = min([c['bbox'][0] for c in cl])
                                maxx = max([c['bbox'][0] + c['bbox'][2] for c in cl])
                                cluster_w = maxx - minx
                                width_ratio = cluster_w / bib_width
                                score = avg_conf * len(cl) * width_ratio
                                if score > best_score:
                                    best_score = score
                                    best_cluster = {'cluster': cl, 'avg_conf': avg_conf, 'width_ratio': width_ratio}

                            if best_cluster is not None:
                                # Validar cantidad de dígitos en el cluster
                                num_digits_cam = len(best_cluster['cluster'])
                                if (best_cluster['avg_conf'] >= Config.CONF_SVHN_AVG_MIN and 
                                    best_cluster['width_ratio'] >= Config.MIN_DIGITS_WIDTH_RATIO and
                                    Config.MIN_DIGITS_COUNT <= num_digits_cam <= Config.MAX_DIGITS_COUNT):
                                    # comprobar solapamiento vertical entre cluster y bib
                                    miny = min([c['bbox'][1] for c in best_cluster['cluster']])
                                    maxy = max([c['bbox'][1] + c['bbox'][3] for c in best_cluster['cluster']])
                                    cluster_h = maxy - miny
                                    bib_h = y2 - y1 if (y2 - y1) > 0 else 1
                                    vert_overlap = cluster_h / bib_h
                                    if vert_overlap >= Config.MIN_VERTICAL_OVERLAP_RATIO:
                                        chars_cam = []
                                        for dd in sorted(best_cluster['cluster'], key=lambda dd: dd['bbox'][0]):
                                            cls = names_svhn[dd['class_id']] if dd['class_id'] < len(names_svhn) else str(dd['class_id'])
                                            chars_cam.append(cls)
                                        numero_cam = ''.join(chars_cam)
                                        accepted_cam = True

                        # dibujar bib
                        cv2.rectangle(frame, (x1, y1), (x2, y2), Config.COLOR_BIB, 2)
                        if numero_cam and accepted_cam:
                            # Buscar participante en la base de datos
                            dorsal_str = str(numero_cam).strip()
                            participante = buscar_participante_por_dorsal(dorsal_str)
                            
                            # Mostrar número y nombre en pantalla
                            if participante:
                                nombre_completo = f"{participante.get('nombre', '')} {participante.get('apellido', '')}"
                                texto_mostrar = f"{numero_cam} - {nombre_completo}"
                                # Dibujar fondo verde para el nombre
                                (tw, th), _ = cv2.getTextSize(texto_mostrar, cv2.FONT_HERSHEY_SIMPLEX, 0.8, 2)
                                cv2.rectangle(frame, (x1, max(0, y1 - 50)), (x1 + tw + 10, y1 - 10), (0, 200, 0), -1)
                                cv2.putText(frame, texto_mostrar, (x1 + 5, max(16, y1 - 25)), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
                            else:
                                cv2.putText(frame, numero_cam, (x1, max(16, y1 - 20)), cv2.FONT_HERSHEY_SIMPLEX, 0.9, Config.COLOR_BIB, 3)
                            
                            # Registrar en Excel (modo cámara) solo si el número fue aceptado y pasa debounce
                            if should_register(dorsal_str):
                                try:
                                    if participante:
                                        nombre_completo = f"{participante.get('nombre', '')} {participante.get('apellido', '')}"
                                        print(f"[✅ DETECTADO] Dorsal {dorsal_str} - {nombre_completo}")
                                    else:
                                        print(f"[⚠️ DETECTADO] Dorsal {dorsal_str} - No encontrado en base de datos")
                                    
                                    out_excel = Path('registros_dorsales.xlsx')
                                    added = ensure_excel_and_append(dorsal_str, out_excel, participante)
                                    if added is not None:
                                        print(f"[REGISTRO] Añadida fila: {added}")
                                except Exception as e:
                                    print(f"[X] Error registrando en Excel (camara): {e}")
                        else:
                            cv2.putText(frame, f"bib {det['confidence']:.2f}", (x1, y1 - 6), cv2.FONT_HERSHEY_SIMPLEX, 0.6, Config.COLOR_BIB, 2)

                        # dibujar dígitos individuales
                        for dd in digits_cam:
                            dx, dy, dw, dh = dd['bbox']
                            cls = names_svhn[dd['class_id']] if dd['class_id'] < len(names_svhn) else str(dd['class_id'])
                            cv2.rectangle(frame, (dx, dy), (dx + dw, dy + dh), Config.COLOR_DIGIT, 2)
                            cv2.putText(frame, f"{cls}", (dx, dy - 6), cv2.FONT_HERSHEY_SIMPLEX, 0.7, Config.COLOR_DIGIT, 2)

                    # calcular FPS
                    elapsed = time.time() - t0
                    fps = 1 / elapsed if elapsed > 0 else 0
                    fps_buffer.append(fps)
                    if len(fps_buffer) > 30:
                        fps_buffer.pop(0)
                    fps_avg = sum(fps_buffer) / len(fps_buffer)

                    cv2.putText(frame, f"FPS: {fps_avg:.1f}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

                cv2.imshow('Bib + SVHN (camara)', frame)
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q') or key == 27:
                    break
                elif key == ord('c'):
                    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
                    fname = output_dir / f'captura_{ts}.jpg'
                    cv2.imwrite(str(fname), frame)
                    print(f'[✓] Captura guardada: {fname}')
                elif key == ord(' '):
                    pausado = not pausado
                    print('[*] PAUSADO' if pausado else '[*] REANUDADO')

        finally:
            cap.release()
            cv2.destroyAllWindows()


if __name__ == '__main__':
    main()
