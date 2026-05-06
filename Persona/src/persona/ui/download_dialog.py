from __future__ import annotations

from threading import Event

from PySide6.QtCore import QThread, Signal
from PySide6.QtGui import QColor, QLinearGradient, QPainter, QPen
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from persona.core.download_task import DownloadTask
from persona.infra.credentials import load_credentials, save_credentials
from persona.ui.help_dialog import HelpDialog
from persona.ui.theme import (
    APP_STYLE, C_BG, C_SURFACE, C_BORDER, C_TEXT_PRI, C_TEXT_SEC,
    C_TEXT_DIM, C_ACCENT1, C_SUCCESS, C_ERROR, PERSONA_G0, PERSONA_G1,
)
from persona.workers.download_worker import DownloadWorker


class _SectionLabel(QLabel):
    def __init__(self, text: str, parent=None) -> None:
        super().__init__(text, parent)
        self.setStyleSheet(
            f"color: {C_TEXT_SEC}; font-size: 11px; font-weight: 700; letter-spacing: 0.8px;"
        )


class DownloadDialog(QDialog):
    models_downloaded = Signal()

    def __init__(self, tasks: list[DownloadTask], parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Modelos no encontrados — Descargar desde HuggingFace")
        self.setMinimumWidth(640)
        self.setMinimumHeight(540)
        self.setStyleSheet(APP_STYLE)

        self._tasks = tasks
        self._cancel_event = Event()
        self._thread: QThread | None = None
        self._worker: DownloadWorker | None = None
        self._downloading = False

        self._build_ui()
        self._load_saved_credentials()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 20)
        layout.setSpacing(14)

        # Título
        title = QLabel("Descargar modelos")
        title.setStyleSheet(
            f"color: {C_TEXT_PRI}; font-size: 20px; font-weight: 800;"
        )
        layout.addWidget(title)

        info = QLabel(
            "No se encontraron los modelos locales necesarios para generar imágenes.\n"
            "Introduce tus credenciales de HuggingFace para descargarlos automáticamente."
        )
        info.setWordWrap(True)
        info.setStyleSheet(f"color: {C_TEXT_SEC}; font-size: 12px; line-height: 1.5;")
        layout.addWidget(info)

        _sep = QWidget(); _sep.setFixedHeight(1)
        _sep.setStyleSheet(f"background: {C_BORDER};")
        layout.addWidget(_sep)

        # Credenciales
        layout.addWidget(_SectionLabel("CREDENCIALES HUGGINGFACE"))

        creds_widget = QWidget()
        creds_widget.setStyleSheet(
            f"background: {C_SURFACE}; border: 1px solid {C_BORDER}; border-radius: 10px;"
        )
        creds_layout = QVBoxLayout(creds_widget)
        creds_layout.setContentsMargins(16, 14, 16, 14)
        creds_layout.setSpacing(10)

        user_row = QHBoxLayout()
        user_lbl = QLabel("Usuario:")
        user_lbl.setFixedWidth(90)
        user_lbl.setStyleSheet(f"color: {C_TEXT_SEC}; font-size: 12px;")
        self.username_edit = QLineEdit()
        self.username_edit.setPlaceholderText("tu_usuario")
        self.username_edit.setFixedHeight(34)
        user_row.addWidget(user_lbl)
        user_row.addWidget(self.username_edit)
        creds_layout.addLayout(user_row)

        token_row = QHBoxLayout()
        token_lbl = QLabel("Token:")
        token_lbl.setFixedWidth(90)
        token_lbl.setStyleSheet(f"color: {C_TEXT_SEC}; font-size: 12px;")
        self.token_edit = QLineEdit()
        self.token_edit.setPlaceholderText("hf_xxxxxxxxxxxxxxxxxxxx")
        self.token_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.token_edit.setFixedHeight(34)
        help_btn = QPushButton("?  Ayuda")
        help_btn.setFixedHeight(34)
        help_btn.setFixedWidth(90)
        help_btn.clicked.connect(self._show_help)
        token_row.addWidget(token_lbl)
        token_row.addWidget(self.token_edit)
        token_row.addWidget(help_btn)
        creds_layout.addLayout(token_row)

        layout.addWidget(creds_widget)

        # Lista de modelos
        layout.addWidget(_SectionLabel("MODELOS A DESCARGAR"))
        self.model_list = QListWidget()
        self.model_list.setMaximumHeight(120)
        for task in self._tasks:
            self.model_list.addItem(QListWidgetItem(f"  {task.label}   —   {task.hf_repo_id}"))
        layout.addWidget(self.model_list)

        # Progreso
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setFixedHeight(8)
        layout.addWidget(self.progress_bar)

        self.status_label = QLabel("Listo para descargar.")
        self.status_label.setStyleSheet(f"color: {C_TEXT_SEC}; font-size: 12px;")
        layout.addWidget(self.status_label)

        # Botones
        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)

        self.download_btn = QPushButton("⬇  Descargar modelos")
        self.download_btn.setObjectName("primary")
        self.download_btn.setFixedHeight(38)

        self.cancel_btn = QPushButton("✖  Cancelar descarga")
        self.cancel_btn.setObjectName("danger")
        self.cancel_btn.setFixedHeight(38)
        self.cancel_btn.setEnabled(False)

        self.close_btn = QPushButton("Cerrar")
        self.close_btn.setFixedHeight(38)

        self.download_btn.clicked.connect(self._on_download)
        self.cancel_btn.clicked.connect(self._on_cancel)
        self.close_btn.clicked.connect(self.reject)

        btn_row.addWidget(self.download_btn)
        btn_row.addWidget(self.cancel_btn)
        btn_row.addStretch()
        btn_row.addWidget(self.close_btn)
        layout.addLayout(btn_row)

    def _show_help(self) -> None:
        HelpDialog(self).exec()

    def _load_saved_credentials(self) -> None:
        username, token = load_credentials()
        if username:
            self.username_edit.setText(username)
        if token:
            self.token_edit.setText(token)

    def _on_download(self) -> None:
        token = self.token_edit.text().strip()
        if not token:
            QMessageBox.warning(self, "Token requerido", "Introduce tu token de HuggingFace.")
            return
        if not token.startswith("hf_"):
            resp = QMessageBox.question(
                self,
                "Token inusual",
                "El token no empieza por 'hf_'. ¿Continuar igualmente?",
            )
            if resp != QMessageBox.StandardButton.Yes:
                return

        self._cancel_event.clear()
        self._set_busy(True)
        self._downloading = True
        self.status_label.setText("Iniciando descarga...")

        self._thread = QThread()   # sin parent: evita destruccion automatica al cerrar el dialogo
        self._worker = DownloadWorker(self._tasks, token, self._cancel_event)
        self._worker.moveToThread(self._thread)

        self._thread.started.connect(self._worker.run)
        self._worker.progress.connect(self._on_progress)
        self._worker.task_done.connect(self._on_task_done)
        self._worker.all_done.connect(self._on_all_done)
        self._worker.failed.connect(self._on_failed)

        self._worker.all_done.connect(self._thread.quit)
        self._worker.failed.connect(self._thread.quit)
        self._thread.finished.connect(self._thread.deleteLater)
        self._thread.start()

    def _on_cancel(self) -> None:
        self._cancel_event.set()
        self.status_label.setText("Cancelando, espera a que termine el fichero en curso...")

    def _on_progress(self, value: int, message: str) -> None:
        self.progress_bar.setValue(value)
        self.status_label.setText(message)

    def _on_task_done(self, label: str) -> None:
        for i in range(self.model_list.count()):
            item = self.model_list.item(i)
            if label in item.text():
                item.setText(f"  ✓  {label}")
                item.setForeground(QColor(C_SUCCESS))

    def _on_all_done(self) -> None:
        save_credentials(self.username_edit.text().strip(), self.token_edit.text().strip())
        self._downloading = False
        self._set_busy(False)
        self.progress_bar.setValue(100)
        self.status_label.setText("Todos los modelos descargados correctamente.")
        QMessageBox.information(
            self,
            "Descarga completada",
            "Todos los modelos se han descargado.\nYa puedes generar imágenes.",
        )
        self.models_downloaded.emit()
        self.accept()

    def _on_failed(self, error: str) -> None:
        self._downloading = False
        self._set_busy(False)
        self.status_label.setText("Error en la descarga.")
        QMessageBox.critical(self, "Error de descarga", error)

    def _set_busy(self, busy: bool) -> None:
        self.download_btn.setEnabled(not busy)
        self.username_edit.setEnabled(not busy)
        self.token_edit.setEnabled(not busy)
        self.close_btn.setEnabled(not busy)
        self.cancel_btn.setEnabled(busy)

    def closeEvent(self, event) -> None:  # noqa: N802
        if self._downloading:
            resp = QMessageBox.question(
                self,
                "Descarga en curso",
                "Hay una descarga en curso. ¿Seguro que quieres cancelarla y cerrar?",
            )
            if resp != QMessageBox.StandardButton.Yes:
                event.ignore()
                return
        self._cancel_event.set()
        if self._thread and self._thread.isRunning():
            self._thread.quit()
            self._thread.wait()  # esperar sin limite hasta que el hilo termine limpiamente
        super().closeEvent(event)
