import os
import shutil
from pathlib import Path
from PySide6.QtWidgets import QFileDialog, QMessageBox

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
            title: 标题
            text: 消息内容
            icon_type: 图标类型，可选值为information, warning, critical, question
        """
        from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
        from PySide6.QtGui import QIcon, QPixmap
        from PySide6.QtCore import Qt
        
        # 创建自定义对话框
        dialog = QDialog()
        dialog.setWindowTitle(title)
        dialog.setFixedSize(280, 120)  # 更小的尺寸
        
        # 确定主题
        is_dark_theme = hasattr(self.navigation_functions, 'is_dark_theme') and self.navigation_functions.is_dark_theme
        
        # 设置对话框样式
        if is_dark_theme:
            dialog.setStyleSheet("""
                QDialog {
                    background-color: #202124;
                    border: 1px solid #444a5a;
                }
                QLabel {
                    color: #f7f7f8;
                    font-size: 14px;
                    font-family: "Microsoft YaHei UI";
                }
                QPushButton {
                    background-color: #444a5a;
                    color: white;
                    border-radius: 3px;
                    padding: 3px 10px;
                    font-size: 14px;
                    font-family: "Microsoft YaHei UI";
                    min-width: 50px;
                }
                QPushButton:hover {
                    background-color: #5d6576;
                }
                QPushButton:pressed {
                    background-color: #353b4a;
                }
            """)
        else:
            dialog.setStyleSheet("""
                QDialog {
                    background-color: #ffffff;
                    border: 1px solid #e6e6e6;
                }
                QLabel {
                    color: #333333;
                    font-size: 14px;
                    font-family: "Microsoft YaHei UI";
                }
                QPushButton {
                    background-color: #f0f0f2;
                    color: #333333;
                    border: 1px solid #e6e6e6;
                    border-radius: 3px;
                    padding: 3px 10px;
                    font-size: 14px;
                    font-family: "Microsoft YaHei UI";
                    min-width: 50px;
                }
                QPushButton:hover {
                    background-color: #e6e6e9;
                }
                QPushButton:pressed {
                    background-color: #d9d9dc;
                }
            """)
        
        # 创建布局
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # 创建消息内容区域
        content_layout = QHBoxLayout()
        
        # 添加图标
        icon_label = QLabel()
        icon_size = 24
        
        # 根据图标类型设置图标
        if icon_type == "information":
            icon_pixmap = QPixmap(":/icons/info.png")  # 使用应用内置图标或者替换为您的图标路径
        elif icon_type == "warning":
            icon_pixmap = QPixmap(":/icons/warning.png")
        elif icon_type == "critical":
            icon_pixmap = QPixmap(":/icons/error.png")
        elif icon_type == "question":
            icon_pixmap = QPixmap(":/icons/question.png")
        
        # 如果没有图标资源，显示一个黄色的警告三角图标（简单的模拟）
        if icon_pixmap.isNull():
            # 创建一个简单的文本替代图标
            icon_label.setText("⚠")
            icon_label.setStyleSheet("font-size: 28px; color: #FFD700;")
        else:
            icon_label.setPixmap(icon_pixmap.scaled(icon_size, icon_size, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        
        content_layout.addWidget(icon_label)
        content_layout.addSpacing(10)
        
        # 添加文本
        text_label = QLabel(text)
        text_label.setWordWrap(True)
        text_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        content_layout.addWidget(text_label, 1)
        
        layout.addLayout(content_layout)
        
        # 创建按钮区域
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        # 添加确定按钮
        ok_button = QPushButton("确定")
        ok_button.setFixedWidth(80)
        ok_button.clicked.connect(dialog.accept)
        button_layout.addWidget(ok_button)
        
        layout.addLayout(button_layout)
        
        # 显示对话框
        return dialog.exec_() 