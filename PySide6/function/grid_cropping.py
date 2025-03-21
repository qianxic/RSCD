import os
import cv2
import numpy as np
from pathlib import Path
from PIL import Image
from PySide6.QtWidgets import QFileDialog, QInputDialog, QMessageBox, QDialog, QVBoxLayout, QPushButton, QLabel, QHBoxLayout, QWidget
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QApplication

class GridCropping:
    def __init__(self, navigation_functions):
        """
        初始化渔网裁剪模块
        
        Args:
            navigation_functions: NavigationFunctions实例，用于日志记录和图像显示
        """
        self.navigation_functions = navigation_functions
    
    def crop_image(self, is_before=True):
        """渔网裁剪功能 - 将图像裁剪为网格"""
        # 弹出文件选择对话框
        file_path, _ = QFileDialog.getOpenFileName(None, 
                                     "选择要裁剪的图像", 
                                     "", 
                                     "Image Files (*.png *.jpg *.jpeg *.tif *.tiff);;All Files (*)")
        if not file_path:
            self.navigation_functions.log_message("未选择图像，裁剪操作取消")
            return
        
        # 获取网格裁剪参数
        grid_size, ok = QInputDialog.getInt(None, "网格裁剪设置", 
                                    "请输入要裁剪的网格数量(例如：输入4表示4x4=16个网格):", 
                                    2, 2, 10)
        if not ok:
            self.navigation_functions.log_message("未设置网格参数，裁剪操作取消")
            return
        
        # 让用户选择保存的目标文件夹
        save_dir = QFileDialog.getExistingDirectory(None, "选择保存裁剪结果的文件夹")
        if not save_dir:
            self.navigation_functions.log_message("未选择保存位置，裁剪操作取消")
            return
        
        try:
            self.navigation_functions.log_message(f"正在裁剪图像: {file_path}")
            self.navigation_functions.log_message(f"网格大小: {grid_size}x{grid_size}")
            self.navigation_functions.log_message(f"保存位置: {save_dir}")
            
            # 保存最后生成的文件路径，用于更新显示
            last_generated_file = None
            
            # 生成网格示意图
            grid_preview_path = self._generate_grid_preview(file_path, grid_size, save_dir)
            if grid_preview_path:
                self.navigation_functions.log_message(f"已生成网格示意图: {grid_preview_path}")
            
            # 根据文件类型使用不同的方法进行裁剪
            if file_path.lower().endswith(('.tif', '.tiff')):
                try:
                    # 尝试使用GDAL裁剪GeoTIFF文件
                    last_files = self._crop_geotiff_grid(file_path, grid_size, save_dir, is_before)
                    if last_files:
                        last_generated_file = last_files[0]  # 获取第一个文件
                except Exception as e:
                    self.navigation_functions.log_message(f"GDAL裁剪失败，回退到OpenCV: {str(e)}")
                    # 如果GDAL裁剪失败，回退到OpenCV
                    last_files = self._crop_image_grid_cv2(file_path, grid_size, save_dir, is_before)
                    if last_files:
                        last_generated_file = last_files[0]  # 获取第一个文件
            else:
                # 使用OpenCV裁剪普通图像
                last_files = self._crop_image_grid_cv2(file_path, grid_size, save_dir, is_before)
                if last_files:
                    last_generated_file = last_files[0]  # 获取第一个文件
            
            # 裁剪完成后，可以选择显示其中一个裁剪后的图像或网格示意图
            if grid_preview_path:
                # 创建对话框
                dialog = QDialog()
                dialog.setWindowTitle("裁剪完成")
                dialog.setFixedSize(350, 180)
                dialog.setStyleSheet("""
                    QDialog {
                        background-color: #202124;
                        color: #f7f7f8;
                    }
                    QLabel {
                        color: #f7f7f8;
                        font-size: 12px;
                        font-weight: bold;
                    }
                """)
                
                # 创建布局
                layout = QVBoxLayout(dialog)
                layout.setSpacing(15)
                layout.setContentsMargins(25, 25, 25, 25)
                
                # 创建提示标签
                label = QLabel("网格裁剪完成，裁剪结果保存至目标文件夹。\n你要查看哪个影像？")
                label.setAlignment(Qt.AlignCenter)
                label.setStyleSheet("""
                    font-size: 13px;
                    font-weight: bold;
                    margin: 0;
                    padding: 5px;
                    qproperty-alignment: AlignCenter;
                """)
                layout.addWidget(label)
                
                # 创建按钮容器，设置透明背景
                button_container = QWidget()
                button_container.setStyleSheet("background-color: transparent;")
                button_layout = QHBoxLayout(button_container)
                button_layout.setContentsMargins(0, 10, 0, 0)
                button_layout.setSpacing(15)
                
                # 按钮样式 - 统一使用灰色背景
                button_style = """
                    QPushButton {
                        background-color: #444a5a;
                        color: white;
                        border-radius: 4px;
                        padding: 6px 10px;
                        min-width: 70px;
                    }
                    QPushButton:hover {
                        background-color: #5d6576;
                    }
                    QPushButton:pressed {
                        background-color: #353b4a;
                    }
                """
                
                # 添加按钮
                btn_preview = QPushButton("网格示意图")
                btn_cropped = QPushButton("裁剪后图像")
                btn_cancel = QPushButton("不查看")
                
                # 设置按钮样式
                btn_preview.setStyleSheet(button_style)
                btn_cropped.setStyleSheet(button_style)
                btn_cancel.setStyleSheet(button_style)
                
                button_layout.addStretch()  # 添加弹性空间，使按钮居中
                button_layout.addWidget(btn_preview)
                button_layout.addWidget(btn_cropped)
                button_layout.addWidget(btn_cancel)
                
                layout.addWidget(button_container)
                
                btn_preview.clicked.connect(lambda: self._show_image(grid_preview_path))
                if last_files and len(last_files) > 0:
                    # 更改为打开图像浏览对话框而不是直接显示第一张图片
                    btn_cropped.clicked.connect(lambda: self._show_cropped_images_browser(last_files))
                else:
                    btn_cropped.setEnabled(False)
                btn_cancel.clicked.connect(dialog.reject)
                
                # 显示对话框
                dialog.exec()
            
            # 裁剪完成后不自动导入图像，只提示用户裁剪已完成
            self.navigation_functions.log_message(f"裁剪完成，共生成 {grid_size*grid_size} 个小块图像")
                
        except Exception as e:
            self.navigation_functions.log_message(f"裁剪图像时出错: {str(e)}")
            import traceback
            self.navigation_functions.log_message(traceback.format_exc())
    
    def _show_image(self, image_path, is_before=True):
        """显示网格示意图，并提供加载为前时相或后时相的选项
        
        Args:
            image_path: 图像路径
            is_before: 默认显示位置参数，已废弃，保持兼容性
        """
        if not image_path:
            self.navigation_functions.log_message("无效的图像路径")
            return
        
        # 创建图像浏览器对话框
        browser = QDialog()
        browser.setWindowTitle("网格示意图")
        browser.setMinimumSize(500, 400)  # 设置更大的初始尺寸
        browser.setStyleSheet("""
            QDialog {
                background-color: #202124;
                color: #f7f7f8;
            }
            QLabel {
                color: #f7f7f8;
            }
        """)
        
        # 创建布局
        layout = QVBoxLayout(browser)
        layout.setContentsMargins(8, 8, 8, 8)  # 边距
        layout.setSpacing(5)  # 组件间距
        
        # 添加图像标签
        image_label = QLabel()
        image_label.setAlignment(Qt.AlignCenter)
        image_label.setMinimumSize(400, 300)  # 设置更大的图像显示区域
        layout.addWidget(image_label)
        
        # 添加图像信息标签
        info_label = QLabel()
        info_label.setAlignment(Qt.AlignCenter)
        info_label.setStyleSheet("""
            font-size: 9pt;
            color: #f7f7f8;
            margin: 0;
            padding: 5px;
            qproperty-alignment: AlignCenter;
        """)
        layout.addWidget(info_label)
        
        # 添加按钮布局
        button_layout = QHBoxLayout()
        button_layout.setSpacing(5)  # 增加按钮之间的间距
        button_layout.setContentsMargins(0, 5, 0, 0)  # 上方添加一些间距
        
        # 创建底部按钮容器，设置透明背景
        button_container = QWidget()
        button_container.setStyleSheet("background-color: transparent;")
        button_container_layout = QHBoxLayout(button_container)
        button_container_layout.setContentsMargins(0, 10, 0, 0)
        button_container_layout.setSpacing(15)
        
        # 添加按钮
        btn_load_before = QPushButton("加载为前时相")
        btn_load_after = QPushButton("加载为后时相")
        
        # 设置按钮样式 - 统一使用灰色背景
        button_style = """
            QPushButton {
                background-color: #444a5a;
                color: white;
                border-radius: 4px;
                padding: 6px 10px;
                min-width: 90px;
            }
            QPushButton:hover {
                background-color: #5d6576;
            }
            QPushButton:pressed {
                background-color: #353b4a;
            }
        """
        
        # 设置按钮样式
        btn_load_before.setStyleSheet(button_style)
        btn_load_after.setStyleSheet(button_style)
        
        button_container_layout.addStretch()  # 添加弹性空间，使按钮居中
        button_container_layout.addWidget(btn_load_before)
        button_container_layout.addWidget(btn_load_after)
        button_container_layout.addStretch()  # 添加弹性空间，使按钮居中
        
        layout.addWidget(button_container)
        
        # 显示图像并调整大小
        try:
            # 读取图像信息
            file_name = Path(image_path).name
            info_label.setText(f"网格示意图: {file_name}")
            
            # 为路径信息设置特定的容器
            path_container = QWidget()
            path_container.setStyleSheet("background-color: #2c2c2e; border: 1px solid #444a5a; border-radius: 4px;")
            path_layout = QVBoxLayout(path_container)
            path_layout.setContentsMargins(5, 5, 5, 5)
            path_layout.addWidget(info_label)
            layout.removeWidget(info_label)
            layout.insertWidget(1, path_container)
            
            # 读取图像并调整对话框大小以适应图像尺寸
            pixmap = QPixmap(image_path)
            if not pixmap.isNull():
                # 计算合适的显示尺寸（限制最大尺寸）
                screen_size = QApplication.primaryScreen().availableSize()
                max_width = min(screen_size.width() * 0.8, 1200)
                max_height = min(screen_size.height() * 0.8, 800)
                
                # 调整图像尺寸以适应屏幕，同时保持宽高比
                img_width = pixmap.width()
                img_height = pixmap.height()
                
                if img_width > max_width or img_height > max_height:
                    # 需要缩小图像
                    scale_ratio = min(max_width/img_width, max_height/img_height)
                    new_width = int(img_width * scale_ratio)
                    new_height = int(img_height * scale_ratio)
                else:
                    # 保持原始尺寸
                    new_width = img_width
                    new_height = img_height
                
                # 调整图像标签大小
                image_label.setPixmap(pixmap.scaled(new_width, new_height, Qt.KeepAspectRatio))
                
                # 调整对话框大小（考虑其他UI元素和边距）
                dialog_width = new_width + 30  # 添加一些边距
                dialog_height = new_height + 100  # 为其他UI元素预留空间
                browser.resize(dialog_width, dialog_height)
            else:
                image_label.setText("无法加载图像")
                self.navigation_functions.log_message(f"无法加载网格示意图: {image_path}")
        except Exception as e:
            self.navigation_functions.log_message(f"显示网格示意图时出错: {str(e)}")
            import traceback
            self.navigation_functions.log_message(traceback.format_exc())
        
        # 加载为前时相并关闭浏览器
        def load_as_before():
            try:
                self.navigation_functions.file_path = image_path
                self.navigation_functions.update_image_display(is_before=True)
                self.navigation_functions.log_message(f"已加载网格示意图为前时相: {image_path}")
                browser.accept()  # 关闭对话框
            except Exception as e:
                self.navigation_functions.log_message(f"加载网格示意图为前时相时出错: {str(e)}")
        
        # 加载为后时相并关闭浏览器
        def load_as_after():
            try:
                self.navigation_functions.file_path_after = image_path
                self.navigation_functions.update_image_display(is_before=False)
                self.navigation_functions.log_message(f"已加载网格示意图为后时相: {image_path}")
                browser.accept()  # 关闭对话框
            except Exception as e:
                self.navigation_functions.log_message(f"加载网格示意图为后时相时出错: {str(e)}")
        
        # 连接按钮事件
        btn_load_before.clicked.connect(load_as_before)
        btn_load_after.clicked.connect(load_as_after)
        
        # 按键事件处理
        def keyPressEvent(event):
            if event.key() == Qt.Key_Escape:
                browser.reject()  # 按ESC键关闭对话框
        
        # 添加键盘事件处理
        browser.keyPressEvent = keyPressEvent
        
        # 显示对话框
        browser.exec()
    
    def _generate_grid_preview(self, file_path, grid_size, save_dir):
        """生成网格划分示意图，在原图上绘制网格并保存
        
        Args:
            file_path: 原始图像路径
            grid_size: 网格大小
            save_dir: 保存目录
            
        Returns:
            str: 示意图路径，失败返回None
        """
        try:
            # 使用pathlib处理路径
            file_path_obj = Path(file_path)
            save_dir_obj = Path(save_dir)
            
            self.navigation_functions.log_message(f"正在生成网格示意图...")
            
            # 读取原始图像
            try:
                img_pil = Image.open(file_path_obj)
                img = np.array(img_pil)
                if len(img.shape) == 3 and img.shape[2] == 3:
                    img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)  # PIL是RGB，OpenCV是BGR
            except Exception as e:
                self.navigation_functions.log_message(f"使用PIL读取失败: {str(e)}，尝试使用OpenCV")
                img = cv2.imread(str(file_path_obj))
            
            if img is None:
                self.navigation_functions.log_message(f"无法读取图像，无法生成网格示意图")
                return None
            
            # 获取图像尺寸
            height, width = img.shape[:2]
            
            # 创建原始图像的副本
            grid_preview = img.copy()
            
            # 计算每个网格的大小
            grid_width = width // grid_size
            grid_height = height // grid_size
            
            # 设置网格线的颜色和粗细，目前是在opencv中绘制，所以颜色是BGR格式
            line_color = (0, 0, 255) # 红色线条
            line_thickness = max(1, min(width, height) // 300)  # 根据图像尺寸自适应线条粗细
            text_color = (255, 0, 0)# 蓝色文字
            font = cv2.FONT_HERSHEY_SIMPLEX
            font_scale = max(0.5, min(width, height) / 1000)  # 自适应字体大小
            
            # 绘制水平线
            for i in range(1, grid_size):
                y = i * grid_height
                cv2.line(grid_preview, (0, y), (width, y), line_color, line_thickness)
            
            # 绘制垂直线
            for i in range(1, grid_size):
                x = i * grid_width
                cv2.line(grid_preview, (x, 0), (x, height), line_color, line_thickness)
            
            # 每个网格添加索引标签
            for row in range(grid_size):
                for col in range(grid_size):
                    # 计算文本位置
                    text_x = col * grid_width + 10
                    text_y = row * grid_height + 30
                    
                    # 添加网格索引文本
                    cv2.putText(grid_preview, f"{row+1}_{col+1}", 
                               (text_x, text_y), font, font_scale, text_color, 
                               max(1, line_thickness), cv2.LINE_AA)
            
            # 创建输出文件名
            filename = file_path_obj.stem
            ext = file_path_obj.suffix
            output_filename = f"{filename}_grid_preview{ext}"
            output_path = save_dir_obj / output_filename
            
            # 确保保存目录存在
            if not save_dir_obj.exists():
                save_dir_obj.mkdir(parents=True, exist_ok=True)
                
            # 保存示意图
            try:
                # 使用PIL保存，避免中文路径问题
                grid_preview_rgb = cv2.cvtColor(grid_preview, cv2.COLOR_BGR2RGB)
                img_pil = Image.fromarray(grid_preview_rgb)
                img_pil.save(str(output_path))
                self.navigation_functions.log_message(f"网格示意图已保存到: {output_path}")
                return str(output_path)
            except Exception as e:
                self.navigation_functions.log_message(f"PIL保存网格示意图失败: {str(e)}，尝试使用OpenCV")
                try:
                    # 如果PIL保存失败，尝试使用OpenCV
                    cv2.imwrite(str(output_path), grid_preview)
                    self.navigation_functions.log_message(f"使用OpenCV保存网格示意图: {output_path}")
                    return str(output_path)
                except Exception as e2:
                    self.navigation_functions.log_message(f"保存网格示意图失败: {str(e2)}")
                    return None
                
        except Exception as e:
            self.navigation_functions.log_message(f"生成网格示意图时出错: {str(e)}")
            import traceback
            self.navigation_functions.log_message(traceback.format_exc())
            return None
            
    def _crop_image_grid_cv2(self, file_path, grid_size, save_dir, is_before=True):
        """使用OpenCV将普通图像裁剪为网格
        
        Returns:
            list: 成功保存的文件路径列表
        """
        try:
            # 保存成功生成的文件路径
            generated_files = []
            
            # 使用pathlib处理路径
            file_path_obj = Path(file_path)
            save_dir_obj = Path(save_dir)
            
            # 记录日志
            self.navigation_functions.log_message(f"使用OpenCV裁剪图像: {file_path_obj}")
            
            # 使用PIL读取图像以避免中文路径问题
            try:
                img_pil = Image.open(file_path_obj)
                img = np.array(img_pil)
                if len(img.shape) == 3 and img.shape[2] == 3:
                    img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)  # PIL是RGB，OpenCV是BGR
                self.navigation_functions.log_message("使用PIL成功读取图像")
            except Exception as e:
                self.navigation_functions.log_message(f"使用PIL读取失败: {str(e)}，尝试使用OpenCV")
                img = cv2.imread(str(file_path_obj))
            
            if img is None:
                self.navigation_functions.log_message(f"无法读取图像: {file_path_obj}")
                return generated_files
            
            # 获取图像尺寸
            height, width = img.shape[:2]
            
            # 存储原始图像尺寸信息
            if is_before:
                self.navigation_functions.before_image_original_size = (width, height)
            else:
                self.navigation_functions.after_image_original_size = (width, height)
            
            # 计算每个网格的大小
            grid_width = width // grid_size
            grid_height = height // grid_size
            
            self.navigation_functions.log_message(f"原始图像尺寸: {width}x{height}")
            self.navigation_functions.log_message(f"每个网格尺寸: {grid_width}x{grid_height}")
            
            # 获取文件基本信息
            basename = file_path_obj.name
            filename = file_path_obj.stem
            ext = file_path_obj.suffix
            
            # 获取文件名，根据是前时相还是后时相来确定前缀
            prefix = f"{'before' if is_before else 'after'}_grid"
            
            # 确保保存目录存在
            if not save_dir_obj.exists():
                save_dir_obj.mkdir(parents=True, exist_ok=True)
                self.navigation_functions.log_message(f"创建保存目录: {save_dir_obj}")
            
            # 裁剪并保存每个网格
            count = 0
            for row in range(grid_size):
                for col in range(grid_size):
                    count += 1
                    
                    # 计算当前网格的坐标
                    x_start = col * grid_width
                    y_start = row * grid_height
                    
                    # 确保不超出图像边界
                    current_width = min(grid_width, width - x_start)
                    current_height = min(grid_height, height - y_start)
                    
                    if current_width <= 0 or current_height <= 0:
                        continue  # 跳过无效的网格
                    
                    # 裁剪当前网格
                    crop_img = img[y_start:y_start+current_height, x_start:x_start+current_width]
                    
                    # 创建输出文件名
                    output_filename = f"{prefix}_{row+1}_{col+1}{ext}"
                    output_path = save_dir_obj / output_filename
                    
                    # 保存裁剪结果
                    try:
                        # 使用PIL保存，以避免中文路径问题
                        if len(crop_img.shape) == 3 and crop_img.shape[2] == 3:
                            crop_img_rgb = cv2.cvtColor(crop_img, cv2.COLOR_BGR2RGB)
                        else:
                            crop_img_rgb = crop_img
                        img_pil = Image.fromarray(crop_img_rgb)
                        img_pil.save(str(output_path))
                        self.navigation_functions.log_message(f"保存网格 {row+1}_{col+1} 到: {output_path}")
                        generated_files.append(str(output_path))
                    except Exception as e:
                        self.navigation_functions.log_message(f"PIL保存失败: {str(e)}，尝试使用OpenCV")
                        try:
                            # 如果PIL保存失败，尝试使用OpenCV（虽然对中文路径支持可能有问题）
                            cv2.imwrite(str(output_path), crop_img)
                            self.navigation_functions.log_message(f"使用OpenCV保存网格 {row+1}_{col+1} 到: {output_path}")
                            generated_files.append(str(output_path))
                        except Exception as e2:
                            self.navigation_functions.log_message(f"保存网格 {row+1}_{col+1} 失败: {str(e2)}")
            
            self.navigation_functions.log_message(f"网格裁剪完成，共生成 {count} 个子图像，保存在: {save_dir_obj}")
            
            return generated_files
            
        except Exception as e:
            self.navigation_functions.log_message(f"网格裁剪图像时出错: {str(e)}")
            import traceback
            self.navigation_functions.log_message(traceback.format_exc())
            return []

    def _crop_geotiff_grid(self, file_path, grid_size, save_dir, is_before=True):
        """使用GDAL将GeoTIFF图像裁剪为网格
        
        Returns:
            list: 成功保存的文件路径列表
        """
        try:
            from osgeo import gdal
            
            # 保存成功生成的文件路径
            generated_files = []
            
            # 使用pathlib处理路径
            file_path_obj = Path(file_path)
            save_dir_obj = Path(save_dir)
            
            # 记录日志
            self.navigation_functions.log_message(f"使用GDAL裁剪GeoTIFF图像: {file_path_obj}")
            
            # 打开数据集 - 使用字符串路径但先进行规范化
            ds = gdal.Open(str(file_path_obj.resolve()), gdal.GA_ReadOnly)
            if ds is None:
                self.navigation_functions.log_message(f"无法使用GDAL打开文件: {file_path_obj}")
                return generated_files
            
            # 获取基本信息
            width = ds.RasterXSize
            height = ds.RasterYSize
            bands = ds.RasterCount
            geo_transform = ds.GetGeoTransform()
            projection = ds.GetProjection()
            
            # 存储原始图像尺寸信息
            if is_before:
                self.navigation_functions.before_image_original_size = (width, height)
            else:
                self.navigation_functions.after_image_original_size = (width, height)
                
            # 计算每个网格的大小
            grid_width = width // grid_size
            grid_height = height // grid_size
            
            self.navigation_functions.log_message(f"GeoTIFF图像信息: 宽度={width}, 高度={height}, 波段数={bands}")
            self.navigation_functions.log_message(f"每个网格尺寸: {grid_width}x{grid_height}")
            
            # 获取文件基本信息
            basename = file_path_obj.name
            filename = file_path_obj.stem
            ext = file_path_obj.suffix
            
            # 获取文件名，根据是前时相还是后时相来确定前缀
            prefix = f"{'before' if is_before else 'after'}_grid"
            
            # 确保保存目录存在
            if not save_dir_obj.exists():
                save_dir_obj.mkdir(parents=True, exist_ok=True)
                self.navigation_functions.log_message(f"创建保存目录: {save_dir_obj}")
            
            # 创建驱动程序
            driver = gdal.GetDriverByName('GTiff')
            
            # 裁剪并保存每个网格
            count = 0
            for row in range(grid_size):
                for col in range(grid_size):
                    count += 1
                    
                    # 计算当前网格的坐标
                    x_start = col * grid_width
                    y_start = row * grid_height
                    
                    # 确保不超出图像边界
                    current_width = min(grid_width, width - x_start)
                    current_height = min(grid_height, height - y_start)
                    
                    if current_width <= 0 or current_height <= 0:
                        continue  # 跳过无效的网格
                    
                    # 创建输出文件名
                    output_filename = f"{prefix}_{row+1}_{col+1}{ext}"
                    output_path = save_dir_obj / output_filename
                    output_path_str = str(output_path.resolve())  # 获取规范化的绝对路径
                    
                    # 创建目标数据集
                    try:
                        # 使用规范化的绝对路径，避免中文路径问题
                        dst_ds = driver.Create(output_path_str, current_width, current_height, bands, gdal.GDT_Byte)
                        
                        # 计算新的地理变换参数
                        if geo_transform is not None:
                            new_geo_transform = list(geo_transform)
                            # 调整左上角x坐标
                            new_geo_transform[0] = geo_transform[0] + x_start * geo_transform[1]
                            # 调整左上角y坐标
                            new_geo_transform[3] = geo_transform[3] + y_start * geo_transform[5]
                            dst_ds.SetGeoTransform(tuple(new_geo_transform))
                            
                        # 设置投影
                        if projection:
                            dst_ds.SetProjection(projection)
                            
                        # 复制波段数据
                        for band_idx in range(1, bands + 1):
                            band = ds.GetRasterBand(band_idx)
                            data = band.ReadAsArray(x_start, y_start, current_width, current_height)
                            dst_band = dst_ds.GetRasterBand(band_idx)
                            dst_band.WriteArray(data)
                            
                        # 清理资源
                        dst_ds = None
                        self.navigation_functions.log_message(f"保存网格 {row+1}_{col+1} 到: {output_path}")
                        generated_files.append(str(output_path))
                    except Exception as e:
                        self.navigation_functions.log_message(f"保存网格 {row+1}_{col+1} 失败: {str(e)}")
                        # 尝试使用替代方法保存
                        try:
                            # 读取数据到内存
                            data_arrays = []
                            for band_idx in range(1, bands + 1):
                                band = ds.GetRasterBand(band_idx)
                                data_arrays.append(band.ReadAsArray(x_start, y_start, current_width, current_height))
                            
                            # 如果是标准RGB图像（3波段），使用PIL保存
                            if bands == 3:
                                # 组合数组并转换为PIL图像
                                img_array = np.dstack(data_arrays)
                                img_pil = Image.fromarray(img_array)
                                img_pil.save(str(output_path))
                                self.navigation_functions.log_message(f"使用PIL保存网格 {row+1}_{col+1} 到: {output_path}")
                                generated_files.append(str(output_path))
                            else:
                                self.navigation_functions.log_message(f"无法使用替代方法保存非RGB的GeoTIFF图像")
                        except Exception as e2:
                            self.navigation_functions.log_message(f"使用替代方法保存失败: {str(e2)}")
            
            # 清理资源
            ds = None
            
            self.navigation_functions.log_message(f"网格裁剪完成，共生成 {count} 个子图像，保存在: {save_dir}")
            
            return generated_files
            
        except Exception as e:
            self.navigation_functions.log_message(f"裁剪GeoTIFF图像时出错: {str(e)}")
            import traceback
            self.navigation_functions.log_message(traceback.format_exc())
            return []

    def _show_cropped_images_browser(self, image_files, is_before=True):
        """显示裁剪后的图像浏览器，允许用户浏览所有裁剪后的图像并选择加载位置
        
        Args:
            image_files: 裁剪后的图像文件列表
            is_before: 已废弃参数，保持兼容性
        """
        if not image_files:
            self.navigation_functions.log_message("没有可显示的裁剪图像")
            return
        
        # 创建图像浏览器对话框
        browser = QDialog()
        browser.setWindowTitle("裁剪图像浏览器")
        browser.setMinimumSize(500, 400)  # 设置更大的初始尺寸
        browser.setStyleSheet("""
            QDialog {
                background-color: #202124;
                color: #f7f7f8;
            }
            QLabel {
                color: #f7f7f8;
            }
            QWidget {
                background-color: #202124;
            }
        """)
        
        # 创建布局
        layout = QVBoxLayout(browser)
        layout.setContentsMargins(8, 8, 8, 8)  # 稍微增加边距使界面更美观
        layout.setSpacing(5)  # 增加组件间距
        
        # 添加图像标签
        image_label = QLabel()
        image_label.setAlignment(Qt.AlignCenter)
        image_label.setMinimumSize(400, 300)  # 设置更大的图像显示区域
        layout.addWidget(image_label)
        
        # 添加图像信息标签
        info_label = QLabel()
        info_label.setAlignment(Qt.AlignCenter)
        info_label.setStyleSheet("""
            font-size: 9pt;
            color: #f7f7f8;
            margin: 0;
            padding: 5px;
            qproperty-alignment: AlignCenter;
        """)
        layout.addWidget(info_label)
        
        # 添加导航按钮布局
        nav_layout = QHBoxLayout()
        nav_layout.setSpacing(5)  # 增加按钮之间的间距
        nav_layout.setContentsMargins(0, 5, 0, 0)  # 上方添加一些间距
        
        # 创建底部按钮容器，设置透明背景
        nav_container = QWidget()
        nav_container.setStyleSheet("background-color: transparent;")
        nav_container_layout = QHBoxLayout(nav_container)
        nav_container_layout.setContentsMargins(0, 10, 0, 0)
        nav_container_layout.setSpacing(15)  # 增加按钮间距
        
        # 导航按钮样式 - 统一使用灰色背景
        button_style = """
            QPushButton {
                background-color: #444a5a;
                color: white;
                border-radius: 4px;
                padding: 6px 10px;
                min-width: 70px;
            }
            QPushButton:hover {
                background-color: #5d6576;
            }
            QPushButton:pressed {
                background-color: #353b4a;
            }
        """
        
        # 添加导航按钮
        btn_prev = QPushButton("上一个")
        btn_next = QPushButton("下一个")
        btn_load_before = QPushButton("加载为前时相")
        btn_load_after = QPushButton("加载为后时相")
        
        # 设置按钮样式
        btn_prev.setStyleSheet(button_style)
        btn_next.setStyleSheet(button_style)
        
        # 设置按钮样式
        btn_load_before.setStyleSheet(button_style)
        btn_load_after.setStyleSheet(button_style)
        
        nav_container_layout.addWidget(btn_prev)
        nav_container_layout.addWidget(btn_next)
        nav_container_layout.addStretch()  # 添加弹性空间在中间
        nav_container_layout.addWidget(btn_load_before)
        nav_container_layout.addWidget(btn_load_after)
        
        layout.addWidget(nav_container)
        
        # 当前图像索引
        current_index = 0
        total_images = len(image_files)
        
        # 为路径信息设置特定的容器
        path_container = QWidget()
        path_container.setStyleSheet("background-color: #2c2c2e; border: 1px solid #444a5a; border-radius: 4px;")
        path_layout = QVBoxLayout(path_container)
        path_layout.setContentsMargins(5, 5, 5, 5)
        path_layout.addWidget(info_label)
        layout.removeWidget(info_label)
        layout.insertWidget(1, path_container)
        
        # 更新状态标签和显示当前图像
        def update_display():
            try:
                current_path = image_files[current_index]
                # 更新信息标签
                file_name = Path(current_path).name
                info_label.setText(f"正在查看: {current_index + 1}/{total_images} - {file_name}")
                
                # 读取图像并调整对话框大小以适应图像尺寸
                pixmap = QPixmap(current_path)
                if not pixmap.isNull():
                    # 计算合适的显示尺寸（限制最大尺寸）
                    screen_size = QApplication.primaryScreen().availableSize()
                    max_width = min(screen_size.width() * 0.8, 1200)
                    max_height = min(screen_size.height() * 0.8, 800)
                    
                    # 调整图像尺寸以适应屏幕，同时保持宽高比
                    img_width = pixmap.width()
                    img_height = pixmap.height()
                    
                    if img_width > max_width or img_height > max_height:
                        # 需要缩小图像
                        scale_ratio = min(max_width/img_width, max_height/img_height)
                        new_width = int(img_width * scale_ratio)
                        new_height = int(img_height * scale_ratio)
                    else:
                        # 保持原始尺寸
                        new_width = img_width
                        new_height = img_height
                    
                    # 调整图像标签大小
                    image_label.setPixmap(pixmap.scaled(new_width, new_height, Qt.KeepAspectRatio))
                    
                    # 调整对话框大小（考虑其他UI元素和边距）
                    dialog_width = new_width + 30  # 添加一些边距
                    dialog_height = new_height + 100  # 为其他UI元素预留空间
                    browser.resize(dialog_width, dialog_height)
                else:
                    image_label.setText("无法加载图像")
            except Exception as e:
                self.navigation_functions.log_message(f"更新图像显示时出错: {str(e)}")
        
        # 导航到上一个图像
        def go_to_prev():
            nonlocal current_index
            if current_index > 0:
                current_index -= 1
                update_display()
                self.navigation_functions.log_message(f"显示上一个裁剪图像: {current_index + 1}/{total_images}")
        
        # 导航到下一个图像
        def go_to_next():
            nonlocal current_index
            if current_index < total_images - 1:
                current_index += 1
                update_display()
                self.navigation_functions.log_message(f"显示下一个裁剪图像: {current_index + 1}/{total_images}")
        
        # 加载当前图像为前时相并关闭浏览器
        def load_as_before():
            try:
                current_path = image_files[current_index]
                self.navigation_functions.file_path = current_path
                self.navigation_functions.update_image_display(is_before=True)
                self.navigation_functions.log_message(f"已加载图像为前时相: {current_path}")
                browser.accept()  # 关闭对话框
            except Exception as e:
                self.navigation_functions.log_message(f"加载图像为前时相时出错: {str(e)}")
        
        # 加载当前图像为后时相并关闭浏览器
        def load_as_after():
            try:
                current_path = image_files[current_index]
                self.navigation_functions.file_path_after = current_path
                self.navigation_functions.update_image_display(is_before=False)
                self.navigation_functions.log_message(f"已加载图像为后时相: {current_path}")
                browser.accept()  # 关闭对话框
            except Exception as e:
                self.navigation_functions.log_message(f"加载图像为后时相时出错: {str(e)}")
        
        # 连接按钮事件
        btn_prev.clicked.connect(go_to_prev)
        btn_next.clicked.connect(go_to_next)
        btn_load_before.clicked.connect(load_as_before)
        btn_load_after.clicked.connect(load_as_after)
        
        # 初始显示第一个图像
        update_display()
        self.navigation_functions.log_message(f"显示第一个裁剪图像: 1/{total_images}")
        
        # 按键事件处理
        def keyPressEvent(event):
            if event.key() == Qt.Key_Left:
                go_to_prev()
            elif event.key() == Qt.Key_Right:
                go_to_next()
            elif event.key() == Qt.Key_Escape:
                browser.reject()  # 按ESC键关闭对话框
        
        # 添加键盘事件处理
        browser.keyPressEvent = keyPressEvent
        
        # 显示对话框
        browser.exec()
