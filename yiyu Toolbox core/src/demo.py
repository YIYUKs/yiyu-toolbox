import os
import sys
import ctypes

# Fix taskbar icon grouping on Windows
try:
    myappid = 'Yiyu.Toolbox.V2' # arbitrary string
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
except:
    pass

# Allow OpenMP duplication (Common fix for Torch+Numpy on Windows)
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

# Safely add DLL directory for torch if we are in a venv/portable/frozen state
# DLL Injection Logic for Frozen and Portable environments
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

if hasattr(os, 'add_dll_directory'):
    try:
        # 1. Search in core directory (new structure)
        core_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        if getattr(sys, 'frozen', False):
            exe_dir = os.path.dirname(sys.executable)
            # PyInstaller/Nuitka frozen state
            internal_dir = os.path.join(exe_dir, "_internal")
            torch_lib_path = os.path.join(internal_dir, "torch", "lib")
            torch_lib_root = os.path.join(exe_dir, "torch", "lib")
            search_paths = [internal_dir, torch_lib_path, exe_dir, torch_lib_root, core_dir]
            
            for path in search_paths:
                if os.path.exists(path):
                    os.add_dll_directory(path)
        else:
            # Source or Venv state
            # DISABLED: Adding core_dir here can cause conflicts with torch's own DLLs (Error 1114)
            # Only enable this if you are sure you have missing system DLLs that can't be found otherwise.
            # os.add_dll_directory(core_dir)
            
            if sys.base_prefix != sys.prefix: # Virtual environment
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
from PyQt5.QtWidgets import QApplication, QWidget, QFileDialog, QMessageBox, QTabWidget, QVBoxLayout, QProgressBar, QLabel
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtGui import QPixmap, QIcon
import cv2, numpy as np
from contact import Ui_contact
from style_manager import StyleManager

# Heavy imports deferred for lazy loading
# from video_ui import VideoSplitterWidget
# from matting_ui import MattingWidget
# from upscale_ui import UpscaleWidget

# from batch_processor import BatchWorkThread

class MainWindow(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("乙羽的工具箱")
        
        # Apply global styling
        self.setStyleSheet(StyleManager.get_main_style())
        
        # Determine icon path (absolute to avoid issues)
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        icon_path = os.path.join(base_dir, "resources", "icon.ico")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        else:
            # Fallback to PNG if ICO is missing
            self.setWindowIcon(QIcon(os.path.join(base_dir, "resources", "icon.png")))
            
        self.resize(1050, 850) # Increased height for progress bars
        
        # Main Layout (Tabbed)
        self.main_layout = QVBoxLayout(self)
        self.tabs = QTabWidget()
        self.main_layout.addWidget(self.tabs)
        
        # --- Tab 1: Watermark Remover ---
        self.tab_watermark = QWidget()
        self.ui = Ui_Form()
        self.ui.setupUi(self.tab_watermark)
        self.tabs.addTab(self.tab_watermark, "自动去水印")
        
        # UI FIX: Hide the old header layout elements
        if hasattr(self.ui, 'header_layout'):
             if hasattr(self.ui, 'btn_tab_watermark'): self.ui.btn_tab_watermark.hide()
             if hasattr(self.ui, 'btn_tab_dev'): self.ui.btn_tab_dev.hide()
             if hasattr(self.ui, 'label_title'): self.ui.label_title.hide()
        
        # --- Tab 2: Automatic Matting (Lazy) ---
        self.tab_matting_loaded = False
        self.tab_matting_container = QWidget()
        self.tab_matting_layout = QVBoxLayout(self.tab_matting_container)
        self.tab_matting_layout.setContentsMargins(0, 0, 0, 0)
        self.tabs.addTab(self.tab_matting_container, "90分自动抠图")
        
        # --- Tab 3: Image Upscaling (Lazy) ---
        self.tab_upscale_loaded = False
        self.tab_upscale_container = QWidget()
        self.tab_upscale_layout = QVBoxLayout(self.tab_upscale_container)
        self.tab_upscale_layout.setContentsMargins(0, 0, 0, 0)
        self.tabs.addTab(self.tab_upscale_container, "90分图片智能放大")

        # --- Tab 4: Video Splitter (Lazy) ---
        self.tab_video_loaded = False
        self.tab_video_container = QWidget()
        self.tab_video_layout = QVBoxLayout(self.tab_video_container)
        self.tab_video_layout.setContentsMargins(0, 0, 0, 0)
        self.tabs.addTab(self.tab_video_container, "截取视频分镜")
        
        # --- Dual Progress Bar Section ---
        self.progress_container = QWidget()
        self.progress_layout = QVBoxLayout(self.progress_container)
        self.progress_layout.setContentsMargins(5, 5, 5, 5)
        self.progress_layout.setSpacing(2)
        
        # Upper: Total Progress
        self.total_pbar_label = QLabel("总进度")
        self.total_pbar_label.setStyleSheet("font-size: 10px; color: #888;")
        self.total_pbar = QProgressBar()
        self.total_pbar.setValue(0)
        self.total_pbar.setTextVisible(False)
        self.total_pbar.setFixedHeight(8)
        
        # Lower: Current Task Progress
        self.item_pbar_label = QLabel("当前任务进度")
        self.item_pbar_label.setStyleSheet("font-size: 10px; color: #888;")
        self.item_pbar = QProgressBar()
        self.item_pbar.setValue(0)
        self.item_pbar.setTextVisible(False)
        self.item_pbar.setFixedHeight(8)
        
        self.progress_layout.addWidget(self.total_pbar_label)
        self.progress_layout.addWidget(self.total_pbar)
        self.progress_layout.addWidget(self.item_pbar_label)
        self.progress_layout.addWidget(self.item_pbar)
        
        self.main_layout.addWidget(self.progress_container)

        # Status Line (Use the one from MainWindow now)
        self.lineEdit = QtWidgets.QLineEdit()
        self.lineEdit.setReadOnly(True)
        self.lineEdit.setPlaceholderText("准备就绪...")
        self.main_layout.addWidget(self.lineEdit)
        
        # Connect Signals
        self.tabs.currentChanged.connect(self.on_tab_changed)
        self.ui.slider_brush.valueChanged.connect(self.update_brush_size)
        self.ui.btn_batch.clicked.connect(self.start_batch_mode)
        self.ui.btn_org.clicked.connect(self.on_btn_org_clicked)
        self.ui.btn_org_2.clicked.connect(self.on_btn_org_2_clicked)
        
        # Connect processing signal to MainWindow for robust UI management
        self.ui.widget.thread.my_signal.connect(self.on_single_processed)
        self.ui.widget.thread.progress_signal.connect(self.update_batch_progress)
        
        if hasattr(self.ui, 'pushButton'):
             self.ui.pushButton.clicked.connect(self.on_pushButton_clicked)
        
        # Set initial brush size
        self.ui.widget.brush_size = self.ui.slider_brush.value()
        self.ui.label_brush.setText(f"画笔大小: {self.ui.widget.brush_size}")
        
        # Initialize references
        self.batch_folder_path = None

    def on_tab_changed(self, index):
        """Lazy load tabs when selected"""
        try:
            if index == 1 and not self.tab_matting_loaded:
                 from matting_ui import MattingWidget
                 self.tab_matting_widget = MattingWidget()
                 self.tab_matting_layout.addWidget(self.tab_matting_widget)
                 self.tab_matting_loaded = True
                 
            elif index == 2 and not self.tab_upscale_loaded:
                 from upscale_ui import UpscaleWidget
                 self.tab_upscale_widget = UpscaleWidget()
                 self.tab_upscale_layout.addWidget(self.tab_upscale_widget)
                 self.tab_upscale_loaded = True

            elif index == 3 and not self.tab_video_loaded:
                 from video_ui import VideoSplitterWidget
                 self.tab_video_widget = VideoSplitterWidget()
                 self.tab_video_layout.addWidget(self.tab_video_widget)
                 self.tab_video_loaded = True
        except Exception as e:
            QMessageBox.critical(self, "组件加载故障", f"初始化标签页时发生错误：\n{str(e)}\n\n这可能是由于依赖库损坏或环境配置问题导致的。")

    def update_brush_size(self, val):
        self.ui.widget.brush_size = val
        self.ui.update_brush_label(val)
        
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
            
            # Init gray mask (Save to temp/cache folder or just project root relative)
            gray0 = np.zeros((self.image_cv.shape[0], self.image_cv.shape[1]), dtype=np.uint8)
            # Keep it in core dir to avoid cluttering parent
            mask_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            gray_path = os.path.join(mask_dir, "gray.png")
            cv2.imwrite(gray_path, gray0)
            self.ui.widget.gray_img = QPixmap(gray_path)
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

    def update_batch_progress(self, item_val, total_val, msg):
        self.item_pbar.setValue(item_val)
        self.total_pbar.setValue(total_val)
        self.lineEdit.setText(f"批量处理中... {total_val}% - {msg}")
        
    def batch_finished(self, msg):
        self.ui.lineEdit.setText(f"批量处理完成: {msg}")
        self.ui.btn_batch.setEnabled(True)
        self.ui.btn_org.setEnabled(True)
        self.ui.btn_org_2.setEnabled(True)
        self.ui.widget.drawing1 = True
        self.batch_folder_path = None

    def on_single_processed(self, msg):
        """Callback for single image processing finished"""
        # Ensure buttons are re-enabled even if Label.timeStop failed
        self.ui.btn_org_2.setEnabled(True)
        self.ui.btn_org.setEnabled(True)
        self.ui.btn_batch.setEnabled(True)
        self.ui.widget.drawing1 = True

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
        # Validation: Ensure image is loaded
        if self.ui.widget.image is None or self.ui.widget.image.isNull():
             QMessageBox.warning(self, "提示", "请先加载图片或文件夹！")
             return

        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        mask_path = os.path.join(base_dir, "mask.png")
        self.ui.widget.gray_img.save(mask_path)
        self.ui.widget.drawing1 = False
        self.ui.btn_org_2.setEnabled(False)
        self.ui.btn_org.setEnabled(False)
        self.ui.btn_batch.setEnabled(False)
        
        if hasattr(self, 'batch_folder_path') and self.batch_folder_path:
             self.ui.lineEdit.setText("正在执行批量去水印 (后台处理中)...")
             from batch_processor import BatchWorkThread
             self.batch_thread = BatchWorkThread(self.batch_folder_path, mask_path, device_str="cpu")
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
