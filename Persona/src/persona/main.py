import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication, QMessageBox

from persona.config.settings import AppConfig, load_app_config
from persona.infra.gpu import evaluate_runtime_gpu
from persona.infra.validation import validate_critical_imports, validate_venv_activation
from persona.ui.main_window import MainWindow


def run() -> int:
    app = QApplication(sys.argv)

    # parents[2] desde src/persona/main.py = D:\SpanishFly\Persona
    persona_root = Path(__file__).resolve().parents[2]
    config_path = persona_root / "config_persona.json"

    # Validar ambiente antes de continuar
    venv_warning = validate_venv_activation()
    if venv_warning:
        QMessageBox.warning(None, "Advertencia de ambiente", venv_warning)
    
    import_error = validate_critical_imports()
    if import_error:
        QMessageBox.warning(
            None,
            "Advertencia de dependencias",
            "Se detectaron problemas en dependencias de backend. "
            "La aplicación continuará, pero la generación puede fallar:\n\n" + import_error,
        )

    cfg: AppConfig = load_app_config(persona_root=persona_root, config_path=config_path)
    gpu_status = evaluate_runtime_gpu()

    if not gpu_status.cuda_available:
        QMessageBox.warning(
            None,
            "CUDA no disponible",
            (
                "PyTorch no detecta CUDA. El modulo continuara en CPU, "
                "pero el rendimiento sera reducido."
            ),
        )

    window = MainWindow(config=cfg, gpu_status=gpu_status)
    window.show()
    return app.exec()
