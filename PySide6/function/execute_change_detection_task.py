import os
from PySide6.QtGui import QPixmap

class ExecuteChangeDetectionTask:
    def __init__(self, navigation_functions, label_output):
        """
        初始化执行变化检测任务模块
        
        Args:
            navigation_functions: NavigationFunctions实例，用于日志记录和图像显示
            label_output: 用于显示解译结果的标签
        """
        self.navigation_functions = navigation_functions
        self.label_output = label_output
        self.result_image_path = None
    
    def on_begin_clicked(self):
        """开始执行变化检测任务"""
        try:
            # 检查是否已导入前后时相影像
            if not self.navigation_functions.file_path or not self.navigation_functions.file_path_after:
                self.navigation_functions.log_message("请先导入前后时相影像")
                self._show_styled_message_box("检测失败", "没有可用影像，请先导入前后时相影像", "warning")
                return
            
            # 获取前后时相影像路径
            before_image_path = self.navigation_functions.file_path
            after_image_path = self.navigation_functions.file_path_after
            
            # 设置统一的输出路径
            output_dir = "D:/VS_WORKBASE/PySide6/遥感影像变化检测系统V2.0/output_image"
            os.makedirs(output_dir, exist_ok=True)
            
            self.navigation_functions.log_message(f"执行变化检测: {before_image_path} 与 {after_image_path}")
            self.navigation_functions.log_message(f"结果将保存到: {output_dir}")
            
            # 在这里添加模型推理代码
            # ...
            
            # 模拟生成结果图像路径（实际应由模型生成）
            import time
            timestamp = int(time.time())
            result_filename = f"change_detection_result_{timestamp}.png"
            result_image_path = os.path.join(output_dir, result_filename)
            
            # TODO: 这里应该有实际的模型推理代码，将结果保存到result_image_path
            
            # 假设模型推理完成并生成了结果
            self.navigation_functions.log_message(f"检测完成，结果保存为: {result_image_path}")
            
            # 缓存结果路径以供导出
            self.result_image_path = result_image_path
            
            # 直接显示结果到解译窗口，无需确认
            self.display_change_detection_result(result_image_path)
            
        except Exception as e:
            self.navigation_functions.log_message(f"执行变化检测时出错: {str(e)}")
            import traceback
            self.navigation_functions.log_message(traceback.format_exc())
            self._show_styled_message_box("检测失败", f"执行变化检测时出错: {str(e)}", "critical")
    
    def display_change_detection_result(self, result_image_path, stats=None):
        """显示变化检测结果
        
        Args:
            result_image_path: 结果图像路径
            stats: 变化统计数据
        """
        try:
            # 加载结果图像
            pixmap = QPixmap(result_image_path)
            if pixmap.isNull():
                self.navigation_functions.log_message(f"无法加载结果图像: {result_image_path}")
                return
            
            # 显示在解译结果区域
            self.label_output.set_pixmap(pixmap)
            self.navigation_functions.log_message("检测结果已加载到解译结果窗口")
            
            # 保存结果路径以供后续导出
            self.result_image_path = result_image_path
            
        except Exception as e:
            self.navigation_functions.log_message(f"显示变化检测结果时出错: {str(e)}")
            import traceback
            self.navigation_functions.log_message(traceback.format_exc())
    
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

class ChangeDetectionModel:
    """变化检测模型类"""
    def __init__(self):
        self.model_type = "BIT-CD"
        self.model_version = "1.0"
        # 其他模型初始化代码...
        
    # 其他模型方法...
