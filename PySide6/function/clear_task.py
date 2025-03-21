import os
import glob
import logging
from PySide6.QtWidgets import QLabel

class ClearTask:
    def __init__(self, navigation_functions, label_before, label_after, label_output, text_log):
        """
        初始化清除任务模块
        
        Args:
            navigation_functions: NavigationFunctions实例，用于日志记录和图像显示
            label_before: 前时相影像标签
            label_after: 后时相影像标签
            label_output: 输出结果标签
            text_log: 日志文本区域
        """
        self.navigation_functions = navigation_functions
        self.label_before = label_before
        self.label_after = label_after
        self.label_output = label_output
        self.text_log = text_log
        
    def clear_interface(self):
        """清除界面显示的所有内容"""
        try:
            # 清除图像显示
            self.label_before.clear()
            if isinstance(self.label_before, QLabel):
                self.label_before.setText("前时相影像")
                
            self.label_after.clear()
            if isinstance(self.label_after, QLabel):
                self.label_after.setText("后时相影像")
                
            self.label_output.clear()
            if isinstance(self.label_output, QLabel):
                self.label_output.setText("解译结果")
            
            # 清除日志
            self.text_log.clear()
            
            # 重置导航功能类的文件路径和图像信息
            self.navigation_functions.file_path = None
            self.navigation_functions.file_path_after = None
            # 重置原始图像尺寸信息
            self.navigation_functions.before_image_original_size = None
            self.navigation_functions.after_image_original_size = None
            # 重置其他相关文件路径
            self.navigation_functions.result_image_path = None
            self.navigation_functions.mask_image_path = None 
            self.navigation_functions.boundary_image_path = None
            # 如果有其他存储的临时文件路径，也应该在这里清除
            
            # 删除临时保存的结果文件
            temp_files = ['result_image_path', 'mask_image_path', 'boundary_image_path']
            for attr in temp_files:
                file_path = getattr(self.navigation_functions, attr, None)
                if file_path and os.path.exists(file_path):
                    try:
                        os.remove(file_path)
                        logging.info(f"已删除临时文件: {file_path}")
                    except Exception as e:
                        logging.warning(f"删除临时文件失败: {file_path}, 错误: {str(e)}")
            
            # 清理目录中所有临时缓存文件
            self.clean_temp_files()
            
            # 添加清除完成的消息到日志
            self.navigation_functions.log_message("任务已退出，所有文件路径和临时文件已清理")
            
        except Exception as e:
            self.navigation_functions.log_message(f"清除界面时出错: {str(e)}")
            import traceback
            self.navigation_functions.log_message(traceback.format_exc())
    
    def clean_temp_files(self):
        """清理所有临时缓存文件"""
        try:
            # 清理变化检测结果临时文件
            temp_patterns = [
                "change_detection_result_*.png",
                "change_detection_mask_*.png",
                "change_detection_boundary_*.png"
            ]
            
            files_removed = 0
            
            for pattern in temp_patterns:
                for file_path in glob.glob(pattern):
                    try:
                        os.remove(file_path)
                        logging.info(f"已清理临时文件: {file_path}")
                        files_removed += 1
                    except Exception as e:
                        logging.warning(f"清理临时文件失败: {file_path}, 错误: {str(e)}")
            
            # 清理__pycache__目录中的缓存文件
            pycache_dirs = ["__pycache__", "*/__pycache__"]
            for cache_dir_pattern in pycache_dirs:
                for cache_dir in glob.glob(cache_dir_pattern):
                    if os.path.isdir(cache_dir):
                        # 只清理目录中的文件，不删除目录本身
                        for cache_file in glob.glob(f"{cache_dir}/*.pyc") + glob.glob(f"{cache_dir}/*.pyo"):
                            try:
                                os.remove(cache_file)
                                logging.info(f"已清理Python缓存文件: {cache_file}")
                                files_removed += 1
                            except Exception as e:
                                logging.warning(f"清理缓存文件失败: {cache_file}, 错误: {str(e)}")
            
            if files_removed > 0:
                logging.info(f"共清理 {files_removed} 个临时文件")
                self.navigation_functions.log_message(f"已清理 {files_removed} 个临时文件")
            else:
                logging.info("没有临时文件需要清理")
                
        except Exception as e:
            logging.error(f"清理临时文件过程中发生错误: {str(e)}")
            self.navigation_functions.log_message(f"清理临时文件时出错: {str(e)}")
