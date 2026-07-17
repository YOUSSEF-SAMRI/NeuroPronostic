from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QFileDialog
)

class DashboardScreen(QWidget):
    def __init__(self):
        super().__init__()

        
        main_layout = QVBoxLayout()

        title = QLabel("Dashboard - Nouveau patient")
        main_layout.addWidget(title)

        # Bloc upload NIfTI 
        nifti_layout = QHBoxLayout()
        self.nifti_button = QPushButton("Choisir fichier NIfTI")
        self.nifti_label = QLabel("Aucun fichier sélectionné")
        self.nifti_button.clicked.connect(self.choisir_nifti)

        nifti_layout.addWidget(self.nifti_button)
        nifti_layout.addWidget(self.nifti_label)
        main_layout.addLayout(nifti_layout)

        # Bloc upload CSV 
        csv_layout = QHBoxLayout()
        self.csv_button = QPushButton("Choisir fichier CSV")
        self.csv_label = QLabel("Aucun fichier sélectionné")
        self.csv_button.clicked.connect(self.choisir_csv)

        csv_layout.addWidget(self.csv_button)
        csv_layout.addWidget(self.csv_label)
        main_layout.addLayout(csv_layout)

        self.setLayout(main_layout)
        
        
        

    def choisir_nifti(self):
        chemin, _ = QFileDialog.getOpenFileName( # katrje3 joj 7wyaj (path,file_type) ex ("C:/Users/youssef/Desktop/a.png","PNG Files")
            self, "Choisir un fichier NIfTI", "", "NIfTI Files (*.nii *.nii.gz)"
        )
        if chemin:
            self.nifti_label.setText(chemin)

    def choisir_csv(self):
        chemin, _ = QFileDialog.getOpenFileName(
            self, "Choisir un fichier CSV", "", "CSV Files (*.csv)"
        )
        if chemin:
            self.csv_label.setText(chemin)