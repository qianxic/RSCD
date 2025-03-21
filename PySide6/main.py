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

from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QTextEdit, QLabel, QPushButton, QWidget, QMessageBox, QGroupBox, QSizePolicy, QDialog, QTextBrowser, QStackedWidget
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QFont, QPixmap, QImage, QIcon

from display import NavigationFunctions, ZoomableLabel
from theme_manager import ThemeManager

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

class HomePage(QWidget):
    def __init__(self, parent=None, is_dark_theme=False):
        """初始化首页界面"""
        super().__init__(parent)
        self.is_dark_theme = is_dark_theme
        self.init_ui()
        # 信号会在应用程序完全初始化后连接
    
    def init_ui(self):
        """初始化首页UI"""
        # 首先清除现有布局和小部件
        if self.layout():
            # 递归删除所有子组件
            def deleteItems(layout):
                if layout is not None:
                    while layout.count():
                        item = layout.takeAt(0)
                        widget = item.widget()
                        if widget is not None:
                            widget.deleteLater()
                        else:
                            deleteItems(item.layout())
            deleteItems(self.layout())
            # 删除旧布局
            QWidget().setLayout(self.layout())
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)
        
        # 系统标题
        title_label = QLabel("遥感影像变化检测系统 V2.0")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setFont(QFont("Microsoft YaHei UI", 24, QFont.Bold))
        
        # 系统描述
        description = QLabel("本系统提供遥感影像的变化检测功能，支持图像标准化、网格分割、变化检测等多种功能。")
        description.setAlignment(Qt.AlignCenter)
        description.setFont(QFont("Microsoft YaHei UI", 12))
        description.setWordWrap(True)
        
        # 进入主界面按钮
        enter_btn = QPushButton("进入主界面")
        enter_btn.setObjectName("enterMainButton")
        enter_btn.setFont(QFont("Microsoft YaHei UI", 9, QFont.Bold))
        enter_btn.setFixedSize(80, 32)  # 与主界面的按钮大小保持一致
        
        # 使用主题管理器获取按钮样式
        enter_btn.setStyleSheet(ThemeManager.get_primary_button_style(self.is_dark_theme))
        
        # 添加组件到主布局
        main_layout.addStretch(1)
        main_layout.addWidget(title_label)
        main_layout.addWidget(description)
        main_layout.addStretch(2)
        
        # 按钮居中
        btn_container = QHBoxLayout()
        btn_container.addStretch(1)
        btn_container.addWidget(enter_btn)
        btn_container.addStretch(1)
        main_layout.addLayout(btn_container)
        main_layout.addStretch(1)
        
        # 根据当前主题设置背景样式
        colors = ThemeManager.get_colors(self.is_dark_theme)
        self.setStyleSheet(f"background-color: {colors['background']}; color: {colors['text']};")
        title_label.setStyleSheet(f"color: {colors['text']};")
        description.setStyleSheet(f"color: {colors['text']};")
        
        # 存储进入主界面按钮的引用，以便后续连接信号
        self.enter_btn = enter_btn
        
    def update_theme(self, is_dark_theme):
        """更新主题"""
        if self.is_dark_theme != is_dark_theme:
            self.is_dark_theme = is_dark_theme
            self.init_ui()  # 重新初始化UI以应用新主题

class RemoteSensingApp(QMainWindow):
    def __init__(self):
        """初始化GUI界面"""
        super().__init__()
        
        # 配置日志
        self.configure_logging()
        
        # 设置窗口属性
        self.setWindowTitle("遥感影像变化检测系统 V2.0")
        self.setGeometry(100, 100, 1280, 800)
        
        # 主题变量 (默认设为浅色主题)
        self.is_dark_theme = False
        
        # 应用当前主题
        self.apply_theme()
        
        # 创建中央控件和主栈式布局
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        # 创建栈式窗口管理器
        self.stacked_widget = QStackedWidget(self.central_widget)
        
        # 创建首页和主界面
        self.home_page = HomePage(self.stacked_widget, self.is_dark_theme)
        self.main_page = QWidget(self.stacked_widget)
        
        # 将页面添加到栈式窗口
        self.stacked_widget.addWidget(self.home_page)
        self.stacked_widget.addWidget(self.main_page)
        
        # 设置中央布局
        central_layout = QVBoxLayout(self.central_widget)
        central_layout.setContentsMargins(0, 0, 0, 0)
        central_layout.addWidget(self.stacked_widget)
        
        # 初始化主界面
        self.init_main_page()
        
        # 默认显示首页
        self.stacked_widget.setCurrentIndex(0)
        
        # 连接首页按钮信号 - 确保在所有组件初始化完成后进行
        self.connect_home_page_signals()

    def connect_home_page_signals(self):
        """显式连接首页中的按钮信号"""
        # 确保首页按钮信号被正确连接到主应用的方法
        if hasattr(self.home_page, 'enter_btn'):
            # 先断开可能存在的连接，避免多次连接
            try:
                self.home_page.enter_btn.clicked.disconnect()
            except TypeError:
                # 如果没有连接，会抛出异常，忽略即可
                pass
            # 重新连接信号
            self.home_page.enter_btn.clicked.connect(self.switch_to_main_page)
            print("首页按钮信号已连接")  # 调试信息

    def init_main_page(self):
        """初始化主界面页面"""
        main_layout = QVBoxLayout(self.main_page)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(8)
        
        # 创建顶部按钮导航栏
        self.create_button_group(main_layout)
        
        # 创建水平布局，分为图像区域
        top_layout = QHBoxLayout()
        top_layout.setSpacing(10)
        main_layout.addLayout(top_layout, 3)
        
        # 创建标签和组
        self.create_before_image_group(top_layout)
        self.create_after_image_group(top_layout)
        
        # 创建下半部分水平布局，包含日志和输出结果
        bottom_layout = QHBoxLayout()
        bottom_layout.setSpacing(10)
        main_layout.addLayout(bottom_layout, 2)
        
        # 创建日志区域和输出结果区域（左右并排）
        log_group = self.create_log_group(None)
        output_group = self.create_output_group(None)
        
        # 设置日志区域宽度比例较小
        log_group.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        output_group.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        # 添加到底部布局
        bottom_layout.addWidget(log_group, 1)
        bottom_layout.addWidget(output_group, 3)
        
        # 初始化NavigationFunctions及其主题属性
        self.navigation_functions = NavigationFunctions(self.label_before, self.label_after, self.label_result, self.text_log)
        # 设置当前主题标志
        self.navigation_functions.is_dark_theme = self.is_dark_theme
        
        # 初始化功能模块
        self.init_function_modules()
        
        # 连接按钮点击事件
        self.connect_buttons()
        
        # 初始化后立即应用按钮样式
        self.apply_button_styles()
    
    def switch_to_main_page(self):
        """切换到主界面"""
        print("开始切换到主界面...")
        # 设置鼠标为等待状态，提示用户正在加载
        QApplication.setOverrideCursor(Qt.WaitCursor)
        try:
            # 确保日志使用正确的颜色
            if hasattr(self, 'text_log'):
                # 刷新日志文本颜色
                self.refresh_log_text_color()
                
            # 切换到主界面页
            self.stacked_widget.setCurrentIndex(1)
            
            # 记录主界面已加载
            if hasattr(self, 'navigation_functions'):
                self.navigation_functions.log_message("已切换至主界面")
                
            print("主界面切换完成")
        finally:
            # 恢复鼠标
            QApplication.restoreOverrideCursor()
    
    def switch_to_home_page(self):
        """切换到首页"""
        print("开始切换到首页...")
        # 确保首页使用当前主题
        if self.home_page.is_dark_theme != self.is_dark_theme:
            self.home_page.update_theme(self.is_dark_theme)
        
        # 确保日志使用正确的颜色
        if hasattr(self, 'text_log'):
            # 刷新日志文本颜色
            self.refresh_log_text_color()
            
        # 切换到首页
        self.stacked_widget.setCurrentIndex(0)
        
        # 记录首页已加载
        if hasattr(self, 'navigation_functions'):
            self.navigation_functions.log_message("已切换至首页")
            
        print("首页切换完成")

    def create_button_group(self, parent_layout):
        """创建按钮组"""
        button_layout = QHBoxLayout()
        
        # 创建首页按钮
        self.btn_home = QPushButton("首页")
        self.btn_home.setIcon(QIcon(":/icons/home.png"))
        button_layout.addWidget(self.btn_home)
        
        # 创建标准化按钮
        self.btn_standard = QPushButton("影像分割")
        self.btn_standard.setIcon(QIcon(":/icons/image.png"))
        
        # 创建渔网裁剪按钮
        self.btn_crop = QPushButton("渔网裁剪")
        self.btn_crop.setIcon(QIcon(":/icons/crop.png"))
        
        # 创建导入前后时相影像按钮
        self.btn_import = QPushButton("导入前时相影像")
        self.btn_import.setIcon(QIcon(":/icons/import.png"))
        
        self.btn_import_after = QPushButton("导入后时相影像")
        self.btn_import_after.setIcon(QIcon(":/icons/import_after.png"))
        
        # 创建开始解译按钮
        self.btn_begin = QPushButton("开始解译")
        self.btn_begin.setIcon(QIcon(":/icons/play.png"))
        
        # 创建结果导出按钮
        self.btn_export = QPushButton("导出结果")
        self.btn_export.setIcon(QIcon(":/icons/export.png"))
        
        # 创建批量处理按钮
        self.btn_batch = QPushButton("批量处理")
        self.btn_batch.setIcon(QIcon(":/icons/batch.png"))
        
        # 创建功能按钮
        self.btn_theme = QPushButton("切换主题")
        self.btn_theme.setIcon(QIcon(":/icons/theme.png"))
        
        self.btn_clear = QPushButton("清空界面")
        self.btn_clear.setIcon(QIcon(":/icons/clear.png"))
        
        self.btn_help = QPushButton("帮助")
        self.btn_help.setIcon(QIcon(":/icons/help.png"))
        
        # 添加所有按钮到布局（除首页按钮外，已在前面添加）
        for btn in [self.btn_standard, self.btn_crop, self.btn_import, self.btn_import_after, self.btn_begin, self.btn_export, self.btn_batch, self.btn_theme, self.btn_clear, self.btn_help]:
            button_layout.addWidget(btn)
            # 设置固定高度并增加间距
            btn.setFixedHeight(32)
            btn.setFont(QFont("Microsoft YaHei UI", 9))
        
        # 设置首页按钮高度和字体
        self.btn_home.setFixedHeight(32)
        self.btn_home.setFont(QFont("Microsoft YaHei UI", 9, QFont.Bold))
            
        # 设置按钮间距
        button_layout.setSpacing(8)
        
        parent_layout.addLayout(button_layout)
        
        # 在按钮下方添加分隔线
        self.nav_separator = QWidget()
        self.nav_separator.setFixedHeight(1)
        self.nav_separator.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.nav_separator.setStyleSheet(ThemeManager.get_separator_style(self.is_dark_theme))
        parent_layout.addWidget(self.nav_separator)
    
    def connect_buttons(self):
        """连接按钮点击事件"""
        self.btn_home.clicked.connect(self.switch_to_home_page)
        self.btn_import.clicked.connect(self.import_before_image.on_import_clicked)
        self.btn_import_after.clicked.connect(self.import_after_image.import_after_image)
        self.btn_standard.clicked.connect(self.image_standardization.standardize_image)
        self.btn_crop.clicked.connect(self.grid_cropping.crop_image)
        self.btn_begin.clicked.connect(self.execute_change_detection.on_begin_clicked)
        self.btn_clear.clicked.connect(self.clear_task.clear_interface)
        self.btn_help.clicked.connect(self.show_help)
        self.btn_export.clicked.connect(self.on_export_clicked)
        self.btn_theme.clicked.connect(self.toggle_theme)
        self.btn_batch.clicked.connect(self.show_batch_processing)

    def toggle_theme(self):
        """切换深浅主题并更新首页主题"""
        # 切换主题
        self.is_dark_theme = not self.is_dark_theme
        
        # 记录当前主题
        theme_name = "深色" if self.is_dark_theme else "浅色"
        print(f"已切换至{theme_name}主题")
        
        # 应用主题样式
        self.setStyleSheet(ThemeManager.get_app_stylesheet(self.is_dark_theme))
        
        # 更新首页主题
        if hasattr(self, 'home_page'):
            self.home_page.update_theme(self.is_dark_theme)
        
        # 重新连接首页信号
        if hasattr(self, 'connect_home_page_signals'):
            self.connect_home_page_signals()
        
        # 更新顶部容器样式
        if hasattr(self, 'top_container'):
            self.top_container.setStyleSheet(f"background-color: {ThemeManager.get_colors(self.is_dark_theme)['header_bg']};")
        
        # 更新标题标签样式
        if hasattr(self, 'title_label'):
            self.title_label.setStyleSheet(f"color: {ThemeManager.get_colors(self.is_dark_theme)['header_text']};")
        
        # 更新图像显示区域样式
        image_labels = [self.label_before, self.label_after, self.label_result]
        for label in image_labels:
            if hasattr(label, 'setStyleSheet'):
                label.setStyleSheet(ThemeManager.get_image_label_style(self.is_dark_theme))
        
        # 更新日志文本区域样式
        if hasattr(self, 'text_log'):
            # 设置样式
            self.text_log.setStyleSheet(ThemeManager.get_log_text_style(self.is_dark_theme))
            # 刷新所有日志文本颜色
            self.refresh_log_text_color()
        
        # 更新分隔线样式
        if hasattr(self, 'nav_separator'):
            self.nav_separator.setStyleSheet(ThemeManager.get_separator_style(self.is_dark_theme))
        
        # 更新所有按钮的尺寸和字体
        all_buttons = [
            self.btn_home, self.btn_standard, self.btn_crop, self.btn_import, 
            self.btn_import_after, self.btn_begin, self.btn_export, self.btn_batch,
            self.btn_theme, self.btn_clear, self.btn_help
        ]
        
        for btn in all_buttons:
            btn.setFixedHeight(32)
            btn.setFont(QFont("Microsoft YaHei UI", 9))
        
        # 主页按钮字体加粗
        self.btn_home.setFont(QFont("Microsoft YaHei UI", 9, QFont.Bold))
        
        # 使用统一的方法应用按钮样式
        self.apply_button_styles()
        
        # 日志记录
        if hasattr(self, 'navigation_functions'):
            # 更新导航功能中的主题标志
            self.navigation_functions.is_dark_theme = self.is_dark_theme
            self.navigation_functions.log_message(f"已切换至{theme_name}主题")

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
        
        # 使用主题管理器设置样式
        self.label_before.setStyleSheet(ThemeManager.get_image_label_style(self.is_dark_theme))
        
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
        
        # 使用主题管理器设置样式
        self.label_after.setStyleSheet(ThemeManager.get_image_label_style(self.is_dark_theme))
        
        # 设置最小尺寸但允许自适应放大
        self.label_after.setMinimumSize(400, 400)
        
        # 使用Expanding的尺寸策略，允许组件随窗口调整而调整大小
        self.label_after.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.group_after.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        layout_after.addWidget(self.label_after)
        parent_layout.addWidget(self.group_after, 1)  # 设置比例权重为1，确保平分区域
    
    def refresh_log_text_color(self):
        """刷新日志文本框中所有文本的颜色，使其与当前主题一致"""
        if hasattr(self, 'text_log'):
            # 获取当前文本并清空
            current_text = self.text_log.toPlainText()
            self.text_log.clear()
            
            # 根据当前主题确定文本颜色
            text_color = "white" if self.is_dark_theme else "black"
            
            # 设置默认文本颜色
            if self.is_dark_theme:
                self.text_log.setTextColor(Qt.GlobalColor.white)
            else:
                self.text_log.setTextColor(Qt.GlobalColor.black)
            
            # 将文本拆分成行并使用HTML格式重新添加，确保每行都有正确的文本颜色
            lines = current_text.split('\n')
            for line in lines:
                if line.strip():  # 跳过空行
                    formatted_line = f"<span style='color:{text_color};'>{line}</span>"
                    self.text_log.append(formatted_line)
    
    def create_log_group(self, parent_layout):
        """创建日志组"""
        self.group_log = QGroupBox("系统日志")
        layout_log = QVBoxLayout(self.group_log)
        layout_log.setContentsMargins(8, 16, 8, 8)  # 增加内边距
        
        self.text_log = QTextEdit()
        self.text_log.setReadOnly(True)
        self.text_log.setFont(QFont("Microsoft YaHei UI", 9))  # 设置合适的字体和大小
        
        # 使用主题管理器设置日志区域样式
        self.text_log.setStyleSheet(ThemeManager.get_log_text_style(self.is_dark_theme))
        
        # 确保文本颜色正确设置
        if self.is_dark_theme:
            self.text_log.setTextColor(Qt.GlobalColor.white)
        else:
            self.text_log.setTextColor(Qt.GlobalColor.black)
        
        layout_log.addWidget(self.text_log)
        
        if parent_layout:
            parent_layout.addWidget(self.group_log)
        
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
        
        # 使用主题管理器设置样式
        self.label_result.setStyleSheet(ThemeManager.get_image_label_style(self.is_dark_theme))
        
        # 移除掩码和边界标签
        self.label_mask = None  # 仅用于兼容性
        self.label_boundary = None  # 仅用于兼容性
        
        layout_output.addWidget(self.label_result)
        
        return self.group_output
    
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
        
        # 根据当前主题设置不同的HTML内容
        if self.is_dark_theme:
            text_browser.setHtml("""
                <html>
                <body style="background-color: #2c2c2e; color: #f7f7f8; font-size: 10pt;">
                    <h2 style="color: #f7f7f8;">遥感影像变化检测系统</h2>
                    <p>本系统用于处理和分析遥感影像，用于变化检测。</p>
                    
                    <h3 style="color: #f7f7f8;">主要功能</h3>
                    <ul>
                        <li><b>导入前时相图像</b>: 导入变化前的遥感影像。</li>
                        <li><b>导入后时相图像</b>: 导入变化后的遥感影像。</li>
                        <li><b>裁剪影像</b>: 将图像裁剪为指定尺寸。</li>
                        <li><b>网格分割</b>: 将图像按网格分割为多个小块。</li>
                        <li><b>开始检测</b>: 执行变化检测算法。</li>
                        <li><b>结果导出</b>: 保存检测结果。</li>
                        <li><b>清空当前界面</b>: 清空当前界面，并清理当前任务的所有相关缓存。</li>
                        <li><b>切换主题</b>: 在深色和浅色主题间切换。</li>
                    </ul>
                    
                    <h3 style="color: #f7f7f8;">注意事项</h3>
                    <p>1. 前时相和后时相图像应当具有相同的尺寸和视角。</p>
                    <p>2. 支持的图像格式包括PNG, JPG, TIFF等。</p>
                    <p>3. 变化检测结果以RGB图像方式展示，其中以黑白色来呈现变化结果</p>
                </body>
                </html>
            """)
        else:
            text_browser.setHtml("""
                <html>
                <body style="background-color: #f5f5f7; color: #333333; font-size: 10pt;">
                    <h2 style="color: #333333;">遥感影像变化检测系统</h2>
                    <p>本系统用于处理和分析遥感影像，用于变化检测。</p>
                    
                    <h3 style="color: #333333;">主要功能</h3>
                    <ul>
                        <li><b>导入前时相图像</b>: 导入变化前的遥感影像。</li>
                        <li><b>导入后时相图像</b>: 导入变化后的遥感影像。</li>
                        <li><b>尺寸裁剪</b>: 将图像裁剪为指定尺寸。</li>
                        <li><b>网格分割</b>: 将图像按网格分割为多个小块。</li>
                        <li><b>开始检测</b>: 执行变化检测算法。</li>
                        <li><b>结果导出</b>: 保存检测结果。</li>
                        <li><b>退出任务</b>: 退出当前检测任务。</li>
                        <li><b>切换主题</b>: 在深色和浅色主题间切换。</li>
                    </ul>
                    
                    <h3 style="color: #333333;">注意事项</h3>
                    <p>1. 前时相和后时相图像应当具有相同的尺寸和视角。</p>
                    <p>2. 支持的图像格式包括PNG, JPG, TIFF等。</p>
                    <p>3. 变化检测结果以RGB图像方式展示，其中以黑白色来呈现变化结果</p>
                </body>
                </html>
            """)
        
        # 根据当前主题设置样式
        if self.is_dark_theme:
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
        else:
            text_browser.setStyleSheet("""
                QTextBrowser {
                    background-color: #f5f5f7; 
                    color: #333333;
                    border: 1px solid #e6e6e6;
                    border-radius: 3px;
                }
                QScrollBar:vertical {
                    border: none;
                    background-color: #f5f5f7;
                    width: 10px;
                    margin: 0;
                }
                QScrollBar::handle:vertical {
                    background-color: #cccccc;
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
                    background-color: #f5f5f7;
                    height: 10px;
                    margin: 0;
                }
                QScrollBar::handle:horizontal {
                    background-color: #cccccc;
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
        close_button.setFixedHeight(32)
        close_button.setFont(QFont("Microsoft YaHei UI", 9))
        
        # 根据当前主题设置按钮样式
        if self.is_dark_theme:
            close_button.setStyleSheet("""
                QPushButton {
                    background-color: #3e3e40;
                    color: #f7f7f8;
                    border: 1px solid #505050;
                    border-radius: 4px;
                    padding: 5px 10px;
                    min-width: 80px;
                }
                QPushButton:hover {
                    background-color: #4a4a4c;
                    border: 1px solid #606060;
                }
                QPushButton:pressed {
                    background-color: #323234;
                    border: 1px solid #404040;
                }
            """)
        else:
            close_button.setStyleSheet("""
                QPushButton {
                    background-color: #f0f0f2;
                    color: #333333;
                    border: 1px solid #e6e6e6;
                    border-radius: 4px;
                    padding: 5px 10px;
                    min-width: 80px;
                }
                QPushButton:hover {
                    background-color: #e6e6e9;
                }
                QPushButton:pressed {
                    background-color: #d9d9dc;
                }
            """)
            
        close_button.clicked.connect(dialog.accept)
        
        # 将按钮添加到布局
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(close_button)
        layout.addLayout(button_layout)
        
        # 设置对话框的整体样式
        if self.is_dark_theme:
            dialog.setStyleSheet("""
                QDialog {
                    background-color: #202124;
                    color: #f7f7f8;
                }
                QLabel {
                    color: #f7f7f8;
                }
            """)
        else:
            dialog.setStyleSheet("""
                QDialog {
                    background-color: #ffffff;
                    color: #333333;
                }
                QLabel {
                    color: #333333;
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
                # 使用图像导出模块导出结果
                result_path = self.execute_change_detection.result_image_path
                self.image_export.export_result_image(result_path)
            else:
                # 没有结果图像路径，表示无法导出
                self.navigation_functions.log_message("导出失败: 没有可用的检测结果")
                self.image_export._show_styled_message_box("导出失败", "没有可用的检测结果，请先执行变化检测。", "warning")
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
        # 初始化导航功能模块并确保所有子模块获取正确的主题信息
        self.navigation_functions = NavigationFunctions(self.label_before, self.label_after, self.label_result, self.text_log)
        # 设置NavigationFunctions的main_window引用，方便子模块访问
        self.navigation_functions.main_window = self
        # 设置当前主题信息，确保子模块使用正确的主题
        self.navigation_functions.is_dark_theme = self.is_dark_theme
        
        # 确保日志文本颜色正确
        if self.is_dark_theme:
            self.text_log.setTextColor(Qt.GlobalColor.white)
        else:
            self.text_log.setTextColor(Qt.GlobalColor.black)
        
        # 初始化各功能模块
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
        
        # 初始化图像导出模块
        from function.image_export import ImageExport
        self.image_export = ImageExport(self.navigation_functions)
        
        # 初始化批量处理模块
        from function.batch_processing import BatchProcessing
        self.batch_processing = BatchProcessing(self.navigation_functions)

    def apply_theme(self):
        """应用当前主题样式"""
        # 应用主题样式表
        self.setStyleSheet(ThemeManager.get_theme_style(self.is_dark_theme))
            
        # 确保首页主题与应用主题一致
        if hasattr(self, 'home_page'):
            if self.home_page.is_dark_theme != self.is_dark_theme:
                self.home_page.update_theme(self.is_dark_theme)

    def show_batch_processing(self):
        """显示批量处理对话框"""
        try:
            self.batch_processing.show_batch_processing_dialog()
        except Exception as e:
            self.navigation_functions.log_message(f"显示批量处理界面出错: {str(e)}")
            import traceback
            self.navigation_functions.log_message(traceback.format_exc())

    def apply_button_styles(self):
        """应用按钮样式"""
        # 首页按钮使用主要按钮样式
        self.btn_home.setStyleSheet(ThemeManager.get_primary_button_style(self.is_dark_theme))
        
        # 解译和导出按钮使用主要按钮样式
        self.btn_begin.setStyleSheet(ThemeManager.get_primary_button_style(self.is_dark_theme))
        self.btn_export.setStyleSheet(ThemeManager.get_primary_button_style(self.is_dark_theme))
        self.btn_batch.setStyleSheet(ThemeManager.get_primary_button_style(self.is_dark_theme))
        
        # 导入按钮使用次要按钮样式
        self.btn_import.setStyleSheet(ThemeManager.get_secondary_button_style(self.is_dark_theme))
        self.btn_import_after.setStyleSheet(ThemeManager.get_secondary_button_style(self.is_dark_theme))
        self.btn_standard.setStyleSheet(ThemeManager.get_secondary_button_style(self.is_dark_theme))
        self.btn_crop.setStyleSheet(ThemeManager.get_secondary_button_style(self.is_dark_theme))
        
        # 功能性按钮使用工具按钮样式
        self.btn_theme.setStyleSheet(ThemeManager.get_utility_button_style(self.is_dark_theme))
        self.btn_help.setStyleSheet(ThemeManager.get_utility_button_style(self.is_dark_theme))
        self.btn_clear.setStyleSheet(ThemeManager.get_utility_button_style(self.is_dark_theme))

def main():
    """主函数"""
    app = QApplication(sys.argv)
    window = RemoteSensingApp()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
