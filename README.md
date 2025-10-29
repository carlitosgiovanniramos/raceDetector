## Detector de dorsales (BibObjectDetection)

Este repositorio contiene un detector de dorsales (bib numbers) entrenado para detectar y procesar números en imágenes y vídeo. Está pensado para usarse en flujo de trabajo de detección en tiempo real (cámara) o en procesamiento por lotes.

### Qué hace

- Detecta regiones que contienen números (dorsales) en imágenes o vídeo.
- Puede ejecutarse en modo cámara para procesar secuencias en tiempo real.
- Usa un modelo YOLOv4-tiny (u otro modelo provisto en `weights-classes/`) para la detección.

### Para qué sirve

- Automatizar la lectura y registro de dorsales en carreras, entrenamientos y eventos deportivos.
- Extraer regiones con números para OCR o pasos de postprocesado.

### Archivos importantes (conservar)

- `pipeline_bib_svhn.py` — Script principal para ejecutar el pipeline (incluye la opción `--modo camara`).
- `requirements.txt` — Dependencias Python necesarias.
- `venv/` — (si usas un entorno virtual local) carpeta del entorno virtual (no versionar normalmente).
- `weights-classes/` — Modelos y archivos de configuración y clases (p. ej. `.weights`, `.cfg`, `.names`).
- `instalar.ps1` — Script de instalación principal (dependencias del proyecto).
- `instalar_pytorch_gpu.ps1` — Script para instalar PyTorch con soporte GPU (cuando aplique).
- `mi_detector.py`, `mi_detector_pytorch.py`, `mi_detector_*.py` — Detectores/ejemplos incluidos en el repo.

### Requisitos previos

- Python 3.11.9
- CUDA Toolkit (compatible con tu versión de GPU)
- CUDA cuDNN: los archivos extraídos deben integrarse en las carpetas `bin` y `lib` (u `obj` si tus instrucciones lo indican) del CUDA Toolkit. Revisa la documentación del fabricante para integrar correctamente los archivos de cuDNN.
- Drivers NVIDIA actualizados y compatibles con la versión de CUDA instalada.

Comprueba la compatibilidad de tu tarjeta gráfica con la versión de CUDA y cuDNN que vas a usar.

### Clonar el repositorio y posicionarse en la rama correcta

## Detector de dorsales (BibObjectDetection)

Este repositorio provee un pipeline para detectar dorsales (bib numbers) y extraer los dígitos contenidos en ellos. El flujo principal utiliza dos detectores YOLOv4-tiny (OpenCV DNN): uno para localizar la caja del dorsal (RBNR) y otro para detectar dígitos (SVHN) dentro de la ROI. Además hay un instalador alternativo que genera un script `mi_detector_pytorch.py` que usa PyTorch + OpenCV DNN para aceleración por GPU.

Este README documenta en detalle la estructura del proyecto, los scripts principales, cómo funciona el pipeline, los scripts de instalación (`instalar.ps1` e `instalar_pytorch_gpu.ps1`), y recomendaciones para simplificar el repositorio (respaldos y limpieza de archivos redundantes).

---

## Estructura clave del repositorio

- `pipeline_bib_svhn.py` — Pipeline principal (CPU/OpenCV DNN):
	- Detecta la caja del dorsal (RBNR) con un modelo YOLOv4-tiny.
	- Recorta la ROI del dorsal y ejecuta un segundo detector (SVHN) para detectar dígitos.
	- Agrupa dígitos por proximidad horizontal, calcula scores (promedio de confianza * número de dígitos * anchura relativa), valida clusters con umbrales configurables y registra dorsales aceptados en `registros_dorsales.xlsx`.
	- Modo imagen (procesa una imagen estática) y modo cámara (procesamiento en tiempo real, hotkeys: q/ESC salir, c capturar, espacio pausar).

- `mi_detector_pytorch.py` — Detector generado por `instalar_pytorch_gpu.ps1` (si se crea):
	- Script Python auto-generado por el instalador alternativo. Implementa una clase `DetectorPyTorch` que carga los pesos y configuraciones YOLO con OpenCV DNN y configura backend/target CUDA si hay soporte.
	- Incluye funciones para detección en cámara e imagen y comandos desde CLI (`--modo camara` / `--modo imagen --archivo ...`).

- `weights-classes/` — Modelos y archivos: `.weights`, `.cfg`, `.names` (RBNR y SVHN). Mantener estos archivos intactos.

- `instalar.ps1` — Instalador principal (Windows):
	- Crea y activa un virtualenv `venv` si no existe.
	- Instala PyTorch (wheels cu118), OpenCV, openpyxl, numpy, pandas, scipy, matplotlib, imgaug, jupyter, tqdm, Pillow, etc.
	- Ejecuta `verificar_instalacion.py` al final.

- `instalar_pytorch_gpu.ps1` — Instalador alternativo orientado a PyTorch+GPU:
	- Activa `venv` (si no activo intenta activar `.\\venv\Scripts\Activate.ps1`).
	- Intenta detectar CUDA mediante `nvidia-smi` y verifica que `torch.cuda.is_available()`.
	- Si PyTorch no tiene soporte CUDA, desinstala `torch/torchvision/torchaudio` y reinstala con `--index-url https://download.pytorch.org/whl/cu118`.
	- Instala `ultralytics` (YOLOv8) y `pillow`.
	- Verifica OpenCV e instala si falta.
	- Construye (a partir de un here-string) el archivo `mi_detector_pytorch.py` y lo escribe en la raíz del repo con `Out-File`.
	- Ejecuta una verificación final que imprime versiones e información de GPU.

---

## Cómo funciona el pipeline (detalle técnico)

1) Carga de modelos:
	 - `pipeline_bib_svhn.py` carga dos redes con `cv2.dnn.readNetFromDarknet(cfg, weights)` y fuerza backend OpenCV/CPU por defecto.
	 - Obtiene las capas de salida con `getLayerNames()` y `getUnconnectedOutLayers()` (con manejo de diferentes formatos de retorno).

2) Detección de bibs (RBNR):
	 - Para cada frame/imágen se crea un blob con `cv2.dnn.blobFromImage(..., INPUT_SIZE_RBNR)` y se ejecuta `net.forward(output_layers)`.
	 - Se calculan bounding boxes, confidencias (objectness * class_score) y se aplican NMS con `cv2.dnn.NMSBoxes`.

3) Procesado de ROI y detección de dígitos (SVHN):
	 - Cada bib detectado se recorta con un padding pequeño y se pasa al detector SVHN.
	 - Los detecciones de dígitos se filtran por confianza individual (`CONF_SVHN_MIN_DIGIT`).
	 - Se calcúan centros X y se agrupan en clusters según gaps relativos al ancho medio de dígito.
	 - Para cada cluster se calcula un score = avg_conf * num_digits * width_ratio (anchura del cluster respecto al bib).
	 - Se selecciona el mejor cluster y se valida usando umbrales: `CONF_SVHN_AVG_MIN`, `MIN_DIGITS_COUNT`, `MAX_DIGITS_COUNT`, `MIN_DIGITS_WIDTH_RATIO`, y `MIN_VERTICAL_OVERLAP_RATIO`.
	 - Si el cluster es aceptado se compone el número por orden X creciente y se marca como `accepted`.

4) Registro y debounce:
	 - Los dorsales aceptados se registran en `registros_dorsales.xlsx` mediante `ensure_excel_and_append()`.
	 - Hay un mecanismo de debounce (`DEBOUNCE_SECONDS` por dorsal) para evitar múltiples registros consecutivos del mismo dorsal.

5) Salidas y UI:
	 - El pipeline guarda una imagen de salida en `output/pipeline_result_{timestamp}.jpg` y, si se solicita, muestra una ventana interactiva con las detecciones.
	 - En modo cámara se muestran indicadores FPS, número detectado y permite capturar frames.

---

## Detalles específicos encontrados en `instalar_pytorch_gpu.ps1`

- Comprobación de entorno virtual:
	- El script comprueba la variable `$env:VIRTUAL_ENV`; si no existe intenta activar `.\\venv\Scripts\Activate.ps1`.

- Detección de CUDA:
	- Ejecuta `nvidia-smi` y extrae la `CUDA Version:` de su salida si está disponible.

- Instalación/Reinstalación de PyTorch:
	- Intenta importar `torch` en Python y comprobar `torch.cuda.is_available()`.
	- Si no detecta CUDA en PyTorch desinstala `torch torchvision torchaudio` y reinstala con `--index-url https://download.pytorch.org/whl/cu118`.
	- Verifica la instalación volviendo a comprobar `torch.cuda.is_available()`.

- Dependencias adicionales:
	- Instala `ultralytics` (YOLOv8), `pillow` y OpenCV si faltan (mediante `pip install`).

- Creación de `mi_detector_pytorch.py`:
	- El script incluye un here-string con la implementación completa del detector (clase `DetectorPyTorch`, funciones de detección y CLI) y lo escribe en la raíz como `mi_detector_pytorch.py` usando:

		```powershell
		$detectorScript | Out-File -FilePath "mi_detector_pytorch.py" -Encoding UTF8
		```

	- Después muestra mensajes con ejemplos de uso:

		```text
		python mi_detector_pytorch.py --modo camara
		python mi_detector_pytorch.py --modo imagen --archivo ruta.jpg
		```

	- Esto es la razón por la que aparece `mi_detector_pytorch.py` en el repo tras ejecutar `instalar_pytorch_gpu.ps1`.

---

## Requisitos y compatibilidades

- Recomendado: Python 3.11.9 (el proyecto fue probado con esta versión).
- CUDA Toolkit y cuDNN compatibles con la versión de PyTorch que instales (en los scripts se usa cu118 / CUDA 11.8).
- Drivers NVIDIA actualizados y `nvidia-smi` disponible para detección automática de CUDA.

Verifica que la tarjeta GPU sea compatible con CUDA 11.8. Si no tienes GPU compatible, el instalador puede instalar versiones CPU de paquetes o fallará la comprobación de CUDA.

---

## Instalación y ejecución (pasos recomendados)

1) Clonar y cambiar a la rama recomendada:

```powershell
git clone https://github.com/carlitosgiovanniramos/raceDetector.git
cd raceDetector
git branch
```

2) Instalación base (crea `venv` y depende de CUDA si está disponible):

```powershell
.\instalar.ps1
```

3) Si quieres soporte explícito de PyTorch con GPU (recomendado en equipos con CUDA compatible):

```powershell
.\instalar_pytorch_gpu.ps1
```

Notas:
- Si el entorno virtual no está activado, actívalo con:

```powershell
venv\Scripts\Activate.ps1
```

4) Ejecutar el pipeline (modo cámara):

```powershell
python pipeline_bib_svhn.py --modo camara
```

o modo imagen:

```powershell
python pipeline_bib_svhn.py --modo imagen --archivo ruta\a\imagen.jpg
```

---
