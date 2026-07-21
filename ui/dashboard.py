from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QFrame, QFileDialog,
    QGraphicsDropShadowEffect, QMessageBox
)
from PyQt6.QtGui import QPixmap, QColor
from PyQt6.QtCore import Qt
import sys
import os
import nibabel as nib
import pandas as pd

# Colonnes attendues dans le CSV clinique — à adapter selon le modele
REQUIRED_CLINICAL_COLUMNS = ["age", "sexe", "grade_tumeur"]  


class DashboardScreen(QWidget):
    def __init__(self):
        super().__init__()

        self.image_path = None
        self.clinical_path = None
        self.evaluate_button = None

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
        content_layout.setContentsMargins(60, 80, 60, 50)
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

        image_card = self.create_upload_card(
            "Image Médicale (NIFTI)", "Upload Images...",
            "NIFTI Files (*.nii *.nii.gz)", "image"
        )
        clinical_card = self.create_upload_card(
            "Données cliniques (.csv)", "Upload File...",
            "CSV Files (*.csv)", "clinical"
        )

        cards_layout.addWidget(image_card)
        cards_layout.addWidget(clinical_card)
        content_layout.addLayout(cards_layout)
        content_layout.addSpacing(30)

        evaluate_button = QPushButton("Evaluate prognosis")
        evaluate_button.setFixedHeight(45)
        evaluate_button.setCursor(Qt.CursorShape.PointingHandCursor)
        evaluate_button.setEnabled(False)
        evaluate_button.clicked.connect(self.run_evaluation)

        content_layout.addWidget(evaluate_button)
        content_layout.addStretch()

        self.evaluate_button = evaluate_button
        self.update_evaluate_button()  

        return content

    def create_upload_card(self, label_text, button_text, file_filter, key):
        card = QFrame()
        card.setFixedHeight(270)
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
        label.setFixedHeight(50)
        label.setStyleSheet("font-weight: 600; font-size: 14px; color: #111827;")

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
        upload_button.clicked.connect(lambda: self.select_file(upload_button, file_filter, key))

        card_layout.addWidget(label)
        card_layout.addWidget(upload_button)

        return card

    def select_file(self, button, file_filter, key):
        file_path, _ = QFileDialog.getOpenFileName(self, "Sélectionner un fichier", "", file_filter)
        if not file_path:
            return

        # verifie le format 
        if key == "image":
            ok, message = self.validate_image(file_path)
        else:
            ok, message = self.validate_clinical(file_path)

        if not ok:
            QMessageBox.critical(self, "Fichier invalide", message)
            return  # on n'accepte pas le fichier, self.image_path/clinical_path restent inchangés

        if key == "image":
            self.image_path = file_path
        elif key == "clinical":
            self.clinical_path = file_path

        filename = os.path.basename(file_path)
        button.setText(f" ✔ {filename}")
        button.setStyleSheet("""
            QPushButton {
                border: 1.5px solid #2dd4bf;
                border-radius: 10px;
                padding: 30px;
                background-color: #ccfbf1;
                color: #0f766e;
                font-size: 13px;
                font-weight: 600;
            }
        """)

        self.update_evaluate_button()

    def validate_image(self, file_path):
        """Vérifie que le fichier NIFTI est lisible et exploitable."""
        try:
            img = nib.load(file_path)
        except Exception as e:
            return False, f"Impossible de lire le fichier NIFTI :\n{e}"

        data = img.get_fdata()

        if data.ndim not in (3, 4):
            return False, f"Dimension inattendue : {data.ndim}D (3D ou 4D attendu)."

        if data.size == 0:
            return False, "L'image est vide."

        # Volume entièrement à zéro = scan probablement vide/corrompu
        if not (data != 0).any():
            return False, "L'image ne contient que des zéros (scan vide ou corrompu)."

        return True, ""

    def validate_clinical(self, file_path):
        """Vérifie que le CSV a les bonnes colonnes et pas de données manquantes critiques."""
        try:
            df = pd.read_csv(file_path)
        except Exception as e:
            return False, f"Impossible de lire le fichier CSV :\n{e}"

        if df.empty:
            return False, "Le fichier CSV est vide."

        missing_columns = [c for c in REQUIRED_CLINICAL_COLUMNS if c not in df.columns]
        if missing_columns:
            return False, "Colonnes manquantes dans le CSV :\n- " + "\n- ".join(missing_columns)

        # Vérifie les valeurs manquantes uniquement sur les colonnes requises
        na_report = df[REQUIRED_CLINICAL_COLUMNS].isna().sum()
        na_report = na_report[na_report > 0]
        if not na_report.empty:
            details = "\n".join(f"- {col} : {count} valeur(s) manquante(s)" for col, count in na_report.items())
            return False, f"Données manquantes détectées :\n{details}"

        return True, ""

    def update_evaluate_button(self):
        ready = self.image_path is not None and self.clinical_path is not None
        self.evaluate_button.setEnabled(ready)
        self.evaluate_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {"#2563eb" if ready else "#6b7280"};
                color: white;
                border-radius: 6px;
                font-weight: bold;
                font-size: 14px;
            }}
            QPushButton:hover {{
                background-color: {"#1d4ed8" if ready else "#4b5563"};
            }}
        """)

    def run_evaluation(self):
        if not self.image_path or not self.clinical_path:
            return
        print(f"Analyse en cours : {self.image_path} + {self.clinical_path}")
        # branche ici ton pipeline (chargement NIFTI, lecture CSV, appel au modèle)

    def _make_shadow(self):
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setXOffset(0)
        shadow.setYOffset(4)
        shadow.setColor(QColor(0, 0, 0, 25))
        return shadow


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = DashboardScreen()
    window.resize(1100, 700)
    window.show()
    sys.exit(app.exec())