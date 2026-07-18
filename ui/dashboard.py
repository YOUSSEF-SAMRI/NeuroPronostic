from PyQt6.QtWidgets import (
    QApplication,QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QFileDialog
)
from PyQt6.QtWidgets import QPushButton
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt
import sys


class DashboardScreen(QWidget):
    def __init__(self):
        super().__init__()
    
        
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet("background-color: #e8e8e8;")
        
        main_layout = QHBoxLayout()        
        sidebare = QWidget()
        content = QWidget()
        
        main_layout.addWidget(sidebare)
        main_layout.addWidget(content)
        
        sidebare.setFixedWidth(250)
        sidebar_layout = QVBoxLayout()
        sidebare.setLayout(sidebar_layout)
        
        logo = QLabel()
        pixmap = QPixmap("assets/logo.png")
        logo.setPixmap(pixmap.scaled(150, 150, Qt.AspectRatioMode.KeepAspectRatio,
                                      Qt.TransformationMode.SmoothTransformation))
        
        sidebar_layout.addWidget(
            logo)
        
        dashboard_button = QPushButton("Dashboard")
        sidebar_layout.addWidget(dashboard_button)
        
        historique_button = QPushButton("historique_button")
        sidebar_layout.addWidget(historique_button)
        
        patients_button = QPushButton( "Patients")
        sidebar_layout.addWidget(patients_button)
        
        settings_button = QPushButton("Paramètres")
        sidebar_layout.addWidget(settings_button)
        
        sidebar_layout.addStretch()
        
        logout_button = QPushButton("Déconnexion")
        sidebar_layout.addWidget(logout_button)
        
        
        
        self.setLayout(main_layout)
        
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = DashboardScreen()
    window.resize(800, 600) # Taille initiale pour bien voir le résultat
    window.show()
    sys.exit(app.exec())

 