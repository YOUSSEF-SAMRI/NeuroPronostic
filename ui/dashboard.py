from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QFrame, QFileDialog,
    QGraphicsDropShadowEffect, QMessageBox, QLineEdit
)
from collections import defaultdict
from models.evaluation import fake_evaluate_prognosis
from models.evaluations import add_evaluation
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
from PyQt6.QtGui import QPixmap, QPainter, QColor
from ui.manage_users import ManageUsersScreen 
from PyQt6.QtWidgets import QTableWidget, QTableWidgetItem
from ui.patient_dialog import AddPatientDialog
from models.patients import add_patient, get_patients_by_medecin
from models.evaluations import get_evaluations_by_medecin
from models.evaluations import (
    add_evaluation,
    get_evaluations_by_medecin,
    get_last_evaluation_by_patient,soft_delete_evaluation, check_recent_duplicate,
    archive_evaluations_before,get_archived_evaluations_by_medecin,
    restore_evaluation,restore_all_evaluations
    
)
from datetime import datetime
from PyQt6.QtWidgets import QDateEdit
from PyQt6.QtCore import QDate, Qt
from PyQt6.QtGui import QTextCharFormat, QColor

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
        
        self.historique_page = self.build_historique_page()   # ← nouvelle ligne, index 3
        self.content_stack.addWidget(self.historique_page)     # ← nouvelle ligne
        
        self.archive_page = self.build_archive_page()
        self.content_stack.addWidget(self.archive_page)
        
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
        
        archive_button = QPushButton("  Archiver")
        archive_button.setCursor(Qt.CursorShape.PointingHandCursor)
        archive_button.setFixedHeight(45)
        archive_button.setStyleSheet(button_style)
        archive_button.clicked.connect(lambda: self.switch_page(4, archive_button))
        sidebar_layout.addWidget(archive_button)
        self.nav_buttons.append(archive_button)
            
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
        historique_button.clicked.connect(lambda: self.switch_page(3, historique_button))
        logout_button.clicked.connect(self.handle_logout)
        
        
        
        sidebar_layout.addWidget(logout_button)

        return sidebar
    
    # def open_archive_dialog(self):
    #     dialog = QDialog(self)
    #     dialog.setWindowTitle("Archiver l'historique")
    #     dialog.resize(380, 420)
    #     dialog.setStyleSheet("background-color: #f4f5f7;")

    #     layout = QVBoxLayout()
    #     layout.setContentsMargins(24, 24, 24, 24)
    #     layout.setSpacing(14)
    #     dialog.setLayout(layout)

    #     label = QLabel("Archiver toutes les évaluations réalisées jusqu'à cette date :")
    #     label.setWordWrap(True)
    #     label.setStyleSheet("color: #374151; font-size: 13px; background: transparent; border: none;")
    #     layout.addWidget(label)

    #     date_edit = QDateEdit()
    #     date_edit.setCalendarPopup(True)
    #     date_edit.setDate(QDate.currentDate())
    #     date_edit.setDisplayFormat("dd/MM/yyyy")
    #     date_edit.setFixedHeight(42)
    #     date_edit.setStyleSheet("""
    #         QDateEdit {
    #             border: 1px solid #dbe2ea;
    #             border-radius: 8px;
    #             padding: 0px 12px;
    #             font-size: 13px;
    #             background-color: white;
    #             color: #111827;
    #         }
    #         QDateEdit:focus {
    #             border: 1px solid #2563eb;
    #         }
    #         QDateEdit::drop-down {
    #             border: none;
    #             width: 30px;
    #         }
    #         QDateEdit::down-arrow {
    #             width: 10px;
    #             height: 10px;
    #         }
    #     """)

    #     calendar = date_edit.calendarWidget()
    #     calendar.setVerticalHeaderFormat(calendar.VerticalHeaderFormat.NoVerticalHeader)
    #     calendar.setStyleSheet("""
    #         QCalendarWidget {
    #             background-color: white;
    #             border: 1px solid #e5e7eb;
    #             border-radius: 10px;
    #         }
    #         QCalendarWidget QWidget#qt_calendar_navigationbar {
    #             background-color: white;
    #             border-bottom: 1px solid #f3f4f6;
    #         }
    #         QCalendarWidget QToolButton {
    #             color: #111827;
    #             background-color: transparent;
    #             font-size: 13px;
    #             font-weight: 600;
    #             border: none;
    #             border-radius: 6px;
    #             padding: 6px 10px;
    #             margin: 4px;
    #         }
    #         QCalendarWidget QToolButton:hover {
    #             background-color: #eff6ff;
    #             color: #2563eb;
    #         }
    #         QCalendarWidget QToolButton::menu-indicator { image: none; }
    #         QCalendarWidget QSpinBox {
    #             background-color: white;
    #             color: #111827;
    #             border: 1px solid #e5e7eb;
    #             border-radius: 6px;
    #             padding: 2px 6px;
    #         }
    #         QCalendarWidget QAbstractItemView {
    #             background-color: white;
    #             color: #111827;
    #             selection-background-color: #2563eb;
    #             selection-color: white;
    #             outline: none;
    #             font-size: 12px;
    #             border: none;
    #         }
    #         QCalendarWidget QAbstractItemView:disabled {
    #             color: #d1d5db;
    #         }
    #     """)

    #     normal_format = QTextCharFormat()
    #     normal_format.setForeground(QColor("#111827"))
    #     calendar.setWeekdayTextFormat(Qt.DayOfWeek.Saturday, normal_format)
    #     calendar.setWeekdayTextFormat(Qt.DayOfWeek.Sunday, normal_format)

    #     layout.addWidget(date_edit)
    #     layout.addSpacing(260)

    #     confirm_button = QPushButton("Archiver")
    #     confirm_button.setCursor(Qt.CursorShape.PointingHandCursor)
    #     confirm_button.setFixedHeight(40)
    #     confirm_button.setStyleSheet("""
    #         QPushButton {
    #             background-color: #2563eb; color: white; border: none;
    #             border-radius: 6px; font-weight: 600;
    #         }
    #         QPushButton:hover { background-color: #1d4ed8; }
    #     """)

    #     def confirm_archive():
    #         cutoff = date_edit.date().toPyDate()
    #         count = archive_evaluations_before(self.user_id, cutoff)
    #         dialog.accept()
    #         self.show_warning_message(
    #             "Archivage terminé",
    #             f"{count} évaluation(s) archivée(s) jusqu'au {cutoff.strftime('%d/%m/%Y')}."
    #         )
    #         if self.content_stack.currentIndex() == 3:
    #             self.load_historique()

    #     confirm_button.clicked.connect(confirm_archive)
    #     layout.addWidget(confirm_button)

    #     dialog.exec()
    def build_archive_page(self):
        page = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(60, 50, 60, 50)
        layout.setSpacing(18)
        page.setLayout(layout)

        header_layout = QHBoxLayout()
        title_col = QVBoxLayout()
        title_col.setSpacing(2)

        title = QLabel("Archive")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #374151;")
        subtitle = QLabel("Dossiers patients archivés et clôturés")
        subtitle.setStyleSheet("color: #9ca3af; font-size: 13px;")
        title_col.addWidget(title)
        title_col.addWidget(subtitle)
        header_layout.addLayout(title_col)
        header_layout.addStretch()

        archive_action_button = QPushButton("Archiver jusqu'à une date")
        archive_action_button.setCursor(Qt.CursorShape.PointingHandCursor)
        archive_action_button.setFixedHeight(44)
        archive_action_button.setStyleSheet("""
            QPushButton {
                background-color: #2563eb; color: white; border: none;
                border-radius: 9px; padding: 0px 20px; font-size: 13px; font-weight: 600;
            }
            QPushButton:hover { background-color: #1d4ed8; }
            QPushButton:pressed { background-color: #1e40af; }
        """)
        archive_action_button.clicked.connect(self.open_archive_dialog)
        header_layout.addWidget(archive_action_button)
        restore_all_button = QPushButton("  Restaurer tout")
        restore_all_button.setCursor(Qt.CursorShape.PointingHandCursor)
        restore_all_button.setFixedHeight(44)
        restore_all_button.setStyleSheet("""
            QPushButton {
                background-color: white; color: #16a34a; border: 1px solid #bbf7d0;
                border-radius: 9px; padding: 0px 20px; font-size: 13px; font-weight: 600;
            }
            QPushButton:hover { background-color: #f0fdf4; }
            QPushButton:pressed { background-color: #dcfce7; }
        """)
        restore_all_button.clicked.connect(self.confirm_restore_all)
        header_layout.addWidget(restore_all_button)
        layout.addLayout(header_layout)

        # --- cartes stats ---
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(16)
        self.archive_total_card, self.archive_total_value = self._make_stat_card("Dossiers archivés", "#374151")
        self.archive_month_card, self.archive_month_value = self._make_stat_card("Archivés ce mois", "#374151")
        stats_layout.addWidget(self.archive_total_card)
        stats_layout.addWidget(self.archive_month_card)
        layout.addLayout(stats_layout)

        # --- filtres ---
        filter_style = """
            QLineEdit, QComboBox {
                border: 1px solid #e5e7eb; border-radius: 8px;
                padding: 0 12px; font-size: 13px; background-color: white; color: #111827;
            }
            QLineEdit:focus, QComboBox:focus { border-color: #2563eb; }
            QComboBox::drop-down { border: none; width: 28px; }
            QComboBox QAbstractItemView {
                background-color: white; color: #111827; border: 1px solid #e5e7eb;
                selection-background-color: #eff6ff; selection-color: #111827;
            }
        """

        filters_layout = QHBoxLayout()
        filters_layout.setSpacing(10)

        self.archive_search = QLineEdit()
        self.archive_search.setPlaceholderText("Rechercher un patient...")
        self.archive_search.setFixedHeight(38)
        self.archive_search.setStyleSheet(filter_style)
        self.archive_search.textChanged.connect(self.filter_archive)
        filters_layout.addWidget(self.archive_search, stretch=1)

        self.archive_year_filter = QComboBox()
        self.archive_year_filter.addItem("Toutes les années")
        self.archive_year_filter.setFixedWidth(150)
        self.archive_year_filter.setFixedHeight(38)
        self.archive_year_filter.setStyleSheet(filter_style)
        self.archive_year_filter.currentIndexChanged.connect(self.filter_archive)
        filters_layout.addWidget(self.archive_year_filter)

        self.archive_risk_filter = QComboBox()
        self.archive_risk_filter.addItems(["Tous les risques", "Élevé", "Modéré", "Faible"])
        self.archive_risk_filter.setFixedWidth(170)
        self.archive_risk_filter.setFixedHeight(38)
        self.archive_risk_filter.setStyleSheet(filter_style)
        self.archive_risk_filter.currentIndexChanged.connect(self.filter_archive)
        filters_layout.addWidget(self.archive_risk_filter)

        layout.addLayout(filters_layout)

        # --- tableau ---
        self.archive_empty_label = QLabel("Aucune évaluation archivée pour l'instant.")
        self.archive_empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.archive_empty_label.setStyleSheet("color: #9ca3af; font-size: 14px; padding: 80px 0;")

        self.archive_table = QTableWidget()
        self.archive_table.setColumnCount(5)
        self.archive_table.setHorizontalHeaderLabels(["Patient", "Archivé le", "Score", "Risque", "Actions"])
        self.archive_table.horizontalHeader().setStretchLastSection(True)
        self.archive_table.setColumnWidth(0, 230)
        self.archive_table.setColumnWidth(1, 150)
        self.archive_table.setColumnWidth(2, 80)
        self.archive_table.setColumnWidth(3, 110)
        self.archive_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.archive_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.archive_table.setStyleSheet(f"""
            QTableWidget {{
                background-color: white; border: 1px solid #e5e7eb; border-radius: 8px;
                gridline-color: #f3f4f6;
            }}
            QTableWidget::item {{ color: #111827; padding: 8px; border: none; }}
            QTableWidget::item:selected {{ background-color: #f3f4f6; color: #111827; outline: none; }}
            QHeaderView::section {{
                background-color: #f9fafb; color: #374151; font-weight: 600;
                padding: 8px; border: none; border-bottom: 1px solid #e5e7eb;
            }}
            {self.scrollbar_style}
        """)
        self.archive_table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.archive_table.setVisible(False)
        self.archive_table.verticalHeader().setDefaultSectionSize(58)

        layout.addWidget(self.archive_empty_label)
        layout.addWidget(self.archive_table)

        self.archive_all_rows = []
        return page
    
    def confirm_restore_all(self):
        if not self.archive_all_rows:
            return

        box = QMessageBox(self)
        box.setWindowTitle("Restaurer tout")
        box.setText(
            f"Voulez-vous vraiment restaurer les {len(self.archive_all_rows)} "
            f"évaluation(s) archivée(s) ? Elles réapparaîtront dans l'Historique."
        )
        box.setIcon(QMessageBox.Icon.Question)
        box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        box.setDefaultButton(QMessageBox.StandardButton.No)
        box.setStyleSheet("""
            QMessageBox { min-width: 380px; }
            QMessageBox QLabel { color: #1f2937; font-size: 13px; }
            QPushButton {
                background-color: #f3f4f6; color: #111827; border: 1px solid #d1d5db;
                border-radius: 6px; padding: 6px 18px; min-width: 70px;
            }
            QPushButton:hover { background-color: #e5e7eb; }
            QPushButton:default { background-color: #16a34a; color: white; border: none; }
            QPushButton:default:hover { background-color: #15803d; }
        """)
        answer = box.exec()
        if answer != QMessageBox.StandardButton.Yes:
            return

        count = restore_all_evaluations(self.user_id)
        self.show_warning_message("Restauration terminée", f"{count} évaluation(s) restaurée(s).")
        self.load_archive()
    
    def load_archive(self):
        rows = get_archived_evaluations_by_medecin(self.user_id)

        # normalise archived_at en objet datetime, que ce soit déjà un datetime ou une string
        normalized_rows = []
        for row in rows:
            row = list(row)
            archived_at = row[5]
            if isinstance(archived_at, str):
                try:
                    archived_at = datetime.fromisoformat(archived_at)
                except ValueError:
                    archived_at = None
            row[5] = archived_at
            normalized_rows.append(tuple(row))

        self.archive_all_rows = normalized_rows

        years = sorted({r[5].year for r in normalized_rows if r[5]}, reverse=True)
        self.archive_year_filter.blockSignals(True)
        self.archive_year_filter.clear()
        self.archive_year_filter.addItem("Toutes les années")
        for y in years:
            self.archive_year_filter.addItem(str(y))
        self.archive_year_filter.blockSignals(False)

        self.archive_search.blockSignals(True)
        self.archive_search.clear()
        self.archive_search.blockSignals(False)
        self.archive_risk_filter.blockSignals(True)
        self.archive_risk_filter.setCurrentIndex(0)
        self.archive_risk_filter.blockSignals(False)

        self.render_archive_rows(normalized_rows)


    def filter_archive(self):
        query = self.archive_search.text().strip().lower()
        year_choice = self.archive_year_filter.currentText()
        risk_choice = self.archive_risk_filter.currentText()

        filtered = []
        for row in self.archive_all_rows:
            eval_id, patient_id, nom, prenom, result, archived_at, created_at, image_path, clinical_csv_path = row
            full_name = f"{nom} {prenom}".lower()
            risk_level = result.get("risk_level", "—")

            if query and query not in full_name:
                continue
            if year_choice != "Toutes les années" and (not archived_at or str(archived_at.year) != year_choice):
                continue
            if risk_choice != "Tous les risques" and risk_level != risk_choice:
                continue
            filtered.append(row)

        self.render_archive_rows(filtered)


    def render_archive_rows(self, rows):
        has_rows = bool(rows)
        self.archive_empty_label.setVisible(not has_rows)
        self.archive_table.setVisible(has_rows)
        self.archive_table.setRowCount(len(rows))

        for row_idx, (eval_id, patient_id, nom, prenom, result, archived_at, created_at, image_path, clinical_csv_path) in enumerate(rows):
            score = result.get("score", "—")
            risk_level = result.get("risk_level", "—")

            self.archive_table.setCellWidget(row_idx, 0, self.create_patient_cell_id(nom, prenom, patient_id))
            date_text = archived_at.strftime("%d/%m/%Y %H:%M") if archived_at else "—"
            self.archive_table.setItem(row_idx, 1, QTableWidgetItem(date_text))
            self.archive_table.setItem(row_idx, 2, QTableWidgetItem(str(score)))
            self.archive_table.setCellWidget(row_idx, 3, self.create_risk_badge(risk_level))

            actions_widget = QWidget()
            actions_widget.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
            actions_widget.setStyleSheet("QWidget { background-color: white; border: none; }")
            actions_layout = QHBoxLayout()
            actions_layout.setContentsMargins(4, 0, 4, 0)
            actions_layout.setSpacing(8)
            actions_widget.setLayout(actions_layout)

            detail_button = QPushButton("Voir détail")
            detail_button.setCursor(Qt.CursorShape.PointingHandCursor)
            detail_button.setFixedWidth(100)
            detail_button.setFixedHeight(28)
            detail_button.setStyleSheet("""
                QPushButton {
                    background-color: #eff6ff; color: #2563eb; border: 1px solid #bfdbfe;
                    border-radius: 6px; padding: 4px 12px; font-size: 12px; font-weight: 600;
                }
                QPushButton:hover { background-color: #dbeafe; }
            """)
            row_data = {
                "nom": nom, "prenom": prenom, "score": score, "risk_level": risk_level,
                "created_at": created_at, "image_path": image_path, "clinical_csv_path": clinical_csv_path,
            }
            detail_button.clicked.connect(lambda checked, d=row_data: self.show_evaluation_detail(d))
            actions_layout.addWidget(detail_button)

            restore_button = QPushButton("Restaurer")
            restore_button.setCursor(Qt.CursorShape.PointingHandCursor)
            restore_button.setFixedWidth(90)
            restore_button.setFixedHeight(28)
            restore_button.setStyleSheet("""
                QPushButton {
                    background-color: #f0fdf4; color: #16a34a; border: 1px solid #bbf7d0;
                    border-radius: 6px; padding: 4px 12px; font-size: 12px; font-weight: 600;
                }
                QPushButton:hover { background-color: #dcfce7; }
            """)
            restore_button.clicked.connect(lambda checked, evaluation_id=eval_id: self.handle_restore(evaluation_id))
            actions_layout.addWidget(restore_button)

            self.archive_table.setCellWidget(row_idx, 4, actions_widget)

        self.update_archive_stats(rows)

    def update_archive_stats(self, rows):
        total = len(self.archive_all_rows)
        self.archive_total_value.setText(str(total))

        now = datetime.now()
        this_month = sum(
            1 for r in self.archive_all_rows
            if r[5] and r[5].year == now.year and r[5].month == now.month
        )
        self.archive_month_value.setText(str(this_month))


    def handle_restore(self, evaluation_id):
        restore_evaluation(evaluation_id)
        self.load_archive()
        
    def open_archive_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Archiver l'historique")
        dialog.resize(380, 420)
        dialog.setStyleSheet("background-color: #f4f5f7;")

        layout = QVBoxLayout()
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(14)
        dialog.setLayout(layout)

        label = QLabel("Archiver toutes les évaluations réalisées jusqu'à cette date :")
        label.setWordWrap(True)
        label.setStyleSheet("color: #374151; font-size: 13px; background: transparent; border: none;")
        layout.addWidget(label)

        date_edit = QDateEdit()
        date_edit.setCalendarPopup(True)
        date_edit.setDate(QDate.currentDate())
        date_edit.setDisplayFormat("dd/MM/yyyy")
        date_edit.setFixedHeight(42)
        date_edit.setStyleSheet("""
            QDateEdit {
                border: 1px solid #dbe2ea; border-radius: 8px; padding: 0px 12px;
                font-size: 13px; background-color: white; color: #111827;
            }
            QDateEdit:focus { border: 1px solid #2563eb; }
            QDateEdit::drop-down { border: none; width: 30px; }
            QDateEdit::down-arrow { width: 10px; height: 10px; }
        """)

        calendar = date_edit.calendarWidget()
        calendar.setVerticalHeaderFormat(calendar.VerticalHeaderFormat.NoVerticalHeader)
        calendar.setStyleSheet("""
            QCalendarWidget { background-color: white; border: 1px solid #e5e7eb; border-radius: 10px; }
            QCalendarWidget QWidget#qt_calendar_navigationbar {
                background-color: white; border-bottom: 1px solid #f3f4f6;
            }
            QCalendarWidget QToolButton {
                color: #111827; background-color: transparent; font-size: 13px;
                font-weight: 600; border: none; border-radius: 6px; padding: 6px 10px; margin: 4px;
            }
            QCalendarWidget QToolButton:hover { background-color: #eff6ff; color: #2563eb; }
            QCalendarWidget QToolButton::menu-indicator { image: none; }
            QCalendarWidget QSpinBox {
                background-color: white; color: #111827; border: 1px solid #e5e7eb;
                border-radius: 6px; padding: 2px 6px;
            }
            QCalendarWidget QAbstractItemView {
                background-color: white; color: #111827; selection-background-color: #2563eb;
                selection-color: white; outline: none; font-size: 12px; border: none;
            }
            QCalendarWidget QAbstractItemView:disabled { color: #d1d5db; }
        """)

        normal_format = QTextCharFormat()
        normal_format.setForeground(QColor("#111827"))
        calendar.setWeekdayTextFormat(Qt.DayOfWeek.Saturday, normal_format)
        calendar.setWeekdayTextFormat(Qt.DayOfWeek.Sunday, normal_format)

        layout.addWidget(date_edit)
        layout.addSpacing(260)

        confirm_button = QPushButton("Archiver")
        confirm_button.setCursor(Qt.CursorShape.PointingHandCursor)
        confirm_button.setFixedHeight(40)
        confirm_button.setStyleSheet("""
            QPushButton {
                background-color: #2563eb; color: white; border: none;
                border-radius: 6px; font-weight: 600;
            }
            QPushButton:hover { background-color: #1d4ed8; }
        """)

        def confirm_archive():
            cutoff = date_edit.date().toPyDate()
            count = archive_evaluations_before(self.user_id, cutoff)
            dialog.accept()
            self.show_warning_message(
                "Archivage terminé",
                f"{count} évaluation(s) archivée(s) jusqu'au {cutoff.strftime('%d/%m/%Y')}."
            )
            self.load_archive()
            if self.content_stack.currentIndex() == 3:
                self.load_historique()

        confirm_button.clicked.connect(confirm_archive)
        layout.addWidget(confirm_button)

        dialog.exec()    
    
    def switch_page(self, index, active_button):
        self.content_stack.setCurrentIndex(index)

        for btn in self.nav_buttons:
            btn.setStyleSheet(self.button_style)
        active_button.setStyleSheet(self.active_button_style)

        if index == 1:  # page Patients
            self.load_patients()
        elif index == 3:
            self.load_historique()
        elif index == 4:
            self.load_archive()
        
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
        page.setStyleSheet("background-color: #f4f5f7;")

        layout = QVBoxLayout()
        layout.setContentsMargins(60, 40, 60, 40)
        layout.setSpacing(18)
        page.setLayout(layout)


        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)

        title_container = QVBoxLayout()
        title_container.setSpacing(4)

        title = QLabel("Mes patients")
        title.setStyleSheet("""
            QLabel {
                color: #172554;
                font-size: 28px;
                font-weight: 700;
                background: transparent;
            }
        """)

        subtitle = QLabel(
            "Gérez la liste des patients enregistrés dans le système."
        )
        subtitle.setStyleSheet("""
            QLabel {
                color: #64748b;
                font-size: 13px;
                background: transparent;
            }
        """)

        title_container.addWidget(title)
        title_container.addWidget(subtitle)

        header_layout.addLayout(title_container)
        header_layout.addStretch()

        # Bouton ajouter
        add_button = QPushButton("  Ajouter un patient")
        add_button.setCursor(Qt.CursorShape.PointingHandCursor)
        add_button.setFixedHeight(44)

        add_button.setStyleSheet("""
            QPushButton {
                background-color: #2563eb;
                color: white;
                border: none;
                border-radius: 9px;
                padding: 0px 20px;
                font-size: 13px;
                font-weight: 600;
            }

            QPushButton:hover {
                background-color: #1d4ed8;
            }

            QPushButton:pressed {
                background-color: #1e40af;
            }
        """)

        add_button.clicked.connect(self.open_add_patient_dialog)

        header_layout.addWidget(add_button)

        layout.addLayout(header_layout)


        filters_card = QFrame()
        filters_card.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #e5e7eb;
                border-radius: 12px;
            }
        """)

        filters_layout = QHBoxLayout()
        filters_layout.setContentsMargins(20, 16, 20, 16)
        filters_layout.setSpacing(16)
        filters_card.setLayout(filters_layout)

        # -------------------------
        # Recherche
        # -------------------------

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Rechercher un patient...")
        self.search_input.setFixedHeight(42)
        self.search_input.setMinimumWidth(300)

        self.search_input.setStyleSheet("""
            QLineEdit {
                background-color: white;
                border: 1px solid #dbe2ea;
                border-radius: 8px;
                padding: 0px 14px;
                color: #1e293b;
                font-size: 13px;
            }

            QLineEdit:focus {
                border: 1px solid #2563eb;
            }

            QLineEdit::placeholder {
                color: #94a3b8;
            }
        """)

        self.search_input.textChanged.connect(self.apply_patient_filters)

        filters_layout.addWidget(self.search_input)


        self.gender_filter = QComboBox()
        self.gender_filter.setFixedHeight(42)
        self.gender_filter.setMinimumWidth(210)

        self.gender_filter.addItem("Tous les sexes", "all")
        self.gender_filter.addItem("Homme", "M")
        self.gender_filter.addItem("Femme", "F")

        self.gender_filter.setStyleSheet("""
            QComboBox {
                background-color: transparent;
                border: 1px solid #dbe2ea;
                border-radius: 8px;
                padding: 0px 12px;
                color: #334155;
                font-size: 13px;
            }

            QComboBox:hover {
                border: 1px solid #94a3b8;
            }

            QComboBox:focus {
                border: 1px solid #2563eb;
            }

            QComboBox::drop-down {
                border: none;
                width: 30px;
            }

            QComboBox QAbstractItemView {
                background-color: white;
                color: #334155;
                selection-background-color: #eff6ff;
                selection-color: #2563eb;
                border: 1px solid #e5e7eb;
            }
        """)

        self.gender_filter.currentIndexChanged.connect(
            self.apply_patient_filters
        )

        filters_layout.addWidget(self.gender_filter)

        filters_layout.addStretch()

        total_card = QFrame()
        total_card.setFixedSize(150, 58)

        total_card.setStyleSheet("""
            QFrame {
                background-color: #f8fafc;
                border: 1px solid #e2e8f0;
                border-radius: 10px;
            }
        """)

        total_layout = QHBoxLayout()
        total_layout.setContentsMargins(12, 8, 12, 8)
        total_card.setLayout(total_layout)




        total_text_layout = QVBoxLayout()
        total_text_layout.setSpacing(0)

        total_title = QLabel("Total patients")
        total_title.setStyleSheet("""
            QLabel {
                color: #64748b;
                font-size: 11px;
                border: none;
                background: transparent;
            }
        """)

        self.total_patients_label = QLabel("0")
        self.total_patients_label.setStyleSheet("""
            QLabel {
                color: #172554;
                font-size: 17px;
                font-weight: 700;
                border: none;
                background: transparent;
            }
        """)

        total_text_layout.addWidget(total_title)
        total_text_layout.addWidget(self.total_patients_label)

        total_layout.addLayout(total_text_layout)

        filters_layout.addWidget(total_card)

        layout.addWidget(filters_card)

        table_card = QFrame()
        table_card.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #e5e7eb;
                border-radius: 12px;
            }
        """)

        table_layout = QVBoxLayout()
        table_layout.setContentsMargins(0, 0, 0, 0)
        table_layout.setSpacing(0)
        table_card.setLayout(table_layout)

        self.empty_state_label = QLabel(
            "Aucun patient pour l'instant.\n"
            "Cliquez sur « Ajouter un patient » pour commencer."
        )

        self.empty_state_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.empty_state_label.setStyleSheet("""
            QLabel {
                color: #94a3b8;
                font-size: 14px;
                padding: 70px;
                background-color: white;
                border: none;
            }
        """)

        self.empty_state_label.setVisible(False)

        self.patients_table = QTableWidget()

        # 7 colonnes maintenant
        self.patients_table.setColumnCount(7)

        self.patients_table.setHorizontalHeaderLabels([
            "#",
            "Nom",
            "Prénom",
            "Age",
            "Sexe",
            "Date d'ajout",
            "Actions"
        ])

        self.patients_table.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers
        )

        self.patients_table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )

        self.patients_table.setSelectionMode(
            QTableWidget.SelectionMode.SingleSelection
        )

        self.patients_table.setFocusPolicy(
            Qt.FocusPolicy.NoFocus
        )

        self.patients_table.verticalHeader().setVisible(False)
        self.patients_table.horizontalHeader().setStretchLastSection(True)

        # Largeurs
        self.patients_table.setColumnWidth(0, 55)
        self.patients_table.setColumnWidth(1, 170)
        self.patients_table.setColumnWidth(2, 170)
        self.patients_table.setColumnWidth(3, 80)
        self.patients_table.setColumnWidth(4, 90)
        self.patients_table.setColumnWidth(5, 150)

        self.patients_table.setStyleSheet("""
            QTableWidget {
                background-color: white;
                border: none;
                gridline-color: #eef2f7;
                color: #1e293b;
                font-size: 13px;
            }

            QTableWidget::item {
                padding: 8px;
                border: none;
                color: #1e293b;
            }

            QTableWidget::item:selected {
                background-color: #eff6ff;
                color: #1e293b;
            }

            QHeaderView::section {
                background-color: #f8fafc;
                color: #334155;
                font-size: 12px;
                font-weight: 600;
                padding: 12px 8px;
                border: none;
                border-bottom: 1px solid #e5e7eb;
            }

            QScrollBar:vertical {
                background: transparent;
                width: 8px;
                margin: 4px;
            }

            QScrollBar::handle:vertical {
                background: #cbd5e1;
                border-radius: 4px;
                min-height: 30px;
            }

            QScrollBar::handle:vertical:hover {
                background: #94a3b8;
            }

            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {
                height: 0px;
            }

            QScrollBar::add-page:vertical,
            QScrollBar::sub-page:vertical {
                background: transparent;
            }
        """)

        self.patients_table.setVisible(False)

        table_layout.addWidget(self.empty_state_label)
        table_layout.addWidget(self.patients_table)


        pagination_container = QFrame()
        pagination_container.setStyleSheet("""
            QFrame {
                background-color: white;
                border: none;
                border-top: 1px solid #eef2f7;
            }
        """)

        pagination_layout = QHBoxLayout()
        pagination_layout.setContentsMargins(20, 12, 20, 12)
        pagination_layout.setSpacing(8)

        pagination_container.setLayout(pagination_layout)

        # Lignes par page

        lines_label = QLabel("Lignes par page :")
        lines_label.setStyleSheet("""
            QLabel {
                color: #64748b;
                font-size: 12px;
                background: transparent;
                border: none;
            }
        """)

        self.page_size_combo = QComboBox()
        self.page_size_combo.setFixedSize(75, 34)

        self.page_size_combo.addItem("10", 10)
        self.page_size_combo.addItem("20", 20)
        self.page_size_combo.addItem("50", 50)

        self.page_size_combo.setStyleSheet("""
            QComboBox {
                background-color: white;
                color: #334155;
                border: 1px solid #dbe2ea;
                border-radius: 7px;
                padding: 0px 8px;
                font-size: 12px;
            }

            QComboBox:hover {
                border: 1px solid #94a3b8;
            }

            QComboBox:focus {
                border: 1px solid #2563eb;
            }

            QComboBox::drop-down {
                border: none;
                width: 22px;
            }

            QComboBox QAbstractItemView {
                background-color: white;
                color: #334155;
                border: 1px solid #dbe2ea;
                selection-background-color: #eff6ff;
                selection-color: #2563eb;
                padding: 4px;
                outline: none;
            }

            QComboBox QAbstractItemView::item {
                color: #334155;
                background-color: white;
                padding: 8px;
            }

            QComboBox QAbstractItemView::item:hover {
                background-color: #eff6ff;
                color: #2563eb;
            }
        """)

        self.page_size_combo.currentIndexChanged.connect(
            self.change_page_size
        )

        pagination_layout.addWidget(lines_label)
        pagination_layout.addWidget(self.page_size_combo)

        pagination_layout.addStretch()

        # Previous

        self.prev_button = QPushButton("‹")
        self.prev_button.setFixedSize(38, 36)

        # Numéro de page

        self.page_label = QLabel("1")
        self.page_label.setFixedSize(38, 36)
        self.page_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Next

        self.next_button = QPushButton("›")
        self.next_button.setFixedSize(38, 36)

        pagination_button_style = """
            QPushButton {
                background-color: white;
                color: #64748b;
                border: 1px solid #dbe2ea;
                border-radius: 8px;
                font-size: 18px;
                font-weight: 500;
            }

            QPushButton:hover {
                background-color: #eff6ff;
                color: #2563eb;
                border-color: #bfdbfe;
            }

            QPushButton:disabled {
                background-color: #f8fafc;
                color: #cbd5e1;
                border-color: #e5e7eb;
            }
        """

        self.prev_button.setStyleSheet(pagination_button_style)
        self.next_button.setStyleSheet(pagination_button_style)

        self.page_label.setStyleSheet("""
            QLabel {
                background-color: #2563eb;
                color: white;
                border-radius: 8px;
                font-size: 13px;
                font-weight: 600;
            }
        """)

        self.prev_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.next_button.setCursor(Qt.CursorShape.PointingHandCursor)

        self.prev_button.clicked.connect(self.go_to_previous_page)
        self.next_button.clicked.connect(self.go_to_next_page)

        pagination_layout.addWidget(self.prev_button)
        pagination_layout.addWidget(self.page_label)
        pagination_layout.addWidget(self.next_button)

        pagination_layout.addStretch()

        self.page_info_label = QLabel("Page 1 sur 1")
        self.page_info_label.setStyleSheet("""
            QLabel {
                color: #64748b;
                font-size: 12px;
                background: transparent;
                border: none;
            }
        """)

        pagination_layout.addWidget(self.page_info_label)

        table_layout.addWidget(pagination_container)

        layout.addWidget(table_card, stretch=1)

        return page   

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
        self.all_patients = get_patients_by_medecin(
        self.user_id
        )

        self.filtered_patients = list(
            self.all_patients
        )

        self.current_page = 1

        self.render_page()
        
    def apply_patient_filters(self):

        query = self.search_input.text().strip().lower()

        selected_gender = self.gender_filter.currentData()

        self.filtered_patients = []

        for patient in self.all_patients:

            id_, nom, prenom, age, sexe, created_at = patient

            # Recherche nom + prénom
            full_name = f"{nom} {prenom}".lower()

            matches_search = (
                query in full_name
            )

            # Filtre sexe
            matches_gender = (
                selected_gender == "all"
                or sexe == selected_gender
            )

            if matches_search and matches_gender:
                self.filtered_patients.append(
                    patient
                )

        self.current_page = 1

        self.render_page()

    def refresh_patients_display(self, patients=None):

        has_patients = bool(
            self.filtered_patients
        )

        self.empty_state_label.setVisible(
            not has_patients
        )

        self.patients_table.setVisible(
            has_patients
        )

        self.prev_button.setVisible(
            has_patients
        )

        self.next_button.setVisible(
            has_patients
        )

        self.page_label.setVisible(
            has_patients
        )

        self.page_info_label.setVisible(
            has_patients
        )

        self.total_patients_label.setText(
            str(len(self.all_patients))
        )

        if not self.all_patients:

            self.empty_state_label.setText(
                "Aucun patient pour l'instant.\n"
                "Cliquez sur « Ajouter un patient » "
                "pour commencer."
            )

        elif not self.filtered_patients:

            self.empty_state_label.setText(
                "Aucun patient ne correspond à votre recherche."
            )

    def total_pages(self):
        if not self.filtered_patients:
            return 1

        return (
            (len(self.filtered_patients) - 1)
            // self.page_size
        ) + 1
        
    def change_page_size(self):

        self.page_size = self.page_size_combo.currentData()

        self.current_page = 1

        self.render_page()

    def render_page(self):
        self.refresh_patients_display()

        total = self.total_pages()

        self.current_page = max(
            1,
            min(self.current_page, total)
        )

        start = (self.current_page - 1) * self.page_size
        end = start + self.page_size

        page_patients = self.filtered_patients[start:end]

        self.patients_table.setRowCount(len(page_patients))
        self.patients_table.verticalHeader().setDefaultSectionSize(58)

        for row, patient in enumerate(page_patients):

            id_, nom, prenom, age, sexe, created_at = patient

            number_item = QTableWidgetItem(
                str(start + row + 1)
            )

            number_item.setTextAlignment(
                Qt.AlignmentFlag.AlignCenter
            )

            number_item.setForeground(
                QColor("#64748b")
            )

            self.patients_table.setItem(
                row, 0, number_item
            )

            self.patients_table.setItem(
                row,
                1,
                QTableWidgetItem(str(nom))
            )

            self.patients_table.setItem(
                row,
                2,
                QTableWidgetItem(str(prenom))
            )

            age_item = QTableWidgetItem(str(age))
            age_item.setTextAlignment(
                Qt.AlignmentFlag.AlignCenter
            )

            self.patients_table.setItem(
                row, 3, age_item
            )

            sexe_text = "M" if sexe == "M" else "F"

            sexe_item = QTableWidgetItem(sexe_text)

            sexe_item.setTextAlignment(
                Qt.AlignmentFlag.AlignCenter
            )

            self.patients_table.setItem(
                row, 4, sexe_item
            )

            date_item = QTableWidgetItem(
                created_at.strftime("%d/%m/%Y")
            )

            self.patients_table.setItem(
                row, 5, date_item
            )

            show_button = QPushButton("Afficher")

            show_button.setCursor(
                Qt.CursorShape.PointingHandCursor
            )

            show_button.setFixedHeight(34)
            show_button.setMinimumWidth(105)

            show_button.setStyleSheet("""
                QPushButton {
                    background-color: #eff6ff;
                    color: #2563eb;
                    border: 1px solid #dbeafe;
                    border-radius: 8px;
                    padding: 5px 12px;
                    font-size: 12px;
                    font-weight: 600;
                }

                QPushButton:hover {
                    background-color: #dbeafe;
                    border-color: #bfdbfe;
                }

                QPushButton:pressed {
                    background-color: #bfdbfe;
                }
            """)

            show_button.clicked.connect(
                lambda checked, p=patient:
                    self.show_patient_details(p)
            )

            self.patients_table.setCellWidget(
                row,
                6,
                show_button
            )
            
        self.page_label.setText(
            str(self.current_page)
        )

        self.page_info_label.setText(
            f"Page {self.current_page} sur {total}"
        )

        self.prev_button.setEnabled(
            self.current_page > 1
        )

        self.next_button.setEnabled(
            self.current_page < total
        )

        # Total patients
        self.total_patients_label.setText(
            str(len(self.all_patients))
        )

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
            
        result = get_last_evaluation_by_patient(id_)

        if result:
            self.display_evaluation_result(result)
        else:
            self.patient_result_area.setText(
                "Aucune évaluation pour l'instant."
            )

            self.patient_result_area.setStyleSheet("""
                background-color: white;
                border: 1px solid #e5e7eb;
                border-radius: 12px;
                color: #9ca3af;
                font-size: 13px;
            """)

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
        
        existing = check_recent_duplicate(pid, uploads["image"], uploads["clinical"], hours=48)
        if existing:
            proceed = self.confirm_duplicate_evaluation(existing)
            if not proceed:
                return  
        
        result = fake_evaluate_prognosis(uploads["image"], uploads["clinical"])
        add_evaluation(
            patient_id=pid,
            image_path=uploads["image"],
            clinical_csv_path=uploads["clinical"],
            result=result,
        )
        self.display_evaluation_result(result)
        # ici fain an7et pipline
        
        
    def display_evaluation_result(self, result):
        risk_color = {"Faible": "#16a34a", "Modéré": "#f59e0b", "Élevé": "#dc2626"}.get(
            result["risk_level"], "#374151"
        )
        self.patient_result_area.setText(
            f"Score : {result['score']}\nNiveau de risque : {result['risk_level']}"
        )
        self.patient_result_area.setStyleSheet(f"""
            background-color: white; border: 2px solid {risk_color};
            border-radius: 12px; color: {risk_color}; font-size: 15px; font-weight: 700;
        """)

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
        back_button = QPushButton(" Retour")
        back_button.setCursor(Qt.CursorShape.PointingHandCursor)
        back_button.setStyleSheet("""
                    QPushButton {
                        background-color: #f3f4f6;
                        color: #2563eb;
                        border: 1px solid #dbeafe;
                        border-radius: 8px;
                        padding: 8px 14px;
                        font-size: 13px;
                        font-weight: 600;
                        text-align: center;
                    }

                    QPushButton:hover {
                        background-color: #eff6ff;
                        color: #1d4ed8;
                        border: 1px solid #bfdbfe;
                    }

                    QPushButton:pressed {
                        background-color: #dbeafe;
                    }
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
            modified_path = self.open_csv_viewer(file_path)

            # Si le médecin a enregistré des modifications
            if modified_path:
                self.patient_uploads[pid]["clinical"] = modified_path

                # Mettre à jour le nom affiché sur le bouton
                self.patient_clinical_upload_button.setText(
                    f"  {os.path.basename(modified_path)}"
                )

                # Mettre à jour l'aperçu
                self.show_clinical_preview(modified_path)

                # Vérifier que le bouton Evaluate est toujours à jour
                self.update_patient_evaluate_button()

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
        table.setEditTriggers(
            QTableWidget.EditTrigger.DoubleClicked |
            QTableWidget.EditTrigger.EditKeyPressed
        )
        table.setStyleSheet(f"""
            QTableWidget {{
                background-color: white;
                border: 1px solid #e5e7eb;
                border-radius: 8px;
                gridline-color: #f3f4f6;
            }}

            QTableWidget::item {{
                color: #111827;
                padding: 6px;
            }}

            QTableWidget QLineEdit {{
                background-color: white;
                color: #111827;
                border: 1px solid #2563eb;
                border-radius: 4px;
                padding: 2px 4px;
                selection-background-color: #bfdbfe;
                selection-color: #111827;
            }}

            QHeaderView::section {{
                background-color: #f9fafb;
                color: #374151;
                font-weight: 600;
                padding: 8px;
                border: none;
                border-bottom: 1px solid #e5e7eb;
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

            QScrollBar::add-line:horizontal,
            QScrollBar::sub-line:horizontal {{
                width: 0px;
                background: none;
                border: none;
            }}

            QScrollBar::add-page:horizontal,
            QScrollBar::sub-page:horizontal {{
                background: none;
            }}
        """)

        for row in range(len(df)):
            for col in range(len(df.columns)):
                value = df.iloc[row, col]
                table.setItem(row, col, QTableWidgetItem(str(value)))

        layout.addWidget(table)
        
        
        save_button = QPushButton("Enregistrer les modifications")
        save_button.setFixedHeight(40)

        save_button.setStyleSheet("""
            QPushButton {
                background-color: #2563eb;
                color: white;
                border: none;
                border-radius: 6px;
                font-weight: 600;
            }

            QPushButton:hover {
                background-color: #1d4ed8;
            }
        """)

        layout.addWidget(save_button)
        saved_path = None
    
        def save_modified_csv():
            try:
                # Copie du DataFrame original
                df_modified = df.copy()

                # Récupérer les valeurs du tableau
                for col in range(table.columnCount()):

                    column_name = df.columns[col]

                    # Récupérer toutes les valeurs de cette colonne
                    values = []

                    for row in range(table.rowCount()):
                        item = table.item(row, col)

                        if item is not None:
                            values.append(item.text())
                        else:
                            values.append("")

                    # Garder le type original de la colonne
                    original_dtype = df[column_name].dtype

                    if pd.api.types.is_numeric_dtype(original_dtype):
                        # Convertir texte → nombre
                        values = pd.to_numeric(values, errors="raise")

                        # Reprendre le type original
                        values = values.astype(original_dtype)

                    # Mettre les valeurs dans le DataFrame
                    df_modified[column_name] = values

                # Nom du fichier modifié
                import os

                folder = os.path.dirname(file_path)
                filename = os.path.basename(file_path)

                name, extension = os.path.splitext(filename)

                modified_path = os.path.join(
                    folder,
                    f"{name}_modified{extension}"
                )
                
                nonlocal saved_path
                saved_path = modified_path

                # Sauvegarder
                df_modified.to_csv(
                    modified_path,
                    index=False
                )

                msg = QMessageBox(dialog)
                msg.setWindowTitle("Succès")
                msg.setIcon(QMessageBox.Icon.Information)
                msg.setText("Les modifications ont été enregistrées.")
                msg.setInformativeText(f"Fichier : {modified_path}")
                msg.setStandardButtons(QMessageBox.StandardButton.Ok)

                msg.setStyleSheet("""
                    QMessageBox {
                        background-color: #f4f5f7;
                    }

                    QMessageBox QLabel {
                        color: #111827;
                        font-size: 13px;
                    }

                    QMessageBox QLabel#qt_msgbox_label {
                        color: #111827;
                        font-size: 15px;
                        font-weight: 600;
                    }

                    QPushButton {
                        background-color: #2563eb;
                        color: white;
                        border: none;
                        border-radius: 6px;
                        padding: 8px 25px;
                        min-width: 70px;
                        font-weight: 600;
                    }

                    QPushButton:hover {
                        background-color: #1d4ed8;
                    }

                    QPushButton:pressed {
                        background-color: #1e40af;
                    }
                """)

                msg.exec()

                dialog.accept()

            except Exception as e:
                self.show_error_message(
                    "Erreur",
                    f"Impossible d'enregistrer les modifications :\n{e}"
                )

        save_button.clicked.connect(save_modified_csv)
        dialog.exec()
        return saved_path


    def build_historique_page(self):
        page = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(60, 50, 60, 50)
        layout.setSpacing(20)
        page.setLayout(layout)
 
        # header : titre + sous-titre 
        header_layout = QHBoxLayout()
        title_col = QVBoxLayout()
        title_col.setSpacing(2)
 
        title = QLabel("Historique des évaluations")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #374151;")
        self.historique_count_label = QLabel("0 évaluation enregistrée")
        self.historique_count_label.setStyleSheet("color: #9ca3af; font-size: 13px;")
 
        title_col.addWidget(title)
        title_col.addWidget(self.historique_count_label)
        header_layout.addLayout(title_col)
        header_layout.addStretch()
 
        # --- Recherche + filtre risque ---
        self.historique_search = QLineEdit()
        self.historique_search.setPlaceholderText("Rechercher un patient")
        self.historique_search.setFixedWidth(200)
        self.historique_search.setFixedHeight(36)
        self.historique_search.setStyleSheet("""
            QLineEdit {
                border: 1px solid #e5e7eb; border-radius: 8px;
                padding: 0 12px; font-size: 13px; background-color: white;
                color: #111827;
            }
            QLineEdit:focus { border-color: #2563eb; }
        """)
        self.historique_search.textChanged.connect(self.filter_historique)
 
        self.historique_risk_filter = QComboBox()
        self.historique_risk_filter.addItems(["Tous les risques", "Élevé", "Modéré", "Faible"])
        self.historique_risk_filter.setFixedWidth(150)
        self.historique_risk_filter.setFixedHeight(36)
        self.historique_risk_filter.setStyleSheet("""
            /* --- Partie visible du ComboBox --- */
    QComboBox {
        background-color: white;
        color: #111827;
        border: 1px solid #e5e7eb;
        border-radius: 8px;
        padding-left: 12px;
        padding-right: 12px;
        font-size: 13px;
    }

    QComboBox:hover {
        border: 1px solid #d1d5db;
    }

    QComboBox:focus {
        border: 1px solid #2563eb;
    }

    /* --- Bouton avec la flèche --- */
    QComboBox::drop-down {
        border: none;
        width: 30px;
    }

    /* --- Menu déroulant --- */
    QComboBox QAbstractItemView {
        background-color: white;
        color: #111827;
        border: 1px solid #d1d5db;
        border-radius: 8px;
        padding: 4px;
        outline: none;
        selection-background-color: #eff6ff;
        selection-color: #111827;
    }

    /* --- Chaque élément du menu --- */
    QComboBox QAbstractItemView::item {
        height: 32px;
        padding-left: 8px;
        padding-right: 8px;
        border-radius: 5px;
    }

    QComboBox QAbstractItemView::item:hover {
        background-color: #f3f4f6;
        color: #111827;
    }
""")
        self.historique_risk_filter.currentIndexChanged.connect(self.filter_historique)
 
        header_layout.addWidget(self.historique_search)
        header_layout.addWidget(self.historique_risk_filter)
        layout.addLayout(header_layout)
 
        # --- Cartes stats ---
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(16)
 
        self.historique_total_card, self.historique_total_value = self._make_stat_card("Total", "#374151")
        self.historique_risk_card, self.historique_risk_value = self._make_stat_card("Risque élevé", "#dc2626")
        self.historique_avg_card, self.historique_avg_value = self._make_stat_card("Score moyen", "#374151")
 
        stats_layout.addWidget(self.historique_total_card)
        stats_layout.addWidget(self.historique_risk_card)
        stats_layout.addWidget(self.historique_avg_card)
        layout.addLayout(stats_layout)
 
        # --- État vide ---
        self.historique_empty_label = QLabel("Aucune évaluation pour l'instant.")
        self.historique_empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.historique_empty_label.setStyleSheet("color: #9ca3af; font-size: 14px; padding: 80px 0;")
 
        # --- Tableau ---
        self.historique_table = QTableWidget()
        self.historique_table.setColumnCount(5)
        self.historique_table.setHorizontalHeaderLabels(["Patient", "Date", "Score", "Risque", "Actions"])
        self.historique_table.horizontalHeader().setStretchLastSection(True)
        self.historique_table.setColumnWidth(0, 220)
        self.historique_table.setColumnWidth(1, 150)
        self.historique_table.setColumnWidth(2, 80)
        self.historique_table.setColumnWidth(3, 110)
        self.historique_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.historique_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.historique_table.setStyleSheet(f"""
            QTableWidget {{
                background-color: white; border: 1px solid #e5e7eb; border-radius: 8px;
                gridline-color: #f3f4f6;
            }}
            QTableWidget::item {{ color: #111827; padding: 8px; border: none; }}
            QTableWidget::item:selected {{ background-color: #f3f4f6; color: #111827; outline: none; }}
            QHeaderView::section {{
                background-color: #f9fafb; color: #374151; font-weight: 600;
                padding: 8px; border: none; border-bottom: 1px solid #e5e7eb;
            }}
            {self.scrollbar_style}
        """)
        self.historique_table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.historique_table.setVisible(False)
        self.historique_table.verticalHeader().setDefaultSectionSize(56)
 
        layout.addWidget(self.historique_empty_label)
        layout.addWidget(self.historique_table)
 
        # stocke les lignes brutes (pour le filtrage) et la source
        self.historique_all_rows = []
 
        return page
    
    
    
    def _make_stat_card(self, label_text, value_color):
        """Petite carte stat, même style que tes autres QFrame + ombre."""
        card = QFrame()
        card.setFixedHeight(76)
        card.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #e5e7eb;
                border-radius: 12px;
            }
        """)
        card.setGraphicsEffect(self._make_shadow())
 
        card_layout = QVBoxLayout()
        card_layout.setContentsMargins(18, 12, 18, 12)
        card_layout.setSpacing(4)
        card.setLayout(card_layout)
 
        label = QLabel(label_text)
        label.setStyleSheet("color: #9ca3af; font-size: 12px; font-weight: 600; border: none; background: transparent;")
 
        value = QLabel("0")
        value.setStyleSheet(f"color: {value_color}; font-size: 22px; font-weight: 700; border: none; background: transparent;")
 
        card_layout.addWidget(label)
        card_layout.addWidget(value)
 
        return card, value
    
    
    def create_risk_badge(self, risk_level):
        """Widget badge coloré pour la colonne Risque."""
        colors = {
            "Faible": ("#dcfce7", "#16a34a"),
            "Modéré": ("#fef3c7", "#b45309"),
            "Élevé":  ("#fee2e2", "#dc2626"),
        }
        bg, fg = colors.get(risk_level, ("#f3f4f6", "#374151"))
 
        wrapper = QWidget()
        wrapper.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        wrapper.setStyleSheet("background-color: transparent;")
        
        wrapper_layout = QHBoxLayout()
        wrapper_layout.setContentsMargins(8, 0, 0, 0)
        wrapper.setLayout(wrapper_layout)
 
        badge = QLabel(risk_level)
        badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        badge.setStyleSheet(f"""
            QLabel {{
                background-color: {bg}; color: {fg};
                border-radius: 10px; padding: 4px 12px;
                font-size: 12px; font-weight: 600; border: none;
            }}
        """)
        wrapper_layout.addWidget(badge)
        wrapper_layout.addStretch()
        return wrapper


    def create_patient_cell(self, nom, prenom):
        """Widget avatar + nom pour la colonne Patient."""
        initials = (nom[:1] + prenom[:1]).upper() if nom and prenom else "?"
 
        wrapper = QWidget()
        wrapper.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        wrapper.setStyleSheet("background-color: transparent;")

        wrapper_layout = QHBoxLayout()
        wrapper_layout.setContentsMargins(10, 0, 0, 0)
        wrapper_layout.setSpacing(10)
        wrapper.setLayout(wrapper_layout)
 
        avatar = QLabel(initials)
        avatar.setFixedSize(30, 30)
        avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        avatar.setStyleSheet("""
            QLabel {
                background-color: #eff6ff; color: #2563eb;
                border-radius: 15px; font-size: 11px; font-weight: 700; border: none;
            }
        """)
 
        name = QLabel(f"{nom} {prenom}")
        name.setStyleSheet("color: #111827; font-size: 13px; border: none; background: transparent;")
 
        wrapper_layout.addWidget(avatar)
        wrapper_layout.addWidget(name)
        wrapper_layout.addStretch()
        return wrapper
    
    def create_patient_cell_id(self, nom, prenom, patient_id):
        initials = (nom[:1] + prenom[:1]).upper() if nom and prenom else "?"

        wrapper = QWidget()
        wrapper.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        wrapper.setStyleSheet("background-color: transparent;")

        wrapper_layout = QHBoxLayout()
        wrapper_layout.setContentsMargins(10, 0, 0, 0)
        wrapper_layout.setSpacing(10)
        wrapper.setLayout(wrapper_layout)

        avatar = QLabel(initials)
        avatar.setFixedSize(32, 32)
        avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        avatar.setStyleSheet("""
            QLabel {
                background-color: #eff6ff; color: #2563eb;
                border-radius: 16px; font-size: 11px; font-weight: 700; border: none;
            }
        """)

        text_col = QVBoxLayout()
        text_col.setSpacing(0)
        text_col.setContentsMargins(0, 0, 0, 0)

        name = QLabel(f"{nom} {prenom}")
        name.setStyleSheet("color: #111827; font-size: 13px; font-weight: 500; border: none; background: transparent;")
        id_label = QLabel(f"#P-{patient_id}")
        id_label.setStyleSheet("color: #9ca3af; font-size: 11px; border: none; background: transparent;")

        text_col.addWidget(name)
        text_col.addWidget(id_label)

        wrapper_layout.addWidget(avatar)
        wrapper_layout.addLayout(text_col)
        wrapper_layout.addStretch()
        return wrapper

    def load_historique(self):
        rows = get_evaluations_by_medecin(self.user_id)
        self.historique_all_rows = rows
        scores = []
        
        for row in rows:
            eval_id, patient_id, nom, prenom, result, created_at, image_path, clinical_csv_path = row

            score = result.get("score")

            if score is not None:
                scores.append(float(score))

        if scores:
            moyenne = sum(scores) / len(scores)
            self.historique_avg_value.setText(f"{moyenne:.2f}")
        else:
            self.historique_avg_value.setText("0.00")
        
        self.historique_search.blockSignals(True)
        self.historique_search.clear()
        self.historique_search.blockSignals(False)
        self.historique_risk_filter.blockSignals(True)
        self.historique_risk_filter.setCurrentIndex(0)
        self.historique_risk_filter.blockSignals(False)
        self.render_historique_rows(rows)
        
    def filter_historique(self):
        query = self.historique_search.text().strip().lower()
        risk_choice = self.historique_risk_filter.currentText()
 
        filtered = []
        for row in self.historique_all_rows:
            eval_id,patient_id, nom, prenom, result, created_at, image_path, clinical_csv_path = row
            full_name = f"{nom} {prenom}".lower()
            risk_level = result.get("risk_level", "—")
 
            if query and query not in full_name:
                continue
            if risk_choice != "Tous les risques" and risk_level != risk_choice:
                continue
            filtered.append(row)
 
        self.render_historique_rows(filtered)
        
    def create_patient_cell_count(self, nom, prenom, count):
        initials = (nom[:1] + prenom[:1]).upper() if nom and prenom else "?"

        wrapper = QWidget()
        wrapper.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        wrapper.setStyleSheet("background-color: transparent;")

        wrapper_layout = QHBoxLayout()
        wrapper_layout.setContentsMargins(10, 0, 0, 0)
        wrapper_layout.setSpacing(10)
        wrapper.setLayout(wrapper_layout)

        avatar = QLabel(initials)
        avatar.setFixedSize(30, 30)
        avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        avatar.setStyleSheet("""
            QLabel {
                background-color: #eff6ff; color: #2563eb;
                border-radius: 15px; font-size: 11px; font-weight: 700; border: none;
            }
        """)

        text_col = QVBoxLayout()
        text_col.setSpacing(0)
        text_col.setContentsMargins(0, 0, 0, 0)

        name = QLabel(f"{nom} {prenom}")
        name.setStyleSheet("color: #111827; font-size: 13px; border: none; background: transparent;")
        text_col.addWidget(name)

        if count > 1:
            count_label = QLabel(f"{count} évaluations")
            count_label.setStyleSheet("color: #2563eb; font-size: 11px; font-weight: 600; border: none; background: transparent;")
            text_col.addWidget(count_label)

        wrapper_layout.addWidget(avatar)
        wrapper_layout.addLayout(text_col)
        wrapper_layout.addStretch()
        return wrapper
   
    def render_historique_rows(self, rows):
        grouped = defaultdict(list)
        for row in rows:
            patient_id = row[1]
            grouped[patient_id].append(row)

        # sépare : items "single" (1 seule éval) vs "group" (plusieurs évals)
        display_items = []
        for patient_id, evals in grouped.items():
            evals_sorted = sorted(evals, key=lambda r: r[5], reverse=True)
            if len(evals_sorted) == 1:
                display_items.append(("single", evals_sorted[0]))
            else:
                display_items.append(("group", evals_sorted))

        def latest_date(item):
            kind, data = item
            return data[5] if kind == "single" else data[0][5]

        display_items.sort(key=latest_date, reverse=True)

        has_rows = bool(display_items)
        self.historique_empty_label.setVisible(not has_rows)
        self.historique_table.setVisible(has_rows)
        self.historique_table.setRowCount(len(display_items))

        for row_idx, (kind, data) in enumerate(display_items):

            if kind == "single":
                eval_id, patient_id, nom, prenom, result, created_at, image_path, clinical_csv_path = data
                score = result.get("score", "—")
                risk_level = result.get("risk_level", "—")

                self.historique_table.setCellWidget(row_idx, 0, self.create_patient_cell(nom, prenom))
                self.historique_table.setItem(row_idx, 1, QTableWidgetItem(created_at.strftime("%d/%m/%Y %H:%M")))
                self.historique_table.setItem(row_idx, 2, QTableWidgetItem(str(score)))
                self.historique_table.setCellWidget(row_idx, 3, self.create_risk_badge(risk_level))

                actions_widget = QWidget()
                actions_widget.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
                actions_widget.setStyleSheet("QWidget { background-color: white; border: none; }")
                actions_layout = QHBoxLayout()
                actions_layout.setContentsMargins(4, 0, 4, 0)
                actions_layout.setSpacing(8)
                actions_widget.setLayout(actions_layout)

                row_data = {
                    "nom": nom, "prenom": prenom, "score": score, "risk_level": risk_level,
                    "created_at": created_at, "image_path": image_path, "clinical_csv_path": clinical_csv_path,
                }
                detail_button = QPushButton("Voir détail")
                detail_button.setCursor(Qt.CursorShape.PointingHandCursor)
                detail_button.setFixedWidth(100)
                detail_button.setFixedHeight(28)
                detail_button.setStyleSheet("""
                    QPushButton {
                        background-color: #eff6ff; color: #2563eb; border: 1px solid #bfdbfe;
                        border-radius: 6px; padding: 4px 12px; font-size: 12px; font-weight: 600;
                    }
                    QPushButton:hover { background-color: #dbeafe; }
                """)
                detail_button.clicked.connect(lambda checked, d=row_data: self.show_evaluation_detail(d))
                actions_layout.addWidget(detail_button)

                delete_button = QPushButton("Supprimer")
                delete_button.setCursor(Qt.CursorShape.PointingHandCursor)
                delete_button.setFixedWidth(85)
                delete_button.setFixedHeight(28)
                delete_button.setStyleSheet("""
                    QPushButton {
                        background-color: #fff1f2; color: #dc2626; border: 1px solid #fecdd3;
                        border-radius: 6px; padding: 4px 12px; font-size: 12px; font-weight: 600;
                    }
                    QPushButton:hover { background-color: #ffe4e6; }
                """)
                delete_button.clicked.connect(lambda checked, evaluation_id=eval_id: self.delete_evaluation(evaluation_id))
                actions_layout.addWidget(delete_button)

                self.historique_table.setCellWidget(row_idx, 4, actions_widget)

            else:  # kind == "group"
                evals_sorted = data
                eval_id, patient_id, nom, prenom, result, created_at, image_path, clinical_csv_path = evals_sorted[0]
                score = result.get("score", "—")
                risk_level = result.get("risk_level", "—")

                self.historique_table.setCellWidget(
                    row_idx, 0, self.create_patient_cell_count(nom, prenom, len(evals_sorted))
                )
                self.historique_table.setItem(row_idx, 1, QTableWidgetItem(created_at.strftime("%d/%m/%Y %H:%M")))
                self.historique_table.setItem(row_idx, 2, QTableWidgetItem(str(score)))
                self.historique_table.setCellWidget(row_idx, 3, self.create_risk_badge(risk_level))

                actions_widget = QWidget()
                actions_widget.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
                actions_widget.setStyleSheet("QWidget { background-color: white; border: none; }")
                actions_layout = QHBoxLayout()
                actions_layout.setContentsMargins(4, 0, 4, 0)
                actions_widget.setLayout(actions_layout)

                detail_button = QPushButton("Voir détail")
                detail_button.setCursor(Qt.CursorShape.PointingHandCursor)
                detail_button.setFixedWidth(100)
                detail_button.setFixedHeight(28)
                detail_button.setStyleSheet("""
                    QPushButton {
                        background-color: #eff6ff; color: #2563eb; border: 1px solid #bfdbfe;
                        border-radius: 6px; padding: 4px 12px; font-size: 12px; font-weight: 600;
                    }
                    QPushButton:hover { background-color: #dbeafe; }
                """)
                detail_button.clicked.connect(
                    lambda checked, g=evals_sorted, n=nom, p=prenom: self.show_patient_evaluations(n, p, g)
                )
                actions_layout.addWidget(detail_button)
                spacer = QWidget()
                spacer.setFixedSize(85, 28)
                actions_layout.addWidget(spacer)
                
                self.historique_table.setCellWidget(row_idx, 4, actions_widget)

        self.update_historique_stats(rows)
        
    def show_patient_evaluations(self, nom, prenom, evaluations):
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Évaluations de {nom} {prenom}")
        dialog.resize(650, 450)
        dialog.setStyleSheet("background-color: #f4f5f7;")

        layout = QVBoxLayout()
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(14)
        dialog.setLayout(layout)

        title = QLabel(f"{nom} {prenom}")
        title.setStyleSheet("font-size: 17px; font-weight: 700; color: #111827; background: transparent; border: none;")
        subtitle = QLabel(f"{len(evaluations)} évaluation(s) enregistrée(s)")
        subtitle.setStyleSheet("color: #9ca3af; font-size: 12px; background: transparent; border: none;")
        layout.addWidget(title)
        layout.addWidget(subtitle)

        table = QTableWidget()
        table.setColumnCount(4)
        table.setHorizontalHeaderLabels(["Date", "Score", "Risque", "Actions"])
        table.horizontalHeader().setStretchLastSection(True)
        table.setColumnWidth(0, 150)
        table.setColumnWidth(1, 70)
        table.setColumnWidth(2, 100)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        table.setStyleSheet(f"""
            QTableWidget {{
                background-color: white; border: 1px solid #e5e7eb; border-radius: 8px;
                gridline-color: #f3f4f6;
            }}
            QTableWidget::item {{ color: #111827; padding: 6px; border: none; }}
            QHeaderView::section {{
                background-color: #f9fafb; color: #374151; font-weight: 600;
                padding: 8px; border: none; border-bottom: 1px solid #e5e7eb;
            }}
            {self.scrollbar_style}
        """)
        table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        table.verticalHeader().setDefaultSectionSize(50)
        layout.addWidget(table)

        current_evals = list(evaluations)

        def refresh_table():
            table.setRowCount(len(current_evals))
            for row_idx, ev in enumerate(current_evals):
                eval_id, patient_id, n, p, result, created_at, image_path, clinical_csv_path = ev
                score = result.get("score", "—")
                risk_level = result.get("risk_level", "—")

                table.setItem(row_idx, 0, QTableWidgetItem(created_at.strftime("%d/%m/%Y %H:%M")))
                table.setItem(row_idx, 1, QTableWidgetItem(str(score)))
                table.setCellWidget(row_idx, 2, self.create_risk_badge(risk_level))

                actions_widget = QWidget()
                actions_widget.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
                actions_widget.setStyleSheet("QWidget { background-color: white; border: none; }")
                actions_layout = QHBoxLayout()
                actions_layout.setContentsMargins(4, 0, 4, 0)
                actions_layout.setSpacing(6)
                actions_widget.setLayout(actions_layout)

                row_data = {
                    "nom": n, "prenom": p, "score": score, "risk_level": risk_level,
                    "created_at": created_at, "image_path": image_path, "clinical_csv_path": clinical_csv_path,
                }
                detail_btn = QPushButton("Détail")
                detail_btn.setCursor(Qt.CursorShape.PointingHandCursor)
                detail_btn.setFixedSize(70, 26)
                detail_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #eff6ff; color: #2563eb; border: 1px solid #bfdbfe;
                        border-radius: 6px; font-size: 11px; font-weight: 600;
                    }
                    QPushButton:hover { background-color: #dbeafe; }
                """)
                detail_btn.clicked.connect(lambda checked, d=row_data: self.show_evaluation_detail(d))
                actions_layout.addWidget(detail_btn)

                delete_btn = QPushButton("Suppr.")
                delete_btn.setCursor(Qt.CursorShape.PointingHandCursor)
                delete_btn.setFixedSize(70, 26)
                delete_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #fff1f2; color: #dc2626; border: 1px solid #fecdd3;
                        border-radius: 6px; font-size: 11px; font-weight: 600;
                    }
                    QPushButton:hover { background-color: #ffe4e6; }
                """)
                delete_btn.clicked.connect(lambda checked, evaluation_id=eval_id: handle_delete(evaluation_id))
                actions_layout.addWidget(delete_btn)

                table.setCellWidget(row_idx, 3, actions_widget)

        def handle_delete(evaluation_id):
            soft_delete_evaluation(evaluation_id)
            nonlocal current_evals
            current_evals = [e for e in current_evals if e[0] != evaluation_id]
            self.load_historique()
            if not current_evals:
                dialog.accept()
            else:
                refresh_table()

        refresh_table()
        dialog.exec()
        
        
    def delete_evaluation(self, evaluation_id):

        msg = QMessageBox(self)
        

        msg.setWindowTitle("Supprimer l'évaluation")
        msg.setText("Voulez-vous vraiment supprimer cette évaluation ?")
        msg.setIcon(QMessageBox.Icon.Question)

        yes_button = msg.addButton(
            "Supprimer",
            QMessageBox.ButtonRole.YesRole
        )

        no_button = msg.addButton(
            "Annuler",
            QMessageBox.ButtonRole.NoRole
        )

        msg.setStyleSheet("""
    QMessageBox {
        background-color: white;
    }

    QMessageBox QLabel {
        background-color: transparent;
        color: #1e293b;
        font-size: 13px;
        padding: 6px;
    }

    QMessageBox QPushButton {
        background-color: white;
        color: #334155;
        border: 1px solid #cbd5e1;
        border-radius: 7px;
        padding: 7px 18px;
        min-width: 80px;
        font-size: 12px;
    }

    QMessageBox QPushButton:hover {
        background-color: #f8fafc;
    }

    QMessageBox QPushButton[text="Supprimer"] {
        background-color: #dc2626;
        color: white;
        border: none;
    }

    QMessageBox QPushButton[text="Supprimer"]:hover {
        background-color: #b91c1c;
    }
""")

        msg.exec()

        if msg.clickedButton() != yes_button:
            return

        try:
            soft_delete_evaluation(evaluation_id)

            self.load_historique()

        except Exception as e:

            QMessageBox.critical(
                self,
                "Erreur",
                f"Impossible de supprimer l'évaluation :\n{e}"
            )
        
        
    def update_historique_stats(self, rows):
        total = len(rows)
        self.historique_count_label.setText(
            f"{total} évaluation{'s' if total != 1 else ''} enregistrée{'s' if total != 1 else ''}"
        )
        self.historique_total_value.setText(str(total))

        if total == 0:
            self.historique_risk_value.setText("0")
            self.historique_avg_value.setText("—")
            return

        elevated = sum(1 for r in rows if r[4].get("risk_level") == "Élevé")
        self.historique_risk_value.setText(str(elevated))

        scores = [r[4].get("score") for r in rows if isinstance(r[4].get("score"), (int, float))]
        avg = round(sum(scores) / len(scores), 2) if scores else "—"
        self.historique_avg_value.setText(str(avg))
            
    def show_evaluation_detail(self, data):
        dialog = QDialog(self)
        dialog.setWindowTitle("Détail de l'évaluation")
        dialog.resize(420, 380)
        dialog.setStyleSheet("background-color: #f4f5f7;")

        layout = QVBoxLayout()
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(14)
        dialog.setLayout(layout)

        name_label = QLabel(f"{data['nom']} {data['prenom']}")
        name_label.setStyleSheet("font-size: 17px; font-weight: 700; color: #111827; background: transparent; border: none;")
        layout.addWidget(name_label)

        date_label = QLabel(data["created_at"].strftime("Évalué le %d/%m/%Y à %H:%M"))
        date_label.setStyleSheet("color: #6b7280; font-size: 12px; background: transparent; border: none;")
        layout.addWidget(date_label)

        risk_color = {"Faible": "#16a34a", "Modéré": "#f59e0b", "Élevé": "#dc2626"}.get(data["risk_level"], "#374151")
        result_frame = QFrame()
        result_frame.setStyleSheet(f"""
            background-color: white; border: 2px solid {risk_color}; border-radius: 12px;
        """)
        result_layout = QVBoxLayout()
        result_layout.setContentsMargins(20, 16, 20, 16)
        result_frame.setLayout(result_layout)

        score_label = QLabel(f"Score : {data['score']}")
        score_label.setStyleSheet(f"color: {risk_color}; font-size: 16px; font-weight: 700; background: transparent; border: none;")
        risk_label = QLabel(f"Niveau de risque : {data['risk_level']}")
        risk_label.setStyleSheet(f"color: {risk_color}; font-size: 14px; font-weight: 600; background: transparent; border: none;")
        result_layout.addWidget(score_label)
        result_layout.addWidget(risk_label)
        layout.addWidget(result_frame)

        #  acces aux fichiers utilises pour cette evaluation
        files_row = QHBoxLayout()
        files_row.setSpacing(10)

        if data["image_path"]:
            img_btn = QPushButton("Voir l'IRM")
            img_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            img_btn.setStyleSheet("""
                QPushButton { background-color: #eff6ff; color: #2563eb; border: 1px solid #bfdbfe;
                    border-radius: 6px; padding: 8px 14px; font-size: 12px; font-weight: 600; }
            QPushButton:hover { background-color: #dbeafe; }
        """)
            img_btn.clicked.connect(lambda: self.open_image_viewer(data["image_path"]))
            files_row.addWidget(img_btn)

        if data["clinical_csv_path"]:
            csv_btn = QPushButton("Voir le CSV")
            csv_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            csv_btn.setStyleSheet("""
                QPushButton { background-color: #eff6ff; color: #2563eb; border: 1px solid #bfdbfe;
                    border-radius: 6px; padding: 8px 14px; font-size: 12px; font-weight: 600; }
                QPushButton:hover { background-color: #dbeafe; }
            """)
            csv_btn.clicked.connect(lambda: self.open_csv_viewer(data["clinical_csv_path"]))
            files_row.addWidget(csv_btn)

        layout.addLayout(files_row)
        layout.addStretch()
        dialog.exec()


    def confirm_duplicate_evaluation(self, existing_eval):
        eval_id, result, created_at = existing_eval
        score = result.get("score", "—")
        risk_level = result.get("risk_level", "—")

        hours_ago = int((datetime.now() - created_at).total_seconds() // 3600)

        box = QMessageBox(self)
        box.setWindowTitle("Évaluation récente détectée")
        box.setText(
            f"Une évaluation identique existe déjà pour ce patient, "
            f"réalisée il y a {hours_ago}h avec un score de {score} ({risk_level}).\n\n"
            f"Voulez-vous quand même relancer une nouvelle évaluation ?"
        )
        box.setIcon(QMessageBox.Icon.Warning)
        box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        box.setDefaultButton(QMessageBox.StandardButton.No)
        box.setStyleSheet("""
            QMessageBox { min-width: 380px; }
            QMessageBox QLabel { color: #1f2937; font-size: 13px; }
            QPushButton {
                background-color: #f3f4f6; color: #111827; border: 1px solid #d1d5db;
                border-radius: 6px; padding: 6px 18px; min-width: 70px;
            }
            QPushButton:hover { background-color: #e5e7eb; }
            QPushButton:default {
                background-color: #f59e0b; color: white; border: none;
            }
            QPushButton:default:hover { background-color: #d97706; }
        """)
        answer = box.exec()
        return answer == QMessageBox.StandardButton.Yes











        
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = DashboardScreen()
    window.resize(1100, 700)
    window.show()
    sys.exit(app.exec())

