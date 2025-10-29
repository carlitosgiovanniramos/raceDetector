# Quick installation script for Windows (ASCII-only)
# Run this script after installing Python, CUDA and cuDNN

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  AUTOMATIC INSTALLATION" -ForegroundColor Cyan
Write-Host "  Bib Number Detection" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 1) Check Python
Write-Host "[1/6] Checking Python..." -ForegroundColor Yellow
$pythonVersion = python --version 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "OK: $pythonVersion found" -ForegroundColor Green
} else {
    Write-Host "ERROR: Python not found. Install from https://www.python.org" -ForegroundColor Red
    exit 1
}

# 2) Check NVIDIA GPU (optional)
Write-Host "" 
Write-Host "[2/6] Checking NVIDIA GPU..." -ForegroundColor Yellow
$nvidiaSmi = nvidia-smi 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "OK: NVIDIA GPU detected" -ForegroundColor Green
} else {
    Write-Host "WARN: nvidia-smi not found. NVIDIA drivers may be missing" -ForegroundColor Yellow
}

# 3) Create virtual environment
Write-Host "" 
Write-Host "[3/6] Creating virtual environment..." -ForegroundColor Yellow
if (Test-Path "venv") {
    Write-Host "WARN: Virtual environment already exists, skipping..." -ForegroundColor Yellow
} else {
    python -m venv venv
    if ($LASTEXITCODE -eq 0) {
        Write-Host "OK: Virtual environment created" -ForegroundColor Green
    } else {
        Write-Host "ERROR: Failed to create virtual environment" -ForegroundColor Red
        exit 1
    }
}

# 4) Activate virtual environment
Write-Host "" 
Write-Host "[4/6] Activating virtual environment..." -ForegroundColor Yellow
& ".\venv\Scripts\Activate.ps1"

# 5) Upgrade pip
Write-Host "" 
Write-Host "[5/6] Upgrading pip..." -ForegroundColor Yellow
python -m pip install --upgrade pip

# 6) Install dependencies
Write-Host "" 
Write-Host "[6/6] Installing dependencies..." -ForegroundColor Yellow
Write-Host "This may take several minutes..." -ForegroundColor Cyan

Write-Host "" 
Write-Host "  -> Installing PyTorch (CUDA wheels)..." -ForegroundColor Cyan
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Failed to install PyTorch" -ForegroundColor Red
    exit 1
}

Write-Host "" 
Write-Host "  -> Installing OpenCV..." -ForegroundColor Cyan
pip install opencv-python opencv-contrib-python
pip install openpyxl

Write-Host "" 
Write-Host "  -> Installing scientific packages..." -ForegroundColor Cyan
pip install numpy pandas scipy h5py matplotlib imgaug

Write-Host "" 
Write-Host "  -> Installing Jupyter..." -ForegroundColor Cyan
pip install jupyter notebook ipython ipykernel

Write-Host "" 
Write-Host "  -> Installing utilities..." -ForegroundColor Cyan
pip install tqdm Pillow

# Verify installation
Write-Host "" 
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  VERIFYING INSTALLATION" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

Write-Host "" 
Write-Host "Running verification script..." -ForegroundColor Yellow
$verifier = Join-Path -Path $PSScriptRoot -ChildPath 'verificar_instalacion.py'
python "$verifier"

if ($LASTEXITCODE -eq 0) {
    Write-Host "" 
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "  INSTALLATION COMPLETED" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "" 
    Write-Host "Next steps:" -ForegroundColor Cyan
    Write-Host "  1. The virtual environment is activated" -ForegroundColor White
    Write-Host "  2. Change to the notebooks folder:" -ForegroundColor White
    Write-Host "     cd notebooks+utils+data" -ForegroundColor Yellow
    Write-Host "  3. Start Jupyter Notebook:" -ForegroundColor White
    Write-Host "     jupyter notebook" -ForegroundColor Yellow
    Write-Host '  4. Open the demo notebook:' -ForegroundColor White
    Write-Host '     05 - Bib Detection Validation & Demo.ipynb' -ForegroundColor Yellow
    Write-Host "" 
} else {
    Write-Host "" 
    Write-Host "========================================" -ForegroundColor Yellow
    Write-Host "  WARNING" -ForegroundColor Yellow
    Write-Host "========================================" -ForegroundColor Yellow
    Write-Host "" 
    Write-Host "Installation completed with warnings." -ForegroundColor Yellow
    Write-Host "See MANUAL_INSTALACION.md for details." -ForegroundColor Yellow
    Write-Host "" 
}
