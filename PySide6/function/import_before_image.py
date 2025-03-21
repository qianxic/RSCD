import os
from PySide6.QtWidgets import QFileDialog

class ImportBeforeImage:
    def __init__(self, navigation_functions):
        """
        初始化导入前时相影像模块
        
        Args:
            navigation_functions: NavigationFunctions实例，用于日志记录和图像显示
        """
        self.navigation_functions = navigation_functions
    
    def on_import_clicked(self):
        """导入前时相影像"""
        options = QFileDialog.Options()
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getOpenFileName(
            None,
            "选择前时相影像",
            "",
            "图像文件 (*.png *.jpg *.jpeg *.tif *.tiff);;所有文件 (*)",
            options=options
        )
        
        if file_path:
            self.navigation_functions.log_message(f"已选择前时相影像: {file_path}")
            
            # 保存图像到指定目录
            saved_path = self.save_image_to_dir(file_path, "前时相")
            if saved_path:
                self.navigation_functions.file_path = saved_path
            else:
                # 如果保存失败，仍然使用原始路径
                self.navigation_functions.file_path = file_path
            
            # 更新图像显示
            self.navigation_functions.update_image_display()
            return self.navigation_functions.file_path
            
        return None
    
    def save_image_to_dir(self, file_path, prefix):
        """
        保存图像到指定目录
        
        Args:
            file_path: 原始图像路径
            prefix: 路径前缀（如"前时相"或"后时相"）
            
        Returns:
            str: 保存后的图像路径，如果保存失败则返回None
        """
        try:
            self.navigation_functions.log_message(f"使用原始图像路径: {file_path}")
            return file_path
            
        except Exception as e:
            self.navigation_functions.log_message(f"处理图像路径时出错: {str(e)}")
            import traceback
            self.navigation_functions.log_message(traceback.format_exc())
            return None 