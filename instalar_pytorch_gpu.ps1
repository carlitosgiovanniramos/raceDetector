# ===================================================================
# INSTALACION DETECTOR CON PYTORCH + GPU
# Este script prepara todo para usar PyTorch con CUDA
# ===================================================================

Write-Host ""
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "  INSTALACION PYTORCH GPU" -ForegroundColor Cyan
Write-Host "  Detector con aceleracion CUDA" -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host ""

# Verificar que el entorno virtual este activo
if (-not $env:VIRTUAL_ENV) {
    Write-Host "[1/7] Activando entorno virtual..." -ForegroundColor Yellow
    & .\venv\Scripts\Activate.ps1
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[X] Error al activar entorno virtual" -ForegroundColor Red
        Write-Host "    Ejecuta primero: .\instalar.ps1" -ForegroundColor Yellow
        Read-Host "Presiona Enter para salir"
        exit 1
    }
    Write-Host "   OK: Entorno virtual activado" -ForegroundColor Green
} else {
    Write-Host "[1/7] Entorno virtual ya activo" -ForegroundColor Green
}

# Verificar CUDA
Write-Host ""
Write-Host "[2/7] Verificando CUDA..." -ForegroundColor Yellow
$cudaVersion = nvidia-smi 2>&1 | Select-String "CUDA Version: (\d+\.\d+)" | ForEach-Object { $_.Matches.Groups[1].Value }

if ($cudaVersion) {
    Write-Host "   OK: CUDA $cudaVersion detectado" -ForegroundColor Green
} else {
    Write-Host "   [!] ADVERTENCIA: No se detecto CUDA" -ForegroundColor Yellow
    Write-Host "       Continuando de todas formas..." -ForegroundColor Yellow
}

# Verificar PyTorch con CUDA
Write-Host ""
Write-Host "[3/7] Verificando PyTorch con CUDA..." -ForegroundColor Yellow
$torchCheck = python -c "import torch; print('OK' if torch.cuda.is_available() else 'NO')" 2>&1

if ($torchCheck -like "*OK*") {
    Write-Host "   OK: PyTorch con CUDA ya instalado y funcionando" -ForegroundColor Green
} else {
    Write-Host "   [!] PyTorch sin CUDA detectado" -ForegroundColor Yellow
    Write-Host "       Reinstalando PyTorch con soporte CUDA..." -ForegroundColor Yellow
    
    Write-Host ""
    Write-Host "   Desinstalando PyTorch actual..." -ForegroundColor Cyan
    pip uninstall -y torch torchvision torchaudio 2>$null
    
    Write-Host ""
    Write-Host "   Instalando PyTorch con CUDA 11.8..." -ForegroundColor Cyan
    pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[X] Error al instalar PyTorch" -ForegroundColor Red
        Read-Host "Presiona Enter para salir"
        exit 1
    }
    
    # Verificar de nuevo
    $torchCheck2 = python -c "import torch; print('OK' if torch.cuda.is_available() else 'NO')" 2>&1
    if ($torchCheck2 -like "*OK*") {
        Write-Host "   OK: PyTorch con CUDA instalado correctamente" -ForegroundColor Green
    } else {
        Write-Host "[X] PyTorch instalado pero CUDA no disponible" -ForegroundColor Red
        Write-Host "    Verifica tu instalacion de CUDA" -ForegroundColor Yellow
        Read-Host "Presiona Enter para salir"
        exit 1
    }
}

# Instalar dependencias adicionales
Write-Host ""
Write-Host "[4/7] Instalando dependencias para deteccion..." -ForegroundColor Yellow
Write-Host "   -> Instalando ultralytics (YOLO v8)..." -ForegroundColor Cyan
pip install ultralytics --quiet

if ($LASTEXITCODE -eq 0) {
    Write-Host "   OK: Ultralytics instalado" -ForegroundColor Green
} else {
    Write-Host "[X] Error al instalar ultralytics" -ForegroundColor Red
    Read-Host "Presiona Enter para salir"
    exit 1
}

Write-Host ""
Write-Host "   -> Instalando librerias de vision..." -ForegroundColor Cyan
pip install pillow --quiet

# Verificar OpenCV
Write-Host ""
Write-Host "[5/7] Verificando OpenCV..." -ForegroundColor Yellow
$opencvCheck = python -c "import cv2; print(cv2.__version__)" 2>&1

if ($LASTEXITCODE -eq 0) {
    Write-Host "   OK: OpenCV version $opencvCheck" -ForegroundColor Green
} else {
    Write-Host "   [!] OpenCV no encontrado, instalando..." -ForegroundColor Yellow
    pip install opencv-python opencv-contrib-python --quiet
    Write-Host "   OK: OpenCV instalado" -ForegroundColor Green
}

# Verificacion final
Write-Host ""
Write-Host "[7/7] Verificacion final..." -ForegroundColor Yellow
Write-Host ""

$verificacion = python -c @"
import torch
import cv2

print('='*60)
print('VERIFICACION DE INSTALACION')
print('='*60)
print(f'Python: OK')
print(f'PyTorch: {torch.__version__}')
print(f'CUDA disponible: {torch.cuda.is_available()}')
if torch.cuda.is_available():
    print(f'GPU: {torch.cuda.get_device_name(0)}')
    print(f'CUDA version: {torch.version.cuda}')
print(f'OpenCV: {cv2.__version__}')
print('='*60)
"@

Write-Host ""
Write-Host "================================================================" -ForegroundColor Green
Write-Host "  INSTALACION COMPLETADA" -ForegroundColor Green
Write-Host "================================================================" -ForegroundColor Green
Write-Host ""
Write-Host "Ahora puedes usar el detector con GPU:" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Camara en tiempo real:" -ForegroundColor Yellow
Write-Host "    python mi_detector_pytorch.py --modo camara" -ForegroundColor White
Write-Host ""
Write-Host "  Procesar imagen:" -ForegroundColor Yellow
Write-Host "    python mi_detector_pytorch.py --modo imagen --archivo ruta.jpg" -ForegroundColor White
Write-Host ""
Write-Host "  Forzar CPU:" -ForegroundColor Yellow
Write-Host "    python mi_detector_pytorch.py --modo camara --cpu" -ForegroundColor White
Write-Host ""
Write-Host "Archivos creados:" -ForegroundColor Cyan
Write-Host "  - mi_detector_pytorch.py (detector con GPU)" -ForegroundColor White
Write-Host ""
Write-Host "="*70 -ForegroundColor Green
Write-Host ""

Read-Host "Presiona Enter para finalizar"
