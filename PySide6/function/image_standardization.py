import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
# sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from PIL import Image
from PySide6.QtWidgets import QFileDialog, QMessageBox, QInputDialog, QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QWidget
from PySide6.QtCore import Qt
# 从theme_utils导入ThemeManager
from .theme_utils import ThemeManager

class ImageStandardization:
    def __init__(self, navigation_functions):
        """
        初始化图像标准化模块
        
        Args:
            navigation_functions: NavigationFunctions实例，用于日志记录和图像显示
        """
        self.navigation_functions = navigation_functions
    
    def standardize_image(self):
        """将图像标准化为用户自定义尺寸"""
        # 弹出文件选择对话框
        file_path, _ = QFileDialog.getOpenFileName(None, 
                                       "选择要标准化的图像", 
                                       "", 
                                       "Image Files (*.png *.jpg *.jpeg *.tif *.tiff);;All Files (*)")
        if not file_path:
            self.navigation_functions.log_message("未选择图像，标准化操作取消")
            return
            
        try:
            # 转换为Path对象处理路径
            file_path_obj = Path(file_path)
            
            # 打开原始图像
            img = Image.open(file_path)
            
            # 记录原始尺寸
            original_size = img.size
            self.navigation_functions.log_message(f"原始图像尺寸: {original_size[0]}x{original_size[1]}")
            
            # 获取用户输入的宽度
            width, ok = QInputDialog.getInt(
                None, 
                "输入宽度", 
                "请输入裁剪后影像的尺寸大小", 
                256, 1, 10000, 1
            )
            if not ok:
                self.navigation_functions.log_message("未指定宽度，标准化操作取消")
                return
                
            # 获取用户输入的高度
            height, ok = QInputDialog.getInt(
                None, 
                "输入高度", 
                "请输入裁剪后影像的尺寸大小", 
                256, 1, 10000, 1
            )
            if not ok:
                self.navigation_functions.log_message("未指定高度，标准化操作取消")
                return
            
            # 使用用户指定的尺寸调整图像
            standardized_img = img.resize((width, height), Image.LANCZOS)
            
            # 生成输出文件名
            file_name = file_path_obj.stem
            file_ext = file_path_obj.suffix
            output_filename = f"{file_name}_{width}x{height}_cliped{file_ext}"
            
            # 获取输出路径（与输入图像相同位置）
            output_dir = file_path_obj.parent
            output_path = output_dir / output_filename
            
            # 保存标准化图像
            standardized_img.save(str(output_path))
            self.navigation_functions.log_message(f"图像已裁剪为{width}x{height}，保存至: {output_path}")
            
            # 检查是否使用深色主题
            is_dark_theme = hasattr(self.navigation_functions, 'is_dark_theme') and self.navigation_functions.is_dark_theme
            
            # 创建自定义对话框
            dialog = QDialog()
            dialog.setWindowTitle("裁剪完成")
            dialog.setFixedSize(350, 180)
            
            # 使用ThemeManager设置对话框样式
            dialog.setStyleSheet(ThemeManager.get_dialog_style(is_dark_theme))
            
            # 创建布局
            layout = QVBoxLayout(dialog)
            layout.setContentsMargins(25, 25, 25, 25)
            layout.setSpacing(15)
            
            # 提示标签
            label = QLabel("加载到哪里？")
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
            
            # 使用ThemeManager获取按钮样式
            button_style = ThemeManager.get_dialog_button_style(is_dark_theme)
            
            # 创建按钮
            btn_before = QPushButton("前时相位置")
            btn_after = QPushButton("后时相位置")
            btn_cancel = QPushButton("不加载")
            
            # 设置按钮样式
            btn_before.setStyleSheet(button_style)
            btn_after.setStyleSheet(button_style)
            btn_cancel.setStyleSheet(button_style)
            
            # 添加按钮到布局
            button_layout.addStretch()
            button_layout.addWidget(btn_before)
            button_layout.addWidget(btn_after)
            button_layout.addWidget(btn_cancel)
            button_layout.addStretch()
            
            # 将按钮容器添加到主布局
            layout.addWidget(button_container)
            
            # 连接按钮事件
            btn_before.clicked.connect(lambda: self._display_standardized_image(str(output_path), True, dialog))
            btn_after.clicked.connect(lambda: self._display_standardized_image(str(output_path), False, dialog))
            btn_cancel.clicked.connect(dialog.reject)
            
            # 显示对话框
            dialog.exec()
            
            return True
        except Exception as e:
            self.navigation_functions.log_message(f"图像标准化失败: {str(e)}")
            import traceback
            self.navigation_functions.log_message(traceback.format_exc())
            return False
            
    def _display_standardized_image(self, image_path, is_before, dialog):
        """显示标准化后的图像
        
        Args:
            image_path: 图像路径
            is_before: 是否在前时相区域显示
            dialog: 对话框实例，用于关闭
        """
        if is_before:
            self.navigation_functions.file_path = image_path
        else:
            self.navigation_functions.file_path_after = image_path
            
        # 更新显示
        self.navigation_functions.update_image_display()
        self.navigation_functions.log_message(f"已将标准化图像显示在{'前' if is_before else '后'}时相区域")
        
        # 关闭对话框
        dialog.accept()
