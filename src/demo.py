import os
import sys

# Allow OpenMP duplication (Common fix for Torch+Numpy on Windows)
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

# Safely add DLL directory for torch if we are in a venv/portable/frozen state
# DLL Injection Logic for Frozen and Portable environments
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

if hasattr(os, 'add_dll_directory'):
    try:
        if getattr(sys, 'frozen', False):
            exe_dir = os.path.dirname(sys.executable)
            # 1. Try PyInstaller 6's default subfolder
            internal_dir = os.path.join(exe_dir, "_internal")
            # 2. Try 'Flat' directory (where things are in the same folder as EXE)
            # Search root and its torch subfolder
            torch_lib_path = os.path.join(internal_dir, "torch", "lib")
            torch_lib_root = os.path.join(exe_dir, "torch", "lib")
            
            search_paths = [internal_dir, torch_lib_path, exe_dir, torch_lib_root]

            for path in search_paths:
                if os.path.exists(path):
                    os.add_dll_directory(path)
        elif sys.base_prefix != sys.prefix: # Virtual environment
            for path in sys.path:
                torch_lib = os.path.join(path, "torch", "lib")
                if os.path.exists(torch_lib):
                    os.add_dll_directory(torch_lib)
    except Exception as e:
        # print(f"DLL directory addition failed: {e}") # For debugging
        pass

# CRITICAL: Import torch FIRST to load DLLs before PyQt5/OpenCV conflicts occur
import torch

from DemoUI import Ui_Form
from PyQt5.QtWidgets import QApplication, QWidget, QFileDialog, QMessageBox, QTabWidget, QVBoxLayout
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtGui import QPixmap, QIcon
import cv2, numpy as np
from contact import Ui_contact
from video_ui import VideoSplitterWidget

from batch_processor import BatchWorkThread

class MainWindow(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("乙羽的工具箱")
        self.setWindowIcon(QIcon("./resources/icon.png"))
        self.resize(1050, 800)
        
        # Main Layout (Tabbed)
        self.main_layout = QVBoxLayout(self)
        self.tabs = QTabWidget()
        self.main_layout.addWidget(self.tabs)
        
        # --- Tab 1: Watermark Remover ---
        self.tab_watermark = QWidget()
        self.ui = Ui_Form()
        self.ui.setupUi(self.tab_watermark)
        self.tabs.addTab(self.tab_watermark, "AI去水印")
        
        # UI FIX: Hide the old header layout elements (Title and Fake Tabs)
        if hasattr(self.ui, 'header_layout'):
             if hasattr(self.ui, 'btn_tab_watermark'): self.ui.btn_tab_watermark.hide()
             if hasattr(self.ui, 'btn_tab_dev'): self.ui.btn_tab_dev.hide()
             if hasattr(self.ui, 'label_title'): self.ui.label_title.hide()
        
        # --- Tab 2: Video Splitter ---
        self.tab_video = VideoSplitterWidget()
        self.tabs.addTab(self.tab_video, "视频自动镜头分割")
        
        # --- Tab 3: Reserved ---
        self.tab_reserved = QWidget()
        layout_res = QVBoxLayout(self.tab_reserved)
        lbl_res = QtWidgets.QLabel("下一个新功能开发中...")
        lbl_res.setAlignment(QtCore.Qt.AlignCenter)
        lbl_res.setStyleSheet("font-size: 24px; color: #888;")
        layout_res.addWidget(lbl_res)
        self.tabs.addTab(self.tab_reserved, "更多功能 (开发中)")
        
        # Connect Signals
        self.ui.slider_brush.valueChanged.connect(self.update_brush_size)
        self.ui.btn_batch.clicked.connect(self.start_batch_mode)
        self.ui.btn_org.clicked.connect(self.on_btn_org_clicked)
        self.ui.btn_org_2.clicked.connect(self.on_btn_org_2_clicked)
        
        if hasattr(self.ui, 'pushButton'):
             self.ui.pushButton.clicked.connect(self.on_pushButton_clicked)
        
        # Set initial brush size
        self.ui.widget.brush_size = self.ui.slider_brush.value()
        self.ui.label_brush.setText(f"画笔大小: {self.ui.widget.brush_size}")
        
        # Initialize references
        self.batch_folder_path = None

    def update_brush_size(self, value):
        self.ui.widget.brush_size = value
        self.ui.label_brush.setText(f"画笔大小: {value}")
        
    @QtCore.pyqtSlot()
    def load_image_from_path(self, path):
        if not path or not os.path.exists(path): return False
        try:
            self.org_path = path
            self.ui.widget.image = QPixmap(path)
            self.ui.widget.image_path = path
            self.ui.widget.thread.image_path = path
            
            # Use imdecode for unicode support
            self.image_cv = cv2.imdecode(np.fromfile(path, dtype=np.uint8), -1)
            if self.image_cv is None: return False
            if len(self.image_cv.shape) == 2:
                self.image_cv = cv2.cvtColor(self.image_cv, cv2.COLOR_GRAY2RGB)
                
            self.ui.widget.image_cv = self.image_cv
            self.image = QPixmap(path)
            
            # Init gray mask
            gray0 = np.zeros((self.image_cv.shape[0], self.image_cv.shape[1]), dtype=np.uint8)
            cv2.imwrite("gray.png", gray0)
            self.ui.widget.gray_img = QPixmap("gray.png")
            return True
        except Exception as e:
            print(f"Load image error: {e}")
            return False

    @QtCore.pyqtSlot()
    def start_batch_mode(self):
        folder_path = QFileDialog.getExistingDirectory(self, "选择要处理的文件夹")
        if not folder_path: return
        
        image_files = [f for f in os.listdir(folder_path) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp'))]
        if not image_files:
            QMessageBox.warning(self, "提示", "文件夹中没有图片！")
            return
            
        first_img_path = os.path.join(folder_path, image_files[0])
        
        if self.load_image_from_path(first_img_path):
            self.batch_folder_path = folder_path
            self.ui.lineEdit.setText(f"批量模式已就绪。请绘制水印区域，然后点击'开始去水印'。")
        else:
             QMessageBox.warning(self, "警告", "无法加载第一张图片！")

    def update_batch_progress(self, val, msg):
        self.ui.lineEdit.setText(f"批量处理中... {val}% - {msg}")
        
    def batch_finished(self, msg):
        self.ui.lineEdit.setText(f"批量处理完成: {msg}")
        self.ui.btn_batch.setEnabled(True)
        self.ui.btn_org.setEnabled(True)
        self.ui.btn_org_2.setEnabled(True)
        self.ui.widget.drawing1 = True
        self.batch_folder_path = None

    @QtCore.pyqtSlot()
    def on_btn_org_clicked(self):
        path, _ = QFileDialog.getOpenFileName(self, "打开文件", ".", "图片文件 (*.jpg *.png *.jpeg)")
        if path:
            self.load_image_from_path(path)
            self.batch_folder_path = None

    @QtCore.pyqtSlot()
    def on_pushButton_clicked(self):
        self.contact_window = my_Ui_contact()
        self.contact_window.show()

    @QtCore.pyqtSlot()
    def on_btn_org_2_clicked(self):
        if not self.ui.widget.image:
             QMessageBox.warning(self, "提示", "请先加载图片")
             return

        self.ui.widget.gray_img.save("mask.png")
        self.ui.widget.drawing1 = False
        self.ui.btn_org_2.setEnabled(False)
        self.ui.btn_org.setEnabled(False)
        self.ui.btn_batch.setEnabled(False)
        
        if hasattr(self, 'batch_folder_path') and self.batch_folder_path:
             self.ui.lineEdit.setText("正在执行批量去水印 (后台处理中)...")
             self.batch_thread = BatchWorkThread(self.batch_folder_path, "mask.png", device_str="cpu")
             self.batch_thread.progress_signal.connect(self.update_batch_progress)
             self.batch_thread.finished_signal.connect(self.batch_finished)
             self.batch_thread.start()
        else:
             self.ui.lineEdit.setText("转换中......")
             self.ui.widget.btn_org_2 = self.ui.btn_org_2
             self.ui.widget.btn_org = self.ui.btn_org
             self.ui.widget.lineEdit = self.ui.lineEdit
             self.ui.widget.btn_batch = self.ui.btn_batch
             self.ui.widget.thread.start()

class my_Ui_contact(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_contact()
        self.ui.setupUi(self)
        self.setWindowIcon(QIcon("./resources/icon.png"))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec_())
