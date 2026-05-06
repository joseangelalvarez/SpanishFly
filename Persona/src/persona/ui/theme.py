"""
SpanishFly – Design System
Paleta de colores y helpers de estilo compartidos por todos los módulos.
"""
from __future__ import annotations

# ──────────────────────────────────────────────────────────────────────────────
# Paleta principal
# ──────────────────────────────────────────────────────────────────────────────
C_BG        = "#0b0c10"
C_SURFACE   = "#13141a"
C_CARD      = "#1a1b24"
C_CARD_HOV  = "#22233a"
C_BORDER    = "#2a2b40"
C_ACCENT1   = "#7c6af7"   # violeta principal (Persona)
C_ACCENT2   = "#5c9cff"   # azul secundario
C_ACCENT3   = "#f76c8f"   # rosa (próximamente)
C_TEXT_PRI  = "#e8e9f3"
C_TEXT_SEC  = "#8889aa"
C_TEXT_DIM  = "#44455a"
C_SUCCESS   = "#4ade80"
C_ERROR     = "#f87171"
C_WARN      = "#f59e0b"

# Gradiente de Persona
PERSONA_G0 = C_ACCENT1
PERSONA_G1 = C_ACCENT2

# ──────────────────────────────────────────────────────────────────────────────
# Estilos reutilizables (str que se pasan a setStyleSheet)
# ──────────────────────────────────────────────────────────────────────────────

APP_STYLE = f"""
QMainWindow, QDialog, QWidget {{
    background-color: {C_BG};
    color: {C_TEXT_PRI};
    font-family: 'Segoe UI', 'Inter', sans-serif;
    font-size: 13px;
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
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}

QLineEdit, QTextEdit {{
    background: {C_SURFACE};
    color: {C_TEXT_PRI};
    border: 1px solid {C_BORDER};
    border-radius: 8px;
    padding: 8px 12px;
    selection-background-color: {C_ACCENT1};
}}
QLineEdit:focus, QTextEdit:focus {{
    border: 1px solid {C_ACCENT1};
}}
QLineEdit[readOnly="true"] {{
    color: {C_TEXT_SEC};
}}

QLabel {{
    color: {C_TEXT_PRI};
    background: transparent;
}}

QPushButton {{
    background: {C_CARD};
    color: {C_TEXT_PRI};
    border: 1px solid {C_BORDER};
    border-radius: 8px;
    padding: 8px 18px;
    font-weight: 600;
}}
QPushButton:hover {{
    background: {C_CARD_HOV};
    border-color: {C_ACCENT1};
}}
QPushButton:pressed {{
    background: {C_SURFACE};
}}
QPushButton:disabled {{
    color: {C_TEXT_DIM};
    background: {C_SURFACE};
    border-color: {C_BORDER};
}}

QPushButton#primary {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 {PERSONA_G0}, stop:1 {PERSONA_G1});
    color: #ffffff;
    border: none;
}}
QPushButton#primary:hover {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 {PERSONA_G1}, stop:1 {PERSONA_G0});
}}
QPushButton#primary:disabled {{
    background: {C_BORDER};
    color: {C_TEXT_DIM};
}}

QPushButton#danger {{
    background: {C_CARD};
    color: {C_ERROR};
    border: 1px solid {C_ERROR}44;
}}
QPushButton#danger:hover {{
    background: {C_ERROR}22;
    border-color: {C_ERROR};
}}

QProgressBar {{
    background: {C_SURFACE};
    border: 1px solid {C_BORDER};
    border-radius: 6px;
    height: 8px;
    text-align: center;
    color: transparent;
}}
QProgressBar::chunk {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 {PERSONA_G0}, stop:1 {PERSONA_G1});
    border-radius: 6px;
}}

QListWidget {{
    background: {C_SURFACE};
    border: 1px solid {C_BORDER};
    border-radius: 8px;
    padding: 4px;
    color: {C_TEXT_PRI};
}}
QListWidget::item {{ padding: 4px 8px; border-radius: 4px; }}
QListWidget::item:selected {{
    background: {C_ACCENT1}33;
    color: {C_TEXT_PRI};
}}

QMessageBox {{
    background: {C_CARD};
}}
QMessageBox QLabel {{ color: {C_TEXT_PRI}; }}
QMessageBox QPushButton {{
    min-width: 80px;
}}
"""


def section_label(text: str) -> str:
    """CSS para etiquetas de sección (caps pequeñas, tono secundario)."""
    return (
        f"color: {C_TEXT_SEC}; font-size: 11px; font-weight: 700; "
        f"letter-spacing: 1px; text-transform: uppercase;"
    )


def status_style(ok: bool = True) -> str:
    color = C_SUCCESS if ok else C_ERROR
    return f"color: {color}; font-size: 12px; font-weight: 500;"
