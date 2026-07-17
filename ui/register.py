from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox
)
from models.database import get_connections
from utils.security import hash_password
import psycopg2

class RegisterScreen(QWidget):
    def __init__(self, stack):
        super().__init__()
        self.stack = stack

        layout = QVBoxLayout()

        title = QLabel("Créer un compte - NeuroPronostic")
        layout.addWidget(title)

        self.nom_input = QLineEdit()
        self.nom_input.setPlaceholderText("Nom complet")
        layout.addWidget(self.nom_input)

        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Email")
        layout.addWidget(self.email_input)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Mot de passe")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(self.password_input)

        register_button = QPushButton("S'inscrire")
        register_button.clicked.connect(self.handle_register)
        layout.addWidget(register_button)

        # Lien vers l'écran Login (pour ceux qui ont déjà un compte)
        go_to_login = QPushButton("Déjà un compte ? Se connecter")
        go_to_login.clicked.connect(lambda: self.stack.setCurrentIndex(0))
        layout.addWidget(go_to_login)

        self.setLayout(layout)

    def handle_register(self):
        nom = self.nom_input.text()
        email = self.email_input.text()
        password = self.password_input.text()

        if not nom or not email or not password:
            QMessageBox.warning(self, "Erreur", "Tous les champs sont obligatoires")
            return

        hashed = hash_password(password)

        conn = get_connections()
        cur = conn.cursor()
        try:
            cur.execute(
                "INSERT INTO users (nom, email, password_hash) VALUES (%s, %s, %s)",
                (nom, email, hashed)
            )
            conn.commit()
            QMessageBox.information(self, "Succès", "Compte créé ! Tu peux te connecter.")
            self.stack.setCurrentIndex(0)   # retourne à l'écran Login
        except psycopg2.errors.UniqueViolation:
            conn.rollback()
            QMessageBox.warning(self, "Erreur", "Cet email est déjà utilisé")
        finally:
            cur.close()
            conn.close()