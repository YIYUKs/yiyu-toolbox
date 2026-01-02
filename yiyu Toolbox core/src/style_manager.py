from PyQt5.QtWidgets import QProxyStyle, QStyle

class StyleManager:
    @staticmethod
    def get_main_style():
        return """
            QWidget {
                background-color: #333333;
                color: #FFFFFF;
                font-family: "Microsoft YaHei", "Segoe UI", sans-serif;
            }
            
            QTabWidget::pane {
                border-top: 2px solid #444444;
                background-color: #333333;
            }
            
            QTabBar::tab {
                background-color: #444444;
                color: #AAAAAA;
                padding: 10px 20px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                margin-right: 2px;
                min-width: 100px;
            }
            
            QTabBar::tab:selected {
                background-color: #555555;
                color: #FFFFFF;
            }
            
            QGroupBox {
                border: 1px solid #555555;
                border-radius: 6px;
                margin-top: 20px;
                font-weight: bold;
                padding-top: 15px;
                padding-bottom: 10px;
            }
            
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                left: 10px;
                padding: 0 5px;
                color: #DDDDDD;
            }
            
            QPushButton {
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
                border: none;
            }
            
            /* Orange: Select Image */
            QPushButton#btn_select_image {
                background-color: #FFCC88;
                color: #333333;
            }
            QPushButton#btn_select_image:hover {
                background-color: #FFB380;
            }
            
            /* Blue: Select Folder */
            QPushButton#btn_select_folder {
                background-color: #AACCFF;
                color: #333333;
            }
            QPushButton#btn_select_folder:hover {
                background-color: #99BBFF;
            }
            
            /* Mint Green: Start Process */
            QPushButton#btn_start {
                background-color: #99FF99;
                color: #333333;
                font-size: 16px;
            }
            QPushButton#btn_start:hover {
                background-color: #80FF80;
            }
            QPushButton#btn_start:disabled {
                background-color: #555555;
                color: #888888;
            }
            
            QLineEdit, QTextEdit {
                background-color: #222222;
                border: 1px solid #444444;
                border-radius: 4px;
                padding: 5px;
                color: #EEEEEE;
            }
            
            QProgressBar {
                border: 1px solid #444444;
                border-radius: 2px;
                background-color: #222222;
                text-align: center;
                height: 12px;
            }
            
            QProgressBar::chunk {
                background-color: #99FFEE;
                width: 10px;
                margin: 0.5px;
            }
            
            QSlider::groove:horizontal {
                border: 1px solid #444444;
                height: 8px;
                background: #222222;
                margin: 2px 0;
                border-radius: 4px;
            }
            
            QSlider::handle:horizontal {
                background: #99FFEE;
                border: 1px solid #5c5c5c;
                width: 18px;
                margin: -5px 0;
                border-radius: 9px;
            }
            
            QRadioButton {
                spacing: 5px;
            }
            
            QRadioButton::indicator {
                width: 18px;
                height: 18px;
            }
        """

class CustomStyle(QProxyStyle):
    def pixelMetric(self, metric, option=None, widget=None):
        if metric == QStyle.PM_TabBarTabHSpace:
            return 30
        return super().pixelMetric(metric, option, widget)
