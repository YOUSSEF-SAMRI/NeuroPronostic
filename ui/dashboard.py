from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QFileDialog
)
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt
import sys
import os


class DashboardScreen(QWidget):
    def __init__(self):
        super().__init__()

        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet("background-color: #f4f5f7;")

        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        sidebar = QWidget()
        sidebar.setFixedWidth(250)
        sidebar.setStyleSheet("background-color: #111827;")

        sidebar_layout = QVBoxLayout()
        sidebar_layout.setContentsMargins(20, 30, 20, 20)
        sidebar_layout.setSpacing(8)
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

        content = QWidget()
        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(30, 30, 30, 30)
        content.setLayout(content_layout)

        title = QLabel("NeuroPronostic")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #111827;")
        content_layout.addWidget(title)
        content_layout.addStretch()

        main_layout.addWidget(sidebar)
        main_layout.addWidget(content)

        self.setLayout(main_layout)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = DashboardScreen()
    window.resize(1000, 650)
    window.show()
    sys.exit(app.exec())