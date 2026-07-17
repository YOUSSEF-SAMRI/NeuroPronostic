from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox
)
from models.database import get_connections
from utils.security import verify_password

class LoginScreen(QWidget):
    def __init__(self, stack):
        super().__init__()
        self.stack = stack   # on garde une référence au QStackedWidget pour naviguer

        layout = QVBoxLayout()

        title = QLabel("Connexion - NeuroPronostic")
        layout.addWidget(title)

        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Email")
        layout.addWidget(self.email_input)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Mot de passe")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(self.password_input)

        login_button = QPushButton("Se connecter")
        login_button.clicked.connect(self.handle_login)
        layout.addWidget(login_button)
        go_to_register = QPushButton("Pas de compte ? S'inscrire")
        go_to_register.clicked.connect(lambda: self.stack.setCurrentIndex(2))
        layout.addWidget(go_to_register)
        self.setLayout(layout)

    def handle_login(self):
        email = self.email_input.text()
        password = self.password_input.text()

        conn = get_connections()
        cur = conn.cursor()
        cur.execute("SELECT password_hash FROM users WHERE email = %s", (email,))
        result = cur.fetchone()
        cur.close()
        conn.close()

        if result is None:
            QMessageBox.warning(self, "Erreur", "Email introuvable")
            return

        stored_hash = result[0]
        if verify_password(password, stored_hash):
            QMessageBox.information(self, "Succès", "Connexion réussie !")
            self.stack.setCurrentIndex(1)   # passe au Dashboard (index 1)
        else:
            QMessageBox.warning(self, "Erreur", "Mot de passe incorrect")