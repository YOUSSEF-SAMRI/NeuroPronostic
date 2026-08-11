from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QComboBox, QPushButton, QMessageBox
)
from PyQt6.QtCore import Qt


class AddPatientDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Ajouter un patient")
        self.setFixedWidth(400)
        self.setStyleSheet("""
           
            QLabel#fieldLabel {
                background-color: transparent;
                color: #374151;
                font-size: 13px;
                font-weight: 600;
                padding: 0px;
                margin: 0px;
            }
            QLineEdit, QComboBox {
                background-color: #f9fafb;
                border: 1px solid #d1d5db;
                border-radius: 8px;
                padding: 10px 12px;
                font-size: 13px;
                color: #111827;
            }
            QLineEdit:focus, QComboBox:focus {
                border: 1.5px solid #2563eb;
                background-color: #ffffff;
            }
            QComboBox::drop-down {
                border: none;
                width: 24px;
            }
            QComboBox QAbstractItemView {
                background-color: #ffffff;
                color: #111827;
                border: 1px solid #d1d5db;
                selection-background-color: #2563eb;
                selection-color: #ffffff;
                outline: none;
                padding: 4px;
            }
        """)

        layout = QVBoxLayout()
        layout.setContentsMargins(28, 26, 28, 26)
        layout.setSpacing(6)
        self.setLayout(layout)

        header = QLabel("Nouveau patient")
        header.setStyleSheet("font-size: 17px; font-weight: 700; color: #111827; margin-bottom: 10px;")
        layout.addWidget(header)

        layout.addWidget(self._make_label("Nom"))
        self.nom_input = QLineEdit()
        self.nom_input.setPlaceholderText("Ex : Bennani")
        layout.addWidget(self.nom_input)
        layout.addSpacing(8)

        layout.addWidget(self._make_label("Prénom"))
        self.prenom_input = QLineEdit()
        self.prenom_input.setPlaceholderText("Ex : Sara")
        layout.addWidget(self.prenom_input)
        layout.addSpacing(8)

        layout.addWidget(self._make_label("Age"))
        self.age_input = QLineEdit()
        self.age_input.setPlaceholderText("Ex : 45")
        layout.addWidget(self.age_input)
        layout.addSpacing(8)

        layout.addWidget(self._make_label("Sexe"))
        self.sexe_input = QComboBox()
        self.sexe_input.addItems(["M", "F"])
        layout.addWidget(self.sexe_input)
        layout.addSpacing(20)

        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(10)

        cancel_button = QPushButton("Annuler")
        cancel_button.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_button.setFixedHeight(42)
        cancel_button.setStyleSheet("""
            QPushButton {
                background-color: #f3f4f6;
                color: #374151;
                border: 1px solid #d1d5db;
                border-radius: 8px;
                font-weight: 600;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #e5e7eb;
            }
        """)
        cancel_button.clicked.connect(self.reject)

        save_button = QPushButton("Enregistrer")
        save_button.setCursor(Qt.CursorShape.PointingHandCursor)
        save_button.setFixedHeight(42)
        save_button.setStyleSheet("""
            QPushButton {
                background-color: #2563eb;
                color: white;
                border: none;
                border-radius: 8px;
                font-weight: 600;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #1d4ed8;
            }
        """)
        save_button.clicked.connect(self.validate_and_accept)

        buttons_layout.addWidget(cancel_button)
        buttons_layout.addWidget(save_button)
        layout.addLayout(buttons_layout)

    def _make_label(self, text):
        label = QLabel(text)
        label.setObjectName("fieldLabel")
        return label

    def validate_and_accept(self):
        nom = self.nom_input.text().strip()
        prenom = self.prenom_input.text().strip()
        age_text = self.age_input.text().strip()

        if not nom or not prenom:
            QMessageBox.warning(self, "Champs manquants", "Le nom et le prénom sont obligatoires.")
            return

        if not age_text.isdigit():
            QMessageBox.warning(self, "Âge invalide", "L'âge doit être un nombre entier.")
            return

        age = int(age_text)
        if age <= 0 or age > 120:
            QMessageBox.warning(self, "Âge invalide", "Merci d'entrer un âge réaliste.")
            return

        self.accept()

    def get_data(self):
        return {
            "nom": self.nom_input.text().strip(),
            "prenom": self.prenom_input.text().strip(),
            "age": int(self.age_input.text().strip()),
            "sexe": self.sexe_input.currentText(),
        }