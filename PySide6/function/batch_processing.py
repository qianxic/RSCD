import os
import traceback
from pathlib import Path
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QGridLayout, QFileDialog, QProgressBar, QListWidget, 
    QTabWidget, QWidget, QMessageBox, QSplitter, QComboBox
)
from PySide6.QtCore import Qt, Signal, QSize, QThread, QObject
from PySide6.QtGui import QFont, QIcon, QPixmap, QCursor

try:
    from .theme_utils import ThemeManager
except ImportError:
    # 尝试直接导入
    from theme_manager import ThemeManager

class BatchProcessingDialog(QDialog):
    """批量化影像变化检测对话框"""
    
    def __init__(self, navigation_functions, parent=None):
        """
        初始化批量处理对话框
        
        Args:
            navigation_functions: NavigationFunctions实例，用于获取主题设置和访问功能模块
            parent: 父窗口
        """
        super().__init__(parent)
        self.navigation_functions = navigation_functions
        self.is_dark_theme = self.navigation_functions.is_dark_theme
        
        # 初始化UI
        self.init_ui()
        
        # 数据存储
        self.before_image_dir = ""
        self.after_image_dir = ""
        self.output_dir = ""
        self.before_images = []
        self.after_images = []
        
    def init_ui(self):
        """初始化用户界面"""
        # 设置窗口标题和大小
        self.setWindowTitle("批量化影像变化检测")
        self.resize(900, 600)
        
        # 应用主题样式
        self.apply_theme()
        
        # 创建主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(10)
        
        # 创建标题
        title_label = QLabel("批量化影像变化检测")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setFont(QFont("Microsoft YaHei UI", 12, QFont.Bold))
        title_label.setStyleSheet(f"color: {ThemeManager.get_colors(self.is_dark_theme)['text']};")
        main_layout.addWidget(title_label)
        
        # 创建选项卡部件
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet(ThemeManager.get_tab_widget_style(self.is_dark_theme))
        
        # 创建三个选项卡页面
        self.setup_tab = QWidget()
        self.process_tab = QWidget()
        self.result_tab = QWidget()
        
        # 添加选项卡
        self.tab_widget.addTab(self.setup_tab, "数据设置")
        self.tab_widget.addTab(self.process_tab, "任务处理")
        self.tab_widget.addTab(self.result_tab, "结果查看")
        
        # 初始化各选项卡内容
        self.init_setup_tab()
        self.init_process_tab()
        self.init_result_tab()
        
        # 添加选项卡到主布局
        main_layout.addWidget(self.tab_widget)
        
        # 创建底部按钮布局
        bottom_layout = QHBoxLayout()
        bottom_layout.setContentsMargins(0, 10, 0, 0)
        
        # 创建按钮
        self.start_button = QPushButton("开始执行")
        self.cancel_button = QPushButton("取消")
        self.start_button.setStyleSheet(ThemeManager.get_primary_button_style(self.is_dark_theme))
        self.cancel_button.setStyleSheet(ThemeManager.get_secondary_button_style(self.is_dark_theme))
        
        # 设置按钮尺寸
        self.start_button.setFixedSize(120, 32)
        self.cancel_button.setFixedSize(120, 32)
        
        # 设置按钮字体
        self.start_button.setFont(QFont("Microsoft YaHei UI", 9))
        self.cancel_button.setFont(QFont("Microsoft YaHei UI", 9))
        
        # 连接信号
        self.cancel_button.clicked.connect(self.reject)
        self.start_button.clicked.connect(self.start_batch_processing)
        
        # 添加按钮到底部布局
        bottom_layout.addStretch()
        bottom_layout.addWidget(self.start_button)
        bottom_layout.addWidget(self.cancel_button)
        
        # 添加底部布局到主布局
        main_layout.addLayout(bottom_layout)
        
    def init_setup_tab(self):
        """初始化数据设置选项卡"""
        # 创建布局
        layout = QVBoxLayout(self.setup_tab)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)
        
        # 创建前时相影像目录选择
        before_layout = QHBoxLayout()
        before_label = QLabel("前时相影像目录:")
        self.before_dir_label = QLabel("未选择")
        self.before_dir_button = QPushButton("浏览...")
        
        before_layout.addWidget(before_label)
        before_layout.addWidget(self.before_dir_label, 1)
        before_layout.addWidget(self.before_dir_button)
        
        # 创建后时相影像目录选择
        after_layout = QHBoxLayout()
        after_label = QLabel("后时相影像目录:")
        self.after_dir_label = QLabel("未选择")
        self.after_dir_button = QPushButton("浏览...")
        
        after_layout.addWidget(after_label)
        after_layout.addWidget(self.after_dir_label, 1)
        after_layout.addWidget(self.after_dir_button)
        
        # 创建输出目录选择
        output_layout = QHBoxLayout()
        output_label = QLabel("结果输出目录:")
        self.output_dir_label = QLabel("未选择")
        self.output_dir_button = QPushButton("浏览...")
        
        output_layout.addWidget(output_label)
        output_layout.addWidget(self.output_dir_label, 1)
        output_layout.addWidget(self.output_dir_button)
        
        # 创建处理选项
        options_layout = QGridLayout()
        
        # 渔网裁剪选项
        grid_label = QLabel("渔网裁剪大小:")
        self.grid_size_combo = QComboBox()
        self.grid_size_combo.addItems(["3x3", "4x4", "5x5", "不裁剪"])
        options_layout.addWidget(grid_label, 0, 0)
        options_layout.addWidget(self.grid_size_combo, 0, 1)
        
        # 添加所有布局到主布局
        layout.addLayout(before_layout)
        layout.addLayout(after_layout)
        layout.addLayout(output_layout)
        layout.addLayout(options_layout)
        layout.addStretch()
        
        # 连接信号
        self.before_dir_button.clicked.connect(self.select_before_dir)
        self.after_dir_button.clicked.connect(self.select_after_dir)
        self.output_dir_button.clicked.connect(self.select_output_dir)
        
        # 设置按钮样式
        self.before_dir_button.setStyleSheet(ThemeManager.get_utility_button_style(self.is_dark_theme))
        self.after_dir_button.setStyleSheet(ThemeManager.get_utility_button_style(self.is_dark_theme))
        self.output_dir_button.setStyleSheet(ThemeManager.get_utility_button_style(self.is_dark_theme))
        
    def init_process_tab(self):
        """初始化任务处理选项卡"""
        # 创建布局
        layout = QVBoxLayout(self.process_tab)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)
        
        # 创建进度条区域
        progress_layout = QVBoxLayout()
        progress_label = QLabel("处理进度:")
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setStyleSheet(ThemeManager.get_progress_bar_style(self.is_dark_theme))
        
        progress_layout.addWidget(progress_label)
        progress_layout.addWidget(self.progress_bar)
        
        # 创建日志区域
        log_label = QLabel("处理日志:")
        self.log_list = QListWidget()
        self.log_list.setStyleSheet(ThemeManager.get_log_text_style(self.is_dark_theme))
        
        # 添加到主布局
        layout.addLayout(progress_layout)
        layout.addWidget(log_label)
        layout.addWidget(self.log_list)
        
    def init_result_tab(self):
        """初始化结果查看选项卡"""
        # 创建布局
        layout = QVBoxLayout(self.result_tab)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)
        
        # 创建结果列表区域
        result_layout = QHBoxLayout()
        
        # 创建结果文件列表
        list_layout = QVBoxLayout()
        list_label = QLabel("结果文件:")
        self.result_list = QListWidget()
        self.result_list.setStyleSheet(ThemeManager.get_list_widget_style(self.is_dark_theme))
        
        list_layout.addWidget(list_label)
        list_layout.addWidget(self.result_list)
        
        # 创建预览区域
        preview_layout = QVBoxLayout()
        preview_label = QLabel("预览:")
        self.preview_label = QLabel("选择文件以预览")
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setStyleSheet(ThemeManager.get_image_label_style(self.is_dark_theme))
        
        preview_layout.addWidget(preview_label)
        preview_layout.addWidget(self.preview_label, 1)
        
        # 设置比例
        result_layout.addLayout(list_layout, 1)
        result_layout.addLayout(preview_layout, 2)
        
        # 创建操作按钮
        button_layout = QHBoxLayout()
        self.open_folder_button = QPushButton("打开输出文件夹")
        self.export_all_button = QPushButton("导出全部结果")
        
        self.open_folder_button.setStyleSheet(ThemeManager.get_secondary_button_style(self.is_dark_theme))
        self.export_all_button.setStyleSheet(ThemeManager.get_primary_button_style(self.is_dark_theme))
        
        button_layout.addStretch()
        button_layout.addWidget(self.open_folder_button)
        button_layout.addWidget(self.export_all_button)
        
        # 添加到主布局
        layout.addLayout(result_layout)
        layout.addLayout(button_layout)
        
        # 连接信号
        self.open_folder_button.clicked.connect(self.open_output_folder)
        self.export_all_button.clicked.connect(self.export_all_results)
        
    def apply_theme(self):
        """应用当前主题到对话框"""
        colors = ThemeManager.get_colors(self.is_dark_theme)
        
        # 设置窗口背景和边框
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {colors['background']};
                color: {colors['text']};
                border: 1px solid {colors['border']};
            }}
            QLabel {{
                color: {colors['text']};
            }}
            QTabWidget::pane {{
                border: 1px solid {colors['border']};
                background-color: {colors['background']};
            }}
            QComboBox {{
                background-color: {colors['background_secondary']};
                color: {colors['text']};
                border: 1px solid {colors['border']};
                border-radius: 3px;
                padding: 5px;
                min-height: 20px;
            }}
        """)
        
    def update_theme(self, is_dark_theme):
        """更新主题，当主应用切换主题时调用"""
        self.is_dark_theme = is_dark_theme
        self.apply_theme()
        
        # 更新各组件样式
        self.tab_widget.setStyleSheet(ThemeManager.get_tab_widget_style(self.is_dark_theme))
        self.progress_bar.setStyleSheet(ThemeManager.get_progress_bar_style(self.is_dark_theme))
        self.log_list.setStyleSheet(ThemeManager.get_log_text_style(self.is_dark_theme))
        self.result_list.setStyleSheet(ThemeManager.get_list_widget_style(self.is_dark_theme))
        self.preview_label.setStyleSheet(ThemeManager.get_image_label_style(self.is_dark_theme))
        
        # 更新按钮样式
        self.start_button.setStyleSheet(ThemeManager.get_primary_button_style(self.is_dark_theme))
        self.cancel_button.setStyleSheet(ThemeManager.get_secondary_button_style(self.is_dark_theme))
        self.before_dir_button.setStyleSheet(ThemeManager.get_utility_button_style(self.is_dark_theme))
        self.after_dir_button.setStyleSheet(ThemeManager.get_utility_button_style(self.is_dark_theme))
        self.output_dir_button.setStyleSheet(ThemeManager.get_utility_button_style(self.is_dark_theme))
        self.open_folder_button.setStyleSheet(ThemeManager.get_secondary_button_style(self.is_dark_theme))
        self.export_all_button.setStyleSheet(ThemeManager.get_primary_button_style(self.is_dark_theme))
        
    def select_before_dir(self):
        """选择前时相影像目录"""
        directory = QFileDialog.getExistingDirectory(self, "选择前时相影像目录")
        if directory:
            self.before_image_dir = directory
            self.before_dir_label.setText(directory)
            self.scan_directory(directory, is_before=True)
            
    def select_after_dir(self):
        """选择后时相影像目录"""
        directory = QFileDialog.getExistingDirectory(self, "选择后时相影像目录")
        if directory:
            self.after_image_dir = directory
            self.after_dir_label.setText(directory)
            self.scan_directory(directory, is_before=False)
            
    def select_output_dir(self):
        """选择输出目录"""
        directory = QFileDialog.getExistingDirectory(self, "选择结果输出目录")
        if directory:
            self.output_dir = directory
            self.output_dir_label.setText(directory)
            
    def scan_directory(self, directory, is_before=True):
        """扫描目录中的图像文件"""
        try:
            image_extensions = ['.png', '.jpg', '.jpeg', '.tif', '.tiff']
            images = []
            
            for ext in image_extensions:
                images.extend(list(Path(directory).glob(f"*{ext}")))
                images.extend(list(Path(directory).glob(f"*{ext.upper()}")))
            
            if is_before:
                self.before_images = images
                self.add_log(f"发现 {len(images)} 个前时相影像文件")
            else:
                self.after_images = images
                self.add_log(f"发现 {len(images)} 个后时相影像文件")
                
        except Exception as e:
            self.add_log(f"扫描目录出错: {str(e)}")
            
    def add_log(self, message):
        """添加日志到日志列表"""
        self.log_list.addItem(message)
        self.log_list.scrollToBottom()
        
    def start_batch_processing(self):
        """开始批量处理"""
        # 检查必要的目录是否已选择
        if not self.before_image_dir or not self.after_image_dir or not self.output_dir:
            QMessageBox.warning(self, "警告", "请先选择前后时相影像目录和输出目录")
            return
            
        if not self.before_images or not self.after_images:
            QMessageBox.warning(self, "警告", "没有找到可处理的影像文件")
            return
            
        # TODO: 实现批量处理逻辑
        self.add_log("开始批量处理...")
        
        # 切换到处理选项卡
        self.tab_widget.setCurrentIndex(1)
        
    def open_output_folder(self):
        """打开输出文件夹"""
        if not self.output_dir:
            QMessageBox.warning(self, "警告", "未设置输出目录")
            return
            
        try:
            import subprocess
            import platform
            
            if platform.system() == "Windows":
                os.startfile(self.output_dir)
            elif platform.system() == "Darwin":  # macOS
                subprocess.call(["open", self.output_dir])
            else:  # Linux
                subprocess.call(["xdg-open", self.output_dir])
                
        except Exception as e:
            QMessageBox.warning(self, "错误", f"无法打开文件夹: {str(e)}")
            
    def export_all_results(self):
        """导出所有结果"""
        # TODO: 实现导出所有结果的逻辑
        self.add_log("导出所有结果...")

class BatchProcessing:
    """批量化影像变化检测功能模块"""
    
    def __init__(self, navigation_functions):
        """
        初始化批量处理模块
        
        Args:
            navigation_functions: NavigationFunctions实例，用于日志记录和功能访问
        """
        self.navigation_functions = navigation_functions
        self.dialog = None
        
    def show_batch_processing_dialog(self):
        """显示批量处理对话框"""
        try:
            # 创建对话框
            self.dialog = BatchProcessingDialog(self.navigation_functions)
            
            # 记录日志
            self.navigation_functions.log_message("启动批量化影像变化检测模块")
            
            # 显示对话框
            self.dialog.exec()
            
        except Exception as e:
            self.navigation_functions.log_message(f"批量处理出错: {str(e)}")
            self.navigation_functions.log_message(traceback.format_exc()) 