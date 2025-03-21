import os
import sys
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
        self.cd_model = None
        self.result_image_path = None
    
    def on_begin_clicked(self):
        """开始执行变化检测任务"""
        try:
            
            # 检查是否已导入前后时相影像
            if not self.navigation_functions.file_path or not self.navigation_functions.file_path_after:
                self.navigation_functions.log_message("请先导入前后时相影像")
                return
            
            # 自动加载模型（如果尚未加载）
            if self.cd_model is None:
                self.navigation_functions.log_message("正在自动加载模型...")
                try:
                    self.cd_model = ChangeDetectionModel()
                    self.navigation_functions.log_message(f"模型加载成功: {self.cd_model.model_type} (版本 {self.cd_model.model_version})")
                except Exception as e:
                    self.navigation_functions.log_message(f"模型加载失败: {str(e)}")
                    return
                self.navigation_functions.log_message("正在执行变化检测...")
            
            # 读取前后时相影像
            before_image_path = self.navigation_functions.file_path
            after_image_path = self.navigation_functions.file_path_after
            
            # 设置输出目录
            output_dir = 'inferrence/test_simple_results'
            os.makedirs(output_dir, exist_ok=True)
            
            self.navigation_functions.log_message(f"执行变化检测: {before_image_path} 与 {after_image_path}")
            self.navigation_functions.log_message(f"结果将保存到: {output_dir}")
            
            # 导入detect_change函数
            try:
                # 添加项目根目录到sys.path，确保可以导入inferrence模块
                project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
                if project_root not in sys.path:
                    sys.path.append(project_root)
                    self.navigation_functions.log_message(f"添加项目根目录到sys.path: {project_root}")
                
                # 导入并使用detect_change函数
                from inferrence.merged_bit_cd import detect_change
                
                # 使用BIT模型进行变化检测
                # 添加参数以确保正确处理裁剪后的图像
                success = detect_change(
                    before_image_path, 
                    after_image_path, 
                    output_dir, 
                    verbose=True,
                    use_original_size=True,  # 使用原始尺寸
                    threshold=0.5  # 调整阈值以获得更好的结果
                )
                
                if success:
                    self.navigation_functions.log_message("检测成功")
                    
                    # 查找生成的结果文件
                    base_name = os.path.basename(before_image_path).split('.')[0]
                    # 对于BIT模型，结果文件名可能不同
                    result_files = os.listdir(output_dir)
                    result_image_path = None
                    
                    # 查找包含"change"或图像基础名称的结果文件
                    for file in result_files:
                        if file.endswith('.png') and ('change' in file.lower() or 'vis' in file.lower()):
                            result_image_path = os.path.join(output_dir, file)
                            break
                    
                    if result_image_path and os.path.exists(result_image_path):
                        # 保存结果文件路径供导出使用
                        self.result_image_path = result_image_path
                        
                        # 创建一个简单的结果字典
                        result = {
                            'result_color_path': result_image_path,
                            'stats': {
                                'processing_time': '使用BIT模型完成处理',
                                'change_percentage': '请查看结果图像'
                            }
                        }
                        
                        # 显示变化检测结果
                        self.display_change_detection_result(result_image_path, result['stats'])
                    else:
                        self.navigation_functions.log_message(f"警告: 未找到结果文件，请直接查看输出目录: {output_dir}")
                else:
                    self.navigation_functions.log_message("变化检测失败!")
            except Exception as e:
                self.navigation_functions.log_message(f"执行变化检测时出错: {str(e)}")
                import traceback
                self.navigation_functions.log_message(traceback.format_exc())
            
        except Exception as e:
            self.navigation_functions.log_message(f"执行变化检测时出错: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def display_change_detection_result(self, result_image_path, stats=None):
        """显示变化检测结果
        
        参数:
        result_image_path: 结果图像路径
        stats: 变化统计数据
        """
        try:
            # 直接加载结果图像
            pixmap = QPixmap(result_image_path)
            
            if pixmap.isNull():
                self.navigation_functions.log_message(f"无法加载结果图像: {result_image_path}")
                return
                
            # 显示在解译结果区域
            self.label_output.set_pixmap(pixmap)
            
            # 添加更详细的成功消息
            self.navigation_functions.log_message("检测成功")
            self.navigation_functions.log_message(f"结果图像已保存到: {result_image_path}")
            
            # 如果提供了统计数据，则显示
            if stats:
                for key, value in stats.items():
                    self.navigation_functions.log_message(f"{key}: {value}")
                
        except Exception as e:
            self.navigation_functions.log_message(f"显示变化检测结果时出错: {str(e)}")
            import traceback
            self.navigation_functions.log_message(traceback.format_exc())


class ChangeDetectionModel:
    """变化检测模型类"""
    def __init__(self):
        self.model_type = "BIT-CD"
        self.model_version = "1.0"
        # 其他模型初始化代码...
        
    # 其他模型方法...
