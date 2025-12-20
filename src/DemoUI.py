from PyQt5 import QtCore, QtGui, QtWidgets
from label import Label

class Ui_Form(object):
    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.resize(1024, 768)
        Form.setStyleSheet("background-color: #f0f0f0;")

        self.d_layout = QtWidgets.QVBoxLayout(Form)
        self.d_layout.setContentsMargins(10, 10, 10, 10)
        self.d_layout.setSpacing(10)

        # --- Header ---
        self.header_layout = QtWidgets.QHBoxLayout()
        self.header_layout.setSpacing(0)
        
        # Tab Buttons (Styled as tabs)
        self.btn_tab_watermark = QtWidgets.QPushButton(Form)
        self.btn_tab_watermark.setText("水印处理")
        self.btn_tab_watermark.setMinimumSize(100, 40)
        self.btn_tab_watermark.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.btn_tab_watermark.setStyleSheet("""
            QPushButton {
                background-color: white;
                border: none;
                font-weight: bold;
                font-size: 14px;
                color: #333;
            }
        """)
        
        self.btn_tab_dev = QtWidgets.QPushButton(Form)
        self.btn_tab_dev.setText("功能开发中..")
        self.btn_tab_dev.setMinimumSize(100, 40)
        self.btn_tab_dev.setEnabled(False)
        self.btn_tab_dev.setStyleSheet("""
            QPushButton {
                background-color: #e0e0e0;
                border: none;
                color: #888;
                font-size: 14px;
            }
        """)

        self.header_layout.addWidget(self.btn_tab_watermark)
        self.header_layout.addWidget(self.btn_tab_dev)
        self.header_layout.addStretch()

        # Title Label
        self.label_title = QtWidgets.QLabel(Form)
        self.label_title.setText("乙羽的工具箱v1.0")
        self.label_title.setStyleSheet("font-size: 12px; color: #666;")
        self.header_layout.addWidget(self.label_title)

        self.d_layout.addLayout(self.header_layout)

        # --- Toolbar ---
        self.toolbar_layout = QtWidgets.QHBoxLayout()
        self.toolbar_layout.setSpacing(15)
        self.toolbar_layout.setContentsMargins(0, 10, 0, 10)

        # Select Image Button (Orange)
        self.btn_org = QtWidgets.QPushButton(Form)
        self.btn_org.setObjectName("btn_org") # CRITICAL for auto-connect
        self.btn_org.setText("选取图片")
        self.btn_org.setMinimumSize(120, 50)
        self.btn_org.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.btn_org.setStyleSheet("""
            QPushButton {
                background-color: #FFCC99; 
                border: none;
                font-size: 16px;
                font-weight: bold;
                color: #333;
            }
            QPushButton:hover { background-color: #FFB380; }
        """)

        # Batch Button (Blue)
        self.btn_batch = QtWidgets.QPushButton(Form)
        self.btn_batch.setObjectName("btn_batch")
        self.btn_batch.setText("批量处理(固定位置)")
        self.btn_batch.setMinimumSize(180, 50)
        self.btn_batch.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.btn_batch.setStyleSheet("""
            QPushButton {
                background-color: #AACCFF;
                border: none;
                font-size: 16px;
                font-weight: bold;
                color: #333;
            }
            QPushButton:hover { background-color: #99BBFF; }
        """)

        # Brush Size Label
        self.label_brush_text = QtWidgets.QLabel(Form)
        self.label_brush_text.setText("画笔大小:")
        self.label_brush_text.setStyleSheet("font-size: 14px;")
        
        self.slider_brush = QtWidgets.QSlider(Form)
        self.slider_brush.setObjectName("slider_brush") # CRITICAL
        self.slider_brush.setOrientation(QtCore.Qt.Horizontal)
        self.slider_brush.setMinimum(1)
        self.slider_brush.setMaximum(100)
        self.slider_brush.setValue(20)
        self.slider_brush.setMinimumWidth(150)
        
        # UI Hint Label (New Request)
        self.label_hint = QtWidgets.QLabel(Form)
        self.label_hint.setText("(滚轮缩放，中键拖拽，右键清除)")
        self.label_hint.setStyleSheet("font-size: 12px; color: #888;")

        # Start Button (Green) (Originally btn_org_2)
        self.btn_org_2 = QtWidgets.QPushButton(Form)
        self.btn_org_2.setObjectName("btn_org_2") # CRITICAL
        self.btn_org_2.setText("开始去水印")
        self.btn_org_2.setMinimumSize(120, 50)
        self.btn_org_2.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.btn_org_2.setStyleSheet("""
            QPushButton {
                background-color: #99FF99;
                border: none;
                font-size: 16px;
                font-weight: bold;
                color: #333;
            }
            QPushButton:hover { background-color: #80FF80; }
        """)
        
        # Add widgets to Toolbar
        self.toolbar_layout.addWidget(self.btn_org)
        self.toolbar_layout.addWidget(self.btn_batch)
        self.toolbar_layout.addStretch()
        self.toolbar_layout.addWidget(self.label_brush_text)
        self.toolbar_layout.addWidget(self.slider_brush)
        self.toolbar_layout.addWidget(self.label_hint) # Add hint here
        self.toolbar_layout.addStretch()
        self.toolbar_layout.addWidget(self.btn_org_2)

        self.d_layout.addLayout(self.toolbar_layout)

        # --- Main Image Area ---
        self.widget = Label(Form)
        self.widget.setObjectName("widget")
        self.widget.setStyleSheet("background-color: #e6e6e6; border: 1px solid #ccc;")
        # Set size policy to expand
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.widget.sizePolicy().hasHeightForWidth())
        self.widget.setSizePolicy(sizePolicy)
        
        self.d_layout.addWidget(self.widget)

        # --- Footer Status ---
        self.lineEdit = QtWidgets.QLineEdit(Form)
        self.lineEdit.setReadOnly(True)
        self.lineEdit.setStyleSheet("""
            QLineEdit {
                border: 1px solid #ccc;
                background-color: white;
                padding: 5px;
                color: #666;
            }
        """)
        self.d_layout.addWidget(self.lineEdit)

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)
        
        # Keep references to important labels if needed by logic
        self.label_brush = self.label_brush_text 

    def retranslateUi(self, Form):
        _translate = QtCore.QCoreApplication.translate
        Form.setWindowTitle(_translate("Form", "乙羽的工具箱"))
