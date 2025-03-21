import sys
import os
import logging
from datetime import datetime

# 设置Qt插件路径 - 在导入PySide6之前设置环境变量
current_dir = os.path.dirname(os.path.abspath(__file__))
plugins_dir = os.path.join(current_dir, "function")

# 设置QT_PLUGIN_PATH环境变量
os.environ["QT_PLUGIN_PATH"] = plugins_dir
print(f"设置Qt插件路径: {plugins_dir}")

# 设置QT_DEBUG_PLUGINS环境变量以启用插件调试
os.environ["QT_DEBUG_PLUGINS"] = "1"

# 添加function目录到sys.path
if plugins_dir not in sys.path:
    sys.path.insert(0, plugins_dir)

# 添加DLL目录到PATH环境变量
if "PATH" in os.environ:
    os.environ["PATH"] = plugins_dir + os.pathsep + os.environ["PATH"]
else:
    os.environ["PATH"] = plugins_dir

from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QTextEdit, QLabel, QPushButton, QWidget, QMessageBox, QGroupBox, QSizePolicy, QDialog, QTextBrowser
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QFont, QPixmap, QImage

from display import NavigationFunctions, ZoomableLabel

# 导入功能模块
from function import (
    ImageStandardization,
    GridCropping,
    ImportBeforeImage,
    ImportAfterImage,
    ExecuteChangeDetectionTask,
    ClearTask,
    ImageDisplay
)

class RemoteSensingApp(QMainWindow):
    def __init__(self):
        """初始化GUI界面"""
        super().__init__()
        
        # 配置日志
        self.configure_logging()
        
        # 设置窗口属性
        self.setWindowTitle("遥感影像变化检测系统 V2.0")
        self.setGeometry(100, 100, 1280, 800)
        
        # 设置应用程序样式 - 使用黑色/灰色背景主题
        self.setStyleSheet("""
            QMainWindow, QWidget {
                background-color: #202124;
                color: #f7f7f8;
            }
            QMenuBar, QStatusBar {
                background-color: #202124;
                color: #f7f7f8;
            }
            QHeaderView::section {
                background-color: #2c2c2e;
                color: #f7f7f8;
                padding: 4px;
                border: 1px solid #444a5a;
            }
            QGroupBox {
                border: 1px solid #444a5a;
                border-radius: 3px;
                margin-top: 8px;
                font-weight: bold;
                color: #f7f7f8;
                background-color: #202124;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 3px 0 3px;
                background-color: #202124;
            }
            QTextEdit, QTextBrowser {
                background-color: #2c2c2e;
                color: #f7f7f8;
                border: 1px solid #444a5a;
                border-radius: 3px;
            }
            QPushButton {
                background-color: #444a5a;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #5d6576;
            }
            QPushButton:pressed {
                background-color: #353b4a;
            }
            QLabel {
                color: #f7f7f8;
            }
            QSplitter::handle {
                background-color: #d8d8de;
            }
            QDialog {
                background-color: #202124;

                color: #f7f7f8;

            }
            QCheckBox, QRadioButton {
                color: #f7f7f8;
            }
            QMessageBox {
                background-color: #202124;
                color: #f7f7f8;
            }
            QTabWidget::pane {
                border: 1px solid #444a5a;
                background-color: #202124;
            }
            QTabBar::tab {
                background-color: #2c2c2e;
                color: #f7f7f8;
                border: 1px solid #444a5a;
                border-bottom: none;
                padding: 5px 10px;
            }
            QTabBar::tab:selected {
                background-color: #202124;
                border-bottom: 1px solid #202124;
            }
            QLineEdit, QComboBox, QSpinBox {
                background-color: #2c2c2e;
                color: #f7f7f8;
                border: 1px solid #444a5a;
                border-radius: 4px;
                padding: 3px;
            }
            QToolTip {
                background-color: #2c2c2e;
                color: #f7f7f8;
                border: 1px solid #444a5a;
            }
            
            /* 滚动条样式 */
            QScrollBar:vertical {
                border: none;
                background-color: #2c2c2e;
                width: 10px;
                margin: 0;
            }
            QScrollBar::handle:vertical {
                background-color: #444a5a;
                min-height: 20px;
                border-radius: 5px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                border: none;
                background: none;
                height: 0;
                width: 0;
            }
            
            /* 水平滚动条样式 */
            QScrollBar:horizontal {
                border: none;
                background-color: #2c2c2e;
                height: 10px;
                margin: 0;
            }
            QScrollBar::handle:horizontal {
                background-color: #444a5a;
                min-width: 20px;
                border-radius: 5px;
            }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                border: none;
                background: none;
                height: 0;
                width: 0;
            }
        """)
        
        # 创建中央控件和主布局
        central_widget = QWidget()
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(8, 8, 8, 8)  # 适当间距
        main_layout.setSpacing(8)  # 增加组件间距
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)
        
        # 创建顶部按钮导航栏
        self.create_button_group(main_layout)
        
        # 创建水平布局，分为图像区域
        top_layout = QHBoxLayout()
        top_layout.setSpacing(10)  # 增加组件间距
        main_layout.addLayout(top_layout, 3)  # 图像区域占比更大
        
        # 创建标签和组
        self.create_before_image_group(top_layout)
        self.create_after_image_group(top_layout)
        
        # 创建下半部分水平布局，包含日志和输出结果
        bottom_layout = QHBoxLayout()
        bottom_layout.setSpacing(10)  # 增加组件间距
        main_layout.addLayout(bottom_layout, 2)  # 底部区域占比略小
        
        # 创建日志区域和输出结果区域（左右并排）
        log_group = self.create_log_group(None)
        output_group = self.create_output_group(None)
        
        # 设置日志区域宽度比例较小
        log_group.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        output_group.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        # 添加到底部布局
        bottom_layout.addWidget(log_group, 1)  # 比例为1
        bottom_layout.addWidget(output_group, 3)  # 比例为3
        
        # 初始化NavigationFunctions
        self.navigation_functions = NavigationFunctions(self.text_log, self.label_before, self.label_after)
        
        # 初始化功能模块
        self.init_function_modules()
        
        # 连接按钮点击事件
        self.connect_buttons()

    def configure_logging(self):
        """配置日志系统"""
        log_dir = "logs"
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = os.path.join(log_dir, f"app_{timestamp}.log")
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
    
    def create_before_image_group(self, parent_layout):
        """创建前时相影像组"""
        self.group_before = QGroupBox("前时相影像")
        layout_before = QVBoxLayout(self.group_before)
        layout_before.setContentsMargins(8, 16, 8, 8)  # 增加内边距
        
        # 创建可缩放标签
        self.label_before = ZoomableLabel()
        self.label_before.setAlignment(Qt.AlignCenter)
        self.label_before.setText("前时相影像")
        self.label_before.setStyleSheet("""
            background-color: #2c2c2e; 
            border: 1px solid #444a5a;
            border-radius: 4px;
            color: #f7f7f8;
            font-size: 12pt;
        """)
        
        # 设置最小尺寸但允许自适应放大
        self.label_before.setMinimumSize(400, 400)
        
        # 使用Expanding的尺寸策略，允许组件随窗口调整而调整大小
        self.label_before.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.group_before.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        layout_before.addWidget(self.label_before)
        parent_layout.addWidget(self.group_before, 1)  # 设置比例权重为1，确保平分区域
    
    def create_after_image_group(self, parent_layout):
        """创建后时相影像组"""
        self.group_after = QGroupBox("后时相影像")
        layout_after = QVBoxLayout(self.group_after)
        layout_after.setContentsMargins(8, 16, 8, 8)  # 增加内边距
        
        # 创建可缩放标签
        self.label_after = ZoomableLabel()
        self.label_after.setAlignment(Qt.AlignCenter)
        self.label_after.setText("后时相影像")
        self.label_after.setStyleSheet("""
            background-color: #2c2c2e; 
            border: 1px solid #444a5a;
            border-radius: 4px;
            color: #f7f7f8;
            font-size: 12pt;
        """)
        
        # 设置最小尺寸但允许自适应放大
        self.label_after.setMinimumSize(400, 400)
        
        # 使用Expanding的尺寸策略，允许组件随窗口调整而调整大小
        self.label_after.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.group_after.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        layout_after.addWidget(self.label_after)
        parent_layout.addWidget(self.group_after, 1)  # 设置比例权重为1，确保平分区域
    
    def create_log_group(self, parent_layout):
        """创建日志组"""
        # 不再添加到主布局，而是返回组件供后续操作
        self.group_log = QGroupBox("日志记录")
        layout_log = QVBoxLayout(self.group_log)
        layout_log.setContentsMargins(8, 16, 8, 8)  # 增加内边距
        
        self.text_log = QTextEdit()
        self.text_log.setReadOnly(True)
        self.text_log.setFont(QFont("Consolas", 9))
        self.text_log.setStyleSheet("""
            background-color: #2c2c2e; 
            color: #f7f7f8;
            border: 1px solid #444a5a;
            border-radius: 4px;
        """)
        
        layout_log.addWidget(self.text_log)
        return self.group_log
    
    def create_output_group(self, parent_layout):
        """创建输出结果组"""
        # 不再添加到主布局，而是返回组件供后续操作
        self.group_output = QGroupBox("解译结果")
        layout_output = QVBoxLayout(self.group_output)
        layout_output.setContentsMargins(8, 16, 8, 8)  # 增加内边距
        
        # 只保留解译结果标签
        self.label_result = ZoomableLabel()
        self.label_result.setAlignment(Qt.AlignCenter)
        self.label_result.setText("未生成结果")
        self.label_result.setStyleSheet("""
            background-color: #2c2c2e; 
            border: 1px solid #444a5a;
            border-radius: 4px;
            color: #f7f7f8;
            font-size: 12pt;
        """)
        
        # 移除掩码和边界标签
        self.label_mask = None  # 仅用于兼容性
        self.label_boundary = None  # 仅用于兼容性
        
        layout_output.addWidget(self.label_result)
        
        return self.group_output
    
    def create_button_group(self, parent_layout):
        """创建按钮组"""
        button_layout = QHBoxLayout()
        # 设置布局左对齐
        button_layout.setAlignment(Qt.AlignLeft)
        button_layout.setContentsMargins(5, 0, 5, 0)
        
        # 创建美化后的按钮
        self.btn_standard = QPushButton("尺寸裁剪")
        self.btn_crop = QPushButton("渔网分割")
        self.btn_import = QPushButton("导入前时相影像")
        self.btn_import_after = QPushButton("导入后时相影像")
        self.btn_begin = QPushButton("开始检测")
        self.btn_export = QPushButton("结果导出")
        self.btn_clear = QPushButton("退出任务")
        self.btn_help = QPushButton("帮助")
        
        # 设置按钮样式
        primary_buttons = [self.btn_begin, self.btn_export]
        for btn in primary_buttons:
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #5e55d6;
                    color: white;
                    font-weight: bold;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background-color: #6c63e6;
                }
                QPushButton:pressed {
                    background-color: #4c44b3;
                }
            """)
        
        secondary_buttons = [self.btn_standard, self.btn_crop, self.btn_import, self.btn_import_after]
        for btn in secondary_buttons:
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #444a5a;
                    color: white;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background-color: #5d6576;
                }
                QPushButton:pressed {
                    background-color: #353b4a;
                }
            """)
        
        utility_buttons = [self.btn_clear, self.btn_help]
        for btn in utility_buttons:
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #2c2c2e;
                    color: white;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background-color: #3e3e40;
                }
                QPushButton:pressed {
                    background-color: #242425;
                }
            """)
        
        # 添加按钮到布局
        for btn in [self.btn_import, self.btn_import_after, self.btn_standard, self.btn_crop, self.btn_begin, self.btn_export, self.btn_clear, self.btn_help]:
            button_layout.addWidget(btn)
            # 设置固定高度并增加间距
            btn.setFixedHeight(32)
            btn.setFont(QFont("Microsoft YaHei UI", 9))
            
        # 设置按钮间距
        button_layout.setSpacing(8)
        
        parent_layout.addLayout(button_layout)
        
        # 在按钮下方添加分隔线
        separator = QWidget()
        separator.setFixedHeight(1)
        separator.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        separator.setStyleSheet("background-color: #444a5a;")
        parent_layout.addWidget(separator)
    
    def connect_buttons(self):
        """连接按钮点击事件"""
        self.btn_import.clicked.connect(self.import_before_image.on_import_clicked)
        self.btn_import_after.clicked.connect(self.import_after_image.import_after_image)
        self.btn_standard.clicked.connect(self.image_standardization.standardize_image)
        self.btn_crop.clicked.connect(self.grid_cropping.crop_image)
        self.btn_begin.clicked.connect(self.execute_change_detection.on_begin_clicked)
        self.btn_clear.clicked.connect(self.clear_task.clear_interface)
        self.btn_help.clicked.connect(self.show_help)
        self.btn_export.clicked.connect(self.on_export_clicked)
    
    def show_help(self):
        """显示帮助信息对话框"""
        dialog = QDialog(self)
        dialog.setWindowTitle("帮助")
        dialog.setModal(True)
        dialog.resize(600, 400)
        
        # 使用垂直布局
        layout = QVBoxLayout(dialog)
        
        # 创建QTextBrowser用于显示帮助内容
        text_browser = QTextBrowser()
        text_browser.setHtml("""
            <html>
            <body style="background-color: #2c2c2e; color: #f7f7f8; font-size: 10pt;">
                <h2 style="color: #f7f7f8;">遥感影像变化检测系统</h2>
                <p>本系统用于处理和分析遥感影像，用于变化检测。</p>
                
                <h3 style="color: #f7f7f8;">主要功能</h3>
                <ul>
                    <li><b>导入前时相图像</b>: 导入变化前的遥感影像。</li>
                    <li><b>导入后时相图像</b>: 导入变化后的遥感影像。</li>
                    <li><b>尺寸裁剪</b>: 将图像裁剪为指定尺寸。</li>
                    <li><b>网格分割</b>: 将图像按网格分割为多个小块。</li>
                    <li><b>开始检测</b>: 执行变化检测算法。</li>
                    <li><b>结果导出</b>: 保存检测结果。</li>
                    <li><b>退出任务</b>: 退出当前检测任务。</li>
                </ul>
                
                <h3 style="color: #f7f7f8;">注意事项</h3>
                <p>1. 前时相和后时相图像应当具有相同的尺寸和视角。</p>
                <p>2. 支持的图像格式包括PNG, JPG, TIFF等。</p>
                <p>3. 变化检测结果以RGB图像方式展示，其中以黑白色来呈现变化结果</p>
            </body>
            </html>
        """)
        
        text_browser.setStyleSheet("""
            QTextBrowser {
                background-color: #2c2c2e; 
                color: #f7f7f8;
                border: 1px solid #444a5a;
                border-radius: 3px;
            }
            QScrollBar:vertical {
                border: none;
                background-color: #2c2c2e;
                width: 10px;
                margin: 0;
            }
            QScrollBar::handle:vertical {
                background-color: #444a5a;
                min-height: 20px;
                border-radius: 5px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                border: none;
                background: none;
                height: 0;
                width: 0;
            }
            QScrollBar:horizontal {
                border: none;
                background-color: #2c2c2e;
                height: 10px;
                margin: 0;
            }
            QScrollBar::handle:horizontal {
                background-color: #444a5a;
                min-width: 20px;
                border-radius: 5px;
            }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                border: none;
                background: none;
                height: 0;
                width: 0;
            }
        """)
        
        layout.addWidget(text_browser)
        
        # 添加"关闭"按钮
        close_button = QPushButton("关闭")
        close_button.setStyleSheet("""
            QPushButton {
                background-color: #2c2c2e;
                color: #f7f7f8;
                border: 1px solid #444a5a;
                border-radius: 3px;
                padding: 5px;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #3e3e40;
            }
            QPushButton:pressed {
                background-color: #242425;
            }
        """)
        close_button.clicked.connect(dialog.accept)
        
        # 将按钮添加到布局
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(close_button)
        layout.addLayout(button_layout)
        
        # 设置对话框的整体样式
        dialog.setStyleSheet("""
            QDialog {
                background-color: #202124;
                color: #f7f7f8;
            }
            QLabel {
                color: #f7f7f8;
            }
        """)
        
        dialog.exec()

    def on_export_clicked(self):
        """导出结果处理"""
        try:
            # 检查是否存在self.execute_change_detection对象以及result_image_path属性
            has_result = (hasattr(self.execute_change_detection, 'result_image_path') and 
                         self.execute_change_detection.result_image_path is not None)
            
            if has_result:
                # 有结果图像路径，表示可以导出
                result_path = self.execute_change_detection.result_image_path
                self.navigation_functions.log_message(f"结果导出成功: {result_path}")
                # 这里可以添加进一步的导出逻辑，如复制文件到用户选择的位置等
            else:
                # 没有结果图像路径，表示无法导出
                self.navigation_functions.log_message("导出失败: 没有可用的检测结果")
        except Exception as e:
            # 捕获可能的异常并记录
            self.navigation_functions.log_message(f"导出过程中发生错误: {str(e)}")
            import traceback
            self.navigation_functions.log_message(traceback.format_exc())
    
    def resizeEvent(self, event):
        """处理窗口调整大小事件"""
        super().resizeEvent(event)
        
        # 如果窗口调整大小，更新ZoomableLabel显示的图像大小
        if hasattr(self, 'navigation_functions'):
            self.navigation_functions.update_image_display()

    def init_function_modules(self):
        """初始化功能模块"""
        self.image_standardization = ImageStandardization(self.navigation_functions)
        self.grid_cropping = GridCropping(self.navigation_functions)
        self.import_before_image = ImportBeforeImage(self.navigation_functions)
        self.import_after_image = ImportAfterImage(self.navigation_functions)
        self.execute_change_detection = ExecuteChangeDetectionTask(
            self.navigation_functions, 
            self.label_result
        )
        self.clear_task = ClearTask(
            self.navigation_functions, 
            self.label_before, 
            self.label_after, 
            self.label_result,
            self.text_log
        )
        self.image_display = ImageDisplay(self.navigation_functions)

def main():
    """主函数"""
    app = QApplication(sys.argv)
    window = RemoteSensingApp()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()

    main()
