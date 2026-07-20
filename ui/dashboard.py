from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QFrame, QFileDialog
)
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt
import sys
import os
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import QGraphicsDropShadowEffect

class DashboardScreen(QWidget):
    def __init__(self):
        super().__init__()

        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet("background-color: #f4f5f7;")

        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        sidebar = self.build_sidebar()
        content = self.build_content()

        main_layout.addWidget(sidebar)
        main_layout.addWidget(content)

        self.setLayout(main_layout)

    
    def build_sidebar(self):
        sidebar = QWidget()
        sidebar.setFixedWidth(250)
        sidebar.setStyleSheet("background-color: #111827;")

        sidebar_layout = QVBoxLayout()
        sidebar_layout.setContentsMargins(20, 30, 20, 20)
        sidebar_layout.setSpacing(10)
        sidebar.setLayout(sidebar_layout)

        logo = QLabel()
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_path = "assets/logo.png"
        if os.path.exists(logo_path):
            pixmap = QPixmap(logo_path)
            logo.setPixmap(pixmap.scaled(
                150, 150,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            ))
        else:
            logo.setText("NeuroPronostic")
            logo.setStyleSheet("color: white; font-size: 18px; font-weight: bold;")
        sidebar_layout.addWidget(logo)
        sidebar_layout.addSpacing(20)

        button_style = """
            QPushButton {
                background-color: transparent;
                color: #d1d5db;
                border: none;
                padding: 12px 15px;
                border-radius: 8px;
                text-align: left;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #1f2937;
                color: white;
            }
            QPushButton:pressed {
                background-color: #2563eb;
                color: white;
            }
        """

        active_button_style = """
            QPushButton {
                background-color: #2563eb;
                color: white;
                border: none;
                padding: 12px 15px;
                border-radius: 8px;
                text-align: left;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1d4ed8;
            }
        """

        dashboard_button = QPushButton("  Dashboard")
        historique_button = QPushButton("  Historique")
        patients_button = QPushButton("  Patients")
        settings_button = QPushButton("  Paramètres")

        dashboard_button.setStyleSheet(active_button_style)
        historique_button.setStyleSheet(button_style)
        patients_button.setStyleSheet(button_style)
        settings_button.setStyleSheet(button_style)

        for btn in (dashboard_button, historique_button, patients_button, settings_button):
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setFixedHeight(45)
            sidebar_layout.addWidget(btn)

        sidebar_layout.addStretch()

        logout_button = QPushButton("  Déconnexion")
        logout_button.setCursor(Qt.CursorShape.PointingHandCursor)
        logout_button.setFixedHeight(45)
        logout_button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #f87171;
                border: 1px solid #f87171;
                padding: 12px 15px;
                border-radius: 8px;
                text-align: left;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #f87171;
                color: white;
            }
        """)
        sidebar_layout.addWidget(logout_button)

        return sidebar

  
    def build_content(self):
        content = QWidget()
        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(60, 50, 60, 50)
        content_layout.setSpacing(10)
        content.setLayout(content_layout)
       
        title = QLabel("NeuroPronostic")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 32px; font-weight: bold; color: #374151;")

        subtitle = QLabel(
            "Upload a medical scan and clinical data — get an instant prognosis and segmentation.\n"
            "Powered by deep learning, from image to insight."
        )
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setWordWrap(True)
        subtitle.setStyleSheet("color: #0f9f76; font-size: 13px;")

        content_layout.addWidget(title)
        content_layout.addWidget(subtitle)
        content_layout.addSpacing(90)

        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(30)

        image_card = self.create_upload_card("Image Médicale (NIFTI)", "Upload Images...")
        clinical_card = self.create_upload_card("Données cliniques (.csv)", "Upload File...")

        cards_layout.addWidget(image_card)
        cards_layout.addWidget(clinical_card)
        content_layout.addLayout(cards_layout)
        content_layout.addSpacing(30)

        evaluate_button = QPushButton("Evaluate prognosis")
        evaluate_button.setFixedHeight(45)
        evaluate_button.setCursor(Qt.CursorShape.PointingHandCursor)
        evaluate_button.setStyleSheet("""
            QPushButton {
                background-color: #6b7280;
                color: white;
                border-radius: 6px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #4b5563;
            }
        """)
        content_layout.addWidget(evaluate_button)
        content_layout.addStretch()

        return content

    def create_upload_card(self, label_text, button_text):
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #e5e7eb;
                border-radius: 12px;
            }
        """)
        card.setGraphicsEffect(self._make_shadow())

        card_layout = QVBoxLayout()
        card_layout.setContentsMargins(24, 24, 24, 24)
        card_layout.setSpacing(16)
        card.setLayout(card_layout)

        label = QLabel(label_text)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet("""
            font-weight: 600;
            font-size: 14px;
            color: #111827;
        """)

        upload_button = QPushButton(f" {button_text}")
        upload_button.setCursor(Qt.CursorShape.PointingHandCursor)
        upload_button.setMinimumHeight(120)
        upload_button.setStyleSheet("""
            QPushButton {
                border: 1.5px dashed #99f6e4;
                border-radius: 10px;
                padding: 30px;
                background-color: #f0fdfa;
                color: #0d9488;
                font-size: 13px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #ccfbf1;
                border-color: #2dd4bf;
                color: #0f766e;
            }
        """)
        upload_button.clicked.connect(lambda: self.select_file(button_text))


        card_layout.addWidget(label)
        card_layout.addWidget(upload_button)

        return card

    def _make_shadow(self):
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setXOffset(0)
        shadow.setYOffset(4)
        shadow.setColor(QColor(0, 0, 0, 25))
        return shadow
    def select_file(self, context_label):
        file_path, _ = QFileDialog.getOpenFileName(self, f"Sélectionner - {context_label}")
        if file_path:
            print(f"[{context_label}] Fichier sélectionné : {file_path}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = DashboardScreen()
    window.resize(1100, 700)
    window.show()
    sys.exit(app.exec())