from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QFrame, QFileDialog,
    QGraphicsDropShadowEffect, QMessageBox
)
from PyQt6.QtWidgets import QDialog, QSlider, QComboBox
from PyQt6.QtWidgets import QScrollArea
from PyQt6.QtWidgets import QStackedWidget
from PyQt6.QtGui import QPixmap, QColor ,QImage
from PyQt6.QtCore import Qt
import sys
import os
import nibabel as nib
import pandas as pd
import numpy as np
from ui.manage_users import ManageUsersScreen 
from PyQt6.QtWidgets import QTableWidget, QTableWidgetItem
from ui.patient_dialog import AddPatientDialog
from models.patients import add_patient, get_patients_by_medecin


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
         
        
        self.all_patients = []
        self.current_page = 1
        self.page_size = 10

        self.image_path = None
        self.clinical_path = None
        self.evaluate_button = None
        
        self.patient_uploads = {}   # {patient_id: {"image": path_or_None, "clinical": path_or_None}}
        self.current_patient = None
        
        self.scrollbar_style = """
                                QScrollBar:vertical {
                                    background: transparent;
                                    width: 10px;
                                    margin: 4px 2px 4px 0px;
                                }
                                QScrollBar::handle:vertical {
                                    background: #cbd5e1;
                                    border-radius: 5px;
                                    min-height: 30px;
                                }
                                QScrollBar::handle:vertical:hover {
                                    background: #94a3b8;
                                }
                                QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                                    height: 0px;
                                    background: none;
                                    border: none;
                                }
                                QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                                    background: none;
                                }
                            """

        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet("background-color: #f4f5f7;")

        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        sidebar = self.build_sidebar()
        self.content_stack = QStackedWidget()
        self.dashboard_page = self.build_content()     
        self.patients_page = self.build_patients_page()      

        self.content_stack.addWidget(self.dashboard_page)
        self.content_stack.addWidget(self.patients_page)
        
        self.patient_detail_page = self.build_patient_detail_page()  
        self.content_stack.addWidget(self.patient_detail_page)
        
        main_layout.addWidget(sidebar)
        main_layout.addWidget(self.content_stack)
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
        
        self.button_style = button_style
        self.active_button_style = active_button_style
        self.nav_buttons = [dashboard_button, historique_button, patients_button, settings_button]

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
        dashboard_button.clicked.connect(lambda: self.switch_page(0, dashboard_button))
        patients_button.clicked.connect(lambda: self.switch_page(1, patients_button))
        logout_button.clicked.connect(self.handle_logout)
        sidebar_layout.addWidget(logout_button)

        return sidebar
    
    def switch_page(self, index, active_button):
        self.content_stack.setCurrentIndex(index)

        for btn in self.nav_buttons:
            btn.setStyleSheet(self.button_style)
        active_button.setStyleSheet(self.active_button_style)

        if index == 1:  # page Patients
            self.load_patients()
        
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
        
        self.all_patients = []
        self.current_page = 1
        self.current_patient = None
        self.patient_uploads = {}
        self.content_stack.setCurrentIndex(0)
        for btn in self.nav_buttons:
            btn.setStyleSheet(self.button_style)
        self.nav_buttons[0].setStyleSheet(self.active_button_style)

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
            
    def reset_patient_upload_buttons(self):
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
        if hasattr(self, "patient_image_upload_button"):
            self.patient_image_upload_button.setText(" Upload Images...")
            self.patient_image_upload_button.setStyleSheet(default_style)
        if hasattr(self, "patient_clinical_upload_button"):
            self.patient_clinical_upload_button.setText(" Upload File...")
            self.patient_clinical_upload_button.setStyleSheet(default_style)
            
            
    def open_register(self):
        if self.role != "admin":
            return 
        self.register_window = ManageUsersScreen()
        self.register_window.show()
        
    def reset_to_dashboard(self):
        # Retour à la page Dashboard
        self.content_stack.setCurrentIndex(0)
        for btn in self.nav_buttons:
            btn.setStyleSheet(self.button_style)
        self.nav_buttons[0].setStyleSheet(self.active_button_style)  # Dashboard actif

        # Vider les données de l'ancien médecin
        self.all_patients = []
        self.current_page = 1
        self.current_patient = None
        self.patient_uploads = {}

        # Vider les uploads du dashboard général
        self.image_path = None
        self.clinical_path = None
        self.update_evaluate_button()
        self.reset_upload_buttons()

    def set_user(self, user_id, nom, role):
        self.user_id = user_id
        self.nom = nom
        self.role = role
        if self.users_button:
            self.users_button.setVisible(role == "admin")
        self.reset_to_dashboard()
        
        
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

    def create_upload_card(self, label_text, button_text, file_filter, key ,scope="dashboard"):
        card = QFrame()
        if scope == "dashboard":
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
        upload_button.setMinimumHeight(100)
        upload_button.setStyleSheet("""
            QPushButton {
                border: 1.5px dashed #99f6e4; border-radius: 10px; padding: 24px;
                background-color: #f0fdfa; color: #0d9488; font-size: 13px; font-weight: 500;
            }
            QPushButton:hover { background-color: #ccfbf1; border-color: #2dd4bf; color: #0f766e; }
        """)
        upload_button.clicked.connect(lambda: self.select_file(upload_button, file_filter, key, scope))
        
        preview_label = QLabel("")
        preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        preview_label.setFixedHeight(170)
        preview_label.setStyleSheet("color: #6b7280; font-size: 12px;")
        preview_label.setVisible(False)
        
        view_button = QPushButton(" Visualiser")
        view_button.setCursor(Qt.CursorShape.PointingHandCursor)
        view_button.setStyleSheet("""
            QPushButton {
                background-color: #eff6ff;
                color: #2563eb;
                border: 1px solid #bfdbfe;
                border-radius: 6px;
                padding: 6px 10px;
                font-size: 12px;
                font-weight: 600;
            }
            QPushButton:hover { background-color: #dbeafe; }
        """)
        view_button.setVisible(False)
        card_layout.addWidget(view_button)

        card_layout.addWidget(label)
        card_layout.addWidget(upload_button)
        card_layout.addWidget(preview_label)
            
        if scope == "dashboard":
            if key == "image":
                self.image_upload_button = upload_button
            elif key == "clinical":
                self.clinical_upload_button = upload_button
        else:  # scope == "patient"
            view_button.clicked.connect(lambda: self.open_viewer(key))
            if key == "image":
                self.patient_image_upload_button = upload_button
                self.patient_image_preview = preview_label
                self.patient_image_view_button = view_button
            elif key == "clinical":
                self.patient_clinical_upload_button = upload_button
                self.patient_clinical_preview = preview_label
                self.patient_clinical_view_button = view_button

            
        

        return card
    
    
    def build_patients_page(self):
        page = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(60, 50, 60, 50)
        layout.setSpacing(20)
        page.setLayout(layout)

        header_layout = QHBoxLayout()
        title = QLabel("Mes patients")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #374151;")

        add_button = QPushButton("  Ajouter un patient")
        add_button.setCursor(Qt.CursorShape.PointingHandCursor)
        add_button.setFixedHeight(40)
        add_button.setStyleSheet("""
            QPushButton {
                background-color: #2563eb;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px 18px;
                font-weight: 600;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #1d4ed8;
            }
        """)
        add_button.clicked.connect(self.open_add_patient_dialog)

        
        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(add_button)
        layout.addLayout(header_layout)

        # etat vide
        self.empty_state_label = QLabel("Aucun patient pour l'instant.\nCliquez sur \"Ajouter un patient\" pour commencer.")
        self.empty_state_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_state_label.setStyleSheet("color: #9ca3af; font-size: 14px; padding: 80px 0;")

        # table
        self.patients_table = QTableWidget()
        self.patients_table.setColumnCount(6)
        self.patients_table.setHorizontalHeaderLabels(["Nom", "Prénom", "Âge", "Sexe", "Date d'ajout", "Actions"])
        self.patients_table.horizontalHeader().setStretchLastSection(True)
        self.patients_table.setColumnWidth(0, 150)  # Nom
        self.patients_table.setColumnWidth(1, 150)  # Prénom
        self.patients_table.setColumnWidth(2, 80)   # Âge
        self.patients_table.setColumnWidth(3, 80)   # Sexe
        self.patients_table.setColumnWidth(4, 150)  # Date d'ajout
        self.patients_table.setColumnWidth(5, 120)  # Actions
        self.patients_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.patients_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.patients_table.setStyleSheet("""
    QTableWidget {
        background-color: white;
        border: 1px solid #e5e7eb;
        border-radius: 8px;
        gridline-color: #f3f4f6;
    }
    QTableWidget::item {
        color: #111827;
        padding: 8px;
        border: none;
    }
    QTableWidget::item:selected {
        background-color: #f3f4f6;
        color: #111827;
        outline: none;

    }
    QHeaderView::section {
        background-color: #f9fafb;
        color: #374151;
        font-weight: 600;
        padding: 8px;
        border: none;
        border-bottom: 1px solid #e5e7eb;
    }
     QScrollBar:vertical {
        background: transparent;
        width: 10px;
        margin: 4px 2px 4px 0px;
    }
    QScrollBar::handle:vertical {
        background: #cbd5e1;
        border-radius: 5px;
        min-height: 30px;
    }
    QScrollBar::handle:vertical:hover {
        background: #94a3b8;
    }
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
        height: 0px;
        background: none;
        border: none;
    }
    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
        background: none;
    }

    QScrollBar:horizontal {
        background: transparent;
        height: 10px;
        margin: 0px 4px 2px 4px;
    }
    QScrollBar::handle:horizontal {
        background: #cbd5e1;
        border-radius: 5px;
        min-width: 30px;
    }
    QScrollBar::handle:horizontal:hover {
        background: #94a3b8;
    }
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
        width: 0px;
        background: none;
        border: none;
    }
    QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
        background: none;
    }

    """)
        self.patients_table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.patients_table.setVisible(False)
        

        pagination_layout = QHBoxLayout()
        pagination_layout.setContentsMargins(0, 10, 0, 0)

        self.prev_button = QPushButton("←  Précédent")
        self.next_button = QPushButton("Suivant  →")
        self.page_label = QLabel("Page 1 / 1")

        pagination_button_style = """
            QPushButton {
                background-color: white;
                color: #374151;
                border: 1px solid #e5e7eb;
                border-radius: 6px;
                padding: 6px 14px;
                font-size: 12px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #f3f4f6;
            }
            QPushButton:disabled {
                color: #d1d5db;
                background-color: #f9fafb;
            }
        """
        self.prev_button.setStyleSheet(pagination_button_style)
        self.next_button.setStyleSheet(pagination_button_style)
        self.prev_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.next_button.setCursor(Qt.CursorShape.PointingHandCursor)

        self.page_label.setStyleSheet("color: #6b7280; font-size: 13px; font-weight: 500;")
        self.page_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.prev_button.clicked.connect(self.go_to_previous_page)
        self.next_button.clicked.connect(self.go_to_next_page)

        pagination_layout.addStretch()
        pagination_layout.addWidget(self.prev_button)
        pagination_layout.addWidget(self.page_label)
        pagination_layout.addWidget(self.next_button)
        pagination_layout.addStretch()

        layout.addLayout(pagination_layout)

        layout.addWidget(self.empty_state_label)
        layout.addWidget(self.patients_table)
        

        return page
    
    # def refresh_patients_display(self, patients=None):
    #     """patients: liste de tuples venant de la DB. None ou [] = aucun patient."""
    #     if not patients:
    #         self.empty_state_label.setVisible(True)
    #         self.patients_table.setVisible(False)
    #     else:
    #         self.empty_state_label.setVisible(False)
    #         self.patients_table.setVisible(True)

    def open_add_patient_dialog(self):
        dialog = AddPatientDialog(self)
        if dialog.exec():
            data = dialog.get_data()
            try:
                add_patient(self.user_id, data["nom"], data["prenom"], data["age"], data["sexe"])
                self.load_patients()
            except Exception as e:
                self.show_error_message("Erreur", f"Impossible d'ajouter le patient :\n{e}")
                
    
    
    def load_patients(self):
        self.all_patients = get_patients_by_medecin(self.user_id)
        self.current_page = 1
        self.render_page()

    def refresh_patients_display(self, patients=None):
        """patients: liste de tuples venant de la DB. None ou [] = aucun patient."""
        has_patients = bool(self.all_patients)
        self.empty_state_label.setVisible(not has_patients)
        self.patients_table.setVisible(has_patients)
        self.prev_button.setVisible(has_patients)
        self.next_button.setVisible(has_patients)
        self.page_label.setVisible(has_patients)

    def total_pages(self):
        if not self.all_patients:
            return 1
        return (len(self.all_patients) - 1) // self.page_size + 1

    def render_page(self):
        self.refresh_patients_display()

        total = self.total_pages()
        self.current_page = max(1, min(self.current_page, total))

        start = (self.current_page - 1) * self.page_size
        end = start + self.page_size
        page_patients = self.all_patients[start:end]

        self.patients_table.setRowCount(len(page_patients))
        self.patients_table.verticalHeader().setDefaultSectionSize(48)

        for row, patient in enumerate(page_patients):
            id_, nom, prenom, age, sexe, created_at = patient
            self.patients_table.setItem(row, 0, QTableWidgetItem(nom))
            self.patients_table.setItem(row, 1, QTableWidgetItem(prenom))
            self.patients_table.setItem(row, 2, QTableWidgetItem(str(age)))
            self.patients_table.setItem(row, 3, QTableWidgetItem(sexe))
            self.patients_table.setItem(row, 4, QTableWidgetItem(created_at.strftime("%d/%m/%Y")))

            show_button = QPushButton("Afficher")
            show_button.setCursor(Qt.CursorShape.PointingHandCursor)
            show_button.setStyleSheet("""
                QPushButton {
                    background-color: #eff6ff;
                    color: #2563eb;
                    border: 1px solid #bfdbfe;
                    border-radius: 6px;
                    padding: 4px 12px;
                    font-size: 12px;
                    font-weight: 600;
                }
                QPushButton:hover {
                    background-color: #dbeafe;
                }
            """)
            show_button.setFixedWidth(90)
            show_button.setFixedHeight(28)
            show_button.clicked.connect(lambda checked, p=patient: self.show_patient_details(p))
            self.patients_table.setCellWidget(row, 5, show_button)

        self.page_label.setText(f"Page {self.current_page} / {total}")
        self.prev_button.setEnabled(self.current_page > 1)
        self.next_button.setEnabled(self.current_page < total)

    def go_to_previous_page(self):
        if self.current_page > 1:
            self.current_page -= 1
            self.render_page()

    def go_to_next_page(self):
        if self.current_page < self.total_pages():
            self.current_page += 1
            self.render_page()
        
    def show_patient_details(self, patient):
        id_, nom, prenom, age, sexe, created_at = patient
        self.current_patient = patient

        initials = (nom[:1] + prenom[:1]).upper() if nom and prenom else "?"
        self.patient_avatar_label.setText(initials)
        self.patient_name_label.setText(f"{nom} {prenom}")
        self.patient_age_badge.setText(f"{age} ans")
        self.patient_sexe_badge.setText("Femme" if sexe == "F" else "Homme")
        self.patient_date_badge.setText(created_at.strftime("%d/%m/%Y"))

        self.reset_patient_upload_buttons()
        self.patient_image_preview.setVisible(False)
        self.patient_clinical_preview.setVisible(False)

        uploads = self.patient_uploads.get(id_, {"image": None, "clinical": None})
        self.patient_image_view_button.setVisible(bool(uploads["image"]))
        self.patient_clinical_view_button.setVisible(bool(uploads["clinical"]))
        if uploads["image"]:
            self.patient_image_upload_button.setText(f"  {os.path.basename(uploads['image'])}")
            self.show_image_preview(uploads["image"])
        if uploads["clinical"]:
            self.patient_clinical_upload_button.setText(f"  {os.path.basename(uploads['clinical'])}")
            self.show_clinical_preview(uploads["clinical"])

        self.update_patient_evaluate_button()
        self.content_stack.setCurrentIndex(2)
        
    def update_patient_evaluate_button(self):
        pid = self.current_patient[0] if self.current_patient else None
        uploads = self.patient_uploads.get(pid, {})
        ready = bool(uploads.get("image") and uploads.get("clinical"))
        self.patient_evaluate_button.setEnabled(ready)
        self.patient_evaluate_button.setStyleSheet(f"""
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
    
    def run_patient_evaluation(self):
        pid = self.current_patient[0]
        uploads = self.patient_uploads[pid]
        print(f"Analyse patient {pid} : {uploads['image']} + {uploads['clinical']}")
        # ici fain an7et pipline

    def select_file(self, button, file_filter, key , scope="dashboard"):
        file_path, _ = QFileDialog.getOpenFileName(self, "Sélectionner un fichier", "", file_filter)
        if not file_path:
            return
        ok, message = self.validate_image(file_path) if key == "image" else self.validate_clinical(file_path)
        
        if not ok:
            self.show_error_message("Fichier invalide", message)
            return 
        if message:  # warning non-bloquant (données secondaires manquantes)
            self.show_warning_message("Attention", message)
            
        if scope == "dashboard":
            if key == "image":
                self.image_path = file_path
            else:
                self.clinical_path = file_path
            self.update_evaluate_button()
        else:  
            pid = self.current_patient[0]
            self.patient_uploads.setdefault(pid, {"image": None, "clinical": None})
            self.patient_uploads[pid][key] = file_path
            self.update_patient_evaluate_button()
            if key == "image":
                self.show_image_preview(file_path)
                self.patient_image_view_button.setVisible(True)   

            else:
                self.show_clinical_preview(file_path)
                self.patient_clinical_view_button.setVisible(True)

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
        

    def _make_shadow(self):
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setXOffset(0)
        shadow.setYOffset(4)
        shadow.setColor(QColor(0, 0, 0, 25))
        return shadow
    
    
    def build_patient_detail_page(self):
        content = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(60, 40, 60, 50)
        layout.setSpacing(20)
        content.setLayout(layout)

        # header retour + patient info
        top_bar = QHBoxLayout()
        back_button = QPushButton("←  Retour")
        back_button.setCursor(Qt.CursorShape.PointingHandCursor)
        back_button.setStyleSheet("""
            QPushButton {
                background: none; border: none; color: #2563eb;
                font-size: 13px; font-weight: 600; text-align: left;
            }
            QPushButton:hover { color: #1d4ed8; }
        """)
        back_button.clicked.connect(lambda: self.content_stack.setCurrentIndex(1))
        top_bar.addWidget(back_button)
        top_bar.addStretch()
        layout.addLayout(top_bar)

        # carte info
        info_card = QFrame()
        info_card.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #e5e7eb;
                border-radius: 14px;
            }
        """)
        info_card.setGraphicsEffect(self._make_shadow())
        info_layout = QHBoxLayout()
        info_layout.setContentsMargins(28, 24, 28, 24)
        info_layout.setSpacing(20)
        info_card.setLayout(info_layout)

        self.patient_avatar_label = QLabel("")
        self.patient_avatar_label.setFixedSize(64, 64)
        self.patient_avatar_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.patient_avatar_label.setStyleSheet("""
            QLabel {
                background-color: #2563eb;
                color: white;
                border-radius: 32px;
                border: none;
                font-size: 20px;
                font-weight: bold;
            }
        """)

        text_col = QVBoxLayout()
        text_col.setSpacing(10)
        text_col.setContentsMargins(0, 0, 0, 0)

        self.patient_name_label = QLabel("")
        self.patient_name_label.setStyleSheet("""
            QLabel {
                font-size: 20px;
                font-weight: 700;
                color: #111827;
                border: none;
                background: transparent;
            }
        """)

        badges_row = QHBoxLayout()
        badges_row.setSpacing(8)
        badges_row.setContentsMargins(0, 0, 0, 0)

        badge_specs = [
            ("age", "#eff6ff", "#2563eb"),
            ("sexe", "#fdf2f8", "#db2777"),
            ("date", "#f3f4f6", "#4b5563"),
        ]

        badge_labels = {}
        for key, bg, fg in badge_specs:
            badge = QLabel("")
            badge.setStyleSheet(f"""
                QLabel {{
                    background-color: {bg};
                    color: {fg};
                    border: none;
                    border-radius: 11px;
                    padding: 4px 12px;
                    font-size: 11.5px;
                    font-weight: 600;
                }}
            """)
            badges_row.addWidget(badge)
            badge_labels[key] = badge

        badges_row.addStretch()

        self.patient_age_badge = badge_labels["age"]
        self.patient_sexe_badge = badge_labels["sexe"]
        self.patient_date_badge = badge_labels["date"]

        text_col.addWidget(self.patient_name_label)
        text_col.addLayout(badges_row)

        info_layout.addWidget(self.patient_avatar_label)
        info_layout.addLayout(text_col, stretch=1)
        layout.addWidget(info_card)

        # carte upload
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(30)

        self.patient_image_card = self.create_upload_card(
            "Image Médicale (NIFTI)", "Upload Images...",
            "NIFTI Files (*.nii *.nii.gz)", "image", scope="patient"
        )
        self.patient_clinical_card = self.create_upload_card(
            "Données cliniques (.csv)", "Upload File...",
            "CSV Files (*.csv)", "clinical", scope="patient"
        )
        cards_layout.addWidget(self.patient_image_card)
        cards_layout.addWidget(self.patient_clinical_card)
        layout.addLayout(cards_layout)

        self.patient_evaluate_button = QPushButton("Evaluate prognosis")
        self.patient_evaluate_button.setFixedHeight(45)
        self.patient_evaluate_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.patient_evaluate_button.setEnabled(False)
        self.patient_evaluate_button.clicked.connect(self.run_patient_evaluation)
        layout.addWidget(self.patient_evaluate_button)

        # zone de visualisation
        self.patient_result_area = QLabel("Aucune évaluation pour l'instant.")
        self.patient_result_area.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.patient_result_area.setMinimumHeight(200)
        self.patient_result_area.setStyleSheet("""
            background-color: white; border: 1px solid #e5e7eb;
            border-radius: 12px; color: #9ca3af; font-size: 13px;
        """)
        layout.addWidget(self.patient_result_area)
        layout.addStretch()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(f"QScrollArea {{ border: none; background-color: #f4f5f7; }}{self.scrollbar_style}")
        scroll.setWidget(content)
        return scroll


    
    
    

    def show_image_preview(self, file_path):
        try:
            img = nib.load(file_path)
            data = img.get_fdata()
            mid = data.shape[2] // 2
            slice_ = np.rot90(data[:, :, mid])
            slice_ = slice_ - slice_.min()
            if slice_.max() > 0:
                slice_ = slice_ / slice_.max()
            slice_ = np.ascontiguousarray((slice_ * 255).astype(np.uint8))
            h, w = slice_.shape
            qimg = QImage(slice_.data, w, h, w, QImage.Format.Format_Grayscale8).copy()
            pixmap = QPixmap.fromImage(qimg).scaled(
                160, 160, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
            )
            self.patient_image_preview.setPixmap(pixmap)
            self.patient_image_preview.setStyleSheet("border-radius: 8px;")
            self.patient_image_preview.setVisible(True)
        except Exception:
            self.patient_image_preview.setVisible(False)

    def show_clinical_preview(self, file_path):
        try:
            df = pd.read_csv(file_path, sep=None, engine="python")
            rows, cols = df.shape
            age = df["Age"].iloc[0] if "Age" in df.columns else "—"
            sexe = df["Sex"].iloc[0] if "Sex" in df.columns else "—"
            self.patient_clinical_preview.setText(
                f"{rows} ligne(s) · {cols} colonnes\nÂge: {age}   Sexe: {sexe}"
            )
            self.patient_clinical_preview.setStyleSheet(
                "color: #374151; font-size: 12px; background-color: #f9fafb; "
                "border-radius: 8px; padding: 10px;"
            )
            self.patient_clinical_preview.setVisible(True)
        except Exception:
            self.patient_clinical_preview.setVisible(False)
            
            
    def open_viewer(self, key):
        pid = self.current_patient[0]
        uploads = self.patient_uploads.get(pid, {})
        file_path = uploads.get(key)
        if not file_path:
            return
        if key == "image":
            self.open_image_viewer(file_path)
        else:
            self.open_csv_viewer(file_path)

    def open_image_viewer(self, file_path):
        try:
            img = nib.load(file_path)
            data = img.get_fdata()
        except Exception as e:
            self.show_error_message("Erreur", f"Impossible de charger l'image :\n{e}")
            return

        dialog = QDialog(self)
        dialog.setWindowTitle("Visualisation IRM")
        dialog.resize(650, 600)
        dialog.setStyleSheet("background-color: #f4f5f7;")

        layout = QVBoxLayout()
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        dialog.setLayout(layout)

       
        title_label = QLabel("Visualisation de l'IRM")
        title_label.setStyleSheet("font-size: 17px; font-weight: 700; color: #111827; background: transparent; border: none;")
        layout.addWidget(title_label)

        plane_row = QHBoxLayout()
        plane_row.setSpacing(8)
        plane_buttons = {}
        plane_toggle_style_off = """
            QPushButton {
                background-color: white; color: #4b5563; border: 1px solid #e5e7eb;
                border-radius: 8px; padding: 8px 18px; font-size: 12px; font-weight: 600;
            }
            QPushButton:hover { background-color: #f3f4f6; }
        """
        plane_toggle_style_on = """
            QPushButton {
                background-color: #2563eb; color: white; border: 1px solid #2563eb;
                border-radius: 8px; padding: 8px 18px; font-size: 12px; font-weight: 700;
            }
        """
        current_plane = {"value": "Axial"}

        for plane in ("Axial", "Sagittal", "Coronal"):
            btn = QPushButton(plane)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet(plane_toggle_style_on if plane == "Axial" else plane_toggle_style_off)
            plane_buttons[plane] = btn
            plane_row.addWidget(btn)
        plane_row.addStretch()
        layout.addLayout(plane_row)

        image_frame = QFrame()
        image_frame.setFixedSize(520, 520)
        image_frame.setStyleSheet("""
            QFrame { background-color: #0a0a0a; border-radius: 14px; border: 1px solid #1f2937; }
        """)
        image_frame_layout = QVBoxLayout()
        image_frame_layout.setContentsMargins(10, 10, 10, 10)
        image_frame.setLayout(image_frame_layout)

        image_label = QLabel()
        image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        image_label.setStyleSheet("background: transparent; border: none;")
        image_frame_layout.addWidget(image_label)

        frame_wrapper = QHBoxLayout()
        frame_wrapper.addStretch()
        frame_wrapper.addWidget(image_frame)
        frame_wrapper.addStretch()
        layout.addLayout(frame_wrapper)

        slider_row = QHBoxLayout()
        slider_row.setSpacing(12)

        slice_slider = QSlider(Qt.Orientation.Horizontal)
        slice_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                height: 5px; background: #e5e7eb; border-radius: 2px;
            }
            QSlider::sub-page:horizontal {
                background: #2563eb; border-radius: 2px;
            }
            QSlider::handle:horizontal {
                background: white; border: 2px solid #2563eb; width: 16px;
                height: 16px; margin: -6px 0; border-radius: 8px;
            }
            QSlider::handle:horizontal:hover { background: #eff6ff; }
        """)
        slider_row.addWidget(slice_slider, stretch=1)

        slice_info_label = QLabel("")
        slice_info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        slice_info_label.setFixedWidth(90)
        slice_info_label.setStyleSheet("""
            color: #2563eb; font-size: 12px; font-weight: 700;
            background-color: #eff6ff; border-radius: 8px; padding: 6px 4px;
            border: none;
        """)
        slider_row.addWidget(slice_info_label)
        layout.addLayout(slider_row)

        def axis_index():
            return {"Axial": 2, "Sagittal": 0, "Coronal": 1}[current_plane["value"]]

        def render_slice():
            axis = axis_index()
            max_index = data.shape[axis] - 1
            slice_slider.blockSignals(True)
            slice_slider.setMaximum(max_index)
            if slice_slider.value() > max_index:
                slice_slider.setValue(max_index // 2)
            slice_slider.blockSignals(False)

            idx = slice_slider.value()
            if axis == 2:
                slice_ = data[:, :, idx]
            elif axis == 0:
                slice_ = data[idx, :, :]
            else:
                slice_ = data[:, idx, :]

            slice_ = np.rot90(slice_)
            slice_ = slice_ - slice_.min()
            if slice_.max() > 0:
                slice_ = slice_ / slice_.max()
            slice_ = np.ascontiguousarray((slice_ * 255).astype(np.uint8))
            h, w = slice_.shape
            qimg = QImage(slice_.data, w, h, w, QImage.Format.Format_Grayscale8).copy()
            pixmap = QPixmap.fromImage(qimg).scaled(
                480, 480, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
            )
            image_label.setPixmap(pixmap)
            slice_info_label.setText(f"{idx + 1} / {max_index + 1}")

        def select_plane(plane):
            current_plane["value"] = plane
            for name, btn in plane_buttons.items():
                btn.setStyleSheet(plane_toggle_style_on if name == plane else plane_toggle_style_off)
            render_slice()

        for plane, btn in plane_buttons.items():
            btn.clicked.connect(lambda checked, p=plane: select_plane(p))

        slice_slider.valueChanged.connect(lambda _: render_slice())

        slice_slider.setValue(data.shape[2] // 2)
        render_slice()

        dialog.exec()

    def open_csv_viewer(self, file_path):
        try:
            df = pd.read_csv(file_path, sep=None, engine="python")
        except Exception as e:
            self.show_error_message("Erreur", f"Impossible de charger le CSV :\n{e}")
            return

        dialog = QDialog(self)
        dialog.setWindowTitle("Données cliniques")
        dialog.resize(900, 500)
        dialog.setStyleSheet("background-color: #f4f5f7;")

        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        dialog.setLayout(layout)

        table = QTableWidget()
        table.setRowCount(len(df))
        table.setColumnCount(len(df.columns))
        table.setHorizontalHeaderLabels([str(c) for c in df.columns])
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.setStyleSheet("""
            QTableWidget {
                background-color: white; border: 1px solid #e5e7eb; border-radius: 8px;
                gridline-color: #f3f4f6;
            }
            QTableWidget::item { color: #111827; padding: 6px; }
            QHeaderView::section {
                background-color: #f9fafb; color: #374151; font-weight: 600;
                padding: 8px; border: none; border-bottom: 1px solid #e5e7eb;
            }
        """)
        table.setStyleSheet(f"""
                            QTableWidget {{
                                background-color: white; border: 1px solid #e5e7eb; border-radius: 8px;
                                gridline-color: #f3f4f6;
                            }}
                            QTableWidget::item {{ color: #111827; padding: 6px; }}
                            QHeaderView::section {{
                                background-color: #f9fafb; color: #374151; font-weight: 600;
                                padding: 8px; border: none; border-bottom: 1px solid #e5e7eb;
                            }}
                            {self.scrollbar_style}
                            QScrollBar:horizontal {{
                                background: transparent;
                                height: 10px;
                                margin: 0px 4px 2px 4px;
                            }}
                            QScrollBar::handle:horizontal {{
                                background: #cbd5e1;
                                border-radius: 5px;
                                min-width: 30px;
                            }}
                            QScrollBar::handle:horizontal:hover {{
                                background: #94a3b8;
                            }}
                            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
                                width: 0px;
                                background: none;
                                border: none;
                            }}
                            QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{
                                background: none;
                            }}
                        """)

        for row in range(len(df)):
            for col in range(len(df.columns)):
                value = df.iloc[row, col]
                table.setItem(row, col, QTableWidgetItem(str(value)))

        layout.addWidget(table)
        dialog.exec()
        
        
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = DashboardScreen()
    window.resize(1100, 700)
    window.show()
    sys.exit(app.exec())

