import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QStackedWidget
from ui.login import LoginScreen
from ui.register import RegisterScreen
from ui.dashboard import DashboardScreen

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("NeuroPronostic")
        self.setGeometry(100, 100, 1000, 650)

        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        login = LoginScreen(self.stack)         # index 0
        dashboard = DashboardScreen()            # index 1
        register = RegisterScreen(self.stack)    # index 2

        self.stack.addWidget(login)
        self.stack.addWidget(dashboard)
        self.stack.addWidget(register)

        self.stack.setCurrentIndex(0)   # démarre sur Login

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())