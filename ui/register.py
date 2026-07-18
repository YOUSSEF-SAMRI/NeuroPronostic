from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox
)
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QCursor
from models.database import get_connections
from utils.security import hash_password
import psycopg2
class RegisterScreen(QWidget):
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
        logo.setPixmap(pixmap.scaled(150, 150, Qt.AspectRatioMode.KeepAspectRatio,
                                      Qt.TransformationMode.SmoothTransformation))
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo.setStyleSheet("border: none; background: transparent;")
        card_layout.addWidget(logo)

        # --- Titre ---
        title = QLabel("Brain tumor detection")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("border: none; background: transparent; font-size: 16px; font-weight: bold; color: #2e7d32;")
        card_layout.addWidget(title)

        # --- Champ Name ---
        name_label = QLabel("Name")
        name_label.setStyleSheet("border: none; background: transparent; color: #444;")
        card_layout.addWidget(name_label)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Enter your name..")
        self.name_input.setStyleSheet(self.input_style())
        card_layout.addWidget(self.name_input)
        
        # --- Champ Email ---
        email_label = QLabel("Email")
        email_label.setStyleSheet("border: none; background: transparent; color: #444;")
        card_layout.addWidget(email_label)

        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Enter your name..")
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

        # --- Lien "Deja un compte ?" ---
        go_to_login = QPushButton("Deja un compte ?")
        go_to_login.setMinimumWidth(160)
        go_to_login.setCursor(
            QCursor(Qt.CursorShape.PointingHandCursor))
        go_to_login.setStyleSheet("""
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
        go_to_login.clicked.connect(lambda: self.stack.setCurrentIndex(0))
        card_layout.addWidget(go_to_login, alignment=Qt.AlignmentFlag.AlignRight)

        # --- Bouton Sign Up ---
        login_button = QPushButton("Sign Up")
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
        login_button.clicked.connect(self.handle_signUp)
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

    def handle_signUp(self):
        name = self.name_input.text()
        email = self.email_input.text()
        password = self.password_input.text()

        if not name or not email or not password :
            QMessageBox.warning(self,"Erreur","Veuillez remplir tous les champs")
            return 
        hashed_password = hash_password(password)
        try:
            conn = get_connections()
            cur = conn.cursor()
            cur.execute("""
                        INSERT INTO users (nom,email,password_hash)
                        VALUES (%s,%s,%s)""",(name,email,hashed_password)
                        )
            conn.commit()
            QMessageBox.information(self, "Succès", "Compte créé ! Tu peux te connecter.")
            self.stack.setCurrentIndex(0)
            
        except psycopg2.errors.UniqueViolation:
            conn.rollback()
            QMessageBox.warning(self, "Erreur", "Cet email est déjà utilisé")
        finally:
            cur.close()
            conn.close()
    
    
        
