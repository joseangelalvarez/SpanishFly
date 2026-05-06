"""
SpanishFly – Lanzador Principal
Ventana de inicio con tarjetas de módulos, diseño moderno oscuro.
"""
from __future__ import annotations

import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

from PySide6.QtCore import (
    QEasingCurve,
    QPoint,
    QPropertyAnimation,
    QRect,
    Signal,
    QSize,
    Qt,
    QTimer,
)
from PySide6.QtGui import (
    QColor,
    QFont,
    QFontDatabase,
    QIcon,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPen,
    QPixmap,
)
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSpacerItem,
    QVBoxLayout,
    QWidget,
)

from bootstrap_module_env import BootstrapError, ensure_module_environment

ROOT = Path(__file__).resolve().parent

# ──────────────────────────────────────────────────────────────────────────────
# Paleta de colores
# ──────────────────────────────────────────────────────────────────────────────
C_BG        = "#0b0c10"
C_SURFACE   = "#13141a"
C_CARD      = "#1a1b24"
C_CARD_HOV  = "#22233a"
C_BORDER    = "#2a2b40"
C_ACCENT1   = "#7c6af7"   # violeta principal
C_ACCENT2   = "#5c9cff"   # azul secundario
C_ACCENT3   = "#f76c8f"   # rosa para estado "próximamente"
C_TEXT_PRI  = "#e8e9f3"
C_TEXT_SEC  = "#8889aa"
C_TEXT_DIM  = "#44455a"
C_SUCCESS   = "#4ade80"
C_WARN      = "#f59e0b"


# ──────────────────────────────────────────────────────────────────────────────
# Definición de módulos
# ──────────────────────────────────────────────────────────────────────────────
@dataclass
class ModuleInfo:
    key:         str
    title:       str
    subtitle:    str
    description: str
    icon:        str          # emoji / unicode símbolo
    gradient:    tuple[str, str]
    available:   bool = True
    launch_fn:   object = None
    tags:        list[str] = field(default_factory=list)


def _launch_persona():
    """Lanza el módulo Persona en un proceso independiente."""
    import os

    persona_root = ROOT / "Persona"
    persona_py = persona_root / "run_persona.py"

    active_window = QApplication.activeWindow()
    try:
        env_info = ensure_module_environment("persona")
    except BootstrapError as exc:
        QMessageBox.critical(
            active_window,
            "Error preparando entorno Persona",
            str(exc),
        )
        return None

    interpreter = env_info.python_executable
    venv_dir = Path(env_info.venv_dir)
    
    # Preparar el entorno heredando el existente
    full_env = os.environ.copy()
    
    # Configurar PYTHONPATH para que encuentre el módulo persona
    full_env["PYTHONPATH"] = str(persona_root / "src")
    
    # Si se está usando el venv, establecer VIRTUAL_ENV
    if venv_dir.exists():
        full_env["VIRTUAL_ENV"] = str(venv_dir)
    
    # Ejecutar en el directorio de Persona para mejor resolución de rutas relativas
    return subprocess.Popen(
        [interpreter, str(persona_py)],
        env=full_env,
        cwd=str(persona_root),
    )


MODULES: list[ModuleInfo] = [
    ModuleInfo(
        key="persona",
        title="Persona",
        subtitle="Generador de personajes",
        description=(
            "Crea y gestiona personajes visuales únicos usando SDXL, "
            "ControlNet e IP-Adapters. Genera retratos de alta calidad "
            "directamente desde tu GPU con modelos 100 % locales."
        ),
        icon="🎭",
        gradient=(C_ACCENT1, C_ACCENT2),
        available=True,
        launch_fn=_launch_persona,
        tags=["SDXL", "ControlNet", "IP-Adapter", "CUDA"],
    ),
    ModuleInfo(
        key="video",
        title="Video",
        subtitle="Animación de personajes",
        description=(
            "Anima tus personajes y genera secuencias de vídeo fluidas "
            "a partir de imágenes base, prompts de movimiento y guías "
            "de pose. Integración con modelos de difusión de vídeo."
        ),
        icon="🎬",
        gradient=(C_ACCENT2, "#38bdf8"),
        available=False,
        tags=["AnimateDiff", "SVD", "MotionLora"],
    ),
    ModuleInfo(
        key="storyboard",
        title="Storyboard",
        subtitle="Narración visual",
        description=(
            "Convierte guiones en storyboards visuales de forma automática. "
            "Define escenas, ángulos de cámara y transiciones. Exporta "
            "como PDF o secuencia de imágenes listo para producción."
        ),
        icon="📋",
        gradient=("#a78bfa", C_ACCENT3),
        available=False,
        tags=["Guion", "Escenas", "PDF Export"],
    ),
    ModuleInfo(
        key="voice",
        title="Voz",
        subtitle="Síntesis de voz",
        description=(
            "Genera voces realistas para tus personajes usando modelos TTS "
            "locales. Clona voces, ajusta tono y cadencia, y exporta audio "
            "sincronizado con las animaciones."
        ),
        icon="🎙️",
        gradient=(C_ACCENT3, C_WARN),
        available=False,
        tags=["TTS", "Voice Clone", "Audio"],
    ),
]


# ──────────────────────────────────────────────────────────────────────────────
# Widget: tarjeta de módulo
# ──────────────────────────────────────────────────────────────────────────────
class ModuleCard(QFrame):
    launch_requested = Signal(str)

    def __init__(self, info: ModuleInfo, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._info   = info
        self._hovered = False
        self.setObjectName("ModuleCard")
        self.setMinimumSize(320, 260)
        self.setMaximumSize(380, 320)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setCursor(
            Qt.CursorShape.PointingHandCursor if info.available
            else Qt.CursorShape.ArrowCursor
        )
        self._setup_shadow()
        self._build_ui()

    def _setup_shadow(self) -> None:
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(28)
        shadow.setOffset(0, 6)
        shadow.setColor(QColor(0, 0, 0, 140))
        self.setGraphicsEffect(shadow)

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 24, 24, 20)
        root.setSpacing(12)

        # ── Cabecera: icono + badge ──────────────────────────────────────────
        header = QHBoxLayout()
        header.setSpacing(0)

        icon_lbl = QLabel(self._info.icon)
        icon_lbl.setFont(QFont("Segoe UI Emoji", 32))
        icon_lbl.setFixedSize(56, 56)
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_lbl.setStyleSheet(
            f"background: qlineargradient("
            f"x1:0, y1:0, x2:1, y2:1, "
            f"stop:0 {self._info.gradient[0]}33, "
            f"stop:1 {self._info.gradient[1]}33);"
            f"border-radius: 14px;"
        )
        header.addWidget(icon_lbl)
        header.addStretch()

        badge_text  = "● Disponible" if self._info.available else "◌ Próximamente"
        badge_color = C_SUCCESS if self._info.available else C_ACCENT3
        badge = QLabel(badge_text)
        badge.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        badge.setStyleSheet(
            f"color: {badge_color}; font-size: 11px; font-weight: 600;"
            f"background: {badge_color}22; border-radius: 8px;"
            f"padding: 3px 10px;"
        )
        header.addWidget(badge)
        root.addLayout(header)

        # ── Título + subtítulo ───────────────────────────────────────────────
        title = QLabel(self._info.title)
        title.setStyleSheet(
            f"color: {C_TEXT_PRI}; font-size: 20px; font-weight: 700; letter-spacing: 0.5px;"
        )
        root.addWidget(title)

        subtitle = QLabel(self._info.subtitle)
        subtitle.setStyleSheet(
            f"color: {self._info.gradient[0]}; font-size: 12px; font-weight: 500;"
        )
        root.addWidget(subtitle)

        # ── Descripción ──────────────────────────────────────────────────────
        desc = QLabel(self._info.description)
        desc.setWordWrap(True)
        desc.setStyleSheet(
            f"color: {C_TEXT_SEC}; font-size: 12px; line-height: 1.6;"
        )
        desc.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        root.addWidget(desc)
        root.addStretch()

        # ── Tags ─────────────────────────────────────────────────────────────
        tags_row = QHBoxLayout()
        tags_row.setSpacing(6)
        for tag in self._info.tags[:3]:
            t = QLabel(tag)
            t.setStyleSheet(
                f"color: {C_TEXT_DIM}; font-size: 10px; font-weight: 600;"
                f"background: {C_BORDER}; border-radius: 5px; padding: 2px 7px;"
            )
            tags_row.addWidget(t)
        tags_row.addStretch()
        root.addLayout(tags_row)

        # ── Botón ────────────────────────────────────────────────────────────
        btn_text = "Abrir módulo →" if self._info.available else "Próximamente"
        btn = QPushButton(btn_text)
        btn.setEnabled(self._info.available)
        btn.setCursor(
            Qt.CursorShape.PointingHandCursor if self._info.available
            else Qt.CursorShape.ArrowCursor
        )
        g0, g1 = self._info.gradient
        if self._info.available:
            btn.setStyleSheet(
                f"QPushButton {{"
                f"  background: qlineargradient(x1:0,y1:0,x2:1,y2:0,"
                f"    stop:0 {g0}, stop:1 {g1});"
                f"  color: #ffffff; font-size: 13px; font-weight: 700;"
                f"  border: none; border-radius: 10px; padding: 10px 20px;"
                f"}}"
                f"QPushButton:hover {{"
                f"  background: qlineargradient(x1:0,y1:0,x2:1,y2:0,"
                f"    stop:0 {g1}, stop:1 {g0});"
                f"}}"
                f"QPushButton:pressed {{ opacity: 0.85; }}"
            )
            btn.clicked.connect(self._emit_launch_requested)
        else:
            btn.setStyleSheet(
                f"QPushButton {{"
                f"  background: {C_BORDER}; color: {C_TEXT_DIM};"
                f"  font-size: 13px; font-weight: 600;"
                f"  border: none; border-radius: 10px; padding: 10px 20px;"
                f"}}"
            )
        root.addWidget(btn)

    def _emit_launch_requested(self) -> None:
        self.launch_requested.emit(self._info.key)

    # ── Hover ────────────────────────────────────────────────────────────────
    def enterEvent(self, event) -> None:
        self._hovered = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:
        self._hovered = False
        self.update()
        super().leaveEvent(event)

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = self.rect().adjusted(1, 1, -1, -1)
        path = QPainterPath()
        path.addRoundedRect(rect, 16, 16)

        # Fondo
        painter.fillPath(path, QColor(C_CARD_HOV if self._hovered else C_CARD))

        # Borde con gradiente de acento cuando hay hover
        if self._hovered:
            pen_color = QColor(self._info.gradient[0])
            pen_color.setAlphaF(0.7)
        else:
            pen_color = QColor(C_BORDER)

        pen = QPen(pen_color, 1.5)
        painter.setPen(pen)
        painter.drawPath(path)

        # Barra de color superior
        bar = QPainterPath()
        bar.addRoundedRect(rect.x(), rect.y(), rect.width(), 3, 1.5, 1.5)
        grad = QLinearGradient(0, 0, rect.width(), 0)
        grad.setColorAt(0, QColor(self._info.gradient[0]))
        grad.setColorAt(1, QColor(self._info.gradient[1]))
        painter.fillPath(bar, grad)


# ──────────────────────────────────────────────────────────────────────────────
# Widget: encabezado
# ──────────────────────────────────────────────────────────────────────────────
class AppHeader(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFixedHeight(110)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 24, 40, 16)
        layout.setSpacing(4)

        title = QLabel("SpanishFly")
        title.setStyleSheet(
            f"color: {C_TEXT_PRI}; font-size: 32px; font-weight: 800;"
            f"letter-spacing: 2px;"
        )
        layout.addWidget(title)

        subtitle = QLabel("Plataforma de producción audiovisual con IA local")
        subtitle.setStyleSheet(
            f"color: {C_TEXT_SEC}; font-size: 13px; font-weight: 400;"
        )
        layout.addWidget(subtitle)

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Línea de separación inferior con gradiente
        y = self.height() - 1
        grad = QLinearGradient(0, y, self.width(), y)
        grad.setColorAt(0.0, QColor(C_ACCENT1))
        grad.setColorAt(0.5, QColor(C_ACCENT2))
        grad.setColorAt(1.0, QColor(C_ACCENT1 + "00"))
        pen = QPen()
        pen.setBrush(grad)
        pen.setWidthF(1.5)
        painter.setPen(pen)
        painter.drawLine(40, y, self.width() - 40, y)


# ──────────────────────────────────────────────────────────────────────────────
# Ventana principal
# ──────────────────────────────────────────────────────────────────────────────
class LauncherWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self._module_by_key: dict[str, ModuleInfo] = {m.key: m for m in MODULES}
        self._active_module_process: subprocess.Popen | None = None
        self._active_module_key: str | None = None
        self._module_monitor = QTimer(self)
        self._module_monitor.setInterval(600)
        self._module_monitor.timeout.connect(self._check_active_module_status)
        self.setWindowTitle("SpanishFly")
        self.setMinimumSize(900, 640)
        self.resize(1080, 720)
        self._setup_style()
        self._build_ui()

    def _setup_style(self) -> None:
        self.setStyleSheet(
            f"""
            QMainWindow, QWidget {{
                background-color: {C_BG};
                color: {C_TEXT_PRI};
                font-family: 'Segoe UI', 'Inter', sans-serif;
            }}
            QScrollArea {{ background: transparent; border: none; }}
            QScrollBar:vertical {{
                background: {C_SURFACE};
                width: 6px;
                border-radius: 3px;
            }}
            QScrollBar::handle:vertical {{
                background: {C_BORDER};
                border-radius: 3px;
                min-height: 40px;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0;
            }}
            """
        )

    def _build_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Encabezado
        root.addWidget(AppHeader())

        # Área con scroll para las tarjetas
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        scroll_content = QWidget()
        scroll.setWidget(scroll_content)

        grid = QHBoxLayout(scroll_content)
        grid.setContentsMargins(40, 32, 40, 32)
        grid.setSpacing(20)
        grid.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)

        for mod in MODULES:
            card = ModuleCard(mod)
            card.launch_requested.connect(self._on_module_requested)
            grid.addWidget(card)

        grid.addStretch()
        root.addWidget(scroll)

        # Barra de estado inferior
        footer = QWidget()
        footer.setFixedHeight(36)
        footer.setStyleSheet(f"background: {C_SURFACE}; border-top: 1px solid {C_BORDER};")
        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(24, 0, 24, 0)

        ver = QLabel("v0.1.0-alpha")
        ver.setStyleSheet(f"color: {C_TEXT_DIM}; font-size: 11px;")
        footer_layout.addWidget(ver)
        footer_layout.addStretch()

        gpu_label = QLabel(self._gpu_info())
        gpu_label.setStyleSheet(f"color: {C_TEXT_DIM}; font-size: 11px;")
        footer_layout.addWidget(gpu_label)

        root.addWidget(footer)

    def _on_module_requested(self, module_key: str) -> None:
        if self._is_module_active():
            QMessageBox.information(
                self,
                "Módulo activo",
                "Ya hay un módulo activo. Cierra el módulo actual antes de abrir otro.",
            )
            return

        mod = self._module_by_key.get(module_key)
        if mod is None or not mod.available or mod.launch_fn is None:
            return

        process = mod.launch_fn()
        if process is None:
            return

        self._active_module_process = process
        self._active_module_key = module_key
        self._set_main_menu_active(False)
        self._module_monitor.start()

    def _is_module_active(self) -> bool:
        return (
            self._active_module_process is not None
            and self._active_module_process.poll() is None
        )

    def _check_active_module_status(self) -> None:
        if self._is_module_active():
            return
        self._module_monitor.stop()
        self._active_module_process = None
        self._active_module_key = None
        self._set_main_menu_active(True)

    def _set_main_menu_active(self, active: bool) -> None:
        if active:
            self.setEnabled(True)
            self.showNormal()
            self.raise_()
            self.activateWindow()
            return
        self.setEnabled(False)
        self.hide()

    @staticmethod
    def _gpu_info() -> str:
        try:
            import torch
            if torch.cuda.is_available():
                name = torch.cuda.get_device_name(0)
                return f"GPU: {name}"
        except Exception:
            pass
        return "GPU: no detectada"


# ──────────────────────────────────────────────────────────────────────────────
# Entrada
# ──────────────────────────────────────────────────────────────────────────────
def run() -> None:
    app = QApplication.instance() or QApplication(sys.argv)
    app.setApplicationName("SpanishFly")
    app.setOrganizationName("SpanishFly")

    win = LauncherWindow()
    win.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    run()
