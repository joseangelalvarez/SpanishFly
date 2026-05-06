#!/usr/bin/env python3
"""
Check if the venv is properly activated and all dependencies are accessible
"""
import sys
import os
from pathlib import Path

print("=" * 80)
print("VENV ACTIVATION CHECK")
print("=" * 80)

print("\n[1] Python Interpreter:")
print(f"  sys.executable: {sys.executable}")
print(f"  In venv: {'venv' in sys.executable or 'VIRTUAL_ENV' in os.environ}")

print("\n[2] Environment Variables:")
print(f"  VIRTUAL_ENV: {os.environ.get('VIRTUAL_ENV', 'NOT SET')}")
print(f"  PYTHONPATH: {os.environ.get('PYTHONPATH', 'NOT SET')}")
print(f"  PATH: {os.environ.get('PATH', 'NOT SET')[:100]}...")

print("\n[3] sys.path:")
for i, p in enumerate(sys.path[:5]):
    print(f"  [{i}] {p}")

print("\n[4] Checking if modules are in sys.path:")
venv_path = Path(sys.executable).parents[1]
site_packages = venv_path / "Lib" / "site-packages"
print(f"  Expected site-packages: {site_packages}")
print(f"  In sys.path: {str(site_packages) in sys.path}")

print("\n[5] Testing import of key packages:")
packages = ["torch", "diffusers", "transformers", "PySide6"]
for pkg in packages:
    try:
        mod = __import__(pkg)
        path = getattr(mod, "__file__", "builtin")
        print(f"  ✓ {pkg}")
        print(f"    Location: {path}")
    except ImportError as e:
        print(f"  ✗ {pkg}: {e}")

print("\n" + "=" * 80)
