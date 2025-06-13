#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import io
import traceback
from pathlib import Path
from typing import Optional

import vtracer
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QSlider,
    QComboBox,
    QPushButton,
    QFileDialog,
    QTextEdit,
    QSplitter,
    QFrame,
    QGroupBox,
    QGridLayout,
    QMessageBox,
    QProgressBar,
    QScrollArea,
    QSpacerItem,
    QSizePolicy,
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QMimeData, QTimer
from PyQt5.QtGui import QPixmap, QDragEnterEvent, QDropEvent, QFont, QIcon
from PyQt5.QtSvg import QSvgWidget


class ConversionWorker(QThread):
    """画像変換を別スレッドで実行するワーカークラス"""

    finished = pyqtSignal(str)  # SVG文字列
    error = pyqtSignal(str)  # エラーメッセージ
    progress = pyqtSignal(int)  # 進捗（0-100）

    def __init__(self, image_path: str, params: dict):
        super().__init__()
        self.image_path = image_path
        self.params = params

    def run(self):
        try:
            self.progress.emit(10)

            # 画像ファイルをバイト形式で読み込み
            with open(self.image_path, "rb") as f:
                image_bytes = f.read()

            self.progress.emit(30)

            # ファイル拡張子から画像形式を判定
            file_extension = Path(self.image_path).suffix.lower()
            img_format_map = {
                ".jpg": "jpg",
                ".jpeg": "jpg",
                ".png": "png",
                ".bmp": "bmp",
                ".gif": "gif",
                ".tiff": "tiff",
            }
            img_format = img_format_map.get(file_extension, "jpg")

            self.progress.emit(50)

            # vtracerでバイト形式の画像をSVGに変換
            svg_content = vtracer.convert_raw_image_to_svg(
                image_bytes, img_format=img_format, **self.params
            )

            self.progress.emit(100)
            self.finished.emit(svg_content)

        except Exception as e:
            self.error.emit(f"変換エラー: {str(e)}")


class ImageDropWidget(QLabel):
    """ドラッグ&ドロップ対応画像表示ウィジェット"""

    imageDropped = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.setAcceptDrops(True)
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet(
            """
            QLabel {
                border: 2px dashed #ccc;
                border-radius: 10px;
                background-color: #f9f9f9;
                color: #666;
                font-size: 14px;
                padding: 20px;
            }
            QLabel:hover {
                border-color: #999;
                background-color: #f0f0f0;
            }
        """
        )
        self.setText("Drag & drop an image here\nor click to select a file")
        self.setMinimumSize(300, 200)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        urls = event.mimeData().urls()
        if urls:
            file_path = urls[0].toLocalFile()
            if self.is_image_file(file_path):
                self.imageDropped.emit(file_path)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.select_file()

    def select_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Image File",
            "",
            "Image Files (*.png *.jpg *.jpeg *.bmp *.gif *.tiff);;All Files (*)",
        )
        if file_path and self.is_image_file(file_path):
            self.imageDropped.emit(file_path)

    def is_image_file(self, file_path: str) -> bool:
        extensions = {".png", ".jpg", ".jpeg", ".bmp", ".gif", ".tiff"}
        return Path(file_path).suffix.lower() in extensions

    def set_image(self, file_path: str):
        pixmap = QPixmap(file_path)
        if not pixmap.isNull():
            # 画像をウィジェットサイズに合わせてスケール
            scaled_pixmap = pixmap.scaled(
                self.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            self.setPixmap(scaled_pixmap)


class ParameterControlWidget(QWidget):
    """パラメータ制御ウィジェット"""

    parametersChanged = pyqtSignal()

    def __init__(self):
        super().__init__()
        # 垂直方向の間延びを防ぐためのサイズポリシー設定
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)  # グループ間のスペースを設定

        # Clustering グループ
        clustering_group = QGroupBox("Clustering")
        clustering_layout = QGridLayout(clustering_group)
        clustering_layout.setSpacing(8)  # 項目間のスペースを設定
        clustering_layout.setVerticalSpacing(12)  # 垂直方向のスペースをより大きく

        # Color Mode
        clustering_layout.addWidget(QLabel("Color Mode:"), 0, 0)
        self.color_mode = QComboBox()
        self.color_mode.addItems(["Color", "B/W"])
        self.color_mode.setCurrentText("Color")  # default: Color
        self.color_mode.currentTextChanged.connect(self.parametersChanged.emit)
        clustering_layout.addWidget(self.color_mode, 0, 1, 1, 2)

        # Hierarchical
        clustering_layout.addWidget(QLabel("Hierarchical:"), 1, 0)
        self.hierarchical_mode = QComboBox()
        self.hierarchical_mode.addItems(["Stacked", "CutOut"])
        self.hierarchical_mode.setCurrentText("Stacked")  # default: Stacked
        self.hierarchical_mode.currentTextChanged.connect(self.parametersChanged.emit)
        clustering_layout.addWidget(self.hierarchical_mode, 1, 1, 1, 2)

        # Filter Speckle (0-128, default: 4)
        clustering_layout.addWidget(QLabel("Filter Speckle:"), 2, 0)
        self.filter_speckle = QSlider(Qt.Horizontal)
        self.filter_speckle.setRange(0, 128)
        self.filter_speckle.setValue(4)
        self.filter_speckle.valueChanged.connect(self.parametersChanged.emit)
        self.filter_speckle_label = QLabel("4")
        self.filter_speckle.valueChanged.connect(
            lambda v: self.filter_speckle_label.setText(str(v))
        )
        clustering_layout.addWidget(self.filter_speckle, 2, 1)
        clustering_layout.addWidget(self.filter_speckle_label, 2, 2)

        # Color Precision (1-8, default: 6)
        clustering_layout.addWidget(QLabel("Color Precision:"), 3, 0)
        self.color_precision = QSlider(Qt.Horizontal)
        self.color_precision.setRange(1, 8)
        self.color_precision.setValue(6)
        self.color_precision.valueChanged.connect(self.parametersChanged.emit)
        self.color_precision_label = QLabel("6")
        self.color_precision.valueChanged.connect(
            lambda v: self.color_precision_label.setText(str(v))
        )
        clustering_layout.addWidget(self.color_precision, 3, 1)
        clustering_layout.addWidget(self.color_precision_label, 3, 2)

        # Gradient Step (0-128, default: 16)
        clustering_layout.addWidget(QLabel("Gradient Step:"), 4, 0)
        self.layer_difference = QSlider(Qt.Horizontal)
        self.layer_difference.setRange(0, 128)
        self.layer_difference.setValue(16)
        self.layer_difference.valueChanged.connect(self.parametersChanged.emit)
        self.layer_difference_label = QLabel("16")
        self.layer_difference.valueChanged.connect(
            lambda v: self.layer_difference_label.setText(str(v))
        )
        clustering_layout.addWidget(self.layer_difference, 4, 1)
        clustering_layout.addWidget(self.layer_difference_label, 4, 2)

        layout.addWidget(clustering_group)

        # Curve Fitting グループ
        curve_group = QGroupBox("Curve Fitting")
        curve_layout = QGridLayout(curve_group)
        curve_layout.setSpacing(8)  # 項目間のスペースを設定
        curve_layout.setVerticalSpacing(12)  # 垂直方向のスペースをより大きく

        # Mode
        curve_layout.addWidget(QLabel("Mode:"), 0, 0)
        self.curve_mode = QComboBox()
        self.curve_mode.addItems(["Spline", "Polygon", "Pixel"])
        self.curve_mode.setCurrentText("Spline")  # default: Spline
        self.curve_mode.currentTextChanged.connect(self.parametersChanged.emit)
        curve_layout.addWidget(self.curve_mode, 0, 1, 1, 2)

        # Corner Threshold (0-180, default: 60)
        curve_layout.addWidget(QLabel("Corner Threshold:"), 1, 0)
        self.corner_threshold = QSlider(Qt.Horizontal)
        self.corner_threshold.setRange(0, 180)
        self.corner_threshold.setValue(60)
        self.corner_threshold.valueChanged.connect(self.parametersChanged.emit)
        self.corner_threshold_label = QLabel("60")
        self.corner_threshold.valueChanged.connect(
            lambda v: self.corner_threshold_label.setText(str(v))
        )
        curve_layout.addWidget(self.corner_threshold, 1, 1)
        curve_layout.addWidget(self.corner_threshold_label, 1, 2)

        # Segment Length (3.5-10 step 0.5, default: 4)
        curve_layout.addWidget(QLabel("Segment Length:"), 2, 0)
        self.length_threshold = QSlider(Qt.Horizontal)
        self.length_threshold.setRange(
            35, 100
        )  # 3.5-10.0 を 35-100 にマップ (step 0.5)
        self.length_threshold.setValue(40)  # 4.0 = 40
        self.length_threshold.valueChanged.connect(self.parametersChanged.emit)
        self.length_threshold_label = QLabel("4.0")
        self.length_threshold.valueChanged.connect(
            lambda v: self.length_threshold_label.setText(f"{v/10:.1f}")
        )
        curve_layout.addWidget(self.length_threshold, 2, 1)
        curve_layout.addWidget(self.length_threshold_label, 2, 2)

        # Splice Threshold (0-180, default: 45)
        curve_layout.addWidget(QLabel("Splice Threshold:"), 3, 0)
        self.splice_threshold = QSlider(Qt.Horizontal)
        self.splice_threshold.setRange(0, 180)
        self.splice_threshold.setValue(45)
        self.splice_threshold.valueChanged.connect(self.parametersChanged.emit)
        self.splice_threshold_label = QLabel("45")
        self.splice_threshold.valueChanged.connect(
            lambda v: self.splice_threshold_label.setText(str(v))
        )
        curve_layout.addWidget(self.splice_threshold, 3, 1)
        curve_layout.addWidget(self.splice_threshold_label, 3, 2)

        layout.addWidget(curve_group)

        # 下部にスペーサーを追加してレイアウトの間延びを防ぐ
        spacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        layout.addItem(spacer)

    def get_parameters(self) -> dict:
        """現在のパラメータを辞書として取得"""
        return {
            "colormode": (
                "color" if self.color_mode.currentText() == "Color" else "binary"
            ),
            "hierarchical": (
                "stacked"
                if self.hierarchical_mode.currentText() == "Stacked"
                else "cutout"
            ),
            "mode": {"Spline": "spline", "Polygon": "polygon", "Pixel": "none"}[
                self.curve_mode.currentText()
            ],
            "filter_speckle": self.filter_speckle.value(),
            "color_precision": self.color_precision.value(),
            "layer_difference": self.layer_difference.value(),
            "corner_threshold": self.corner_threshold.value(),
            "length_threshold": self.length_threshold.value() / 10.0,
            "max_iterations": 10,
            "splice_threshold": self.splice_threshold.value(),
        }


class VTracerGUI(QMainWindow):
    """メインアプリケーションウィンドウ"""

    def __init__(self):
        super().__init__()
        self.current_image_path: Optional[str] = None
        self.current_svg_content: Optional[str] = None
        self.conversion_worker: Optional[ConversionWorker] = None

        self.init_ui()
        self.setWindowTitle("VTracer GUI - Image to SVG Converter")
        self.setWindowIcon(QIcon("app.ico"))
        self.resize(1200, 800)

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # メインレイアウト
        main_layout = QHBoxLayout(central_widget)

        # 左側：画像表示エリア（上下50%ずつ分割）
        left_splitter = QSplitter(Qt.Vertical)

        # 元画像エリア（上部50%）
        self.image_widget = ImageDropWidget()
        self.image_widget.imageDropped.connect(self.load_image)
        left_splitter.addWidget(self.image_widget)

        # SVGプレビューエリア（下部50%）
        self.svg_widget = QSvgWidget()
        self.svg_widget.setStyleSheet(
            """
            QSvgWidget {
                border: 1px solid #ccc;
                background-color: white;
            }
        """
        )
        left_splitter.addWidget(self.svg_widget)

        # 50%ずつに分割
        left_splitter.setSizes([400, 400])

        # 右側：パラメータとボタン
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)

        # パラメータコントロール
        scroll_area = QScrollArea()
        self.param_controls = ParameterControlWidget()
        self.param_controls.parametersChanged.connect(self.on_parameters_changed)
        scroll_area.setWidget(self.param_controls)
        scroll_area.setWidgetResizable(True)
        scroll_area.setMaximumWidth(350)
        right_layout.addWidget(scroll_area)

        # ボタンエリア
        button_layout = QVBoxLayout()

        # ベクター化ボタン
        self.convert_button = QPushButton("Vectorize")
        self.convert_button.clicked.connect(self.convert_image)
        self.convert_button.setEnabled(False)
        self.convert_button.setStyleSheet(
            """
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 12px;
                font-size: 16px;
                font-weight: bold;
                border-radius: 6px;
                margin: 5px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """
        )
        button_layout.addWidget(self.convert_button)

        # 進捗バー
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        button_layout.addWidget(self.progress_bar)

        # SVG保存ボタン
        self.save_button = QPushButton("Save SVG")
        self.save_button.clicked.connect(self.save_svg)
        self.save_button.setEnabled(False)
        self.save_button.setStyleSheet(
            """
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 12px;
                font-size: 16px;
                font-weight: bold;
                border-radius: 6px;
                margin: 5px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """
        )
        button_layout.addWidget(self.save_button)

        right_layout.addLayout(button_layout)

        # スプリッター（左側：画像表示、右側：コントロール）
        main_splitter = QSplitter()
        main_splitter.addWidget(left_splitter)
        main_splitter.addWidget(right_panel)
        main_splitter.setSizes([800, 400])

        main_layout.addWidget(main_splitter)

    def load_image(self, file_path: str):
        """画像を読み込む"""
        self.current_image_path = file_path
        self.image_widget.set_image(file_path)
        self.convert_button.setEnabled(True)

        # ファイル名を表示
        file_name = Path(file_path).name
        self.image_widget.setToolTip(f"Selected image: {file_name}")

    def on_parameters_changed(self):
        """パラメータが変更された時の処理"""
        # 自動変換は負荷が高いため、手動変換のみとする
        pass

    def convert_image(self):
        """画像をSVGに変換"""
        if not self.current_image_path:
            return

        # 変換中のUI状態
        self.convert_button.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)

        # パラメータを取得
        params = self.param_controls.get_parameters()

        # ワーカースレッドで変換実行
        self.conversion_worker = ConversionWorker(self.current_image_path, params)
        self.conversion_worker.finished.connect(self.on_conversion_finished)
        self.conversion_worker.error.connect(self.on_conversion_error)
        self.conversion_worker.progress.connect(self.progress_bar.setValue)
        self.conversion_worker.start()

    def on_conversion_finished(self, svg_content: str):
        """変換完了時の処理"""
        self.current_svg_content = svg_content

        # SVGをプレビューに表示
        try:
            svg_bytes = svg_content.encode("utf-8")
            self.svg_widget.load(svg_bytes)
        except Exception as e:
            QMessageBox.warning(self, "Warning", f"Failed to display SVG: {str(e)}")

        # UI状態を復元
        self.convert_button.setEnabled(True)
        self.save_button.setEnabled(True)
        self.progress_bar.setVisible(False)

        QMessageBox.information(
            self, "Complete", "Image conversion completed successfully."
        )

    def on_conversion_error(self, error_message: str):
        """変換エラー時の処理"""
        QMessageBox.critical(self, "Error", error_message)

        # UI状態を復元
        self.convert_button.setEnabled(True)
        self.progress_bar.setVisible(False)

    def save_svg(self):
        """SVGファイルを保存"""
        if not self.current_svg_content:
            return

        # 保存先ファイル名を取得
        default_name = ""
        if self.current_image_path:
            default_name = Path(self.current_image_path).stem + ".svg"

        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save SVG File", default_name, "SVG Files (*.svg);;All Files (*)"
        )

        if file_path:
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(self.current_svg_content)
                QMessageBox.information(
                    self, "Success", f"SVG file saved successfully:\n{file_path}"
                )
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save file:\n{str(e)}")


def main():
    """メイン関数"""
    app = QApplication(sys.argv)
    app.setApplicationName("VTracer GUI")
    app.setApplicationVersion("1.0")

    # アプリケーションスタイル
    app.setStyleSheet(
        """
        QMainWindow {
            background-color: #f5f5f5;
        }
        QGroupBox {
            font-weight: bold;
            border: 1px solid #cccccc;
            border-radius: 5px;
            margin-top: 1ex;
            padding-top: 10px;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px 0 5px;
        }
    """
    )

    window = VTracerGUI()
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
