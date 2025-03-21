import os
import cv2
import numpy as np
from pathlib import Path
from PySide6.QtWidgets import QFileDialog, QInputDialog, QMessageBox
from osgeo import gdal
import traceback

class GridCrop:
    def __init__(self, navigation_functions):
        """
        初始化网格裁剪模块
        
        Args:
            navigation_functions: NavigationFunctions实例，用于日志记录和图像显示
        """
        self.navigation_functions = navigation_functions
        self.last_generated_file = None
    
    def crop_image(self):
        """
        将图像裁剪为网格
        返回生成的文件列表
        """
        try:
            # 选择要裁剪的图像文件
            options = QFileDialog.Options()
            file_dialog = QFileDialog()
            file_path, _ = file_dialog.getOpenFileName(
                None,
                "选择要裁剪的图像",
                "",
                "图像文件 (*.png *.jpg *.jpeg *.tif *.tiff);;所有文件 (*)",
                options=options
            )
            
            if not file_path:
                self.navigation_functions.log_message("未选择图像文件")
                return []
            
            # 获取网格大小
            grid_size, ok = QInputDialog.getInt(None, "网格大小", "请输入网格大小 (2-10):", 2, 2, 10)
            if not ok:
                self.navigation_functions.log_message("未指定网格大小")
                return []
            
            # 选择保存目录
            save_dir = QFileDialog.getExistingDirectory(None, "选择保存目录")
            if not save_dir:
                self.navigation_functions.log_message("未选择保存目录")
                return []
            
            self.navigation_functions.log_message(f"正在裁剪图像: {file_path}")
            self.navigation_functions.log_message(f"网格大小: {grid_size} x {grid_size}")
            self.navigation_functions.log_message(f"保存位置: {save_dir}")
            
            # 检查文件类型
            is_geotiff = file_path.lower().endswith(('.tif', '.tiff'))
            generated_files = []
            
            # 尝试使用GDAL裁剪GeoTIFF文件
            if is_geotiff:
                try:
                    self.navigation_functions.log_message("检测到GeoTIFF文件，尝试使用GDAL进行裁剪...")
                    generated_files = self._crop_geotiff_grid(file_path, save_dir, grid_size)
                except Exception as e:
                    self.navigation_functions.log_message(f"使用GDAL裁剪失败，将尝试使用OpenCV: {str(e)}")
                    # 回退到OpenCV
                    generated_files = self._crop_image_grid_cv2(file_path, save_dir, grid_size)
            else:
                # 使用OpenCV裁剪普通图像
                generated_files = self._crop_image_grid_cv2(file_path, save_dir, grid_size)
            
            # 记录裁剪完成的消息和生成的文件数量
            if generated_files:
                self.navigation_functions.log_message(f"裁剪完成，共生成 {len(generated_files)} 个文件")
                self.last_generated_file = generated_files[0]  # 保存第一个生成的文件路径
                
                # 询问用户是否查看裁剪后的图像
                reply = QMessageBox.question(None, "裁剪完成", 
                                             f"裁剪完成，是否显示裁剪后的图像？\n生成了 {len(generated_files)} 个文件。",
                                             QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
                
                if reply == QMessageBox.Yes and generated_files:
                    # 更新文件路径并更新显示
                    self.navigation_functions.file_path = generated_files[0]
                    self.navigation_functions.update_image_display()
                    
            else:
                self.navigation_functions.log_message("裁剪过程中未生成任何文件")
            
            return generated_files
            
        except Exception as e:
            self.navigation_functions.log_message(f"裁剪图像时出错: {str(e)}")
            traceback.print_exc()
            return []
    
    def _crop_image_grid_cv2(self, image_path, save_dir, grid_size):
        """
        使用OpenCV将图像裁剪为网格
        
        参数:
        image_path: 图像路径
        save_dir: 保存目录
        grid_size: 网格大小
        
        返回:
        生成的文件路径列表
        """
        generated_files = []
        
        try:
            # 读取图像
            try:
                img = cv2.imread(image_path)
                if img is None:
                    # 尝试使用PIL读取，避免中文路径问题
                    from PIL import Image
                    img_pil = Image.open(image_path)
                    img = np.array(img_pil)
                    if img.shape[2] == 4:  # RGBA
                        img = img[:, :, :3]
                    img = img[:, :, ::-1]  # RGB to BGR
            except Exception as e:
                self.navigation_functions.log_message(f"无法读取图像: {str(e)}")
                return generated_files
            
            if img is None:
                self.navigation_functions.log_message(f"无法读取图像: {image_path}")
                return generated_files
            
            # 获取图像大小
            height, width = img.shape[:2]
            self.navigation_functions.log_message(f"图像尺寸: {width}x{height}")
            
            # 计算每个网格的大小
            cell_width = width // grid_size
            cell_height = height // grid_size
            self.navigation_functions.log_message(f"网格尺寸: {cell_width}x{cell_height}")
            
            # 创建保存目录（如果不存在）
            os.makedirs(save_dir, exist_ok=True)
            
            # 获取基本文件名（不含扩展名）和扩展名
            base_name = os.path.basename(image_path)
            file_name, ext = os.path.splitext(base_name)
            
            # 裁剪并保存每个网格
            for i in range(grid_size):
                for j in range(grid_size):
                    # 计算裁剪区域
                    x = j * cell_width
                    y = i * cell_height
                    # 确保不会超出图像边界
                    crop_width = min(cell_width, width - x)
                    crop_height = min(cell_height, height - y)
                    
                    if crop_width <= 0 or crop_height <= 0:
                        continue
                    
                    # 裁剪图像
                    crop = img[y:y+crop_height, x:x+crop_width]
                    
                    # 构建输出文件名
                    output_filename = f"{file_name}_grid_{i+1}_{j+1}{ext}"
                    output_path = Path(save_dir) / output_filename
                    
                    try:
                        # 使用imencode和tofile处理中文路径
                        is_success, im_buf_arr = cv2.imencode(ext, crop)
                        if is_success:
                            im_buf_arr.tofile(str(output_path))
                            self.navigation_functions.log_message(f"已保存: {output_path}")
                            generated_files.append(str(output_path))
                        else:
                            self.navigation_functions.log_message(f"编码图像失败: {output_path}")
                    except Exception as e:
                        self.navigation_functions.log_message(f"保存图像失败: {str(e)}")
            
            return generated_files
            
        except Exception as e:
            self.navigation_functions.log_message(f"使用OpenCV裁剪图像时出错: {str(e)}")
            traceback.print_exc()
            return generated_files
    
    def _crop_geotiff_grid(self, geotiff_path, save_dir, grid_size):
        """
        使用GDAL将GeoTIFF图像裁剪为网格
        
        参数:
        geotiff_path: GeoTIFF文件路径
        save_dir: 保存目录
        grid_size: 网格大小
        
        返回:
        生成的文件路径列表
        """
        generated_files = []
        
        try:
            self.navigation_functions.log_message(f"开始裁剪GeoTIFF: {geotiff_path}")
            
            # 打开GeoTIFF文件
            ds = gdal.Open(geotiff_path)
            if ds is None:
                self.navigation_functions.log_message(f"无法打开GeoTIFF文件: {geotiff_path}")
                return generated_files
            
            # 获取图像尺寸和波段数
            width = ds.RasterXSize
            height = ds.RasterYSize
            bands_count = ds.RasterCount
            
            # 获取地理变换信息
            geotransform = ds.GetGeoTransform()
            self.navigation_functions.log_message(f"图像尺寸: {width}x{height}, 波段数: {bands_count}")
            
            # 计算每个网格的大小
            cell_width = width // grid_size
            cell_height = height // grid_size
            self.navigation_functions.log_message(f"网格尺寸: {cell_width}x{cell_height}")
            
            # 创建保存目录（如果不存在）
            os.makedirs(save_dir, exist_ok=True)
            
            # 获取基本文件名（不含扩展名）和扩展名
            base_name = os.path.basename(geotiff_path)
            file_name, ext = os.path.splitext(base_name)
            
            # 裁剪并保存每个网格
            for i in range(grid_size):
                for j in range(grid_size):
                    # 计算裁剪区域
                    x = j * cell_width
                    y = i * cell_height
                    # 确保不会超出图像边界
                    crop_width = min(cell_width, width - x)
                    crop_height = min(cell_height, height - y)
                    
                    if crop_width <= 0 or crop_height <= 0:
                        continue
                    
                    try:
                        # 构建输出文件名
                        output_filename = f"{file_name}_grid_{i+1}_{j+1}{ext}"
                        output_path = os.path.join(save_dir, output_filename)
                        
                        # 使用GDAL的Translate方法裁剪并保存
                        gdal.Translate(
                            output_path, 
                            ds, 
                            srcWin=[x, y, crop_width, crop_height],
                            options=gdal.TranslateOptions(format='GTiff')
                        )
                        
                        self.navigation_functions.log_message(f"已保存: {output_path}")
                        generated_files.append(output_path)
                    except Exception as e:
                        self.navigation_functions.log_message(f"裁剪和保存网格 ({i+1},{j+1}) 时出错: {str(e)}")
            
            # 关闭数据集
            ds = None
            return generated_files
            
        except Exception as e:
            self.navigation_functions.log_message(f"使用GDAL裁剪GeoTIFF时出错: {str(e)}")
            traceback.print_exc()
            return generated_files 