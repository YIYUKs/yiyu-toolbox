from PyQt5 import QtCore, QtGui, QtWidgets
from label import Label

class Ui_Form(object):
    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.resize(1024, 768)
        # Style is now handled by StyleManager in demo.py

        self.d_layout = QtWidgets.QVBoxLayout(Form)
        self.d_layout.setContentsMargins(20, 10, 20, 20)
        self.d_layout.setSpacing(20)

        # --- Row 1: Selection (Grouped) ---
        self.group_selection = QtWidgets.QGroupBox(Form)
        self.group_selection.setTitle("选择图片或文件夹")
        self.selection_group_layout = QtWidgets.QHBoxLayout(self.group_selection)
        self.selection_group_layout.setContentsMargins(10, 10, 10, 10)
        self.selection_group_layout.setSpacing(10)
        
        # Instruction Hint
        self.label_instr = QtWidgets.QLabel(self.group_selection)
        self.label_instr.setText("左键涂满水印，右键清除，滚轮缩放，按滚轮拖拽")
        self.label_instr.setStyleSheet("font-size: 14px; color: #CCCCCC;")
        
        # Select Image Button
        self.btn_org = QtWidgets.QPushButton(self.group_selection)
        self.btn_org.setObjectName("btn_select_image")
        self.btn_org.setText("选择图片")
        self.btn_org.setMinimumSize(120, 40)
        self.btn_org.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        
        # Batch Button
        self.btn_batch = QtWidgets.QPushButton(self.group_selection)
        self.btn_batch.setObjectName("btn_select_folder")
        self.btn_batch.setText("选择文件夹")
        self.btn_batch.setMinimumSize(120, 40)
        self.btn_batch.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        
        self.selection_group_layout.addWidget(self.label_instr)
        self.selection_group_layout.addStretch()
        self.selection_group_layout.addWidget(self.btn_org)
        self.selection_group_layout.addWidget(self.btn_batch)
        
        self.d_layout.addWidget(self.group_selection)

        # --- Row 2: Options (Grouped) ---
        self.group_options = QtWidgets.QGroupBox(Form)
        self.group_options.setTitle("画笔设置")
        self.options_layout = QtWidgets.QHBoxLayout(self.group_options)
        self.options_layout.setContentsMargins(10, 10, 10, 10)
        self.options_layout.setSpacing(15)
        
        # Brush Size Label
        self.label_brush_text = QtWidgets.QLabel(self.group_options)
        self.label_brush_text.setText("画笔大小: 20")
        self.label_brush_text.setFixedWidth(120)
        
        # Brush Slider
        self.slider_brush = QtWidgets.QSlider(self.group_options)
        self.slider_brush.setObjectName("slider_brush") # CRITICAL
        self.slider_brush.setOrientation(QtCore.Qt.Horizontal)
        self.slider_brush.setMinimum(1)
        self.slider_brush.setMaximum(100)
        self.slider_brush.setValue(20)
        
        self.options_layout.addWidget(self.label_brush_text)
        self.options_layout.addWidget(self.slider_brush)
        
        self.d_layout.addWidget(self.group_options)

        # --- Row 3: Action (Large Start Button) ---
        self.btn_org_2 = QtWidgets.QPushButton(Form)
        self.btn_org_2.setObjectName("btn_start")
        self.btn_org_2.setText("一键开始去水印")
        self.btn_org_2.setMinimumSize(0, 50)
        self.btn_org_2.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.d_layout.addWidget(self.btn_org_2)

        # --- Row 4: Content (Image Area) ---
        self.widget = Label(Form)
        self.widget.setObjectName("widget")
        # Style is now handled globally, but keeping layout properties
        # Set size policy to expand
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.widget.sizePolicy().hasHeightForWidth())
        self.widget.setSizePolicy(sizePolicy)
        self.d_layout.addWidget(self.widget)

        # Hidden Status Line
        self.lineEdit = QtWidgets.QLineEdit(Form)
        self.lineEdit.hide()

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)
        
        # Keep references to important labels if needed by logic
        self.label_brush = self.label_brush_text 

    def retranslateUi(self, Form):
        _translate = QtCore.QCoreApplication.translate
        Form.setWindowTitle(_translate("Form", "Form"))

    def update_brush_label(self, val):
        self.label_brush_text.setText(f"画笔大小: {val}")
