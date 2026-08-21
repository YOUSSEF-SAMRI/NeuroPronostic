import nibabel as nib
import numpy as np
import cv2
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtCore import Qt
import cv2
from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QSlider,
    QWidget,
    QFrame
)

def get_slice(volume, axis, index):

    if axis == "axial":
        slice_2d = volume[:, :, index]

    elif axis == "sagittal":
        slice_2d = volume[index, :, :]

    elif axis == "coronal":
        slice_2d = volume[:, index, :]

    # Rotation pour avoir une orientation d'affichage médicale correcte
    slice_2d = np.rot90(slice_2d)

    return slice_2d

def load_nii_volume(path):
    img = nib.load(path)

    # Mettre le volume dans une orientation anatomique standard RAS
    img = nib.as_closest_canonical(img)

    data = img.get_fdata()

    data = np.nan_to_num(data)

    # Normalisation 0-255
    data = (
        (data - data.min())
        / (data.max() - data.min() + 1e-8)
        * 255
    )

    return data.astype(np.uint8)


def build_segmentation_overlay(
    image_slice,
    mask_slice,
    fill_color=(239, 68, 68),
    contour_color=(250, 204, 21),
    alpha=0.35,
    contour_thickness=2
):
    base_rgb = np.stack([image_slice] * 3, axis=-1).astype(np.uint8)
    mask_bool = mask_slice > 0

    colored_layer = np.zeros_like(base_rgb)
    colored_layer[mask_bool] = fill_color
    blended = cv2.addWeighted(base_rgb, 1 - alpha, colored_layer, alpha, 0)

    result = base_rgb.copy()
    result[mask_bool] = blended[mask_bool]

    mask_uint8 = (mask_bool.astype(np.uint8)) * 255
    contours, _ = cv2.findContours(mask_uint8, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cv2.drawContours(result, contours, -1, contour_color, contour_thickness)

    return result


def numpy_to_qpixmap(arr_rgb):
    h, w, ch = arr_rgb.shape
    arr_rgb = np.ascontiguousarray(arr_rgb)
    qimg = QImage(arr_rgb.data, w, h, ch * w, QImage.Format.Format_RGB888)
    return QPixmap.fromImage(qimg.copy())

class SegmentationViewerDialog(QDialog):

    def __init__(self, image_path, mask_path, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Visualisation de la segmentation")
        self.resize(1300, 620)
        self.setMinimumSize(1000, 580)

        self.image_volume = load_nii_volume(image_path)
        self.mask_volume = load_nii_volume(mask_path)

        self.setStyleSheet("""
            QDialog {
                background-color: #f4f6f9;
            }

            QLabel {
                color: #1f2937;
            }

            QLabel#windowTitle {
                color: #111827;
                font-size: 22px;
                font-weight: 700;
            }

            QLabel#windowSubtitle {
                color: #6b7280;
                font-size: 13px;
            }

            QFrame#viewCard {
                background-color: white;
                border: 1px solid #e5e7eb;
                border-radius: 14px;
            }

            QLabel#viewTitle {
                color: #111827;
                font-size: 15px;
                font-weight: 700;
                padding: 4px;
                background-color: transparent;
            }

            QLabel#imageLabel {
                background-color: #050505;
            }

            QSlider::groove:horizontal {
                height: 5px;
                background: #e5e7eb;
                border-radius: 3px;
            }

            QSlider::sub-page:horizontal {
                background: #2563eb;
                border-radius: 3px;
            }

            QSlider::add-page:horizontal {
                background: #e5e7eb;
                border-radius: 3px;
            }

            QSlider::handle:horizontal {
                background: #2563eb;
                border: 2px solid white;
                width: 14px;
                height: 14px;
                margin: -5px 0;
                border-radius: 7px;
            }
            
            QLabel#indexLabel {
                color: #6b7280;
                font-size: 11px;
                background-color: transparent;
            }
        """)

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(24, 20, 24, 20)
        main_layout.setSpacing(18)

        self.setLayout(main_layout)

        header_layout = QVBoxLayout()
        header_layout.setSpacing(3)

        title = QLabel("Visualisation de la segmentation")
        title.setObjectName("windowTitle")

        subtitle = QLabel(
            "Visualisation des régions segmentées sur les différentes orientations"
        )
        subtitle.setObjectName("windowSubtitle")

        header_layout.addWidget(title)
        header_layout.addWidget(subtitle)

        main_layout.addLayout(header_layout)

        views_layout = QHBoxLayout()
        views_layout.setSpacing(18)

        self.views = {}

        axes_config = [
            ("axial", 2),
            ("sagittal", 0),
            ("coronal", 1),
        ]

        for axis_name, axis_dim in axes_config:

            card = QFrame()
            card.setObjectName("viewCard")

            card_layout = QVBoxLayout()
            card_layout.setContentsMargins(14, 14, 14, 14)
            card_layout.setSpacing(10)

            card.setLayout(card_layout)

            title = QLabel(axis_name.capitalize())
            title.setObjectName("viewTitle")
            title.setAlignment(Qt.AlignmentFlag.AlignCenter)

            card_layout.addWidget(title)

            label = QLabel()
            label.setObjectName("imageLabel")
            label.setFixedSize(320, 300)
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)

            card_layout.addWidget(label, alignment=Qt.AlignmentFlag.AlignCenter)

            slider = QSlider(Qt.Orientation.Horizontal)

            n = self.image_volume.shape[axis_dim]

            slider.setMinimum(0)
            slider.setMaximum(n - 1)
            slider.setValue(n // 2)

            slider.setFixedHeight(25)

            card_layout.addWidget(slider)

            index_label = QLabel()
            index_label.setObjectName("indexLabel")
            index_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

            card_layout.addWidget(index_label)

            self.views[axis_name] = {
                "label": label,
                "slider": slider,
                "dim": axis_dim,
                "index_label": index_label
            }

            # IMPORTANT
            slider.valueChanged.connect(
                lambda val, a=axis_name: self.update_view(a)
            )

            views_layout.addWidget(card)

        main_layout.addLayout(views_layout)

        legend = QHBoxLayout()
        legend.setSpacing(20)

        segmentation_indicator = QLabel("●")
        segmentation_indicator.setStyleSheet("""
            QLabel {
                color: #facc15;
                font-size: 18px;
            }
        """)

        segmentation_text = QLabel("Contour : segmentation")
        segmentation_text.setStyleSheet("""
            QLabel {
                color: #6b7280;
                font-size: 12px;
            }
        """)

        legend.addWidget(segmentation_indicator)
        legend.addWidget(segmentation_text)
        legend.addStretch()

        main_layout.addLayout(legend)

        for axis_name in self.views:
            self.update_view(axis_name)

    def update_view(self, axis_name):

        view = self.views[axis_name]

        index = view["slider"].value()

        # Image slice
        img_slice = get_slice(
            self.image_volume,
            axis_name,
            index
        )

        # Mask slice
        mask_slice = get_slice(
            self.mask_volume,
            axis_name,
            index
        )

        # Overlay
        overlay = build_segmentation_overlay(
            img_slice,
            mask_slice
        )

        # Convert to QPixmap
        pixmap = numpy_to_qpixmap(overlay)

        # Display
        view["label"].setPixmap(
            pixmap.scaled(
                view["label"].size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
        )

        # Display slice number
        total = self.image_volume.shape[view["dim"]]

        view["index_label"].setText(
            f"Slice {index + 1} / {total}"
        )