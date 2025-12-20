from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
    QFileDialog, QRadioButton, QButtonGroup, QTextEdit, QProgressBar, QMessageBox, QGroupBox
)
from PyQt5.QtCore import Qt, pyqtSlot
from video_splitter import VideoSplitterThread
import os

class VideoSplitterWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        self.worker = None

    def init_ui(self):
        layout = QVBoxLayout(self)

        # 1. Folder Selection
        file_box = QGroupBox("文件夹选择")
        file_layout = QHBoxLayout(file_box)
        
        self.lbl_path = QLabel("未选择文件夹")
        self.lbl_path.setWordWrap(True)
        self.btn_select = QPushButton("选择文件夹")
        self.btn_select.setCursor(Qt.PointingHandCursor)
        self.btn_select.setStyleSheet("""
            QPushButton {
                background-color: #AACCFF;
                border: none;
                font-size: 16px;
                font-weight: bold;
                color: #333;
                padding: 10px;
            }
            QPushButton:hover { background-color: #99BBFF; }
        """)
        self.btn_select.clicked.connect(self.select_folder)
        
        file_layout.addWidget(self.lbl_path, stretch=1)
        file_layout.addWidget(self.btn_select)
        layout.addWidget(file_box)

        # 2. Mode Selection
        mode_box = QGroupBox("截图模式")
        mode_layout = QHBoxLayout(mode_box)
        
        self.mode_group = QButtonGroup(self)
        
        self.rb_start = QRadioButton("镜头开始")
        self.rb_middle = QRadioButton("镜头中间")
        self.rb_end = QRadioButton("镜头结束")
        self.rb_avg = QRadioButton("均分 (20张)")
        
        self.rb_middle.setChecked(True)
        
        self.mode_group.addButton(self.rb_start, 1)
        self.mode_group.addButton(self.rb_middle, 2)
        self.mode_group.addButton(self.rb_end, 3)
        self.mode_group.addButton(self.rb_avg, 4)
        
        mode_layout.addWidget(self.rb_start)
        mode_layout.addWidget(self.rb_middle)
        mode_layout.addWidget(self.rb_end)
        mode_layout.addWidget(self.rb_avg)
        layout.addWidget(mode_box)

        # 3. Action
        self.btn_start = QPushButton("开始分割并保存截图")
        self.btn_start.setFixedHeight(50)
        self.btn_start.setCursor(Qt.PointingHandCursor)
        self.btn_start.setStyleSheet("""
            QPushButton {
                background-color: #99FF99;
                border: none;
                font-size: 16px;
                font-weight: bold;
                color: #333;
            }
            QPushButton:hover { background-color: #80FF80; }
        """)
        self.btn_start.clicked.connect(self.start_processing)
        layout.addWidget(self.btn_start)

        # 4. Progress
        self.pbar = QProgressBar()
        self.pbar.setValue(0)
        layout.addWidget(self.pbar)

        # 5. Log
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        layout.addWidget(self.log_text)

        self.video_path = None

    def select_folder(self):
        path = QFileDialog.getExistingDirectory(self, "选择包含视频的文件夹")
        if path:
            self.video_path = path # Renaming logic concept: this is now folder_path
            self.lbl_path.setText(path)
            self.log(f"已选择文件夹: {path}")

    def get_mode(self):
        mid = self.mode_group.checkedId()
        if mid == 1: return 'start'
        if mid == 2: return 'middle'
        if mid == 3: return 'end'
        if mid == 4: return 'average'
        return 'middle'

    def start_processing(self):
        if not self.video_path or not os.path.exists(self.video_path):
            QMessageBox.warning(self, "提示", "请先选择有效的视频文件！")
            return

        if self.worker and self.worker.isRunning():
            return

        mode = self.get_mode()
        self.log(f"开始处理... 模式: {mode}")
        self.btn_start.setEnabled(False)
        self.btn_select.setEnabled(False)
        self.pbar.setValue(0)

        self.worker = VideoSplitterThread(self.video_path, mode)
        self.worker.log_signal.connect(self.log)
        self.worker.progress_signal.connect(self.pbar.setValue)
        self.worker.finished_signal.connect(self.on_finished)
        self.worker.start()

    def on_finished(self, success, msg):
        self.btn_start.setEnabled(True)
        self.btn_select.setEnabled(True)
        if success:
            self.log("任务完成。" + msg)
        else:
            QMessageBox.critical(self, "错误", "处理失败！\n" + msg)
            self.log(f"任务失败: {msg}")

    def log(self, text):
        self.log_text.append(text)
        # Scroll to bottom
        sb = self.log_text.verticalScrollBar()
        sb.setValue(sb.maximum())
