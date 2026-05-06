#!/usr/bin/env python3
"""
Diagnostic script para SpanishFly Persona
Verifica ambiente, imports, y carga de modelos
"""
from pathlib import Path
import sys
import json

# ─────────────────────────────────────────────────────────────────────────────
# Paso 1: Verificar venv y Python
# ─────────────────────────────────────────────────────────────────────────────
print("=" * 80)
print("DIAGNÓSTICO - SpanishFly Persona")
print("=" * 80)

print("\n[1/6] Python Environment")
print(f"  Interpreter: {sys.executable}")
print(f"  Version: {sys.version}")
print(f"  Executable in venv: {'venv' in sys.executable}")

# ─────────────────────────────────────────────────────────────────────────────
# Paso 2: Verificar imports críticos
# ─────────────────────────────────────────────────────────────────────────────
print("\n[2/6] Critical Imports")

def test_import(module_name: str) -> bool:
    try:
        __import__(module_name)
        print(f"  ✓ {module_name}")
        return True
    except ImportError as e:
        print(f"  ✗ {module_name}: {e}")
        return False

imports = [
    "torch",
    "PySide6",
    "diffusers",
    "transformers",
    "accelerate",
    "safetensors",
    "huggingface_hub",
    "omegaconf",
    "PIL",
    "cv2",
    "numpy",
]

results = {}
for imp in imports:
    results[imp] = test_import(imp)

if not all(results.values()):
    print("\n  ⚠ Some imports failed. Check venv activation and requirements.txt")

# ─────────────────────────────────────────────────────────────────────────────
# Paso 3: Verificar PyTorch CUDA
# ─────────────────────────────────────────────────────────────────────────────
print("\n[3/6] PyTorch CUDA Support")
try:
    import torch
    print(f"  PyTorch version: {torch.__version__}")
    print(f"  CUDA available: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"  GPU: {torch.cuda.get_device_name(0)}")
        major, minor = torch.cuda.get_device_capability(0)
        print(f"  Compute Capability: {major}.{minor}")
except Exception as e:
    print(f"  ✗ Error: {e}")

# ─────────────────────────────────────────────────────────────────────────────
# Paso 4: Verificar archivos de configuración y modelos
# ─────────────────────────────────────────────────────────────────────────────
print("\n[4/6] Configuration & Model Files")
persona_root = Path(__file__).resolve().parent
config_path = persona_root / "config_persona.json"

print(f"  Persona root: {persona_root}")
print(f"  Config exists: {config_path.exists()}")

if config_path.exists():
    try:
        cfg = json.loads(config_path.read_text(encoding="utf-8"))
        print(f"  Config valid: ✓")
        
        # Verificar rutas de modelos
        models_cfg = cfg.get("models", {})
        sdxl_path = persona_root / models_cfg.get("sdxl_base_path", "models/sdxl/base")
        print(f"\n  SDXL base path: {sdxl_path}")
        print(f"    Exists: {sdxl_path.exists()}")
        if sdxl_path.exists():
            files = list(sdxl_path.glob("*"))
            print(f"    Files: {len(files)}")
            for f in files[:5]:
                print(f"      - {f.name}")
        
    except Exception as e:
        print(f"  Config parse error: {e}")

# ─────────────────────────────────────────────────────────────────────────────
# Paso 5: Probar carga de modelos sin UI
# ─────────────────────────────────────────────────────────────────────────────
print("\n[5/6] Model Loading Test")

try:
    from diffusers import DiffusionPipeline
    print("  DiffusionPipeline imported ✓")
    
    sdxl_path = persona_root / "models" / "juggernaut" / "base"
    if sdxl_path.exists():
        print(f"  Attempting to load model from: {sdxl_path}")
        print("  (This may take 30-60 seconds on first load...)")
        
        try:
            # Prueba sin cargar completamente en memoria
            pipeline = DiffusionPipeline.from_pretrained(
                str(sdxl_path),
                torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
                local_files_only=True,
            )
            print("  ✓ Model loaded successfully")
            print(f"  Pipeline type: {type(pipeline).__name__}")
        except Exception as e:
            print(f"  ✗ Model loading failed: {e}")
            import traceback
            traceback.print_exc()
    else:
        print(f"  ✗ Model path does not exist: {sdxl_path}")
        
except Exception as e:
    print(f"  ✗ Error: {e}")
    import traceback
    traceback.print_exc()

# ─────────────────────────────────────────────────────────────────────────────
# Paso 6: Resumen
# ─────────────────────────────────────────────────────────────────────────────
print("\n[6/6] Summary")
print("=" * 80)

if all(results.values()):
    print("✓ All imports successful")
else:
    failed = [k for k, v in results.items() if not v]
    print(f"✗ Failed imports: {', '.join(failed)}")
    print("  ACTION: Run 'pip install -r requirements.txt' in the venv")

print("\nNext steps:")
print("  1. If all tests pass, run: python run_persona.py")
print("  2. If imports fail, check venv activation")
print("  3. If model loading fails, verify model files exist")

print("\n" + "=" * 80)
