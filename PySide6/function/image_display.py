import os
import numpy as np
import logging
from pathlib import Path
from PIL import Image
from PySide6.QtGui import QPixmap, QImage
from PySide6.QtCore import Qt
import cv2

class ImageDisplay:
    def __init__(self, navigation_functions):
        """
        初始化图像显示模块
        
        Args:
            navigation_functions: NavigationFunctions实例，用于日志记录和图像显示
        """
        self.navigation_functions = navigation_functions
        
    def display_image(self, file_path, is_before=True):
        """
        显示图像
        
        Args:
            file_path: 图像文件路径
            is_before: 是否为前时相图像
        """
        try:
            # 优先使用GDAL处理GeoTIFF文件
            if file_path.lower().endswith(('.tif', '.tiff')):
                self.navigation_functions.log_message(f"检测到TIFF格式图像，使用GDAL进行处理...")
                
                try:
                    # 尝试使用GDAL读取并转换图像
                    from osgeo import gdal, osr
                    
                    # 注册所有的GDAL驱动
                    gdal.AllRegister()
                    
                    # 打开数据集
                    ds = gdal.Open(file_path, gdal.GA_ReadOnly)
                    if ds is None:
                        self.navigation_functions.log_message(f"无法使用GDAL打开文件: {file_path}")
                        raise Exception("GDAL无法打开文件")
                    
                    # 获取基本信息
                    width = ds.RasterXSize
                    height = ds.RasterYSize
                    bands = ds.RasterCount
                    
                    self.navigation_functions.log_message(f"TIFF文件信息: 宽度={width}, 高度={height}, 波段数={bands}")
                    
                    # 提取地理变换参数
                    geo_transform = ds.GetGeoTransform()
                    if geo_transform:
                        self.navigation_functions.log_message("地理变换参数:")
                        self.navigation_functions.log_message(f"  左上角X坐标: {geo_transform[0]}")
                        self.navigation_functions.log_message(f"  X方向分辨率: {geo_transform[1]}")
                        self.navigation_functions.log_message(f"  行旋转参数: {geo_transform[2]}")
                        self.navigation_functions.log_message(f"  左上角Y坐标: {geo_transform[3]}")
                        self.navigation_functions.log_message(f"  列旋转参数: {geo_transform[4]}")
                        self.navigation_functions.log_message(f"  Y方向分辨率: {geo_transform[5]}")
                        
                        # 计算四个角的坐标
                        minx = geo_transform[0]
                        maxy = geo_transform[3]
                        maxx = minx + width * geo_transform[1]
                        miny = maxy + height * geo_transform[5]  # 注意y方向分辨率通常是负值
                        
                        self.navigation_functions.log_message("图像四角坐标:")
                        self.navigation_functions.log_message(f"  左上角: ({minx}, {maxy})")
                        self.navigation_functions.log_message(f"  右上角: ({maxx}, {maxy})")
                        self.navigation_functions.log_message(f"  左下角: ({minx}, {miny})")
                        self.navigation_functions.log_message(f"  右下角: ({maxx}, {miny})")
                    
                    # 提取投影信息
                    projection = ds.GetProjection()
                    if projection:
                        self.navigation_functions.log_message("投影信息:")
                        srs = osr.SpatialReference()
                        srs.ImportFromWkt(projection)
                        
                        # 获取EPSG代码
                        srs.AutoIdentifyEPSG()
                        if srs.GetAuthorityCode(None):
                            self.navigation_functions.log_message(f"  EPSG代码: {srs.GetAuthorityCode(None)}")
                        
                        # 获取投影类型
                        if srs.IsProjected():
                            self.navigation_functions.log_message(f"  投影类型: 投影坐标系 ({srs.GetAttrValue('PROJCS', 0)})")
                            self.navigation_functions.log_message(f"  投影方法: {srs.GetAttrValue('PROJECTION', 0)}")
                            
                            # 获取投影的线性单位
                            linear_units = srs.GetLinearUnitsName()
                            if linear_units:
                                self.navigation_functions.log_message(f"  线性单位: {linear_units}")
                        
                        elif srs.IsGeographic():
                            self.navigation_functions.log_message(f"  投影类型: 地理坐标系 ({srs.GetAttrValue('GEOGCS', 0)})")
                            
                            # 获取角度单位
                            angular_units = srs.GetAngularUnitsName()
                            if angular_units:
                                self.navigation_functions.log_message(f"  角度单位: {angular_units}")
                        
                        # 获取椭球体信息
                        if srs.GetAttrValue('DATUM', 0):
                            self.navigation_functions.log_message(f"  基准面: {srs.GetAttrValue('DATUM', 0)}")
                        
                        if srs.GetAttrValue('SPHEROID', 0):
                            self.navigation_functions.log_message(f"  椭球体: {srs.GetAttrValue('SPHEROID', 0)}")
                            self.navigation_functions.log_message(f"  椭球体半长轴: {srs.GetAttrValue('SPHEROID', 1)} 米")
                            self.navigation_functions.log_message(f"  扁率倒数: {srs.GetAttrValue('SPHEROID', 2)}")
                    
                    # 读取图像数据
                    if bands == 1:  # 单波段（灰度）
                        band = ds.GetRasterBand(1)
                        img_array = band.ReadAsArray()
                        
                        # 获取统计信息
                        try:
                            min_val, max_val, mean_val, std_val = band.GetStatistics(True, True)
                            self.navigation_functions.log_message(f"波段统计: 最小值={min_val:.2f}, 最大值={max_val:.2f}, 平均值={mean_val:.2f}")
                        except:
                            # 如果无法获取统计信息，使用数据范围
                            min_val = img_array.min()
                            max_val = img_array.max()
                            self.navigation_functions.log_message(f"使用数据范围: 最小值={min_val}, 最大值={max_val}")
                        
                        # 对数据进行归一化处理，转换为8位整数
                        if img_array.dtype != np.uint8:
                            if max_val > min_val:  # 避免除以零
                                img_array = np.clip((img_array - min_val) * 255.0 / (max_val - min_val), 0, 255).astype(np.uint8)
                            else:
                                img_array = np.zeros((height, width), dtype=np.uint8)
                        
                        # 转换为RGB
                        img_array = cv2.cvtColor(img_array, cv2.COLOR_GRAY2RGB)
                        
                    elif bands >= 3:  # RGB或多光谱
                        # 读取前三个波段
                        red_band = ds.GetRasterBand(1)
                        green_band = ds.GetRasterBand(2)
                        blue_band = ds.GetRasterBand(3)
                        
                        # 分别读取每个波段
                        red_array = red_band.ReadAsArray()
                        green_array = green_band.ReadAsArray()
                        blue_array = blue_band.ReadAsArray()
                        
                        # 归一化函数
                        def normalize_band(band_array, band_obj):
                            try:
                                min_val, max_val, _, _ = band_obj.GetStatistics(True, True)
                            except:
                                min_val = band_array.min()
                                max_val = band_array.max()
                            
                            if band_array.dtype != np.uint8 and max_val > min_val:
                                return np.clip((band_array - min_val) * 255.0 / (max_val - min_val), 0, 255).astype(np.uint8)
                            elif band_array.dtype != np.uint8:
                                return np.zeros_like(band_array, dtype=np.uint8)
                            return band_array
                        
                        # 归一化每个波段
                        red_array = normalize_band(red_array, red_band)
                        green_array = normalize_band(green_array, green_band)
                        blue_array = normalize_band(blue_array, blue_band)
                        
                        # 组合为RGB图像
                        img_array = np.dstack((red_array, green_array, blue_array))
                        
                    else:  # 2波段等情况
                        # 处理2波段情况
                        band1 = ds.GetRasterBand(1)
                        band2 = ds.GetRasterBand(2)
                        
                        array1 = band1.ReadAsArray()
                        array2 = band2.ReadAsArray()
                        
                        # 归一化每个波段
                        def normalize(array):
                            min_val = array.min()
                            max_val = array.max()
                            if max_val > min_val:
                                return np.clip((array - min_val) * 255.0 / (max_val - min_val), 0, 255).astype(np.uint8)
                            return np.zeros_like(array, dtype=np.uint8)
                        
                        array1 = normalize(array1)
                        array2 = normalize(array2)
                        
                        # 创建一个RGB图像 (使用前两个波段和一个零波段)
                        img_array = np.dstack((array1, array2, np.zeros_like(array1)))
                    
                    # 清理GDAL资源
                    ds = None
                    
                    # 记录原始图像大小信息
                    orig_shape = img_array.shape
                    img_size_mb = (img_array.nbytes / (1024 * 1024))
                    self.navigation_functions.log_message(f"原始图像内存大小: {img_size_mb:.2f} MB")
                    
                    # 保存原始尺寸信息（用于后续可能的操作）
                    if is_before:
                        self.navigation_functions.before_image_original_size = (width, height)
                    else:
                        self.navigation_functions.after_image_original_size = (width, height)
                    
                    # 确保数据是连续的
                    if not img_array.flags['C_CONTIGUOUS']:
                        img_array = np.ascontiguousarray(img_array)
                    
                    # 将NumPy数组转换为QImage
                    height, width, channel = img_array.shape
                    bytes_per_line = 3 * width
                    q_img = QImage(img_array.data, width, height, bytes_per_line, QImage.Format_RGB888)
                    
                    # 转换为QPixmap
                    pixmap = QPixmap.fromImage(q_img)
                    self.navigation_functions.log_message(f"成功转换TIFF为可显示图像: {pixmap.width()}x{pixmap.height()}, 原始尺寸: {orig_shape}")
                    
                except Exception as e:
                    self.navigation_functions.log_message(f"使用GDAL处理TIFF失败: {str(e)}")
                    import traceback
                    self.navigation_functions.log_message(traceback.format_exc())
                    
                    # 回退到常规方法
                    self.navigation_functions.log_message("尝试使用常规方法加载图像...")
                    pixmap = QPixmap(file_path)
            else:
                # 非TIFF格式，使用常规方法
                pixmap = QPixmap(file_path)
            
            if not pixmap.isNull():
                # 根据是前时相还是后时相选择不同的标签
                label = self.navigation_functions.label_before if is_before else self.navigation_functions.label_after
                
                # 设置图像到可缩放标签
                if hasattr(label, 'set_pixmap'):
                    label.set_pixmap(pixmap)
                    self.navigation_functions.log_message(f"{'前' if is_before else '后'}时相影像加载成功 (放大图像后，双击可恢复原始视图)")
                else:
                    # 如果标签不是可缩放标签，则直接设置
                    label.setPixmap(pixmap.scaled(
                        label.width(), 
                        label.height(), 
                        aspectRatioMode=Qt.KeepAspectRatio
                    ))
                    self.navigation_functions.log_message(f"{'前' if is_before else '后'}时相影像加载成功")
            else:
                self.navigation_functions.log_message("无法加载图像：图像为空")
                # 排查原因
                if file_path.lower().endswith(('.tif', '.tiff')):
                    self.navigation_functions.log_message("提示:GeoTIFF文件可能需要安装GDAL和rasterio库才能正确显示")
                    self.navigation_functions.log_message("请确保已通过requirements.txt安装所有依赖")
                    
        except Exception as e:
            self.navigation_functions.log_message(f"加载图像时出错: {str(e)}")
            import traceback
            self.navigation_functions.log_message(traceback.format_exc())
            
    def read_geotiff_info(self, image_path):
        """
        读取图像信息，返回图像数据和地理变换参数
        
        参数:
        image_path: 图像文件路径
        """
        try:
            self.navigation_functions.log_message(f"尝试读取图像信息: {image_path}")
            img = Image.open(image_path)
            img_array = np.array(img)
            
            # 获取图像尺寸
            width, height = img.size
            # 设置默认地理变换参数
            pixel_size = 1  # 米/像素
            
            # GDAL格式的地理变换参数
            # transform = [左上角x坐标, x方向分辨率, 0, 左上角y坐标, 0, y方向分辨率]
            transform = [
                0.0,                # 左上角x坐标
                pixel_size,         # x方向分辨率（米/像素）
                0.0,                # 行旋转（通常为0）
                height * pixel_size,# 左上角y坐标
                0.0,                # 列旋转（通常为0）
                -pixel_size         # y方向分辨率（米/像素，负值因为y轴向下）
            ]
            
            self.navigation_functions.log_message(f"成功读取图像: {image_path}")
            self.navigation_functions.log_message(f"图像尺寸: {width}x{height}，通道数: {img_array.shape[2] if len(img_array.shape) > 2 else 1}")
            
            return img_array, transform
            
        except Exception as e:
            self.navigation_functions.log_message(f"读取图像信息时出错: {str(e)}")
            import traceback
            self.navigation_functions.log_message(traceback.format_exc())
            return None, None
