from PySide6.QtWidgets import QDialog, QPushButton, QTextBrowser, QVBoxLayout

from persona.ui.theme import (
    APP_STYLE, C_BG, C_SURFACE, C_BORDER, C_TEXT_PRI, C_TEXT_SEC,
    C_ACCENT1, C_ACCENT2, C_WARN, PERSONA_G0, PERSONA_G1,
)


class HelpDialog(QDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Ayuda — Cuenta y Token de HuggingFace")
        self.setMinimumWidth(580)
        self.setMinimumHeight(560)
        self.setStyleSheet(APP_STYLE)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 16)
        layout.setSpacing(12)

        browser = QTextBrowser()
        browser.setOpenLinks(False)
        browser.setStyleSheet(
            f"background: {C_SURFACE}; border: 1px solid {C_BORDER};"
            f"border-radius: 10px; padding: 8px;"
        )
        browser.setHtml(
            f"""
            <style>
                body  {{
                    font-family: 'Segoe UI', Arial, sans-serif;
                    font-size: 13px;
                    line-height: 1.6;
                    color: {C_TEXT_PRI};
                    background: {C_SURFACE};
                    margin: 4px 8px;
                }}
                h2    {{ color: {PERSONA_G0}; font-size: 16px; margin-bottom: 4px; }}
                h3    {{ color: {PERSONA_G1}; font-size: 13px; margin-top: 18px; }}
                ol,ul {{ margin-left: 20px; color: {C_TEXT_SEC}; }}
                li    {{ margin-bottom: 4px; }}
                code  {{
                    background: {C_BG};
                    color: {C_ACCENT2};
                    padding: 1px 5px;
                    border-radius: 4px;
                    font-size: 12px;
                }}
                .warn {{
                    background: {C_WARN}22;
                    border-left: 3px solid {C_WARN};
                    padding: 10px 14px;
                    border-radius: 6px;
                    margin-top: 16px;
                    color: {C_TEXT_SEC};
                }}
            </style>

            <h2>&#x2753; Cómo crear una cuenta y token en HuggingFace</h2>

            <h3>Paso 1 &mdash; Crear una cuenta gratuita</h3>
            <ol>
              <li>Abre en tu navegador:<br>
                  <code>https://huggingface.co/join</code></li>
              <li>Rellena el formulario (email y contraseña).</li>
              <li>Confirma tu email cuando lo recibas.</li>
            </ol>

            <h3>Paso 2 &mdash; Generar un token de acceso</h3>
            <ol>
              <li>Inicia sesión en <code>https://huggingface.co</code></li>
              <li>Haz clic en tu avatar (arriba a la derecha) &rarr; <b>Settings</b>.</li>
              <li>En el menú lateral selecciona <b>Access Tokens</b>.</li>
              <li>Pulsa <b>New token</b>.</li>
              <li>Dale un nombre, por ejemplo: <i>SpanishFly</i>.</li>
              <li>Elige el rol <b>Read</b> (suficiente para descargar modelos).</li>
              <li>Pulsa <b>Generate a token</b> y copia el valor
                  (empieza por <code>hf_...</code>).</li>
            </ol>

            <h3>Paso 3 &mdash; Aceptar los términos de uso de los modelos</h3>
            <p style="color:{C_TEXT_SEC}">Algunos modelos requieren que aceptes sus condiciones
            antes de descargarlos. Visita la página del modelo en HuggingFace, inicia sesión
            y acepta los términos.</p>
            <ul>
              <li>SDXL Base:
                  <code>https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0</code>
              </li>
              <li>ControlNet Union:
                  <code>https://huggingface.co/xinsir/controlnet-union-sdxl-1.0</code>
              </li>
              <li>IP-Adapter:
                  <code>https://huggingface.co/h94/IP-Adapter</code>
              </li>
            </ul>

            <div class="warn">
              <b>&#x26A0; Seguridad:</b> Tu token equivale a una contraseña.
              Nunca lo compartas ni lo incluyas en código fuente público.<br>
              Si crees que está comprometido, revócalo en
              <code>Settings &rarr; Access Tokens &rarr; Delete</code>.
            </div>
            """
        )
        layout.addWidget(browser)

        close_btn = QPushButton("Cerrar")
        close_btn.setFixedHeight(36)
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)

