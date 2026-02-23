import os
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QSlider, QCheckBox, QGroupBox, QSpinBox, QFileDialog, QMessageBox, QTextEdit

class GifCompressWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        self.selected_path = None
        self.compress_thread = None

    def init_ui(self):
        self.main_layout = QVBoxLayout(self)

        # 1. IO Selection Group
        self.group_io = QGroupBox("选择图片或文件夹")
        self.io_layout = QHBoxLayout(self.group_io)
        self.io_layout.setContentsMargins(10, 10, 10, 10)
        self.io_layout.setSpacing(10)

        self.lbl_path = QLabel("未选择 (支持单张图片或整个文件夹)")
        self.lbl_path.setWordWrap(True)

        self.btn_select_file = QPushButton("选择单图")
        self.btn_select_file.setObjectName("btn_select_image")
        self.btn_select_file.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.btn_select_file.clicked.connect(self.select_file)

        self.btn_select_folder = QPushButton("选择文件夹")
        self.btn_select_folder.setObjectName("btn_select_folder")
        self.btn_select_folder.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.btn_select_folder.clicked.connect(self.select_folder)

        self.io_layout.addWidget(self.lbl_path, stretch=1)
        self.io_layout.addWidget(self.btn_select_file)
        self.io_layout.addWidget(self.btn_select_folder)
        
        self.main_layout.addWidget(self.group_io)

        # 2. Settings Group
        self.group_settings = QGroupBox("压缩参数设置")
        self.settings_layout = QVBoxLayout(self.group_settings)
        self.settings_layout.setContentsMargins(10, 10, 10, 10)
        self.settings_layout.setSpacing(15)

        # 2.1 Compression level (Lossy)
        self.h_layout_lossy = QHBoxLayout()
        self.lbl_lossy = QLabel("压缩强度 (Lossy Level):")
        self.lbl_lossy.setFixedWidth(140)
        
        self.spin_lossy = QSpinBox()
        self.spin_lossy.setRange(0, 200)
        self.spin_lossy.setValue(30)
        self.spin_lossy.setFixedWidth(60)

        self.slider_lossy = QSlider(QtCore.Qt.Horizontal)
        self.slider_lossy.setRange(0, 200)
        self.slider_lossy.setValue(30)
        self.slider_lossy.setSingleStep(5)
        
        self.lbl_lossy_desc = QLabel("(30 极轻微压缩, 200 极大压缩)")
        self.lbl_lossy_desc.setStyleSheet("color: #888; font-size: 11px;")

        # Connect spinbox and slider bidirectionally
        self.spin_lossy.valueChanged.connect(self.slider_lossy.setValue)
        self.slider_lossy.valueChanged.connect(self.spin_lossy.setValue)

        self.h_layout_lossy.addWidget(self.lbl_lossy)
        self.h_layout_lossy.addWidget(self.spin_lossy)
        self.h_layout_lossy.addWidget(self.slider_lossy)
        self.h_layout_lossy.addWidget(self.lbl_lossy_desc)
        self.settings_layout.addLayout(self.h_layout_lossy)

        # 2.2 Proportional Shrink (按比例缩小)
        self.h_layout_scale = QHBoxLayout()
        self.lbl_scale = QLabel("按比例缩小尺寸 (%):")
        self.lbl_scale.setFixedWidth(140)
        
        self.spin_scale = QSpinBox()
        self.spin_scale.setRange(0, 90)
        self.spin_scale.setValue(0)
        self.spin_scale.setFixedWidth(60)

        self.slider_scale = QSlider(QtCore.Qt.Horizontal)
        self.slider_scale.setRange(0, 90)
        self.slider_scale.setValue(0)
        self.slider_scale.setSingleStep(5)
        
        self.lbl_scale_desc = QLabel("(0%为保持原尺寸。拉大数值会显著减小文件体积)")
        self.lbl_scale_desc.setStyleSheet("color: #888; font-size: 11px;")

        self.spin_scale.valueChanged.connect(self.slider_scale.setValue)
        self.slider_scale.valueChanged.connect(self.spin_scale.setValue)

        self.h_layout_scale.addWidget(self.lbl_scale)
        self.h_layout_scale.addWidget(self.spin_scale)
        self.h_layout_scale.addWidget(self.slider_scale)
        self.h_layout_scale.addWidget(self.lbl_scale_desc)
        self.settings_layout.addLayout(self.h_layout_scale)

        # 2.3 Fuzz % (Mapped to color reduction internally)
        self.h_layout_fuzz = QHBoxLayout()
        self.lbl_fuzz = QLabel("颜色相似度容差 (Fuzz %):")
        self.lbl_fuzz.setFixedWidth(140)
        
        self.spin_fuzz = QSpinBox()
        self.spin_fuzz.setRange(0, 100)
        self.spin_fuzz.setValue(3)
        self.spin_fuzz.setFixedWidth(60)

        self.slider_fuzz = QSlider(QtCore.Qt.Horizontal)
        self.slider_fuzz.setRange(0, 100)
        self.slider_fuzz.setValue(3)
        self.slider_fuzz.setSingleStep(1)
        
        self.lbl_fuzz_desc = QLabel("(容差越高，合并的相似颜色越多，体积越小但也可能失真)")
        self.lbl_fuzz_desc.setStyleSheet("color: #888; font-size: 11px;")

        self.spin_fuzz.valueChanged.connect(self.slider_fuzz.setValue)
        self.slider_fuzz.valueChanged.connect(self.spin_fuzz.setValue)

        self.h_layout_fuzz.addWidget(self.lbl_fuzz)
        self.h_layout_fuzz.addWidget(self.spin_fuzz)
        self.h_layout_fuzz.addWidget(self.slider_fuzz)
        self.h_layout_fuzz.addWidget(self.lbl_fuzz_desc)
        self.settings_layout.addLayout(self.h_layout_fuzz)

        # 2.2 Eliminate local color tables
        self.chk_color_tables = QCheckBox("去除局部色表 (消除多余颜色数据，减小体积)")
        self.chk_color_tables.setStyleSheet("margin-left: 140px; color: #BBB;")
        self.settings_layout.addWidget(self.chk_color_tables)

        self.main_layout.addWidget(self.group_settings)

        # 3. Action Button
        self.btn_start = QPushButton("一键开始压缩 GIF")
        self.btn_start.setObjectName("btn_start")
        self.btn_start.setFixedHeight(50)
        self.btn_start.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.btn_start.clicked.connect(self.start_compression)
        self.main_layout.addWidget(self.btn_start)

        # 4. Log text
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setPlaceholderText("完成压缩的 GIF 将保存至原目录下的 gif_output_yiyu_box 文件夹中...")
        self.main_layout.addWidget(self.log_text)

    def select_file(self):
        from demo import ConfigManager
        last_path = ConfigManager.get_last_path()
        path, _ = QFileDialog.getOpenFileName(self, "选择 GIF 文件", last_path, "GIF Files (*.gif)")
        if path:
            ConfigManager.save_last_path(path)
            self.selected_path = path
            self.lbl_path.setText(f"已选择单图: {path}")
            self.log(f"已加载单图: {path}")

    def select_folder(self):
        from demo import ConfigManager
        last_path = ConfigManager.get_last_path()
        path = QFileDialog.getExistingDirectory(self, "选择包含 GIF 的文件夹", last_path)
        if path:
            ConfigManager.save_last_path(path)
            self.selected_path = path
            self.lbl_path.setText(f"已选择文件夹: {path}")
            self.log(f"已加载文件夹: {path}")

    def start_compression(self):
        if not self.selected_path:
            QMessageBox.warning(self, "警告", "请先选择需要压缩的 GIF图片或文件夹！")
            return

        if self.compress_thread and self.compress_thread.isRunning():
            return

        self.log(f"开始任务... 缩小尺寸: {self.spin_scale.value()}%, 压缩强度: {self.spin_lossy.value()}, 去除局部色表: {self.chk_color_tables.isChecked()}, Fuzz容差: {self.spin_fuzz.value()}")
        self.btn_start.setEnabled(False)
        self.btn_start.setText("压缩中，请稍候...")
        self.btn_select_file.setEnabled(False)
        self.btn_select_folder.setEnabled(False)

        main_win = self.window()
        from gif_processor import GifCompressThread
        self.compress_thread = GifCompressThread(
            target_path=self.selected_path,
            compression_level=self.spin_lossy.value(),
            fuzz_pct=self.spin_fuzz.value(),
            scale_pct=self.spin_scale.value(),
            eliminate_colors=self.chk_color_tables.isChecked()
        )

        if hasattr(main_win, 'update_batch_progress'):
            self.compress_thread.progress_signal.connect(main_win.update_batch_progress)
        
        # Also connect to local log
        self.compress_thread.progress_signal.connect(self.update_progress)
        self.compress_thread.finished_signal.connect(self.on_process_finished)
        self.compress_thread.start()

    def update_progress(self, item_val, total_val, msg):
        self.log(msg)

    def on_process_finished(self, success, msg):
        self.btn_start.setEnabled(True)
        self.btn_start.setText("一键开始压缩 GIF")
        self.btn_select_file.setEnabled(True)
        self.btn_select_folder.setEnabled(True)
        
        if success:
            self.log("压缩任务圆满完成！")
            self.log(msg)
        else:
            self.log(f"出现错误: {msg}")
            QMessageBox.critical(self, "错误", f"压缩失败！{msg}")

    def log(self, text):
        self.log_text.append(text)
        sb = self.log_text.verticalScrollBar()
        sb.setValue(sb.maximum())

