from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox
)
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QCursor
from models.database import get_connections
from utils.security import verify_password


class LoginScreen(QWidget):
    def __init__(self, stack):
        super().__init__()
        self.stack = stack

        # IMPORTANT : sans ça, le background-color ne s'applique pas sur un QWidget custom
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet("background-color: #e8e8e8;")

        # --- La "carte" blanche centrée ---
        card = QWidget()
        card.setObjectName("card")   # nom unique pour cibler UNIQUEMENT ce widget
        card.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        card.setFixedWidth(500)
        card.setStyleSheet("""
            QWidget#card {
                background-color: white;
                border: 1px solid #d63384;
                border-radius: 10px;
            }
        """)
        card_layout = QVBoxLayout()
        card_layout.setContentsMargins(40, 30, 40, 30)
        card_layout.setSpacing(15)

        # --- Logo (pas de bordure) ---
        logo = QLabel()
        pixmap = QPixmap("assets/logo.png")
        logo.setPixmap(pixmap.scaled(200, 200, Qt.AspectRatioMode.KeepAspectRatio,
                                      Qt.TransformationMode.SmoothTransformation))
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo.setStyleSheet("border: none; background: transparent;")
        card_layout.addWidget(logo)

        # --- Titre ---
        title = QLabel("Brain tumor detection")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("border: none; background: transparent; font-size: 16px; font-weight: bold; color: #2e7d32;")
        card_layout.addWidget(title)

        # --- Champ Email ---
        email_label = QLabel("Email")
        email_label.setStyleSheet("border: none; background: transparent; color: #444;")
        card_layout.addWidget(email_label)

        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Enter your email..")
        self.email_input.setStyleSheet(self.input_style())
        card_layout.addWidget(self.email_input)

        # --- Champ Mot de passe ---
        password_label = QLabel("Password")
        password_label.setStyleSheet("border: none; background: transparent; color: #333;")
        card_layout.addWidget(password_label)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Enter your password..")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setStyleSheet(self.input_style())
        card_layout.addWidget(self.password_input)

        # --- Lien "Pas de compte ?" ---
        go_to_register = QPushButton("Pas de compte ? S'inscrire")
        go_to_register.setMinimumWidth(180)
        go_to_register.setCursor(
            QCursor(Qt.CursorShape.PointingHandCursor))
        
        go_to_register.setStyleSheet("""
        QPushButton{
            border:none;
            background:transparent;
            color:#d63384;
            font-size:13px;
        }

        QPushButton:hover{
            color:#a61c5d;
            text-decoration:underline;
            font-weight:bold;
        }

        QPushButton:pressed{
            color:#7d1647;
        }

        """)
        go_to_register.clicked.connect(lambda: self.stack.setCurrentIndex(2))
        card_layout.addWidget(go_to_register, alignment=Qt.AlignmentFlag.AlignRight)

        # --- Bouton Login ---
        login_button = QPushButton("Login")
        login_button.setStyleSheet("""
            QPushButton {
                background-color: #a63d7c;
                color: white;
                border: none;
                border-radius: 15px;
                padding: 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #8f3369;
            }
        """)
        login_button.clicked.connect(self.handle_login)
        card_layout.addWidget(login_button)

        card.setLayout(card_layout)

        # --- Centrer la carte dans la fenêtre ---
        outer_layout = QVBoxLayout()
        outer_layout.addStretch()
        h_layout = QHBoxLayout()
        h_layout.addStretch()
        h_layout.addWidget(card)
        h_layout.addStretch()
        outer_layout.addLayout(h_layout)
        outer_layout.addStretch()

        self.setLayout(outer_layout)
        

    def input_style(self):
        return """
            QLineEdit{

            background-color:#edf4fc;
            border:2px solid #bfd9f5;
            border-radius:12px;
            padding:12px;
            color:black;
            font-size:14px;

        }

        

        QLineEdit:focus{

            border:2px solid #3d8bfd;
            background-color:white;

        }
        """

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
            self.stack.setCurrentIndex(1)
        else:
            QMessageBox.warning(self, "Erreur", "Mot de passe incorrect")