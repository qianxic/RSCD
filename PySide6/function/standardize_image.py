import os
import cv2
from PySide6.QtWidgets import QMessageBox
import numpy as np

class StandardizeImage:
    def __init__(self, navigation_functions):
        """
        初始化图像标准化模块
        
        Args:
            navigation_functions: NavigationFunctions实例，用于日志记录和图像显示
        """
        self.navigation_functions = navigation_functions
    
    def standardize_image(self):
        """
        将图像标准化为256x256像素大小
        """
        try:
            # 检查是否已选择图像
            if not self.navigation_functions.file_path:
                self.navigation_functions.log_message("请先导入图像")
                return
            
            # 获取图像路径
            file_path = self.navigation_functions.file_path
            
            # 使用OpenCV读取图像
            try:
                image = cv2.imread(file_path)
                if image is None:
                    # 尝试使用中文路径兼容的方式读取
                    image = cv2.imdecode(np.fromfile(file_path, dtype=np.uint8), cv2.IMREAD_COLOR)
                    if image is None:
                        self.navigation_functions.log_message(f"无法读取图像: {file_path}")
                        return
            except Exception as e:
                self.navigation_functions.log_message(f"读取图像时出错: {str(e)}")
                return
            
            # 标准化到256x256
            resized_image = cv2.resize(image, (256, 256), interpolation=cv2.INTER_AREA)
            
            # 构建输出文件名
            filename, ext = os.path.splitext(os.path.basename(file_path))
            output_filename = f"{filename}_256x256{ext}"
            output_dir = os.path.dirname(file_path)
            output_path = os.path.join(output_dir, output_filename)
            
            # 保存标准化图像
            try:
                # 使用针对中文路径的保存方法
                cv2.imencode(ext, resized_image)[1].tofile(output_path)
                self.navigation_functions.log_message(f"图像已标准化并保存为: {output_path}")
            except Exception as e:
                self.navigation_functions.log_message(f"保存标准化图像时出错: {str(e)}")
                # 尝试使用不同的保存路径
                try:
                    alt_output_path = os.path.join(os.getcwd(), output_filename)
                    cv2.imencode(ext, resized_image)[1].tofile(alt_output_path)
                    self.navigation_functions.log_message(f"图像已标准化并保存为: {alt_output_path}")
                    output_path = alt_output_path
                except Exception as e:
                    self.navigation_functions.log_message(f"保存到备用路径时出错: {str(e)}")
                    return
            
            # 更新文件路径
            self.navigation_functions.file_path = output_path
            
            # 更新显示
            self.navigation_functions.update_image_display()
            
            # 显示成功消息
            QMessageBox.information(None, "标准化完成", f"图像已标准化为256x256像素并保存到:\n{output_path}")
            
        except Exception as e:
            self.navigation_functions.log_message(f"标准化图像时出错: {str(e)}")
            import traceback
            self.navigation_functions.log_message(traceback.format_exc()) 