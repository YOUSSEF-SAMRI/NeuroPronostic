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
import numpy as np
from ui.manage_users import ManageUsersScreen 



REQUIRED_CLINICAL_COLUMNS = [
                            "Center",
                            "Sex",
                            "Age",
                            "Atrial fibrillation",
                            "Hypertension",
                            "Diabetes",
                            "Hyperlipidemia",
                            "Anticoagulation",
                            "Lipid lowering drugs",
                            "PAIs",
                            "Glucose",
                            "Leucocytes",
                            "CRP",
                            "INR",
                            "Wake-up",
                            "In-House",
                            "Referral",
                            "Onset to door",
                            "Alert to door",
                            "NIHSS at admission",
                            "mRS at admission",
                            "mRS premorbid",
                            "Door to imaging",
                            "Door to groin",
                            "Door to first series",
                            "Time of intervention",
                            "Door to recanalization",
                            ]  
STRICTLY_REQUIRED_COLUMNS = [
                            "Age",
                            "Sex",
                            "NIHSS at admission",
                            "mRS premorbid",
                            ]


class DashboardScreen(QWidget):
    def __init__(self,stack=None,user_id=None, nom=None, role="user"):
        super().__init__()
        self.stack = stack
        self.user_id = user_id
        self.nom = nom
        self.role = role
        self.users_button = None  

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
        sidebar.setStyleSheet("background-color: #111837;")

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
            
        self.users_button = QPushButton("  Gérer les utilisateurs")
        self.users_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.users_button.setFixedHeight(45)
        self.users_button.setStyleSheet(button_style)
        self.users_button.clicked.connect(self.open_register)
        self.users_button.setVisible(self.role == "admin")
        sidebar_layout.addWidget(self.users_button)
            
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
        logout_button.clicked.connect(self.handle_logout)
        sidebar_layout.addWidget(logout_button)

        return sidebar
    
    def handle_logout(self):
        box = QMessageBox(self)
        box.setWindowTitle("Déconnexion")
        box.setText("Voulez-vous vraiment vous déconnecter ?")
        box.setIcon(QMessageBox.Icon.Question)
        box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        box.setDefaultButton(QMessageBox.StandardButton.No)

        box.setStyleSheet("""
            QMessageBox QLabel {
                color: #111827;
                font-size: 14px;
            }
            QPushButton {
                background-color: #f3f4f6;
                color: #111827;
                border: 1px solid #d1d5db;
                border-radius: 6px;
                padding: 6px 18px;
                min-width: 70px;
            }
            QPushButton:hover {
                background-color: #e5e7eb;
            }
            QPushButton:default {
                background-color: #2563eb;
                color: white;
                border: none;
            }
            QPushButton:default:hover {
                background-color: #1d4ed8;
            }
        """)

        answer = box.exec()

        if answer != QMessageBox.StandardButton.Yes:
            return 

        # Nettoyer la session
        self.user_id = None
        self.nom = None
        self.role = "user"
        if self.users_button:
            self.users_button.setVisible(False)

        # Nettoyer les fichiers uploadés
        self.image_path = None
        self.clinical_path = None
        self.update_evaluate_button()
        self.reset_upload_buttons()

        # Retour au login
        if self.stack:
            self.stack.setCurrentIndex(0)

    def reset_upload_buttons(self):
        default_style = """
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
        """
        if hasattr(self, "image_upload_button"):
            self.image_upload_button.setText(" Upload Images...")
            self.image_upload_button.setStyleSheet(default_style)
        if hasattr(self, "clinical_upload_button"):
            self.clinical_upload_button.setText(" Upload File...")
            self.clinical_upload_button.setStyleSheet(default_style)
            
            
    def open_register(self):
        if self.role != "admin":
            return 
        self.register_window = ManageUsersScreen()
        self.register_window.show()
        
        
    def set_user(self, user_id, nom, role):
        self.user_id  = user_id
        self.nom = nom
        self.role = role
        if self.users_button:
            self.users_button.setVisible(role == "admin")
            
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

        if key == "image":
            self.image_upload_button = upload_button
        elif key == "clinical":
            self.clinical_upload_button = upload_button
            
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
            self.show_error_message("Fichier invalide", message)
            return 
        if message:  # warning non-bloquant (données secondaires manquantes)
            self.show_warning_message("Attention", message)

        if key == "image":
            self.image_path = file_path
        elif key == "clinical":
            self.clinical_path = file_path

        filename = os.path.basename(file_path)
        button.setText(f"  {filename}")
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
        
    def show_warning_message(self, title, text):
        box = QMessageBox(self)
        box.setWindowTitle(title)
        box.setText(text)
        box.setIcon(QMessageBox.Icon.Warning)
        box.setStandardButtons(QMessageBox.StandardButton.Ok)
        box.setStyleSheet("""
            QMessageBox { min-width: 350px; }
            QMessageBox QLabel { color: #1f2937; font-size: 13px; }
            QPushButton {
                background-color: #f59e0b;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px 24px;
                min-width: 70px;
                font-weight: 600;
            }
            QPushButton:hover { background-color: #d97706; }
        """)
        box.exec()    
        
    def show_error_message(self, title, text):
        box = QMessageBox(self)          
        box.setWindowTitle(title)
        box.setText(text)
        box.setIcon(QMessageBox.Icon.Critical)
        box.setStandardButtons(QMessageBox.StandardButton.Ok)

        box.setStyleSheet("""
            QMessageBox {
                min-width: 350px;
            }
            QMessageBox QLabel {
                color: #1f2937;
                font-size: 13px;
            }
            QPushButton {
                background-color: #f87171;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px 24px;
                min-width: 70px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #ef4444;
            }
            QPushButton:pressed {
                background-color: #dc2626;
            }
        """)
        box.exec()

    def validate_image(self, file_path):
        """Vérifie que le fichier NIFTI est lisible et exploitable."""
        try:
            img = nib.load(file_path)
        except Exception as e:
            return False, f"Impossible de lire le fichier NIFTI :\n{e}"

        # Check dimensions sans charger les données en mémoire
        shape = img.shape
        if len(shape) not in (3, 4):
            return False, f"Dimension inattendue : {len(shape)}D (3D ou 4D attendu)."
        if any(d < 10 for d in shape[:3]):
            return False, f"Résolution trop faible : {shape[:3]} (minimum 10x10x10 attendu)."

        data = img.get_fdata()

        if not np.isfinite(data).all():
            return False, "L'image contient des valeurs invalides (NaN/Inf) — scan probablement corrompu."

        if not (data != 0).any():
            return False, "L'image ne contient que des zéros (scan vide ou corrompu)."

        return True, ""

    def validate_clinical(self, file_path):
        """Vérifie que le CSV a les bonnes colonnes et pas de données manquantes critiques."""
        try:
            df = pd.read_csv(file_path,sep=None, engine="python")
        except Exception as e:
            return False, f"Impossible de lire le fichier CSV :\n{e}"

        if df.empty:
            return False, "Le fichier CSV est vide."

        missing_columns = [c for c in REQUIRED_CLINICAL_COLUMNS if c not in df.columns]
        if missing_columns:
            return False, "Colonnes manquantes dans le CSV :\n- " + "\n- ".join(missing_columns)

        # Bloquant : seulement les champs strictement nécessaires
        critical_na = df[STRICTLY_REQUIRED_COLUMNS].isna().sum()
        critical_na = critical_na[critical_na > 0]
        if not critical_na.empty:
            details = "\n".join(f"- {col} : {count} valeur(s) manquante(s)" for col, count in critical_na.items())
            return False, f"Données critiques manquantes :\n{details}"
        
        # Non-bloquant : le reste, juste un avertissement
        other_columns = [c for c in REQUIRED_CLINICAL_COLUMNS if c not in STRICTLY_REQUIRED_COLUMNS]
        na_report = df[other_columns].isna().sum()
        na_report = na_report[na_report > 0]
        warning = ""
        if not na_report.empty:
            details = "\n".join(f"- {col} : {count} valeur(s) manquante(s)" for col, count in na_report.items())
            warning = f"Attention, données secondaires manquantes (l'upload continue quand même) :\n{details}"

        return True, warning



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
        # branche ici le pipeline (chargement NIFTI, lecture CSV, appel au modèle)

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

