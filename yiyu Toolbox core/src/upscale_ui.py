from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
    QFileDialog, QTextEdit, QProgressBar, QMessageBox, QGroupBox,
    QRadioButton, QButtonGroup
)
from PyQt5.QtCore import Qt, pyqtSlot
from upscale_processor import UpscaleThread
import os

class UpscaleWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        self.worker = None
        self.input_path = None
        self.is_folder = False

    def init_ui(self):
        layout = QVBoxLayout(self)

        # 1. Selection
        file_box = QGroupBox("选择图片或文件夹")
        file_layout = QHBoxLayout(file_box)
        file_layout.setContentsMargins(10, 10, 10, 10)
        file_layout.setSpacing(10)
        
        self.lbl_path = QLabel("未选择 (支持单张图片或整个文件夹)")
        self.lbl_path.setWordWrap(True)
        
        self.btn_select_file = QPushButton("选择单图")
        self.btn_select_file.setObjectName("btn_select_image")
        self.btn_select_file.setCursor(Qt.PointingHandCursor)
        self.btn_select_file.clicked.connect(self.select_file)
        
        self.btn_select_folder = QPushButton("选择文件夹")
        self.btn_select_folder.setObjectName("btn_select_folder")
        self.btn_select_folder.setCursor(Qt.PointingHandCursor)
        self.btn_select_folder.clicked.connect(self.select_folder)
        
        file_layout.addWidget(self.lbl_path, stretch=1)
        file_layout.addWidget(self.btn_select_file)
        file_layout.addWidget(self.btn_select_folder)
        layout.addWidget(file_box)

        # 2. Model Selection
        model_box = QGroupBox("AI 模型选择")
        model_layout = QHBoxLayout(model_box)
        model_layout.setContentsMargins(10, 10, 10, 10)
        model_layout.setSpacing(15)
        
        self.model_group = QButtonGroup(self)
        self.rb_gen = QRadioButton("全能通用 (写实人像/高清CG, 23层神经网络)")
        self.rb_anime = QRadioButton("动漫插画 (线条平滑/去影, 6层神经网络)")
        
        self.rb_gen.setChecked(True)
        
        self.model_group.addButton(self.rb_gen, 1) # 1 for General
        self.model_group.addButton(self.rb_anime, 2) # 2 for Anime
        
        model_layout.addWidget(self.rb_gen)
        model_layout.addWidget(self.rb_anime)
        layout.addWidget(model_box)

        # 3. Scale Selection
        scale_box = QGroupBox("放大倍数")
        scale_layout = QHBoxLayout(scale_box)
        scale_layout.setContentsMargins(10, 10, 10, 10)
        scale_layout.setSpacing(15)
        
        self.scale_group = QButtonGroup(self)
        self.rb_2x = QRadioButton("2x (快速)")
        self.rb_4x = QRadioButton("4x (推荐)")
        self.rb_6x = QRadioButton("6x (超高清/慢)")
        
        self.rb_4x.setChecked(True)
        
        self.scale_group.addButton(self.rb_2x, 2)
        self.scale_group.addButton(self.rb_4x, 4)
        self.scale_group.addButton(self.rb_6x, 6)
        
        scale_layout.addWidget(self.rb_2x)
        scale_layout.addWidget(self.rb_4x)
        scale_layout.addWidget(self.rb_6x)
        layout.addWidget(scale_box)

        # 3. Action
        self.btn_start = QPushButton("一键 AI 自动放大")
        self.btn_start.setObjectName("btn_start")
        self.btn_start.setFixedHeight(50)
        self.btn_start.setCursor(Qt.PointingHandCursor)
        self.btn_start.clicked.connect(self.start_processing)
        layout.addWidget(self.btn_start)

        # 4. Progress (Removed, using main window)
        pass

        # 5. Log
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setPlaceholderText("放大后的图片将保存至原目录下的 upscale_output_yiyu_box 文件夹中...")
        layout.addWidget(self.log_text)

    def select_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "选择图片", ".", "图片文件 (*.jpg *.png *.jpeg *.bmp)")
        if path:
            self.input_path = path
            self.is_folder = False
            self.lbl_path.setText(f"已选择单图: {path}")
            self.log(f"已加载单图: {path}")

    def select_folder(self):
        path = QFileDialog.getExistingDirectory(self, "选择包含图片的文件夹")
        if path:
            self.input_path = path
            self.is_folder = True
            self.lbl_path.setText(f"已选择文件夹: {path}")
            self.log(f"已加载文件夹: {path}")

    def start_processing(self):
        if not self.input_path or not os.path.exists(self.input_path):
            QMessageBox.warning(self, "提示", "请先选择图片或文件夹！")
            return

        if self.worker and self.worker.isRunning():
            return

        scale = self.scale_group.checkedId()
        model_type = "general" if self.model_group.checkedId() == 1 else "anime"
        
        self.log(f"开始任务... 放大倍数: {scale}x, 引擎: {model_type}")
        self.btn_start.setEnabled(False)
        self.btn_select_file.setEnabled(False)
        self.btn_select_folder.setEnabled(False)
        self.pbar.setValue(0)

        self.worker = UpscaleThread(self.input_path, self.is_folder, scale=scale, model_type=model_type)
        self.worker.progress_signal.connect(self.update_progress)
        self.worker.finished_signal.connect(self.on_finished)
        self.worker.start()

    def update_progress(self, item_val, total_val, msg):
        parent = self.window()
        if hasattr(parent, 'item_pbar'):
            parent.item_pbar.setValue(item_val)
        if hasattr(parent, 'total_pbar') and total_val != -1:
            parent.total_pbar.setValue(total_val)
        if hasattr(parent, 'lineEdit'):
            parent.lineEdit.setText(msg)
        self.log(msg)

    def on_finished(self, success, msg):
        self.btn_start.setEnabled(True)
        self.btn_select_file.setEnabled(True)
        self.btn_select_folder.setEnabled(True)
        if success:
            self.log("放大任务圆满完成！")
            self.log(msg)
        else:
            self.log(f"出现错误: {msg}")
            QMessageBox.critical(self, "错误", f"放大失败：{msg}")

    def log(self, text):
        self.log_text.append(text)
        sb = self.log_text.verticalScrollBar()
        sb.setValue(sb.maximum())
