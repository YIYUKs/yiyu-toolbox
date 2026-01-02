from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
    QFileDialog, QTextEdit, QProgressBar, QMessageBox, QGroupBox,
    QRadioButton, QButtonGroup
)
from PyQt5.QtCore import Qt, pyqtSlot
from matting_processor import MattingThread
import os

class MattingWidget(QWidget):
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

        # 1.5 Edge Strength Selection
        strength_box = QGroupBox("边缘处理强度")
        strength_layout = QHBoxLayout(strength_box)
        strength_layout.setContentsMargins(10, 10, 10, 10)
        strength_layout.setSpacing(15)
        
        self.strength_group = QButtonGroup(self)
        self.rb_low = QRadioButton("低 (保留原生边缘，适合大面积主体)")
        self.rb_medium = QRadioButton("中 (适度平滑，适合普通场景)")
        self.rb_high = QRadioButton("强 (深度清理，适合发丝/复杂背景，默认)")
        self.rb_all = QRadioButton("一次生成3种 (低/中/强，速度较慢)")
        
        self.rb_high.setChecked(True)
        
        self.strength_group.addButton(self.rb_low, 1)
        self.strength_group.addButton(self.rb_medium, 2)
        self.strength_group.addButton(self.rb_high, 3)
        self.strength_group.addButton(self.rb_all, 4)
        
        strength_layout.addWidget(self.rb_low)
        strength_layout.addWidget(self.rb_medium)
        strength_layout.addWidget(self.rb_high)
        strength_layout.addWidget(self.rb_all)
        layout.addWidget(strength_box)

        # 2. Action
        self.btn_start = QPushButton("一键自动抠图 (保存为透明PNG)")
        self.btn_start.setObjectName("btn_start")
        self.btn_start.setFixedHeight(50)
        self.btn_start.setCursor(Qt.PointingHandCursor)
        self.btn_start.clicked.connect(self.start_processing)
        layout.addWidget(self.btn_start)

        # 3. Progress (Removed, using main window)
        pass

        # 4. Log
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setPlaceholderText("抠图结果将保存至原图目录下的 images_output_yiyu_box 文件夹中...")
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

    def get_strength_value(self):
        checked_id = self.strength_group.checkedId()
        if checked_id == 1: return "low"
        if checked_id == 2: return "medium"
        if checked_id == 3: return "high"
        return "all"

    def start_processing(self):
        if not self.input_path or not os.path.exists(self.input_path):
            QMessageBox.warning(self, "提示", "请先选择图片或文件夹！")
            return

        if self.worker and self.worker.isRunning():
            return

        strength = self.get_strength_value()
        self.log(f"开始任务... 强度设定: {strength}")
        self.btn_start.setEnabled(False)
        self.btn_select_file.setEnabled(False)
        self.btn_select_folder.setEnabled(False)
        self.pbar.setValue(0)

        self.worker = MattingThread(self.input_path, self.is_folder, strength=strength)
        self.worker.progress_signal.connect(self.update_progress)
        self.worker.finished_signal.connect(self.on_finished)
        self.worker.start()

    def update_progress(self, item_val, total_val, msg):
        # Update parent progress bars if available
        parent = self.window()
        if hasattr(parent, 'item_pbar'):
            parent.item_pbar.setValue(item_val)
        if hasattr(parent, 'total_pbar'):
            parent.total_pbar.setValue(total_val)
        if hasattr(parent, 'lineEdit'):
            parent.lineEdit.setText(msg)
        self.log(msg)

    def on_finished(self, success, msg):
        self.btn_start.setEnabled(True)
        self.btn_select_file.setEnabled(True)
        self.btn_select_folder.setEnabled(True)
        if success:
            self.log("任务圆满完成！")
            self.log(f"结果已保存: {msg}")
        else:
            self.log(f"出现错误: {msg}")
            QMessageBox.critical(self, "错误", f"抠图失败：{msg}")

    def log(self, text):
        self.log_text.append(text)
        sb = self.log_text.verticalScrollBar()
        sb.setValue(sb.maximum())
