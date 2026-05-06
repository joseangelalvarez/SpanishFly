"""
Validación del ambiente en tiempo de ejecución.
Se ejecuta al iniciar la aplicación para detectar problemas tempranamente.
"""
import sys
from typing import Optional


class EnvironmentValidationError(Exception):
    """Error de validación del ambiente."""
    pass


def validate_critical_imports() -> Optional[str]:
    """
    Valida que los imports críticos para generación de imágenes estén disponibles.
    
    Returns:
        Un mensaje de error si algo falta, None si todo está bien.
    """
    errors = []
    
    # Verificar torch
    try:
        import torch
        if not torch.cuda.is_available():
            errors.append(
                "⚠ CUDA no disponible. Se usará CPU (muy lento).\n"
                "  Para activar GPU, instala PyTorch con CUDA support ejecutando setup_persona.ps1"
            )
    except ImportError:
        errors.append(
            "✗ PyTorch no instalado.\n"
            "  Ejecuta setup_persona.ps1 en el directorio Persona para instalar dependencias."
        )
    
    # Verificar dependencias de backend sin abortar por errores de tipado/runtime.
    critical_modules = [
        ("diffusers", "diffusers library para modelos de difusión"),
        ("transformers", "transformers library para encoding de texto"),
        ("accelerate", "accelerate para optimización"),
        ("safetensors", "safetensors para cargar modelos"),
        ("PIL", "PIL para procesamiento de imágenes"),
        (
            "insightface",
            "insightface para consistencia de rostro con IP-Adapter Face (se puede instalar en runtime)",
        ),
    ]
    
    for module_name, description in critical_modules:
        try:
            __import__(module_name)
        except Exception as exc:  # noqa: BLE001
            errors.append(
                f"✗ {module_name} no disponible ({description}).\n"
                f"  Detalle: {type(exc).__name__}: {exc}\n"
                "  La aplicación puede abrir, pero la generación puede fallar en runtime."
            )
    
    if errors:
        return "\n\n".join(errors)
    
    return None


def validate_venv_activation() -> Optional[str]:
    """
    Valida que se está ejecutando dentro del venv correcto.
    
    Returns:
        Un mensaje de advertencia si se detectan problemas, None si todo está bien.
    """
    import os
    
    venv_var = os.environ.get("VIRTUAL_ENV")
    executable_path = sys.executable
    
    if "venv" not in executable_path.lower():
        if not venv_var:
            return (
                "⚠ Posible problema de activación del venv.\n"
                "  Expected: Python from Persona/venv/Scripts/python.exe\n"
                f"  Current: {executable_path}\n"
                "\n  Esto puede causar que diffusers y dependencias no se encuentren."
            )
    
    return None
