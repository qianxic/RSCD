import os
import sys
import shutil
from pathlib import Path

# 添加项目根目录到Python路径
# sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from PySide6.QtWidgets import QFileDialog, QMessageBox, QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QWidget
from PySide6.QtCore import Qt
# 从theme_utils导入ThemeManager
from .theme_utils import ThemeManager

class ImageExport:
    def __init__(self, navigation_functions):
        """
        初始化图像导出模块
        
        Args:
            navigation_functions: NavigationFunctions实例，用于日志记录和图像显示
        """
        self.navigation_functions = navigation_functions
        self.temp_output_dir = "D:/VS_WORKBASE/PySide6/遥感影像变化检测系统V2.0/output_image"
    
    def export_result_image(self, result_image_path=None):
        """
        导出结果图像到用户选择的位置
        
        Args:
            result_image_path: 结果图像路径，如果为None则尝试从变化检测模块获取
        """
        try:
            # 确定需要导出的图像路径
            if result_image_path is None:
                # 尝试从主程序的变化检测模块获取结果路径
                if hasattr(self.navigation_functions, 'main_window') and \
                   hasattr(self.navigation_functions.main_window, 'execute_change_detection') and \
                   hasattr(self.navigation_functions.main_window.execute_change_detection, 'result_image_path'):
                    result_image_path = self.navigation_functions.main_window.execute_change_detection.result_image_path
            
            if not result_image_path or not os.path.exists(result_image_path):
                self.navigation_functions.log_message("没有可导出的结果图像")
                self._show_styled_message_box("导出失败", "没有可导出的结果图像，请先执行变化检测。", "warning")
                return False
                
            # 获取原始文件名
            original_filename = os.path.basename(result_image_path)
            
            # 弹出文件保存对话框
            options = QFileDialog.Options()
            save_path, _ = QFileDialog.getSaveFileName(
                None,
                "保存检测结果",
                original_filename,
                "图像文件 (*.png *.jpg *.jpeg *.tif *.tiff);;所有文件 (*)",
                options=options
            )
            
            if not save_path:
                self.navigation_functions.log_message("用户取消导出操作")
                return False
                
            # 确保目标目录存在
            target_dir = os.path.dirname(save_path)
            os.makedirs(target_dir, exist_ok=True)
            
            # 移动（剪切）文件到新位置
            shutil.move(result_image_path, save_path)
            self.navigation_functions.log_message(f"结果图像已导出到: {save_path}")
            
            # 检查临时目录是否为空，如果为空则删除
            if os.path.exists(self.temp_output_dir) and len(os.listdir(self.temp_output_dir)) == 0:
                try:
                    os.rmdir(self.temp_output_dir)
                    self.navigation_functions.log_message(f"已删除临时目录: {self.temp_output_dir}")
                except Exception as e:
                    self.navigation_functions.log_message(f"尝试删除临时目录时出错: {str(e)}")
            
            # 显示成功消息
            self._show_styled_message_box("导出成功", f"结果图像已成功导出到:\n{save_path}", "information")
            return True
            
        except Exception as e:
            self.navigation_functions.log_message(f"导出图像时出错: {str(e)}")
            import traceback
            self.navigation_functions.log_message(traceback.format_exc())
            self._show_styled_message_box("导出失败", f"导出图像时发生错误:\n{str(e)}", "critical")
            return False

    def _show_styled_message_box(self, title, text, icon_type="information"):
        """显示符合应用主题的消息框
        
        Args:
            title: 对话框标题
            text: 消息内容
            icon_type: 图标类型，可选值：information, warning, error, success
        """
        # 检查是否使用深色主题
        is_dark_theme = hasattr(self.navigation_functions, 'is_dark_theme') and self.navigation_functions.is_dark_theme
        
        # 创建自定义对话框
        dialog = QDialog()
        dialog.setWindowTitle(title)
        dialog.setFixedSize(400, 150)
        
        # 使用ThemeManager设置对话框样式
        dialog.setStyleSheet(ThemeManager.get_dialog_style(is_dark_theme))
        
        # 创建布局
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # 创建消息容器
        message_container = QWidget()
        message_layout = QHBoxLayout(message_container)
        message_layout.setContentsMargins(0, 0, 0, 0)
        message_layout.setSpacing(15)
        
        # 创建图标标签
        icon_label = QLabel()
        
        # 设置字体图标，使用Unicode字符
        if icon_type == "warning":
            icon_label.setText("⚠️")
        elif icon_type == "error":
            icon_label.setText("❌")
        elif icon_type == "success":
            icon_label.setText("✅")
        else:  # information
            icon_label.setText("ℹ️")
            
        # 使用ThemeManager设置图标样式
        icon_label.setStyleSheet(ThemeManager.get_icon_style(icon_type, is_dark_theme))
        
        # 创建文本标签
        text_label = QLabel(text)
        text_label.setWordWrap(True)
        text_label.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
        text_label.setStyleSheet(ThemeManager.get_dialog_label_style(is_dark_theme))
        
        # 添加图标和文本到消息布局
        message_layout.addWidget(icon_label)
        message_layout.addWidget(text_label, 1)  # 文本标签扩展
        
        # 创建按钮容器
        button_container = QWidget()
        button_layout = QHBoxLayout(button_container)
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.setSpacing(10)
        
        # 创建确定按钮
        ok_button = QPushButton("确定")
        ok_button.setFixedWidth(100)
        ok_button.setStyleSheet(ThemeManager.get_dialog_button_style(is_dark_theme))
        ok_button.clicked.connect(dialog.accept)
        
        # 添加按钮到布局
        button_layout.addStretch()
        button_layout.addWidget(ok_button)
        
        # 添加组件到主布局
        layout.addWidget(message_container)
        layout.addStretch()
        layout.addWidget(button_container)
        
        # 显示对话框
        dialog.exec() 