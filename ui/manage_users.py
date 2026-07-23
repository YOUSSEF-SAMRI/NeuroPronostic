import psycopg2
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
    QDialog, QLineEdit, QComboBox, QFormLayout, QDialogButtonBox,
    QFrame
)
from PyQt6.QtCore import Qt
from models.database import get_connections
from utils.security import hash_password

# ==========================================
# STYLESHEET (QSS) GLOBAL
# ==========================================
DARK_STYLESHEET = """
QWidget {
    background-color: #1e1e2e;
    color: #cdd6f4;
    font-family: 'Segoe UI', Helvetica, Arial, sans-serif;
    font-size: 13px;
}

/* Titre */
QLabel#TitleLabel {
    font-size: 20px;
    font-weight: bold;
    color: #10b981;
    margin-bottom: 5px;
}

/* Tableau */
QTableWidget {
    background-color: #181825;
    border: 1px solid #313244;
    border-radius: 8px;
    gridline-color: transparent;
    selection-background-color: #45475a;
    selection-color: #f5e0dc;
}

QHeaderView::section {
    background-color: #313244;
    color: #a6adc8;
    padding: 8px;
    font-weight: bold;
    border: none;
}

QTableWidget::item {
    padding: 6px;
}

/* Inputs & Combobox */
QLineEdit, QComboBox {
    background-color: #313244;
    border: 1px solid #45475a;
    border-radius: 6px;
    padding: 6px 10px;
    color: #cdd6f4;
}

QLineEdit:focus, QComboBox:focus {
    border: 1px solid #89b4fa;
}

QComboBox::drop-down {
    border: none;
    padding-right: 10px;
}

/* Boutons de la barre principale */
QPushButton {
    background-color: #313244;
    color: #cdd6f4;
    border: 1px solid #45475a;
    border-radius: 6px;
    padding: 8px 16px;
    font-weight: 600;
}

QPushButton:hover {
    background-color: #45475a;
}

QPushButton:pressed {
    background-color: #585b70;
}

/* Boutons spécifiques */
QPushButton#BtnAdd {
    background-color: #89b4fa;
    color: #11111b;
    border: none;
}
QPushButton#BtnAdd:hover {
    background-color: #b4befe;
}

QPushButton#BtnDelete {
    background-color: #f38ba8;
    color: #11111b;
    border: none;
}
QPushButton#BtnDelete:hover {
    background-color: #eba0ac;
}

/* Dialogue Modal */
QDialog {
    background-color: #1e1e2e;
}
"""


class UserFormDialog(QDialog):
    """Formulaire pour Ajouter / Modifier un utilisateur."""
    def __init__(self, parent=None, user_data=None):
        super().__init__(parent)
        self.user_data = user_data
        self.setWindowTitle("Modifier l'utilisateur" if user_data else "Ajouter un utilisateur")
        self.setFixedWidth(380)
        self.setStyleSheet(DARK_STYLESHEET)

        layout = QVBoxLayout()
        self.setLayout(layout)

        # En-tête
        title = QLabel("Modifier l'utilisateur" if user_data else "Nouvel utilisateur")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #89b4fa; margin-bottom: 10px;")
        layout.addWidget(title)

        form_layout = QFormLayout()
        form_layout.setSpacing(12)

        self.nom_input = QLineEdit(user_data["nom"] if user_data else "")
        self.nom_input.setPlaceholderText("Ex: Jean Dupont")
        
        self.email_input = QLineEdit(user_data["email"] if user_data else "")
        self.email_input.setPlaceholderText("Ex: jean@exemple.com")

        self.role_input = QComboBox()
        self.role_input.addItems(["user", "admin"])
        if user_data:
            self.role_input.setCurrentText(user_data["role"])

        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setPlaceholderText(
            "Laisser vide pour conserver" if user_data else "Mot de passe"
        )

        form_layout.addRow("Nom :", self.nom_input)
        form_layout.addRow("Email :", self.email_input)
        form_layout.addRow("Rôle :", self.role_input)
        form_layout.addRow("Mot de passe :", self.password_input)

        layout.addLayout(form_layout)

        # Séparateur
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet("color: #313244; margin: 10px 0;")
        layout.addWidget(line)

        # Boutons d'action
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_data(self):
        return {
            "nom": self.nom_input.text().strip(),
            "email": self.email_input.text().strip(),
            "role": self.role_input.currentText(),
            "password": self.password_input.text(),
        }


class ManageUsersScreen(QWidget):
    def __init__(self, admin_id=None):
        super().__init__()
        self.admin_id = admin_id
        self.setWindowTitle("Gestion des utilisateurs")
        self.resize(750, 500)
        self.setStyleSheet(DARK_STYLESHEET)

        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        self.setLayout(layout)

        # En-tête
        title = QLabel("Gestion des utilisateurs")
        title.setObjectName("TitleLabel")
        layout.addWidget(title)

        # Tableau
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["ID", "Nom", "Email", "Rôle"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setShowGrid(False)
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet("QTableWidget { alternate-background-color: #1e1e2e; }")
        layout.addWidget(self.table)

        # Barre de boutons
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(10)

        add_button = QPushButton("Ajouter")
        add_button.setObjectName("BtnAdd")

        edit_button = QPushButton("Modifier")

        delete_button = QPushButton("Supprimer")
        delete_button.setObjectName("BtnDelete")

        refresh_button = QPushButton("Rafraîchir")

        add_button.clicked.connect(self.add_user)
        edit_button.clicked.connect(self.edit_user)
        delete_button.clicked.connect(self.delete_user)
        refresh_button.clicked.connect(self.load_users)

        for btn in (add_button, edit_button, delete_button, refresh_button):
            btn.setCursor(Qt.CursorShape.PointingHandCursor)

        buttons_layout.addWidget(add_button)
        buttons_layout.addWidget(edit_button)
        buttons_layout.addWidget(delete_button)
        buttons_layout.addStretch()  # Espace flexible
        buttons_layout.addWidget(refresh_button)

        layout.addLayout(buttons_layout)

        self.load_users()

    # ---------- READ ----------
    def load_users(self):
        try:
            conn = get_connections()
            cur = conn.cursor()
            cur.execute("SELECT id, nom, email, role FROM users WHERE role = 'user' AND is_active = TRUE ORDER BY id")
            rows = cur.fetchall()
            cur.close()
            conn.close()
        except psycopg2.Error as e:
            QMessageBox.critical(self, "Erreur", f"Impossible de charger les utilisateurs :\n{e}")
            return

        self.table.setRowCount(len(rows))
        for i, (user_id, nom, email, role) in enumerate(rows):
            item_id = QTableWidgetItem(str(user_id))
            item_id.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            self.table.setItem(i, 0, item_id)
            self.table.setItem(i, 1, QTableWidgetItem(nom))
            self.table.setItem(i, 2, QTableWidgetItem(email))
            self.table.setItem(i, 3, QTableWidgetItem(role))

    def get_selected_user(self):
        row = self.table.currentRow()
        if row == -1:
            return None
        return {
            "id": int(self.table.item(row, 0).text()),
            "nom": self.table.item(row, 1).text(),
            "email": self.table.item(row, 2).text(),
            "role": self.table.item(row, 3).text(),
        }

    # ---------- CREATE ----------
    def add_user(self):
        dialog = UserFormDialog(self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        data = dialog.get_data()
        if not data["nom"] or not data["email"] or not data["password"]:
            QMessageBox.warning(self, "Erreur", "Tous les champs sont obligatoires pour un ajout.")
            return

        hashed = hash_password(data["password"])
        try:
            conn = get_connections()
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO users (nom, email, password_hash, role) VALUES (%s, %s, %s, %s)",
                (data["nom"], data["email"], hashed, data["role"])
            )
            conn.commit()
            cur.close()
            conn.close()
        except psycopg2.errors.UniqueViolation:
            conn.rollback()
            QMessageBox.warning(self, "Erreur", "Cet email est déjà utilisé.")
            return
        except psycopg2.Error as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de l'ajout :\n{e}")
            return

        QMessageBox.information(self, "Succès", "Utilisateur ajouté.")
        self.load_users()

    # ---------- UPDATE ----------
    def edit_user(self):
        selected = self.get_selected_user()
        if not selected:
            QMessageBox.information(self, "Info", "Sélectionne un utilisateur à modifier.")
            return

        dialog = UserFormDialog(self, user_data=selected)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        data = dialog.get_data()
        if not data["nom"] or not data["email"]:
            QMessageBox.warning(self, "Erreur", "Le nom et l'email sont obligatoires.")
            return

        try:
            conn = get_connections()
            cur = conn.cursor()
            if data["password"]:
                hashed = hash_password(data["password"])
                cur.execute(
                    "UPDATE users SET nom=%s, email=%s, role=%s, password_hash=%s WHERE id=%s",
                    (data["nom"], data["email"], data["role"], hashed, selected["id"])
                )
            else:
                cur.execute(
                    "UPDATE users SET nom=%s, email=%s, role=%s WHERE id=%s",
                    (data["nom"], data["email"], data["role"], selected["id"])
                )
            conn.commit()
            cur.close()
            conn.close()
        except psycopg2.errors.UniqueViolation:
            conn.rollback()
            QMessageBox.warning(self, "Erreur", "Cet email est déjà utilisé.")
            return
        except psycopg2.Error as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de la modification :\n{e}")
            return

        QMessageBox.information(self, "Succès", "Utilisateur modifié.")
        self.load_users()

    # ---------- DELETE ----------
    def delete_user(self):
        selected = self.get_selected_user()
        if not selected:
            QMessageBox.information(self, "Info", "Sélectionne un utilisateur à supprimer.")
            return

        if self.admin_id is not None and selected["id"] == self.admin_id:
            QMessageBox.warning(self, "Erreur", "Tu ne peux pas supprimer ton propre compte.")
            return

        confirm = QMessageBox.question(
            self, "Confirmation",
            f"Supprimer l'utilisateur « {selected['nom']} » ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return

        try:
            conn = get_connections()
            cur = conn.cursor()
            cur.execute("UPDATE users SET is_active = FALSE WHERE id=%s", (selected["id"],))
            conn.commit()
            cur.close()
            conn.close()
        except psycopg2.Error as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de la suppression :\n{e}")
            return

        QMessageBox.information(self, "Succès", "Utilisateur supprimé.")
        self.load_users()