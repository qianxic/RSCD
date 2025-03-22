import os
import sys
import cv2
import numpy as np
from pathlib import Path

# 添加项目根目录到Python路径
# sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from PIL import Image
from PySide6.QtWidgets import QFileDialog, QInputDialog, QMessageBox, QDialog, QVBoxLayout, QPushButton, QLabel, QHBoxLayout, QWidget
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QApplication
# from PySide6.theme_manager import ThemeManager
# 使用相对导入
from .theme_utils import ThemeManager

class GridCropping:
    def __init__(self, navigation_functions):
        """
        初始化渔网裁剪模块
        
        Args:
            navigation_functions: NavigationFunctions实例，用于日志记录和图像显示
        """
        self.navigation_functions = navigation_functions
    
    def crop_image(self, is_before=True):
        """渔网裁剪功能 - 将图像裁剪为网格"""
        # 弹出文件选择对话框
        file_path, _ = QFileDialog.getOpenFileName(None, 
                                     "选择要裁剪的图像", 
                                     "", 
                                     "Image Files (*.png *.jpg *.jpeg *.tif *.tiff);;All Files (*)")
        if not file_path:
            self.navigation_functions.log_message("未选择图像，裁剪操作取消")
            return
        
        # 获取网格裁剪参数
        grid_size, ok = QInputDialog.getInt(None, "网格裁剪设置", 
                                    "请输入要裁剪的网格数量(例如：输入4表示4x4=16个网格):", 
                                    2, 2, 10)
        if not ok:
            self.navigation_functions.log_message("未设置网格参数，裁剪操作取消")
            return
        
        # 让用户选择保存的目标文件夹
        save_dir = QFileDialog.getExistingDirectory(None, "选择保存裁剪结果的文件夹")
        if not save_dir:
            self.navigation_functions.log_message("未选择保存位置，裁剪操作取消")
            return
        
        try:
            # 检查文件类型
            file_ext = os.path.splitext(file_path)[1].lower()
            
            # 初始化变量
            grid_preview_path = None
            last_files = []
            
            # 处理不同类型的图像
            if file_ext in ['.tif', '.tiff']:
                # 处理GeoTIFF格式
                self.navigation_functions.log_message("检测到GeoTIFF格式，使用GDAL处理...")
                last_files = self._crop_geotiff_grid(file_path, grid_size, save_dir, is_before)
                
                # 创建网格示例图
                if last_files:
                    # 保存一张示意图
                    grid_preview_path = self._generate_grid_preview(file_path, grid_size, save_dir)
            else:
                # 处理普通图像格式
                self.navigation_functions.log_message("检测到普通图像格式，使用PIL处理...")
                last_files = self._crop_image_grid_cv2(file_path, grid_size, save_dir, is_before)
                
                # 创建网格示例图（普通图像也需要生成网格预览）
                if last_files:
                    grid_preview_path = self._generate_grid_preview(file_path, grid_size, save_dir)
            
            # 裁剪完成后，可以选择显示其中一个裁剪后的图像或网格示意图
            if grid_preview_path:
                # 检查是否使用深色主题
                is_dark_theme = hasattr(self.navigation_functions, 'is_dark_theme') and self.navigation_functions.is_dark_theme
                
                # 创建对话框
                dialog = QDialog()
                dialog.setWindowTitle("裁剪完成")
                dialog.setFixedSize(350, 180)
                
                # 使用ThemeManager设置对话框样式
                dialog.setStyleSheet(ThemeManager.get_dialog_style(is_dark_theme))
                
                # 创建布局
                layout = QVBoxLayout(dialog)
                layout.setSpacing(15)
                layout.setContentsMargins(25, 25, 25, 25)
                
                # 创建提示标签
                label = QLabel("网格裁剪完成，裁剪结果保存至目标文件夹。\n你要查看哪个影像？")
                label.setAlignment(Qt.AlignCenter)
                
                # 使用ThemeManager设置标签样式
                label.setStyleSheet(ThemeManager.get_dialog_label_style(is_dark_theme))
                
                layout.addWidget(label)
                
                # 创建按钮容器，设置透明背景
                button_container = QWidget()
                button_container.setStyleSheet(ThemeManager.get_transparent_container_style())
                button_layout = QHBoxLayout(button_container)
                button_layout.setContentsMargins(0, 10, 0, 0)
                button_layout.setSpacing(15)
                
                # 使用ThemeManager获取对话框按钮样式
                button_style = ThemeManager.get_dialog_button_style(is_dark_theme)
                
                # 创建按钮
                btn_preview = QPushButton("裁剪示意图")
                btn_cropped = QPushButton("裁剪块")
                btn_cancel = QPushButton("不查看")
                
                # 设置按钮样式
                btn_preview.setStyleSheet(button_style)
                btn_cropped.setStyleSheet(button_style)
                btn_cancel.setStyleSheet(button_style)
                
                # 添加按钮到布局
                button_layout.addStretch()
                button_layout.addWidget(btn_preview)
                button_layout.addWidget(btn_cropped)
                button_layout.addWidget(btn_cancel)
                button_layout.addStretch()
                
                # 添加按钮容器到布局
                layout.addWidget(button_container)
                
                # 准备显示网格预览或每个块的浏览器
                btn_preview.clicked.connect(lambda: self._show_preview_image(grid_preview_path, dialog))
                btn_cropped.clicked.connect(lambda: self._show_cropped_browser(save_dir, last_files, is_before, dialog))
                btn_cancel.clicked.connect(dialog.reject)
                
                # 显示对话框
                dialog.exec()
                
            return True
        except Exception as e:
            self.navigation_functions.log_message(f"图像网格裁剪失败: {str(e)}")
            import traceback
            self.navigation_functions.log_message(traceback.format_exc())
            return False
    
    def _show_cropped_browser(self, save_dir, file_list, is_before, parent_dialog=None):
        """显示裁剪块的浏览器，允许用户逐张预览并加载裁剪后的图像块
        
        Args:
            save_dir: 保存目录
            file_list: 裁剪后的文件列表
            is_before: 是否为前时相
            parent_dialog: 父对话框，如果有的话
        """
        # 如果没有文件，直接返回
        if not file_list:
            return
            
        # 导入Qt库
        from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QScrollArea, QWidget, QHBoxLayout
        from PySide6.QtCore import Qt, QSize
        from PySide6.QtGui import QPixmap, QImage
        
        # 检查是否使用深色主题
        is_dark_theme = hasattr(self.navigation_functions, 'is_dark_theme') and self.navigation_functions.is_dark_theme
        
        # 关闭父对话框如果存在
        if parent_dialog:
            parent_dialog.accept()
        
        # 创建浏览对话框
        browser = QDialog()
        browser.setWindowTitle("裁剪图像浏览器")
        browser.setMinimumSize(600, 550)
        
        # 使用ThemeManager设置浏览器样式
        browser.setStyleSheet(ThemeManager.get_dialog_style(is_dark_theme))
        
        # 创建主布局
        main_layout = QVBoxLayout(browser)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        
        # 创建信息标签
        info_label = QLabel()
        info_label.setWordWrap(True)
        info_label.setAlignment(Qt.AlignCenter)
        
        # 使用ThemeManager设置标签样式
        info_label.setStyleSheet(ThemeManager.get_dialog_label_style(is_dark_theme))
        
        main_layout.addWidget(info_label)
        
        # 创建图像显示区域
        image_container = QWidget()
        image_container.setStyleSheet(ThemeManager.get_container_style(is_dark_theme))
        image_layout = QVBoxLayout(image_container)
        image_layout.setContentsMargins(10, 10, 10, 10)
        image_layout.setSpacing(5)
        
        # 创建图像标签
        image_label = QLabel()
        image_label.setAlignment(Qt.AlignCenter)
        image_label.setMinimumSize(400, 300)
        image_label.setStyleSheet("background-color: transparent;")
        
        # 添加到图像容器
        image_layout.addWidget(image_label)
        
        # 添加图像容器到主布局
        main_layout.addWidget(image_container)
        
        # 创建导航按钮容器
        nav_container = QWidget()
        nav_container.setStyleSheet(ThemeManager.get_container_style(is_dark_theme))
        nav_layout = QHBoxLayout(nav_container)
        nav_layout.setContentsMargins(10, 10, 10, 10)
        nav_layout.setSpacing(10)
        
        # 使用ThemeManager获取按钮样式
        button_style = ThemeManager.get_dialog_button_style(is_dark_theme)
        
        # 创建导航按钮
        btn_prev = QPushButton("上一张")
        btn_prev.setStyleSheet(button_style)
        btn_prev.setFixedWidth(100)
        
        btn_next = QPushButton("下一张")
        btn_next.setStyleSheet(button_style)
        btn_next.setFixedWidth(100)
        
        # 当前图像索引
        current_index = [0]  # 使用列表以便在闭包中修改
        total_images = len(file_list)
        
        # 更新图像显示函数
        def update_image_display():
            if not file_list or current_index[0] >= len(file_list):
                return
                
            current_path = file_list[current_index[0]]
            file_name = os.path.basename(current_path)
            
            # 更新信息文本
            info_label.setText(f"图像 {current_index[0]+1}/{total_images}: {file_name}")
            
            # 加载并显示图像
            try:
                img = cv2.imread(current_path)
                if img is not None:
                    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                    qimg = QImage(img.data, img.shape[1], img.shape[0], img.shape[1] * 3, QImage.Format_RGB888)
                    pixmap = QPixmap.fromImage(qimg)
                    
                    # 调整图像大小以适应显示区域，保持宽高比
                    image_label.setPixmap(pixmap.scaled(image_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))
                else:
                    image_label.setText("无法加载图像")
            except Exception as e:
                image_label.setText(f"加载错误: {str(e)}")
        
        # 设置按钮点击事件
        def on_prev_clicked():
            current_index[0] = (current_index[0] - 1) % total_images
            update_image_display()
            
        def on_next_clicked():
            current_index[0] = (current_index[0] + 1) % total_images
            update_image_display()
            
        # 连接按钮事件
        btn_prev.clicked.connect(on_prev_clicked)
        btn_next.clicked.connect(on_next_clicked)
        
        # 添加按钮到导航布局
        nav_layout.addStretch()
        nav_layout.addWidget(btn_prev)
        nav_layout.addWidget(btn_next)
        nav_layout.addStretch()
        
        # 添加导航容器到主布局
        main_layout.addWidget(nav_container)
        
        # 创建操作按钮容器
        action_container = QWidget()
        action_container.setStyleSheet(ThemeManager.get_container_style(is_dark_theme))
        action_layout = QHBoxLayout(action_container)
        action_layout.setContentsMargins(10, 10, 10, 10)
        action_layout.setSpacing(15)
        
        # 创建操作按钮
        btn_load_before = QPushButton("加载为前时相")
        btn_load_before.setStyleSheet(button_style)
        
        btn_load_after = QPushButton("加载为后时相")
        btn_load_after.setStyleSheet(button_style)
        
        btn_close = QPushButton("关闭")
        btn_close.setStyleSheet(button_style)
        
        # 设置加载按钮点击事件
        def load_current_as_before():
            if current_index[0] < len(file_list):
                self._load_as_time(file_list[current_index[0]], True, browser)
                
        def load_current_as_after():
            if current_index[0] < len(file_list):
                self._load_as_time(file_list[current_index[0]], False, browser)
        
        # 连接按钮事件
        btn_load_before.clicked.connect(load_current_as_before)
        btn_load_after.clicked.connect(load_current_as_after)
        btn_close.clicked.connect(browser.reject)
        
        # 添加按钮到操作布局
        action_layout.addStretch()
        action_layout.addWidget(btn_load_before)
        action_layout.addWidget(btn_load_after)
        action_layout.addWidget(btn_close)
        action_layout.addStretch()
        
        # 添加操作容器到主布局
        main_layout.addWidget(action_container)
        
        # 初始化显示第一张图像
        update_image_display()
        
        # 显示对话框
        browser.exec()
    
    def _show_preview_image(self, image_path, parent_dialog=None):
        """显示网格预览图像
        
        Args:
            image_path: 图像路径
            parent_dialog: 父对话框，如果有的话
        """
        # 导入Qt库
        from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QHBoxLayout, QScrollArea
        from PySide6.QtCore import Qt
        from PySide6.QtGui import QPixmap
        
        # 检查是否使用深色主题
        is_dark_theme = hasattr(self.navigation_functions, 'is_dark_theme') and self.navigation_functions.is_dark_theme
        
        # 不再关闭父对话框
        # if parent_dialog:
        #     parent_dialog.accept()
        
        # 创建预览对话框
        preview = QDialog()
        preview.setWindowTitle("网格预览")
        preview.setMinimumSize(800, 600)
        preview.resize(1000, 800)  # 设置更合适的默认大小
        
        # 使用ThemeManager设置对话框样式
        preview.setStyleSheet(ThemeManager.get_dialog_style(is_dark_theme))
        
        # 创建主布局
        main_layout = QVBoxLayout(preview)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        
        # 创建信息标签
        info_label = QLabel(f"预览图: {os.path.basename(image_path)}")
        
        # 使用ThemeManager设置标签样式
        info_label.setStyleSheet(ThemeManager.get_dialog_label_style(is_dark_theme))
        
        main_layout.addWidget(info_label)
        
        # 创建滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        
        # 创建图像标签
        image_label = QLabel()
        image_label.setAlignment(Qt.AlignCenter)
        
        # 加载图像
        pixmap = QPixmap(image_path)
        if not pixmap.isNull():
            image_label.setPixmap(pixmap)
        else:
            image_label.setText("无法加载图像")
        
        # 设置滚动区域内容
        scroll_area.setWidget(image_label)
        main_layout.addWidget(scroll_area)
        
        # 移除按钮容器及关闭按钮
        
        # 显示对话框
        preview.exec()
    
    def _show_image(self, image_path, is_before=True):
        """显示网格示意图，并提供加载为前时相或后时相的选项
        
        Args:
            image_path: 图像路径
            is_before: 默认显示位置参数，已废弃，保持兼容性
        """
        if not image_path:
            self.navigation_functions.log_message("无效的图像路径")
            return
        
        # 检查是否使用深色主题
        is_dark_theme = hasattr(self.navigation_functions, 'is_dark_theme') and self.navigation_functions.is_dark_theme
        
        # 创建图像浏览器对话框
        browser = QDialog()
        browser.setWindowTitle("网格示意图")
        browser.setMinimumSize(500, 400)  # 设置更大的初始尺寸
        
        # 根据主题设置样式
        if is_dark_theme:
            browser.setStyleSheet("""
                QDialog {
                    background-color: #202124;
                    color: #f7f7f8;
                }
                QLabel {
                    color: #f7f7f8;
                }
            """)
        else:
            browser.setStyleSheet("""
                QDialog {
                    background-color: #ffffff;
                    color: #333333;
                }
                QLabel {
                    color: #333333;
                }
            """)
        
        # 创建布局
        layout = QVBoxLayout(browser)
        layout.setContentsMargins(8, 8, 8, 8)  # 边距
        layout.setSpacing(5)  # 组件间距
        
        # 添加图像标签
        image_label = QLabel()
        image_label.setAlignment(Qt.AlignCenter)
        image_label.setMinimumSize(400, 300)  # 设置更大的图像显示区域
        layout.addWidget(image_label)
        
        # 添加图像信息标签
        info_label = QLabel()
        info_label.setAlignment(Qt.AlignCenter)
        
        # 显示图像并调整大小
        try:
            # 读取图像信息
            file_name = Path(image_path).name
            info_label.setText(f"网格示意图: {file_name}")
            
            # 为路径信息设置特定的容器
            path_container = QWidget()
            if is_dark_theme:
                path_container.setStyleSheet("background-color: #2c2c2e; border: 1px solid #444a5a; border-radius: 4px;")
            else:
                path_container.setStyleSheet("background-color: #f5f5f7; border: 1px solid #e6e6e6; border-radius: 4px;")
            
            path_layout = QVBoxLayout(path_container)
            path_layout.setContentsMargins(5, 5, 5, 5)
            path_layout.addWidget(info_label)
            layout.removeWidget(info_label)
            layout.insertWidget(1, path_container)
            
            # 读取图像并调整对话框大小以适应图像尺寸
            pixmap = QPixmap(image_path)
            if not pixmap.isNull():
                # 计算合适的显示尺寸（限制最大尺寸）
                screen_size = QApplication.primaryScreen().availableSize()
                max_width = min(screen_size.width() * 0.8, 1200)
                max_height = min(screen_size.height() * 0.8, 800)
                
                # 调整图像尺寸以适应屏幕，同时保持宽高比
                img_width = pixmap.width()
                img_height = pixmap.height()
                
                if img_width > max_width or img_height > max_height:
                    # 需要缩小图像
                    scale_ratio = min(max_width/img_width, max_height/img_height)
                    new_width = int(img_width * scale_ratio)
                    new_height = int(img_height * scale_ratio)
                else:
                    # 保持原始尺寸
                    new_width = img_width
                    new_height = img_height
                
                # 调整图像标签大小
                image_label.setPixmap(pixmap.scaled(new_width, new_height, Qt.KeepAspectRatio))
                
                # 调整对话框大小（考虑其他UI元素和边距）
                dialog_width = new_width + 30  # 添加一些边距
                dialog_height = new_height + 100  # 为其他UI元素预留空间
                browser.resize(dialog_width, dialog_height)
            else:
                image_label.setText("无法加载图像")
                self.navigation_functions.log_message(f"无法加载网格示意图: {image_path}")
        except Exception as e:
            self.navigation_functions.log_message(f"显示网格示意图时出错: {str(e)}")
            import traceback
            self.navigation_functions.log_message(traceback.format_exc())
        
        # 添加按钮
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(10, 0, 10, 10)
        button_layout.setSpacing(10)
        
        # 根据主题设置按钮样式
        if is_dark_theme:
            button_style = """
                QPushButton {
                    background-color: #444a5a;
                    color: white;
                    border-radius: 4px;
                    padding: 6px 10px;
                    min-width: 100px;
                }
                QPushButton:hover {
                    background-color: #5d6576;
                }
                QPushButton:pressed {
                    background-color: #353b4a;
                }
            """
        else:
            button_style = """
                QPushButton {
                    background-color: #f0f0f2;
                    color: #333333;
                    border: 1px solid #e6e6e6;
                    border-radius: 4px;
                    padding: 6px 10px;
                    min-width: 100px;
                }
                QPushButton:hover {
                    background-color: #e6e6e9;
                }
                QPushButton:pressed {
                    background-color: #d9d9dc;
                }
            """
        
        # 加载为前时相按钮
        btn_as_before = QPushButton("加载为前时相")
        btn_as_before.setStyleSheet(button_style)
        btn_as_before.clicked.connect(lambda: self._load_as_before_image(image_path, browser))
        
        # 加载为后时相按钮
        btn_as_after = QPushButton("加载为后时相")
        btn_as_after.setStyleSheet(button_style)
        btn_as_after.clicked.connect(lambda: self._load_as_after_image(image_path, browser))
        
        # 关闭按钮
        btn_close = QPushButton("不加载")
        btn_close.setStyleSheet(button_style)
        btn_close.clicked.connect(browser.close)
        
        # 添加按钮到布局
        button_layout.addWidget(btn_as_before)
        button_layout.addWidget(btn_as_after)
        button_layout.addWidget(btn_close)
        layout.addLayout(button_layout)
        
        # 显示对话框
        browser.exec()
    
    def _generate_grid_preview(self, file_path, grid_size, save_dir):
        """生成网格划分示意图，在原图上绘制网格并保存
        
        Args:
            file_path: 原始图像路径
            grid_size: 网格大小
            save_dir: 保存目录
            
        Returns:
            str: 示意图路径，失败返回None
        """
        try:
            # 使用pathlib处理路径
            file_path_obj = Path(file_path)
            save_dir_obj = Path(save_dir)
            
            self.navigation_functions.log_message(f"正在生成网格示意图...")
            
            # 读取原始图像
            try:
                img_pil = Image.open(file_path_obj)
                img = np.array(img_pil)
                if len(img.shape) == 3 and img.shape[2] == 3:
                    img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)  # PIL是RGB，OpenCV是BGR
            except Exception as e:
                self.navigation_functions.log_message(f"使用PIL读取失败: {str(e)}，尝试使用OpenCV")
                img = cv2.imread(str(file_path_obj))
            
            if img is None:
                self.navigation_functions.log_message(f"无法读取图像，无法生成网格示意图")
                return None
            
            # 获取图像尺寸
            height, width = img.shape[:2]
            
            # 创建原始图像的副本
            grid_preview = img.copy()
            
            # 计算每个网格的大小
            grid_width = width // grid_size
            grid_height = height // grid_size
            
            # 设置网格线的颜色和粗细，颜色是BGR格式
            line_color = (0, 0, 255)  # 红色线条 (BGR)
            line_thickness = max(2, min(width, height) // 200)  # 加粗线条
            
            # 设置文字样式，使文字为红色
            text_color = (0, 0, 255)  # 红色文字 (BGR)
            # 使用更精致的字体 - FONT_HERSHEY_SIMPLEX比较美观，或者尝试FONT_HERSHEY_TRIPLEX
            font = cv2.FONT_HERSHEY_TRIPLEX  
            font_scale = max(0.5, min(width, height) / 600)  # 字体稍大一些
            font_thickness = max(1, min(width, height) // 500)  # 字体粗细
            
            # 绘制水平线
            for i in range(1, grid_size):
                y = i * grid_height
                cv2.line(grid_preview, (0, y), (width, y), line_color, line_thickness)
            
            # 绘制垂直线
            for i in range(1, grid_size):
                x = i * grid_width
                cv2.line(grid_preview, (x, 0), (x, height), line_color, line_thickness)
            
            # 每个网格添加索引标签
            for row in range(grid_size):
                for col in range(grid_size):
                    # 计算文本位置
                    text_x = col * grid_width + grid_width // 10  # 动态调整文本位置
                    text_y = row * grid_height + grid_height // 6  # 动态调整文本位置
                    
                    # 添加网格索引文本 - 直接添加，不使用背景
                    text = f"{row+1}_{col+1}"
                    cv2.putText(grid_preview, text, 
                               (text_x, text_y), font, font_scale, text_color, 
                               font_thickness, cv2.LINE_AA)
            
            # 创建输出文件名
            filename = file_path_obj.stem
            ext = file_path_obj.suffix
            output_filename = f"{filename}_grid_preview{ext}"
            output_path = save_dir_obj / output_filename
            
            # 确保保存目录存在
            if not save_dir_obj.exists():
                save_dir_obj.mkdir(parents=True, exist_ok=True)
                
            # 保存示意图
            try:
                # 使用PIL保存，避免中文路径问题
                grid_preview_rgb = cv2.cvtColor(grid_preview, cv2.COLOR_BGR2RGB)
                img_pil = Image.fromarray(grid_preview_rgb)
                img_pil.save(str(output_path))
                self.navigation_functions.log_message(f"网格示意图已保存到: {output_path}")
                return str(output_path)
            except Exception as e:
                self.navigation_functions.log_message(f"PIL保存网格示意图失败: {str(e)}，尝试使用OpenCV")
                try:
                    # 如果PIL保存失败，尝试使用OpenCV
                    cv2.imwrite(str(output_path), grid_preview)
                    self.navigation_functions.log_message(f"使用OpenCV保存网格示意图: {output_path}")
                    return str(output_path)
                except Exception as e2:
                    self.navigation_functions.log_message(f"保存网格示意图失败: {str(e2)}")
                    return None
                
        except Exception as e:
            self.navigation_functions.log_message(f"生成网格示意图时出错: {str(e)}")
            import traceback
            self.navigation_functions.log_message(traceback.format_exc())
            return None
            
    def _crop_image_grid_cv2(self, file_path, grid_size, save_dir, is_before=True):
        """使用OpenCV将普通图像裁剪为网格
        
        Returns:
            list: 成功保存的文件路径列表
        """
        try:
            # 保存成功生成的文件路径
            generated_files = []
            
            # 使用pathlib处理路径
            file_path_obj = Path(file_path)
            save_dir_obj = Path(save_dir)
            
            # 记录日志
            self.navigation_functions.log_message(f"使用OpenCV裁剪图像: {file_path_obj}")
            
            # 使用PIL读取图像以避免中文路径问题
            try:
                img_pil = Image.open(file_path_obj)
                img = np.array(img_pil)
                if len(img.shape) == 3 and img.shape[2] == 3:
                    img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)  # PIL是RGB，OpenCV是BGR
                self.navigation_functions.log_message("使用PIL成功读取图像")
            except Exception as e:
                self.navigation_functions.log_message(f"使用PIL读取失败: {str(e)}，尝试使用OpenCV")
                img = cv2.imread(str(file_path_obj))
            
            if img is None:
                self.navigation_functions.log_message(f"无法读取图像: {file_path_obj}")
                return generated_files
            
            # 获取图像尺寸
            height, width = img.shape[:2]
            
            # 存储原始图像尺寸信息
            if is_before:
                self.navigation_functions.before_image_original_size = (width, height)
            else:
                self.navigation_functions.after_image_original_size = (width, height)
            
            # 计算每个网格的大小
            grid_width = width // grid_size
            grid_height = height // grid_size
            
            self.navigation_functions.log_message(f"原始图像尺寸: {width}x{height}")
            self.navigation_functions.log_message(f"每个网格尺寸: {grid_width}x{grid_height}")
            
            # 获取文件基本信息
            basename = file_path_obj.name
            filename = file_path_obj.stem
            ext = file_path_obj.suffix
            
            # 获取文件名，根据是前时相还是后时相来确定前缀
            prefix = f"{'before' if is_before else 'after'}_grid"
            
            # 确保保存目录存在
            if not save_dir_obj.exists():
                save_dir_obj.mkdir(parents=True, exist_ok=True)
                self.navigation_functions.log_message(f"创建保存目录: {save_dir_obj}")
            
            # 裁剪并保存每个网格
            count = 0
            for row in range(grid_size):
                for col in range(grid_size):
                    count += 1
                    
                    # 计算当前网格的坐标
                    x_start = col * grid_width
                    y_start = row * grid_height
                    
                    # 确保不超出图像边界
                    current_width = min(grid_width, width - x_start)
                    current_height = min(grid_height, height - y_start)
                    
                    if current_width <= 0 or current_height <= 0:
                        continue  # 跳过无效的网格
                    
                    # 裁剪当前网格
                    crop_img = img[y_start:y_start+current_height, x_start:x_start+current_width]
                    
                    # 创建输出文件名
                    output_filename = f"{prefix}_{row+1}_{col+1}{ext}"
                    output_path = save_dir_obj / output_filename
                    
                    # 保存裁剪结果
                    try:
                        # 使用PIL保存，以避免中文路径问题
                        if len(crop_img.shape) == 3 and crop_img.shape[2] == 3:
                            crop_img_rgb = cv2.cvtColor(crop_img, cv2.COLOR_BGR2RGB)
                        else:
                            crop_img_rgb = crop_img
                        img_pil = Image.fromarray(crop_img_rgb)
                        img_pil.save(str(output_path))
                        self.navigation_functions.log_message(f"保存网格 {row+1}_{col+1} 到: {output_path}")
                        generated_files.append(str(output_path))
                    except Exception as e:
                        self.navigation_functions.log_message(f"PIL保存失败: {str(e)}，尝试使用OpenCV")
                        try:
                            # 如果PIL保存失败，尝试使用OpenCV（虽然对中文路径支持可能有问题）
                            cv2.imwrite(str(output_path), crop_img)
                            self.navigation_functions.log_message(f"使用OpenCV保存网格 {row+1}_{col+1} 到: {output_path}")
                            generated_files.append(str(output_path))
                        except Exception as e2:
                            self.navigation_functions.log_message(f"保存网格 {row+1}_{col+1} 失败: {str(e2)}")
            
            self.navigation_functions.log_message(f"网格裁剪完成，共生成 {count} 个子图像，保存在: {save_dir_obj}")
            
            return generated_files
            
        except Exception as e:
            self.navigation_functions.log_message(f"网格裁剪图像时出错: {str(e)}")
            import traceback
            self.navigation_functions.log_message(traceback.format_exc())
            return []

    def _crop_geotiff_grid(self, file_path, grid_size, save_dir, is_before=True):
        """使用GDAL将GeoTIFF图像裁剪为网格
        
        Returns:
            list: 成功保存的文件路径列表
        """
        try:
            from osgeo import gdal
            
            # 保存成功生成的文件路径
            generated_files = []
            
            # 使用pathlib处理路径
            file_path_obj = Path(file_path)
            save_dir_obj = Path(save_dir)
            
            # 记录日志
            self.navigation_functions.log_message(f"使用GDAL裁剪GeoTIFF图像: {file_path_obj}")
            
            # 打开数据集 - 使用字符串路径但先进行规范化
            ds = gdal.Open(str(file_path_obj.resolve()), gdal.GA_ReadOnly)
            if ds is None:
                self.navigation_functions.log_message(f"无法使用GDAL打开文件: {file_path_obj}")
                return generated_files
            
            # 获取基本信息
            width = ds.RasterXSize
            height = ds.RasterYSize
            bands = ds.RasterCount
            geo_transform = ds.GetGeoTransform()
            projection = ds.GetProjection()
            
            # 存储原始图像尺寸信息
            if is_before:
                self.navigation_functions.before_image_original_size = (width, height)
            else:
                self.navigation_functions.after_image_original_size = (width, height)
                
            # 计算每个网格的大小
            grid_width = width // grid_size
            grid_height = height // grid_size
            
            self.navigation_functions.log_message(f"GeoTIFF图像信息: 宽度={width}, 高度={height}, 波段数={bands}")
            self.navigation_functions.log_message(f"每个网格尺寸: {grid_width}x{grid_height}")
            
            # 获取文件基本信息
            basename = file_path_obj.name
            filename = file_path_obj.stem
            ext = file_path_obj.suffix
            
            # 获取文件名，根据是前时相还是后时相来确定前缀
            prefix = f"{'before' if is_before else 'after'}_grid"
            
            # 确保保存目录存在
            if not save_dir_obj.exists():
                save_dir_obj.mkdir(parents=True, exist_ok=True)
                self.navigation_functions.log_message(f"创建保存目录: {save_dir_obj}")
            
            # 创建驱动程序
            driver = gdal.GetDriverByName('GTiff')
            
            # 裁剪并保存每个网格
            count = 0
            for row in range(grid_size):
                for col in range(grid_size):
                    count += 1
                    
                    # 计算当前网格的坐标
                    x_start = col * grid_width
                    y_start = row * grid_height
                    
                    # 确保不超出图像边界
                    current_width = min(grid_width, width - x_start)
                    current_height = min(grid_height, height - y_start)
                    
                    if current_width <= 0 or current_height <= 0:
                        continue  # 跳过无效的网格
                    
                    # 创建输出文件名
                    output_filename = f"{prefix}_{row+1}_{col+1}{ext}"
                    output_path = save_dir_obj / output_filename
                    output_path_str = str(output_path.resolve())  # 获取规范化的绝对路径
                    
                    # 创建目标数据集
                    try:
                        # 使用规范化的绝对路径，避免中文路径问题
                        dst_ds = driver.Create(output_path_str, current_width, current_height, bands, gdal.GDT_Byte)
                        
                        # 计算新的地理变换参数
                        if geo_transform is not None:
                            new_geo_transform = list(geo_transform)
                            # 调整左上角x坐标
                            new_geo_transform[0] = geo_transform[0] + x_start * geo_transform[1]
                            # 调整左上角y坐标
                            new_geo_transform[3] = geo_transform[3] + y_start * geo_transform[5]
                            dst_ds.SetGeoTransform(tuple(new_geo_transform))
                            
                        # 设置投影
                        if projection:
                            dst_ds.SetProjection(projection)
                            
                        # 复制波段数据
                        for band_idx in range(1, bands + 1):
                            band = ds.GetRasterBand(band_idx)
                            data = band.ReadAsArray(x_start, y_start, current_width, current_height)
                            dst_band = dst_ds.GetRasterBand(band_idx)
                            dst_band.WriteArray(data)
                            
                        # 清理资源
                        dst_ds = None
                        self.navigation_functions.log_message(f"保存网格 {row+1}_{col+1} 到: {output_path}")
                        generated_files.append(str(output_path))
                    except Exception as e:
                        self.navigation_functions.log_message(f"保存网格 {row+1}_{col+1} 失败: {str(e)}")
                        # 尝试使用替代方法保存
                        try:
                            # 读取数据到内存
                            data_arrays = []
                            for band_idx in range(1, bands + 1):
                                band = ds.GetRasterBand(band_idx)
                                data_arrays.append(band.ReadAsArray(x_start, y_start, current_width, current_height))
                            
                            # 如果是标准RGB图像（3波段），使用PIL保存
                            if bands == 3:
                                # 组合数组并转换为PIL图像
                                img_array = np.dstack(data_arrays)
                                img_pil = Image.fromarray(img_array)
                                img_pil.save(str(output_path))
                                self.navigation_functions.log_message(f"使用PIL保存网格 {row+1}_{col+1} 到: {output_path}")
                                generated_files.append(str(output_path))
                            else:
                                self.navigation_functions.log_message(f"无法使用替代方法保存非RGB的GeoTIFF图像")
                        except Exception as e2:
                            self.navigation_functions.log_message(f"使用替代方法保存失败: {str(e2)}")
            
            # 清理资源
            ds = None
            
            self.navigation_functions.log_message(f"网格裁剪完成，共生成 {count} 个子图像，保存在: {save_dir}")
            
            return generated_files
            
        except Exception as e:
            self.navigation_functions.log_message(f"裁剪GeoTIFF图像时出错: {str(e)}")
            import traceback
            self.navigation_functions.log_message(traceback.format_exc())
            return []

    def _load_as_time(self, image_path, is_before, dialog=None):
        """加载图像为特定时相
        
        Args:
            image_path: 图像路径
            is_before: 是否为前时相
            dialog: 对话框实例，如果要关闭
        """
        try:
            if is_before:
                self.navigation_functions.file_path = image_path
                self.navigation_functions.log_message(f"已将图像 {os.path.basename(image_path)} 加载为前时相")
            else:
                self.navigation_functions.file_path_after = image_path
                self.navigation_functions.log_message(f"已将图像 {os.path.basename(image_path)} 加载为后时相")
                
            # 更新图像显示
            self.navigation_functions.update_image_display()
            
            # 如果提供了对话框实例，关闭它
            if dialog:
                dialog.accept()
                
            return True
        except Exception as e:
            self.navigation_functions.log_message(f"加载图像时出错: {str(e)}")
            return False

    def _load_as_before_image(self, image_path, dialog):
        """加载图像为前时相并关闭对话框
        
        Args:
            image_path: 要加载的图像路径
            dialog: 要关闭的对话框
        """
        try:
            self.navigation_functions.file_path = image_path
            self.navigation_functions.update_image_display(is_before=True)
            self.navigation_functions.log_message(f"已加载图像为前时相: {image_path}")
            dialog.accept()  # 关闭对话框
        except Exception as e:
            self.navigation_functions.log_message(f"加载图像为前时相时出错: {str(e)}")
    
    def _load_as_after_image(self, image_path, dialog):
        """加载图像为后时相并关闭对话框
        
        Args:
            image_path: 要加载的图像路径
            dialog: 要关闭的对话框
        """
        try:
            self.navigation_functions.file_path_after = image_path
            self.navigation_functions.update_image_display(is_before=False)
            self.navigation_functions.log_message(f"已加载图像为后时相: {image_path}")
            dialog.accept()  # 关闭对话框
        except Exception as e:
            self.navigation_functions.log_message(f"加载图像为后时相时出错: {str(e)}")
