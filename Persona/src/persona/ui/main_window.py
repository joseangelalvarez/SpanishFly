from __future__ import annotations

import secrets
from functools import lru_cache
from pathlib import Path
from threading import Event

from PySide6.QtCore import QRegularExpression, Qt, QThread
from PySide6.QtGui import (
    QColor, QLinearGradient, QPainter, QPainterPath, QPen, QPixmap, QRegularExpressionValidator,
)
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QProgressBar,
    QScrollArea,
    QSlider,
    QSpinBox,
    QSizePolicy,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from persona.config.settings import AppConfig
from persona.core.generator import (
    IMAGE_STYLE_PREFIXES,
    MAX_PROMPT_TOKENS,
    GenerationService,
)
from persona.core.model_registry import (
    FACE_IP_ADAPTER_BIN,
    FACE_IP_ADAPTER_SAFETENSORS,
    ModelRegistry,
)
from persona.core.persona_store import PersonaStore
from persona.core.schemas import PersonaRecord, now_iso
from persona.infra.errors import ModelLoadError
from persona.infra.gpu import GPUStatus
from persona.ui.download_dialog import DownloadDialog
from persona.ui.theme import (
    APP_STYLE, C_BG, C_SURFACE, C_CARD, C_BORDER,
    C_TEXT_PRI, C_TEXT_SEC, C_TEXT_DIM,
    C_ACCENT1, C_SUCCESS, C_ERROR, C_WARN,
    PERSONA_G0, PERSONA_G1,
)
from persona.workers.generation_worker import GenerationWorker


# ──────────────────────────────────────────────────────────────────────────────
# Encabezado del módulo Persona
# ──────────────────────────────────────────────────────────────────────────────
class _PersonaHeader(QWidget):
    def __init__(self, gpu_status: GPUStatus, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFixedHeight(100)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 20, 32, 12)
        layout.setSpacing(4)

        breadcrumb = QLabel("SpanishFly  ›  Persona")
        breadcrumb.setStyleSheet(
            f"color: {C_TEXT_DIM}; font-size: 11px; font-weight: 600; letter-spacing: 1px;"
        )
        layout.addWidget(breadcrumb)

        title_row = QHBoxLayout()
        title_row.setSpacing(12)

        icon = QLabel("🎭")
        icon.setStyleSheet("font-size: 24px; background: transparent;")
        title_row.addWidget(icon)

        title = QLabel("Persona")
        title.setStyleSheet(
            f"color: {C_TEXT_PRI}; font-size: 26px; font-weight: 800; letter-spacing: 1px;"
        )
        title_row.addWidget(title)
        title_row.addStretch()

        # Badge de GPU
        if gpu_status.cuda_available:
            badge_txt   = f"  ● {gpu_status.gpu_name}  "
            badge_color = C_SUCCESS
        else:
            badge_txt   = "  ◌ CPU – sin CUDA  "
            badge_color = C_WARN

        gpu_badge = QLabel(badge_txt)
        gpu_badge.setStyleSheet(
            f"color: {badge_color}; font-size: 11px; font-weight: 600;"
            f"background: {badge_color}22; border-radius: 8px; padding: 3px 10px;"
        )
        title_row.addWidget(gpu_badge)
        layout.addLayout(title_row)

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        y = self.height() - 1
        grad = QLinearGradient(0, y, self.width(), y)
        grad.setColorAt(0.0, QColor(PERSONA_G0))
        grad.setColorAt(0.5, QColor(PERSONA_G1))
        grad.setColorAt(1.0, QColor(PERSONA_G0 + "00"))
        pen = QPen()
        pen.setBrush(grad)
        pen.setWidthF(1.5)
        painter.setPen(pen)
        painter.drawLine(32, y, self.width() - 32, y)


# ──────────────────────────────────────────────────────────────────────────────
# Etiqueta de campo
# ──────────────────────────────────────────────────────────────────────────────
def _field_label(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setStyleSheet(
        f"color: {C_TEXT_SEC}; font-size: 11px; font-weight: 700; letter-spacing: 0.8px;"
    )
    return lbl


# ──────────────────────────────────────────────────────────────────────────────
# Ventana principal
# ──────────────────────────────────────────────────────────────────────────────
class MainWindow(QMainWindow):
    _JUGGERNAUT_SIZES: list[tuple[int, int]] = [
        (1024, 1024),
        (1152, 896),
        (896, 1152),
        (1216, 832),
        (832, 1216),
    ]
    _IMAGE_STYLES: list[tuple[str, str]] = [
        ("Fotorealismo", "photorealism"),
        ("Anime", "anime"),
        ("3D", "3d"),
        ("Ilustración", "illustration"),
        ("Cómic", "comic"),
        ("Fantasia", "fantasy"),
    ]
    _NEGATIVE_FIXED_PROMPT = (
        "deformed anatomy, disfigured, malformed face, bad eyes, cross-eyed, bad hands, "
        "extra fingers, missing fingers, fused fingers, extra limbs, missing limbs, "
        "artifact, jpeg artifacts, blurry, lowres, text, watermark, logo, worst quality"
    )

    def __init__(self, config: AppConfig, gpu_status: GPUStatus) -> None:
        super().__init__()
        self._cfg = config
        self._gpu_status = gpu_status
        self._store = PersonaStore(config.data_personas_dir)
        self._registry = ModelRegistry(config.models)
        self._generator = GenerationService(config)

        self._thread: QThread | None = None
        self._worker: GenerationWorker | None = None
        self._cancel_event = Event()
        self._return_to_main_menu_after_cancel = False
        self._last_image_path: str | None = None
        self._prompt_tokenizer = None
        self._token_counter_fallback = False
        self._controlnet_pose_paths: list[Path] = []

        self.setWindowTitle("SpanishFly – Persona")
        self.resize(1180, 740)
        self.setStyleSheet(APP_STYLE)

        self._build_ui()
        self._show_gpu_banner()

    # ──────────────────────────────────────────────────────────────────────────
    # Construcción de la UI
    # ──────────────────────────────────────────────────────────────────────────
    def _build_ui(self) -> None:
        root = QWidget()
        self.setCentralWidget(root)
        root_layout = QVBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        root_layout.addWidget(_PersonaHeader(self._gpu_status))

        # ── Cuerpo: formulario (scrollable) + preview ────────────────────
        body = QWidget()
        body.setStyleSheet(f"background: {C_BG};")
        body_h = QHBoxLayout(body)
        body_h.setContentsMargins(32, 24, 16, 16)
        body_h.setSpacing(24)

        # Columna izquierda — formulario envuelto en scroll area
        form_inner = QWidget()
        form_inner.setStyleSheet(f"background: {C_BG};")
        form_col = QVBoxLayout(form_inner)
        form_col.setSpacing(14)
        form_col.setContentsMargins(0, 0, 8, 0)

        form_col.addWidget(_field_label("NOMBRE DEL PERSONAJE"))
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Ej: Elena la Guerrera")
        self.name_edit.setFixedHeight(38)
        form_col.addWidget(self.name_edit)

        form_col.addWidget(_field_label("IMAGEN BASE"))
        base_row = QHBoxLayout()
        base_row.setSpacing(8)
        self.base_image_edit = QLineEdit()
        self.base_image_edit.setPlaceholderText("Ruta a la imagen de referencia (opcional)")
        self.base_image_edit.setFixedHeight(38)
        browse_btn = QPushButton("Examinar…")
        browse_btn.setFixedHeight(38)
        browse_btn.setFixedWidth(110)
        browse_btn.clicked.connect(self._choose_base_image)
        base_row.addWidget(self.base_image_edit)
        base_row.addWidget(browse_btn)
        form_col.addLayout(base_row)

        ip_adapter_row = QHBoxLayout()
        ip_adapter_row.setSpacing(6)
        self.ip_adapter_face_icon = QLabel("◌")
        self.ip_adapter_face_icon.setFixedWidth(14)
        self.ip_adapter_face_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.ip_adapter_face_indicator = QLabel()
        self.ip_adapter_face_indicator.setWordWrap(True)
        ip_adapter_row.addWidget(self.ip_adapter_face_icon)
        ip_adapter_row.addWidget(self.ip_adapter_face_indicator, stretch=1)
        form_col.addLayout(ip_adapter_row)
        self.base_image_edit.textChanged.connect(self._update_ip_adapter_face_indicator)

        form_col.addWidget(_field_label("PROMPT DEL PERSONAJE"))
        self.prompt_edit = QTextEdit()
        self.prompt_edit.setPlaceholderText(
            "Describe el personaje: apariencia, ropa, expresión, estilo artístico…"
        )
        self.prompt_edit.setMinimumHeight(110)
        form_col.addWidget(self.prompt_edit)

        self.prompt_counter_label = QLabel()
        self.prompt_counter_label.setStyleSheet(
            f"color: {C_TEXT_DIM}; font-size: 11px; padding-top: 2px;"
        )
        form_col.addWidget(self.prompt_counter_label)

        form_col.addWidget(_field_label("TIPO DE IMAGEN"))
        self.image_type_combo = QComboBox()
        self.image_type_combo.setFixedHeight(34)
        for label, value in self._IMAGE_STYLES:
            self.image_type_combo.addItem(label, value)
        self.image_type_combo.currentIndexChanged.connect(self._update_prompt_counter)
        form_col.addWidget(self.image_type_combo)
        self.prompt_edit.textChanged.connect(self._update_prompt_counter)

        form_col.addWidget(_field_label("PROMPT NEGATIVO (BASE FIJA)"))
        self.negative_fixed_edit = QLineEdit(self._NEGATIVE_FIXED_PROMPT)
        self.negative_fixed_edit.setReadOnly(True)
        self.negative_fixed_edit.setFixedHeight(34)
        form_col.addWidget(self.negative_fixed_edit)

        form_col.addWidget(_field_label("PROMPT NEGATIVO (ADICIONAL EDITABLE)"))
        self.negative_prompt_edit = QTextEdit()
        self.negative_prompt_edit.setPlaceholderText(
            "Ej: bad skin texture, plastic look, oversaturated colors..."
        )
        self.negative_prompt_edit.setMinimumHeight(72)
        form_col.addWidget(self.negative_prompt_edit)

        form_col.addWidget(_field_label("PARAMETROS DE GENERACION"))
        params_card = QFrame()
        params_card.setStyleSheet(
            f"background: {C_CARD}; border: 1px solid {C_BORDER}; border-radius: 12px;"
        )
        params_layout = QGridLayout(params_card)
        params_layout.setContentsMargins(12, 12, 12, 12)
        params_layout.setHorizontalSpacing(10)
        params_layout.setVerticalSpacing(8)

        sampler_lbl = QLabel("Sampler")
        sampler_lbl.setStyleSheet(f"color: {C_TEXT_SEC};")
        self.sampler_value = QLineEdit("DPM++ 2M SDE")
        self.sampler_value.setReadOnly(True)
        self.sampler_value.setFixedHeight(34)

        schedule_lbl = QLabel("Schedule")
        schedule_lbl.setStyleSheet(f"color: {C_TEXT_SEC};")
        self.schedule_value = QLineEdit("Exponential")
        self.schedule_value.setReadOnly(True)
        self.schedule_value.setFixedHeight(34)

        steps_lbl = QLabel("Steps")
        steps_lbl.setStyleSheet(f"color: {C_TEXT_SEC};")
        self.steps_spin = QSpinBox()
        self.steps_spin.setRange(10, 120)
        self.steps_spin.setValue(max(10, int(self._cfg.runtime.steps)))
        self.steps_spin.setFixedHeight(34)

        cfg_lbl = QLabel("CFG scale")
        cfg_lbl.setStyleSheet(f"color: {C_TEXT_SEC};")
        self.cfg_spin = QDoubleSpinBox()
        self.cfg_spin.setRange(1.0, 15.0)
        self.cfg_spin.setDecimals(1)
        self.cfg_spin.setSingleStep(0.1)
        self.cfg_spin.setValue(float(self._cfg.runtime.guidance_scale))
        self.cfg_spin.setFixedHeight(34)

        size_lbl = QLabel("Size")
        size_lbl.setStyleSheet(f"color: {C_TEXT_SEC};")
        self.size_combo = QComboBox()
        self.size_combo.setFixedHeight(34)
        self._populate_size_options()

        seed_mode_lbl = QLabel("Modo semilla")
        seed_mode_lbl.setStyleSheet(f"color: {C_TEXT_SEC};")
        self.seed_mode_combo = QComboBox()
        self.seed_mode_combo.addItems(["Aleatoria", "Fija"])
        self.seed_mode_combo.setFixedHeight(34)

        seed_lbl = QLabel("Seed")
        seed_lbl.setStyleSheet(f"color: {C_TEXT_SEC};")
        self.seed_edit = QLineEdit()
        # QSpinBox usa int con signo (32-bit) y no soporta uint32 completo.
        # Usamos QLineEdit validado para permitir 0..4294967295.
        self.seed_edit.setMaxLength(10)
        self.seed_edit.setPlaceholderText("0..4294967295")
        self.seed_edit.setValidator(
            QRegularExpressionValidator(QRegularExpression(r"^\d{0,10}$"), self.seed_edit)
        )
        seed_default = self._cfg.runtime.seed if self._cfg.runtime.seed is not None else 2554065581
        self.seed_edit.setText(str(int(seed_default)))
        self.seed_edit.setFixedHeight(34)

        if self._cfg.runtime.seed is None:
            self.seed_mode_combo.setCurrentText("Aleatoria")
            self.seed_edit.setEnabled(False)
        else:
            self.seed_mode_combo.setCurrentText("Fija")

        self.seed_mode_combo.currentTextChanged.connect(self._on_seed_mode_changed)

        ref_lbl = QLabel("Influencia referencia")
        ref_lbl.setStyleSheet(f"color: {C_TEXT_SEC};")
        ref_row = QHBoxLayout()
        ref_row.setSpacing(8)
        self.ref_strength_slider = QSlider(Qt.Orientation.Horizontal)
        self.ref_strength_slider.setRange(0, 100)
        self.ref_strength_slider.setValue(75)
        self.ref_strength_value = QLabel("0.75")
        self.ref_strength_value.setMinimumWidth(36)
        self.ref_strength_slider.valueChanged.connect(self._on_reference_strength_changed)
        ref_row.addWidget(self.ref_strength_slider)
        ref_row.addWidget(self.ref_strength_value)

        controlnet_lbl = QLabel("ControlNet")
        controlnet_lbl.setStyleSheet(f"color: {C_TEXT_SEC};")
        self.controlnet_check = QCheckBox("Activar ControlNet")
        self.controlnet_check.setChecked(False)
        self.controlnet_check.toggled.connect(self._on_controlnet_toggled)

        nsfw_lbl = QLabel("NSFW")
        nsfw_lbl.setStyleSheet(f"color: {C_TEXT_SEC};")
        self.nsfw_check = QCheckBox("Usar modelo NSFW")
        self.nsfw_check.setChecked(False)

        pose_lbl = QLabel("Pose ControlNet")
        pose_lbl.setStyleSheet(f"color: {C_TEXT_SEC};")
        self.controlnet_pose_combo = QComboBox()
        self.controlnet_pose_combo.setFixedHeight(34)
        self._populate_controlnet_pose_options()
        self.controlnet_pose_combo.setEnabled(False)

        params_layout.addWidget(sampler_lbl, 0, 0)
        params_layout.addWidget(self.sampler_value, 0, 1)
        params_layout.addWidget(schedule_lbl, 0, 2)
        params_layout.addWidget(self.schedule_value, 0, 3)

        params_layout.addWidget(steps_lbl, 1, 0)
        params_layout.addWidget(self.steps_spin, 1, 1)
        params_layout.addWidget(cfg_lbl, 1, 2)
        params_layout.addWidget(self.cfg_spin, 1, 3)

        params_layout.addWidget(size_lbl, 2, 0)
        params_layout.addWidget(self.size_combo, 2, 1)
        params_layout.addWidget(seed_mode_lbl, 2, 2)
        params_layout.addWidget(self.seed_mode_combo, 2, 3)

        params_layout.addWidget(seed_lbl, 3, 0)
        params_layout.addWidget(self.seed_edit, 3, 1)
        params_layout.addWidget(ref_lbl, 3, 2)
        params_layout.addLayout(ref_row, 3, 3)

        params_layout.addWidget(controlnet_lbl, 4, 0)
        params_layout.addWidget(self.controlnet_check, 4, 1)
        params_layout.addWidget(pose_lbl, 4, 2)
        params_layout.addWidget(self.controlnet_pose_combo, 4, 3)

        params_layout.addWidget(nsfw_lbl, 5, 0)
        params_layout.addWidget(self.nsfw_check, 5, 1)
        form_col.addWidget(params_card)

        form_col.addWidget(_field_label("NOTAS"))
        self.notes_edit = QTextEdit()
        self.notes_edit.setPlaceholderText("Notas internas, referencias, ideas…")
        self.notes_edit.setMinimumHeight(80)
        form_col.addWidget(self.notes_edit)

        form_col.addStretch()

        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setFixedHeight(8)
        form_col.addWidget(self.progress)

        self.status_label = QLabel("Listo")
        self.status_label.setStyleSheet(
            f"color: {C_TEXT_SEC}; font-size: 12px; padding-top: 2px;"
        )
        form_col.addWidget(self.status_label)

        form_scroll = QScrollArea()
        form_scroll.setWidget(form_inner)
        form_scroll.setWidgetResizable(True)
        form_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        form_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        form_scroll.setFrameShape(QFrame.Shape.NoFrame)
        form_scroll.setStyleSheet(f"background: {C_BG}; border: none;")

        body_h.addWidget(form_scroll, stretch=5)

        # Columna derecha — preview de imagen
        body_h.addWidget(self._build_preview_panel(), stretch=4)

        root_layout.addWidget(body)

        # ── Barra de acciones ────────────────────────────────────────────────
        actions_bar = QWidget()
        actions_bar.setFixedHeight(60)
        actions_bar.setStyleSheet(
            f"background: {C_SURFACE}; border-top: 1px solid {C_BORDER};"
        )
        actions_layout = QHBoxLayout(actions_bar)
        actions_layout.setContentsMargins(32, 10, 32, 10)
        actions_layout.setSpacing(10)

        self.generate_btn = QPushButton("⚡  Generar")
        self.generate_btn.setObjectName("primary")
        self.generate_btn.setFixedHeight(38)

        self.save_btn = QPushButton("💾  Guardar personaje")
        self.save_btn.setFixedHeight(38)
        self.save_btn.setEnabled(False)   # habilitado solo tras generación exitosa

        self.cancel_btn = QPushButton("✖  Cancelar")
        self.cancel_btn.setObjectName("danger")
        self.cancel_btn.setFixedHeight(38)
        self.cancel_btn.setEnabled(True)

        actions_layout.addWidget(self.generate_btn)
        actions_layout.addWidget(self.save_btn)
        actions_layout.addStretch()
        actions_layout.addWidget(self.cancel_btn)

        self.generate_btn.clicked.connect(self._on_generate)
        self.save_btn.clicked.connect(self._on_save)
        self.cancel_btn.clicked.connect(self._on_cancel)

        root_layout.addWidget(actions_bar)
        self._update_prompt_counter()
        self._update_ip_adapter_face_indicator()

    def _build_preview_panel(self) -> QFrame:
        """Panel derecho con la imagen generada."""
        panel = QFrame()
        panel.setObjectName("PreviewPanel")
        panel.setStyleSheet(
            f"QFrame#PreviewPanel {{"
            f"  background: {C_CARD};"
            f"  border: 1px solid {C_BORDER};"
            f"  border-radius: 14px;"
            f"}}"
        )
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        lbl_title = _field_label("IMAGEN GENERADA")
        layout.addWidget(lbl_title)

        # Contenedor de imagen con relación de aspecto cuadrada
        self._img_container = QFrame()
        self._img_container.setStyleSheet(
            f"background: {C_SURFACE}; border-radius: 10px; border: 1px solid {C_BORDER};"
        )
        self._img_container.setMinimumSize(280, 280)
        self._img_container.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        img_layout = QVBoxLayout(self._img_container)
        img_layout.setContentsMargins(0, 0, 0, 0)

        self._img_label = QLabel()
        self._img_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._img_label.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        self._show_placeholder()
        img_layout.addWidget(self._img_label)
        layout.addWidget(self._img_container)

        # Info debajo de la imagen
        self._img_info = QLabel("")
        self._img_info.setWordWrap(True)
        self._img_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._img_info.setStyleSheet(
            f"color: {C_TEXT_DIM}; font-size: 11px; background: transparent; border: none;"
        )
        layout.addWidget(self._img_info)

        return panel

    def _show_placeholder(self) -> None:
        self._img_label.setPixmap(QPixmap())
        self._img_label.setText(
            f"<span style='color:{C_TEXT_DIM}; font-size:13px;'>"
            "Genera un personaje<br>para ver la imagen aquí"
            "</span>"
        )

    def _show_generated_image(self, image_path: str) -> None:
        px = QPixmap(image_path)
        if px.isNull():
            self._show_placeholder()
            return
        size = self._img_label.size()
        self._img_label.setText("")
        self._img_label.setPixmap(
            px.scaled(size, Qt.AspectRatioMode.KeepAspectRatio,
                      Qt.TransformationMode.SmoothTransformation)
        )
        name = Path(image_path).name
        self._img_info.setText(name)

    def resizeEvent(self, event) -> None:  # noqa: N802
        super().resizeEvent(event)
        # Re-escalar imagen al redimensionar ventana
        if self._last_image_path:
            self._show_generated_image(self._last_image_path)


    def _show_gpu_banner(self) -> None:
        if self._gpu_status.warning:
            QMessageBox.information(self, "Estado de GPU", self._gpu_status.warning)

    def _choose_base_image(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Seleccionar imagen base",
            str(self._cfg.persona_root),
            "Images (*.png *.jpg *.jpeg *.webp)",
        )
        if file_path:
            self.base_image_edit.setText(file_path)

    def _on_generate(self) -> None:
        name = self.name_edit.text().strip()
        prompt = self.prompt_edit.toPlainText().strip()
        nsfw_enabled = self.nsfw_check.isChecked()

        if not name:
            QMessageBox.warning(self, "Validacion", "El nombre del personaje es obligatorio.")
            return
        if not prompt:
            QMessageBox.warning(self, "Validacion", "El prompt del personaje es obligatorio.")
            return

        try:
            self._registry.validate_local_paths(nsfw_enabled=nsfw_enabled)
        except ModelLoadError as exc:
            tasks = self._registry.get_missing_download_tasks(nsfw_enabled=nsfw_enabled)
            if tasks:
                dlg = DownloadDialog(tasks=tasks, parent=self)
                if dlg.exec():
                    try:
                        self._registry.validate_local_paths(nsfw_enabled=nsfw_enabled)
                    except ModelLoadError as post_download_exc:
                        QMessageBox.critical(self, "Modelos locales faltantes", str(post_download_exc))
                        return
                else:
                    return
            else:
                QMessageBox.critical(self, "Modelos locales faltantes", str(exc))
                return

        optional_missing = self._registry.get_missing_optional_paths()
        if optional_missing:
            self.status_label.setText(
                f"Aviso: faltan {len(optional_missing)} recursos opcionales (ControlNet/IP-Adapter)."
            )

        self._start_generation(name, prompt)

    def _start_generation(self, name: str, prompt: str) -> None:
        self._cancel_event.clear()
        self._set_busy(True)
        self.status_label.setText("Iniciando generación…")

        base_image = self.base_image_edit.text().strip() or None
        try:
            gen_options = self._collect_generation_options()
        except ValueError:
            self._set_busy(False)
            return
        if gen_options.get("controlnet_enabled"):
            pose_name = Path(str(gen_options.get("controlnet_pose_path") or "")).name
            self.status_label.setText(f"Preparando ControlNet con pose: {pose_name}...")
        self._thread = QThread(self)
        self._worker = GenerationWorker(
            self._generator,
            name,
            prompt,
            self._cancel_event,
            base_image,
            generation_options=gen_options,
        )
        self._worker.moveToThread(self._thread)

        self._thread.started.connect(self._worker.run)
        self._worker.progress.connect(self._on_progress)
        self._worker.preview.connect(self._on_preview)
        self._worker.completed.connect(self._on_completed)
        self._worker.failed.connect(self._on_failed)
        self._worker.cancelled.connect(self._on_cancelled)

        self._worker.completed.connect(self._thread.quit)
        self._worker.failed.connect(self._thread.quit)
        self._worker.cancelled.connect(self._thread.quit)

        self._thread.finished.connect(self._clear_thread)
        self._thread.start()

    def _on_save(self) -> None:
        name = self.name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "Validación", "Indica un nombre de personaje antes de guardar.")
            return

        # Comprobar si el nombre ya está ocupado por otro personaje
        existing = self._store.load(name)
        if existing is not None:
            resp = QMessageBox.question(
                self,
                "Nombre en uso",
                f"Ya existe un personaje llamado «{name}».\n¿Quieres sobreescribirlo?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if resp != QMessageBox.StandardButton.Yes:
                return

        created_at = existing.created_at if existing is not None else now_iso()
        last_metadata = existing.last_generation_metadata if existing is not None else None
        last_image = self._last_image_path or (existing.last_generated_image if existing is not None else None)

        record = PersonaRecord(
            name=name,
            base_image_path=self.base_image_edit.text().strip(),
            created_at=created_at,
            notes=self.notes_edit.toPlainText().strip(),
            base_prompt=self.prompt_edit.toPlainText().strip(),
            last_generated_image=last_image,
            last_generation_metadata=last_metadata,
        )
        path = self._store.save(record)
        self.status_label.setText(f"Personaje guardado: {path.name}")
        self.save_btn.setEnabled(False)

    def _on_cancel(self) -> None:
        if self._thread and self._thread.isRunning():
            self.status_label.setText("Generación en pausa: confirma si deseas cancelar y volver al menú.")
            resp = QMessageBox.question(
                self,
                "Confirmar cancelación",
                "Hay una operación activa.\n\n"
                "¿Deseas cancelar la operación y volver al menú principal?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if resp != QMessageBox.StandardButton.Yes:
                self.status_label.setText("Continuando generación...")
                return

            self._return_to_main_menu_after_cancel = True
            self.cancel_btn.setEnabled(False)
            self._cancel_event.set()
            self.status_label.setText("Cancelando operación y regresando al menú principal...")
            return

        resp = QMessageBox.question(
            self,
            "Volver al menú principal",
            "¿Deseas salir del módulo Persona y volver al menú principal?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if resp == QMessageBox.StandardButton.Yes:
            self._return_to_main_menu_after_cancel = True
            self.close()

    def _on_progress(self, value: int, message: str) -> None:
        self.progress.setValue(value)
        self.status_label.setText(message)

    def _on_preview(self, image_path: str) -> None:
        self._show_generated_image(image_path)
        self._img_info.setText("Vista previa latente en generación…")

    def _on_completed(self, image_path: str, metadata: dict) -> None:
        self._last_image_path = image_path
        self.progress.setValue(100)
        if metadata.get("prompt_truncated"):
            self.status_label.setText(
                f"Generación completada (prompt recortado a {MAX_PROMPT_TOKENS} tokens): "
                f"{Path(image_path).name}"
            )
        else:
            self.status_label.setText(f"Generación completada: {Path(image_path).name}")
        seed_from_run = metadata.get("seed")
        if seed_from_run is not None:
            self.seed_edit.setText(str(seed_from_run))
        self._show_generated_image(image_path)
        self._persist_last_generation(image_path=image_path, metadata=metadata)
        self._set_busy(False)
        self.save_btn.setEnabled(True)
        if self._return_to_main_menu_after_cancel:
            self.close()

    def _persist_last_generation(self, image_path: str, metadata: dict) -> None:
        name = self.name_edit.text().strip()
        if not name:
            return

        current = self._store.load(name)
        if current is not None:
            created_at = current.created_at
        else:
            created_at = now_iso()

        record = PersonaRecord(
            name=name,
            base_image_path=self.base_image_edit.text().strip(),
            created_at=created_at,
            notes=self.notes_edit.toPlainText().strip(),
            base_prompt=self.prompt_edit.toPlainText().strip(),
            last_generated_image=image_path,
            last_generation_metadata=metadata,
        )
        self._store.save(record)

    def _on_failed(self, error: str) -> None:
        self.status_label.setText("Error en generación")
        QMessageBox.critical(self, "Fallo de generación", error)
        self._set_busy(False)
        if self._return_to_main_menu_after_cancel:
            self.close()

    def _on_cancelled(self, message: str) -> None:
        self.status_label.setText(message)
        self._set_busy(False)
        if self._return_to_main_menu_after_cancel:
            self.close()

    def _clear_thread(self) -> None:
        self._thread = None
        self._worker = None

    def _set_busy(self, busy: bool) -> None:
        self.generate_btn.setEnabled(not busy)
        # save_btn se gestiona independientemente (solo activo tras generación exitosa)
        self.cancel_btn.setEnabled(True)

    def _populate_size_options(self) -> None:
        for w, h in self._JUGGERNAUT_SIZES:
            self.size_combo.addItem(f"{w}x{h}", (w, h))

        current = (int(self._cfg.runtime.width), int(self._cfg.runtime.height))
        found = False
        for i in range(self.size_combo.count()):
            if self.size_combo.itemData(i) == current:
                self.size_combo.setCurrentIndex(i)
                found = True
                break

        if not found:
            self.size_combo.addItem(f"{current[0]}x{current[1]}", current)
            self.size_combo.setCurrentIndex(self.size_combo.count() - 1)

    def _on_seed_mode_changed(self, mode: str) -> None:
        self.seed_edit.setEnabled(mode == "Fija")

    def _on_reference_strength_changed(self, value: int) -> None:
        self.ref_strength_value.setText(f"{value / 100.0:.2f}")

    def _collect_generation_options(self) -> dict:
        size = self.size_combo.currentData()
        width, height = int(size[0]), int(size[1])
        seed = None
        seed_mode = self.seed_mode_combo.currentText()
        if self.seed_mode_combo.currentText() == "Fija":
            seed_text = self.seed_edit.text().strip()
            if not seed_text:
                QMessageBox.warning(self, "Validacion", "La semilla fija es obligatoria.")
                raise ValueError("Semilla fija vacia")
            seed_value = int(seed_text)
            if seed_value < 0 or seed_value > 4294967295:
                QMessageBox.warning(self, "Validacion", "La semilla debe estar entre 0 y 4294967295.")
                raise ValueError("Semilla fuera de rango")
            seed = seed_value
        else:
            seed = secrets.randbelow(4294967296)
            self.seed_edit.setText(str(seed))

        controlnet_enabled = self.controlnet_check.isChecked()
        controlnet_pose_path: str | None = None
        if controlnet_enabled:
            if not any(path.exists() for path in self._cfg.models.controlnet_paths):
                QMessageBox.warning(
                    self,
                    "ControlNet",
                    "ControlNet está activado, pero no hay modelos locales disponibles en las rutas configuradas.",
                )
                raise ValueError("Modelo ControlNet no disponible")
            pose_path = self.controlnet_pose_combo.currentData()
            if not pose_path:
                QMessageBox.warning(
                    self,
                    "Validación",
                    "Debes seleccionar una pose para usar ControlNet.",
                )
                raise ValueError("Pose de ControlNet no seleccionada")
            if not Path(pose_path).exists():
                QMessageBox.warning(
                    self,
                    "Validación",
                    "La imagen de pose seleccionada no existe.",
                )
                raise ValueError("Pose de ControlNet inexistente")
            controlnet_pose_path = str(pose_path)

        return {
            "steps": int(self.steps_spin.value()),
            "cfg_scale": float(self.cfg_spin.value()),
            "seed": seed,
            "seed_mode": "fixed" if seed_mode == "Fija" else "random",
            "width": width,
            "height": height,
            "reference_strength": float(self.ref_strength_slider.value()) / 100.0,
            "image_style": self.image_type_combo.currentData(),
            "negative_prompt_user": self.negative_prompt_edit.toPlainText().strip(),
            "controlnet_enabled": controlnet_enabled,
            "controlnet_pose_path": controlnet_pose_path,
            "nsfw_enabled": self.nsfw_check.isChecked(),
        }

    def _populate_controlnet_pose_options(self) -> None:
        self.controlnet_pose_combo.clear()
        self._controlnet_pose_paths = []

        pose_dir = self._cfg.persona_root / "models" / "controlnet" / "pose" / "images"
        if pose_dir.exists():
            self._controlnet_pose_paths = sorted(pose_dir.glob("*.png"))

        if not self._controlnet_pose_paths:
            self.controlnet_pose_combo.addItem("No hay poses disponibles", None)
            return

        for pose_path in self._controlnet_pose_paths:
            self.controlnet_pose_combo.addItem(pose_path.stem, str(pose_path))

    def _on_controlnet_toggled(self, enabled: bool) -> None:
        has_poses = bool(self._controlnet_pose_paths)
        self.controlnet_pose_combo.setEnabled(enabled and has_poses)
        if enabled and not has_poses:
            QMessageBox.warning(
                self,
                "ControlNet",
                "No se encontraron poses en models/controlnet/pose/images.",
            )
            self.controlnet_check.setChecked(False)
        self._update_ip_adapter_face_indicator()

    def _has_ip_adapter_face_assets(self) -> bool:
        face_root = self._cfg.models.ip_adapter_paths.get("face")
        if face_root is None or not face_root.exists():
            return False
        subfolder = self._cfg.models.ip_adapter_subfolders.get("face", "sdxl_models")
        adapter_dir = face_root / subfolder if subfolder else face_root
        if not adapter_dir.exists():
            return False
        face_bin = adapter_dir / FACE_IP_ADAPTER_BIN
        face_safe = adapter_dir / FACE_IP_ADAPTER_SAFETENSORS
        return face_bin.exists() and face_safe.exists()

    def _update_ip_adapter_face_indicator(self) -> None:
        has_assets = self._has_ip_adapter_face_assets()
        base_path = self.base_image_edit.text().strip()
        has_reference = bool(base_path)
        ref_exists = Path(base_path).exists() if has_reference else False
        controlnet_enabled = self.controlnet_check.isChecked()

        if not has_assets:
            self.ip_adapter_face_icon.setStyleSheet(
                f"color: {C_WARN}; font-size: 12px; font-weight: 700;"
            )
            self.ip_adapter_face_icon.setText("!")
            self.ip_adapter_face_indicator.setStyleSheet(
                f"color: {C_WARN}; font-size: 11px; font-weight: 600; padding-top: 2px;"
            )
            self.ip_adapter_face_indicator.setText(
                "IP-Adapter Face: no disponible (faltan modelos locales)."
            )
            return

        if controlnet_enabled:
            self.ip_adapter_face_icon.setStyleSheet(
                f"color: {C_TEXT_DIM}; font-size: 12px; font-weight: 700;"
            )
            self.ip_adapter_face_icon.setText("◌")
            self.ip_adapter_face_indicator.setStyleSheet(
                f"color: {C_TEXT_DIM}; font-size: 11px; font-weight: 600; padding-top: 2px;"
            )
            self.ip_adapter_face_indicator.setText(
                "IP-Adapter Face: inactivo (ControlNet activo)."
            )
            return

        if not has_reference:
            self.ip_adapter_face_icon.setStyleSheet(
                f"color: {C_TEXT_DIM}; font-size: 12px; font-weight: 700;"
            )
            self.ip_adapter_face_icon.setText("◌")
            self.ip_adapter_face_indicator.setStyleSheet(
                f"color: {C_TEXT_DIM}; font-size: 11px; font-weight: 600; padding-top: 2px;"
            )
            self.ip_adapter_face_indicator.setText(
                "IP-Adapter Face: inactivo (agrega una imagen de referencia)."
            )
            return

        if not ref_exists:
            self.ip_adapter_face_icon.setStyleSheet(
                f"color: {C_ERROR}; font-size: 12px; font-weight: 700;"
            )
            self.ip_adapter_face_icon.setText("x")
            self.ip_adapter_face_indicator.setStyleSheet(
                f"color: {C_ERROR}; font-size: 11px; font-weight: 700; padding-top: 2px;"
            )
            self.ip_adapter_face_indicator.setText(
                "IP-Adapter Face: no se usará (la imagen de referencia no existe)."
            )
            return

        self.ip_adapter_face_icon.setStyleSheet(
            f"color: {C_SUCCESS}; font-size: 12px; font-weight: 700;"
        )
        self.ip_adapter_face_icon.setText("●")
        self.ip_adapter_face_indicator.setStyleSheet(
            f"color: {C_SUCCESS}; font-size: 11px; font-weight: 700; padding-top: 2px;"
        )
        self.ip_adapter_face_indicator.setText(
            "IP-Adapter Face: activo (se usará en la próxima generación)."
        )

    def _update_prompt_counter(self, *_args) -> None:
        composed = self._compose_prompt_for_counter()
        token_count = self._count_prompt_tokens(composed)
        over_limit = token_count > MAX_PROMPT_TOKENS
        mode_suffix = " (aprox.)" if self._token_counter_fallback else ""
        if over_limit:
            self.prompt_counter_label.setStyleSheet(
                f"color: {C_ERROR}; font-size: 11px; font-weight: 700; padding-top: 2px;"
            )
            self.prompt_counter_label.setText(
                f"Tokens prompt compuesto: {token_count}/{MAX_PROMPT_TOKENS}{mode_suffix} "
                "(se recortará al generar)"
            )
            return

        self.prompt_counter_label.setStyleSheet(
            f"color: {C_TEXT_DIM}; font-size: 11px; padding-top: 2px;"
        )
        self.prompt_counter_label.setText(
            f"Tokens prompt compuesto: {token_count}/{MAX_PROMPT_TOKENS}{mode_suffix}"
        )

    def _compose_prompt_for_counter(self) -> str:
        style_key = (self.image_type_combo.currentData() or "photorealism").strip().lower()
        style_prefix = IMAGE_STYLE_PREFIXES.get(style_key, IMAGE_STYLE_PREFIXES["photorealism"])
        user_prompt = self.prompt_edit.toPlainText().strip()
        return f"style: {style_prefix}. {user_prompt}".strip()

    def _count_prompt_tokens(self, text: str) -> int:
        tokenizer = self._get_prompt_tokenizer()
        if tokenizer is None:
            self._token_counter_fallback = True
            return len(text.split())
        try:
            self._token_counter_fallback = False
            return len(tokenizer(text, add_special_tokens=False).input_ids)
        except Exception:
            self._token_counter_fallback = True
            return len(text.split())

    @lru_cache(maxsize=1)
    def _get_prompt_tokenizer(self):
        try:
            from transformers import AutoTokenizer

            model_dir = self._cfg.models.sdxl_base_path
            tokenizer_2_path = model_dir / "tokenizer_2"
            tokenizer_path = model_dir / "tokenizer"
            if tokenizer_2_path.exists():
                return AutoTokenizer.from_pretrained(
                    str(tokenizer_2_path),
                    local_files_only=True,
                    use_fast=True,
                )
            if tokenizer_path.exists():
                return AutoTokenizer.from_pretrained(
                    str(tokenizer_path),
                    local_files_only=True,
                    use_fast=True,
                )
        except Exception:
            return None
        return None

    def closeEvent(self, event) -> None:  # noqa: N802
        if self._thread and self._thread.isRunning() and not self._return_to_main_menu_after_cancel:
            resp = QMessageBox.question(
                self,
                "Operación en curso",
                "Hay una operación activa.\n\n"
                "¿Deseas cancelarla y volver al menú principal?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if resp != QMessageBox.StandardButton.Yes:
                event.ignore()
                return
            self._return_to_main_menu_after_cancel = True
            self._cancel_event.set()

        self._cancel_event.set()
        try:
            if self._thread and self._thread.isRunning():
                self._thread.quit()
                self._thread.wait(2000)
        except RuntimeError:
            pass  # objeto C++ ya destruido, ignorar
        super().closeEvent(event)
