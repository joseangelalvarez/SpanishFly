#!/usr/bin/env python3
"""
Diagnóstico específico: ¿Por qué DiffusionPipeline no se carga?
"""
from pathlib import Path
import sys
import traceback

print("=" * 80)
print("DIAGNÓSTICO DETALLADO - DiffusionPipeline")
print("=" * 80)

# ─────────────────────────────────────────────────────────────────────────────
# Paso 1: Test de imports individuales
# ─────────────────────────────────────────────────────────────────────────────
print("\n[1] Testing diffusers imports individually:")

try:
    print("  Importing diffusers...", end=" ")
    import diffusers
    print("✓")
    print(f"    Version: {diffusers.__version__}")
except Exception as e:
    print(f"✗ Failed: {e}")
    traceback.print_exc()
    sys.exit(1)

try:
    print("  Importing diffusers.DiffusionPipeline...", end=" ")
    from diffusers import DiffusionPipeline
    print("✓")
except Exception as e:
    print(f"✗ Failed: {e}")
    traceback.print_exc()
    sys.exit(1)

try:
    print("  Importing diffusers.ControlNetModel...", end=" ")
    from diffusers import ControlNetModel
    print("✓")
except Exception as e:
    print(f"✗ Failed: {e}")
    traceback.print_exc()
    sys.exit(1)

try:
    print("  Importing diffusers.StableDiffusionXLControlNetPipeline...", end=" ")
    from diffusers import StableDiffusionXLControlNetPipeline
    print("✓")
except Exception as e:
    print(f"✗ Failed: {e}")
    traceback.print_exc()
    sys.exit(1)

# ─────────────────────────────────────────────────────────────────────────────
# Paso 2: Verificar dependencias de diffusers
# ─────────────────────────────────────────────────────────────────────────────
print("\n[2] Checking diffusers dependencies:")

deps = [
    "transformers",
    "accelerate",
    "safetensors",
    "torch",
    "PIL",
    "numpy",
]

for dep in deps:
    try:
        __import__(dep)
        print(f"  ✓ {dep}")
    except ImportError as e:
        print(f"  ✗ {dep}: {e}")

# ─────────────────────────────────────────────────────────────────────────────
# Paso 3: Test del código de generator.py
# ─────────────────────────────────────────────────────────────────────────────
print("\n[3] Testing generator.py import code:")

try:
    from diffusers import ControlNetModel, DiffusionPipeline, StableDiffusionXLControlNetPipeline
    print("  ✓ All imports successful")
    print(f"    DiffusionPipeline is not None: {DiffusionPipeline is not None}")
except Exception as e:
    print(f"  ✗ Import failed: {e}")
    traceback.print_exc()

# ─────────────────────────────────────────────────────────────────────────────
# Paso 4: Simulation del código actual de generator.py
# ─────────────────────────────────────────────────────────────────────────────
print("\n[4] Simulating generator.py except block:")

try:
    from diffusers import ControlNetModel, DiffusionPipeline, StableDiffusionXLControlNetPipeline
except Exception as e:
    print(f"  Exception caught: {type(e).__name__}: {e}")
    ControlNetModel = None
    DiffusionPipeline = None
    StableDiffusionXLControlNetPipeline = None

print(f"  DiffusionPipeline is None: {DiffusionPipeline is None}")
print(f"  ControlNetModel is None: {ControlNetModel is None}")
print(f"  StableDiffusionXLControlNetPipeline is None: {StableDiffusionXLControlNetPipeline is None}")

# ─────────────────────────────────────────────────────────────────────────────
# Paso 5: Verificar rutas de configuración
# ─────────────────────────────────────────────────────────────────────────────
print("\n[5] Configuration paths:")

persona_root = Path(__file__).resolve().parent
print(f"  Persona root: {persona_root}")

models_base = persona_root / "models" / "juggernaut" / "base"
print(f"  SDXL base path: {models_base}")
print(f"  Exists: {models_base.exists()}")

if models_base.exists():
    required_files = ["model_index.json", "unet", "vae", "text_encoder"]
    for f in required_files:
        fpath = models_base / f
        print(f"    {f}: {'✓' if fpath.exists() else '✗'}")

print("\n" + "=" * 80)
print("If all steps passed, the issue is not in the venv or imports.")
print("The problem may be in how the app is launched or environment variables.")
print("=" * 80)
