# daohanglan.py
import cv2
import logging
from datetime import datetime
from PySide6.QtWidgets import QFileDialog, QLabel, QMessageBox, QInputDialog, QApplication, QTextEdit, QScrollBar, QDialog, QVBoxLayout, QPushButton, QGridLayout
from PySide6.QtGui import QPixmap, QImage, QPainter, Qt, QWheelEvent, QMouseEvent, QResizeEvent
from PySide6.QtCore import QEvent, Qt, QPoint
import os
import tempfile
from PIL import Image
from pathlib import Path

class ZoomableLabel(QLabel):#定义图像为缩放的标签类
    """可缩放的标签类，支持鼠标滚轮缩放图像和拖动"""
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.original_pixmap = None
        self.scale_factor = 1.0
        self.setAlignment(Qt.AlignCenter)
        # 启用鼠标追踪，以便能够接收鼠标事件
        self.setMouseTracking(True)
        # 设置焦点策略，使标签可以接收键盘焦点
        self.setFocusPolicy(Qt.StrongFocus)
        # 安装事件过滤器，以便能够处理鼠标滚轮事件
        self.installEventFilter(self)
        
        # 拖动相关变量
        self.dragging = False
        self.drag_start_position = QPoint()
        self.offset = QPoint(0, 0)  # 图像偏移量
        
        # 当前显示的图像尺寸
        self.current_pixmap_size = None
        
        # 区域选择相关变量
        self.selecting = False  # 是否正在选择区域
        self.selection_start = QPoint()  # 选择区域的起始点
        self.selection_end = QPoint()  # 选择区域的结束点
        self.selection_active = False  # 是否有活动的选择区域
        
        # 选择模式
        self.selection_mode = False  # 是否处于选择模式

    def set_pixmap(self, pixmap):
        """设置原始图像并显示"""
        self.original_pixmap = pixmap
        self.scale_factor = 1.0
        self.offset = QPoint(0, 0)  # 重置偏移量
        self.selection_active = False  # 重置选择状态
        self.update_display()

    def reset_view(self):
        """重置视图到原始状态"""
        if self.original_pixmap:
            self.scale_factor = 1.0
            self.offset = QPoint(0, 0)
            self.selection_active = False  # 重置选择状态
            self.update_display()
            self.setCursor(Qt.ArrowCursor)  # 恢复鼠标光标

    def enter_selection_mode(self):
        """进入区域选择模式"""
        if self.original_pixmap:
            self.selection_mode = True
            self.selection_active = False
            self.setCursor(Qt.CrossCursor)  # 设置十字光标
            self.update()  # 更新显示

    def exit_selection_mode(self):
        """退出区域选择模式"""
        self.selection_mode = False
        self.selecting = False
        self.setCursor(Qt.ArrowCursor)  # 恢复默认光标
        self.update()  # 更新显示

    def get_selected_area(self):
        """获取选择区域在原始图像上的坐标
        
        返回：
            tuple: (x, y, width, height) 或 None（如果没有选择区域）
        """
        if not self.selection_active or not self.original_pixmap:
            return None
            
        # 将选择区域的坐标从显示坐标转换为原始图像坐标
        
        # 获取标签和图像的尺寸信息
        label_width = self.width()
        label_height = self.height()
        
        # 如果当前有缩放
        if self.scale_factor != 1.0:
            # 确定图像在标签中的位置
            scaled_width = int(self.current_pixmap_size[0])
            scaled_height = int(self.current_pixmap_size[1])
            
            # 计算图像在标签中的偏移量（居中显示）
            x_offset = (label_width - scaled_width) // 2 + self.offset.x()
            y_offset = (label_height - scaled_height) // 2 + self.offset.y()
            
            # 计算选择区域在缩放图像上的坐标
            sel_x1 = min(self.selection_start.x(), self.selection_end.x()) - x_offset
            sel_y1 = min(self.selection_start.y(), self.selection_end.y()) - y_offset
            sel_width = abs(self.selection_end.x() - self.selection_start.x())
            sel_height = abs(self.selection_end.y() - self.selection_start.y())
            
            # 确保坐标在图像范围内
            sel_x1 = max(0, sel_x1)
            sel_y1 = max(0, sel_y1)
            
            if sel_x1 >= scaled_width or sel_y1 >= scaled_height:
                return None
                
            # 限制宽度和高度不超出图像边界
            sel_width = min(sel_width, scaled_width - sel_x1)
            sel_height = min(sel_height, scaled_height - sel_y1)
            
            # 转换回原始图像的坐标
            orig_x = int(sel_x1 / self.scale_factor)
            orig_y = int(sel_y1 / self.scale_factor)
            orig_width = int(sel_width / self.scale_factor)
            orig_height = int(sel_height / self.scale_factor)
            
            return (orig_x, orig_y, orig_width, orig_height)
        else:
            # 获取原始图像的尺寸
            pixmap_width = self.original_pixmap.width()
            pixmap_height = self.original_pixmap.height()
            
            # 计算图像在标签中的缩放比例
            scale_x = pixmap_width / self.current_pixmap_size[0]
            scale_y = pixmap_height / self.current_pixmap_size[1]
            
            # 计算图像在标签中的偏移量（居中显示）
            x_offset = (label_width - self.current_pixmap_size[0]) // 2
            y_offset = (label_height - self.current_pixmap_size[1]) // 2
            
            # 计算选择区域在显示图像上的坐标
            sel_x1 = min(self.selection_start.x(), self.selection_end.x()) - x_offset
            sel_y1 = min(self.selection_start.y(), self.selection_end.y()) - y_offset
            sel_width = abs(self.selection_end.x() - self.selection_start.x())
            sel_height = abs(self.selection_end.y() - self.selection_start.y())
            
            # 确保坐标在图像范围内
            sel_x1 = max(0, sel_x1)
            sel_y1 = max(0, sel_y1)
            
            if sel_x1 >= self.current_pixmap_size[0] or sel_y1 >= self.current_pixmap_size[1]:
                return None
                
            # 限制宽度和高度不超出图像边界
            sel_width = min(sel_width, self.current_pixmap_size[0] - sel_x1)
            sel_height = min(sel_height, self.current_pixmap_size[1] - sel_y1)
            
            # 转换为原始图像的坐标
            orig_x = int(sel_x1 * scale_x)
            orig_y = int(sel_y1 * scale_y)
            orig_width = int(sel_width * scale_x)
            orig_height = int(sel_height * scale_y)
            
            return (orig_x, orig_y, orig_width, orig_height)

    def update_display(self):
        """更新显示，根据当前缩放因子和偏移量重新绘制图像"""
        if not self.original_pixmap:
            return
            
        # 获取标签的尺寸
        label_width = self.width()
        label_height = self.height()
        
        # 创建新的pixmap用于绘制，使用标签当前大小
        display_pixmap = QPixmap(label_width, label_height)
        display_pixmap.fill(Qt.transparent)  # 使背景透明
        
        # 创建绘图器
        painter = QPainter(display_pixmap)
        
        # 计算缩放后的图像尺寸
        pixmap_width = self.original_pixmap.width() * self.scale_factor
        pixmap_height = self.original_pixmap.height() * self.scale_factor
        
        # 保存当前显示的图像尺寸，用于其他计算
        self.current_pixmap_size = (pixmap_width, pixmap_height)
        
        # 计算图像在标签中的位置（居中显示）
        x = (label_width - pixmap_width) / 2 + self.offset.x()
        y = (label_height - pixmap_height) / 2 + self.offset.y()
        
        # 绘制原始图像
        painter.drawPixmap(int(x), int(y), int(pixmap_width), int(pixmap_height), self.original_pixmap)
        
        # 如果有选择区域且选择是活跃的，绘制选择矩形
        if self.selection_active:
            # 设置矩形颜色和样式
            painter.setPen(Qt.red)  # 设置红色边框
            
            # 计算选择矩形的坐标
            sel_x = min(self.selection_start.x(), self.selection_end.x())
            sel_y = min(self.selection_start.y(), self.selection_end.y())
            sel_width = abs(self.selection_end.x() - self.selection_start.x())
            sel_height = abs(self.selection_end.y() - self.selection_start.y())
            
            # 绘制矩形
            painter.drawRect(sel_x, sel_y, sel_width, sel_height)
        
        # 结束绘图
        painter.end()
        
        # 设置标签的pixmap
        super().setPixmap(display_pixmap)

    def can_drag(self):
        """判断当前是否可以拖动图像"""
        if not self.original_pixmap or not self.current_pixmap_size:
            return False
            
        # 如果图像实际显示尺寸大于标签尺寸，则可以拖动
        label_width = self.width()
        label_height = self.height()
        pixmap_width, pixmap_height = self.current_pixmap_size
        
        return pixmap_width > label_width or pixmap_height > label_height or self.scale_factor > 1.0

    def eventFilter(self, obj, event):
        """事件过滤器，处理鼠标滚轮事件和鼠标拖动事件"""
        if obj == self and self.original_pixmap:
            # 处理鼠标双击事件 - 恢复原始视图
            if event.type() == QEvent.MouseButtonDblClick:
                mouse_event = QMouseEvent(event)
                if mouse_event.button() == Qt.LeftButton:
                    # 对于前时相标签，检查NavigationFunctions中的file_path
                    # 对于后时相标签，检查NavigationFunctions中的file_path_after
                    # 只有当文件路径存在时才恢复视图
                    
                    # 获取标签的父窗口，通过层次结构查找NavigationFunctions实例
                    parent = self.parent()
                    while parent:
                        # 检查父对象是否有navigation_functions属性
                        if hasattr(parent, 'navigation_functions'):
                            # 判断当前标签是前时相还是后时相
                            if parent.navigation_functions.label_before == self:
                                # 是前时相标签，检查file_path
                                if not parent.navigation_functions.file_path:
                                    # 如果文件路径为None，不执行任何操作
                                    return True
                            elif parent.navigation_functions.label_after == self:
                                # 是后时相标签，检查file_path_after
                                if not parent.navigation_functions.file_path_after:
                                    # 如果文件路径为None，不执行任何操作
                                    return True
                            # 如果存在有效的文件路径，则继续执行恢复视图的操作
                            break
                        parent = parent.parent()
                        
                    self.reset_view()
                    return True
            
            # 处理鼠标滚轮事件
            elif event.type() == QEvent.Wheel:
                wheel_event = QWheelEvent(event)
                # 获取滚轮角度增量
                delta = wheel_event.angleDelta().y()
                
                # 根据滚轮方向调整缩放因子
                if delta > 0:  # 向上滚动，放大
                    self.scale_factor *= 1.1
                else:  # 向下滚动，缩小
                    self.scale_factor /= 1.1
                
                # 限制缩放范围
                self.scale_factor = max(0.1, min(self.scale_factor, 5.0))
                
                # 更新显示
                self.update_display()
                
                # 根据当前状态更新鼠标光标
                if self.selection_mode:
                    self.setCursor(Qt.CrossCursor)
                elif self.can_drag():
                    self.setCursor(Qt.OpenHandCursor)
                else:
                    self.setCursor(Qt.ArrowCursor)
                    
                return True
            
            # 处理鼠标按下事件
            elif event.type() == QEvent.MouseButtonPress:
                mouse_event = QMouseEvent(event)
                if mouse_event.button() == Qt.LeftButton:
                    if self.selection_mode:
                        # 在选择模式下开始绘制选择框
                        self.selecting = True
                        self.selection_active = True
                        self.selection_start = mouse_event.position().toPoint()
                        self.selection_end = self.selection_start  # 初始化为相同点
                        self.update()  # 更新显示
                        return True
                    elif self.can_drag():
                        # 在非选择模式下，如果可以拖动图像，开始拖动
                        self.dragging = True
                        self.drag_start_position = mouse_event.position().toPoint()
                        self.setCursor(Qt.ClosedHandCursor)  # 更改鼠标光标为抓取状态
                        return True
            
            # 处理鼠标移动事件
            elif event.type() == QEvent.MouseMove:
                mouse_event = QMouseEvent(event)
                
                if self.selecting:
                    # 更新选择区域的结束点
                    self.selection_end = mouse_event.position().toPoint()
                    self.update()  # 更新显示
                    return True
                elif self.dragging:
                    # 计算鼠标移动的距离
                    delta = mouse_event.position().toPoint() - self.drag_start_position
                    # 更新偏移量
                    self.offset += delta
                    # 更新拖动起始位置
                    self.drag_start_position = mouse_event.position().toPoint()
                    # 更新显示
                    self.update_display()
                    return True
                # 如果鼠标悬停在图像上且可以拖动，显示手形光标
                elif not self.dragging and self.can_drag() and not self.selection_mode:
                    self.setCursor(Qt.OpenHandCursor)
            
            # 处理鼠标释放事件
            elif event.type() == QEvent.MouseButtonRelease:
                mouse_event = QMouseEvent(event)
                if mouse_event.button() == Qt.LeftButton:
                    if self.selecting:
                        # 完成选择区域的绘制
                        self.selecting = False
                        self.selection_end = mouse_event.position().toPoint()
                        
                        # 检查选择区域是否有效（不是一个点）
                        if self.selection_start.x() == self.selection_end.x() and self.selection_start.y() == self.selection_end.y():
                            self.selection_active = False
                        
                        self.update()  # 更新显示
                        return True
                    elif self.dragging:
                        self.dragging = False
                        # 恢复为打开手形光标，表示可以拖动但当前未拖动
                        if self.can_drag() and not self.selection_mode:
                            self.setCursor(Qt.OpenHandCursor)
                        elif self.selection_mode:
                            self.setCursor(Qt.CrossCursor)
                        else:
                            self.setCursor(Qt.ArrowCursor)
                        return True
            
            # 处理鼠标离开事件
            elif event.type() == QEvent.Leave:
                if not self.dragging and not self.selection_mode:
                    self.setCursor(Qt.ArrowCursor)
                return False
        
        return super().eventFilter(obj, event)

    def resizeEvent(self, event: QResizeEvent):
        """处理缩放标签的调整大小事件"""
        super().resizeEvent(event)
        # 图片大小随标签大小调整（如果允许缩放）
        if hasattr(self, 'pixmap') and self.pixmap() and self._can_zoom:
            self.updateLabelDimensions()

class NavigationFunctions:
    """提供导航和图像显示功能的类"""
    
    def __init__(self, label_before, label_after, label_result, text_log):
        """
        初始化导航功能
        
        Args:
            label_before: 前时相图像显示标签
            label_after: 后时相图像显示标签
            label_result: 结果图像显示标签
            text_log: 日志文本框
        """
        self.label_before = label_before
        self.label_after = label_after
        self.label_result = label_result
        self.text_log = text_log
        
        # 初始化图像文件路径
        self.file_path = None  # 前时相图像路径
        self.file_path_after = None  # 后时相图像路径
        
        # 初始化主题设置
        self.is_dark_theme = False  # 默认使用浅色主题
        
        # 初始化日志时间
        self.log_start_time = datetime.now()
        
        # 记录启动时间
        self.log_message("NavigationFunctions模块已初始化")
        
        # 确保标签是可缩放的
        self.replace_with_zoomable_label(self.label_before)
        self.replace_with_zoomable_label(self.label_after)
        
        # 初始化原始图像尺寸信息
        self.before_image_original_size = None
        self.after_image_original_size = None
        
        # 设置日志系统
        self.setup_logging()
        
    def replace_with_zoomable_label(self, label):
        """将标准标签替换为可缩放标签（如果还不是）"""
        if not isinstance(label, ZoomableLabel):
            # 如果标签尚未是ZoomableLabel实例，则替换它
            # 此处实际上是一个占位，因为我们已经在UI设计中使用了ZoomableLabel
            pass
    
    def setup_logging(self):
        """设置日志系统"""
        try:
            # 确保日志目录存在
            log_dir = "logs"
            if not os.path.exists(log_dir):
                os.makedirs(log_dir)
                
            # 创建一个带有时间戳的日志文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            log_file = os.path.join(log_dir, f"log_{timestamp}.txt")
            
            # 配置日志
            logging.basicConfig(
                filename=log_file,
                level=logging.INFO,
                format='%(asctime)s - %(levelname)s - %(message)s',
                encoding='utf-8'
            )
            
            # 记录日志系统启动
            self.log_message("=== 日志系统已启动 ===")
            
        except Exception as e:
            # 如果设置日志系统失败，仍然能够在UI中记录消息
            if self.text_log:
                self.text_log.append(f"设置日志系统失败: {str(e)}")
    
    def log_message(self, message):
        """记录消息到日志文件和界面"""
        try:
            # 记录到日志文件
            logging.info(message)
            
            # 记录到UI
            if self.text_log:
                # 记录消息前确保文本使用正确的颜色
                if hasattr(self, 'is_dark_theme'):
                    try:
                        from theme_manager import ThemeManager
                        # 根据主题获取正确的文本颜色
                        colors = ThemeManager.get_colors(self.is_dark_theme)
                        text_color = colors["text"]
                        # 使用HTML格式应用文本颜色
                        formatted_message = f"<span style='color:{text_color};'>{message}</span>"
                        # 添加格式化后的消息
                        self.text_log.append(formatted_message)
                    except Exception as e:
                        # 如果设置颜色失败，不影响主流程，使用默认文本添加
                        print(f"设置文本颜色失败: {str(e)}")
                        self.text_log.append(message)
                else:
                    # 如果没有主题属性，使用默认文本添加
                    self.text_log.append(message)
                
                # 自动滚动到底部
                self.text_log.verticalScrollBar().setValue(self.text_log.verticalScrollBar().maximum())
        except Exception as e:
            # 如果记录消息失败，至少尝试在UI中显示
            if self.text_log:
                self.text_log.append(f"记录消息失败: {str(e)}")
                self.text_log.append(f"原始消息: {message}")
                # 自动滚动到底部
                self.text_log.verticalScrollBar().setValue(self.text_log.verticalScrollBar().maximum())
    
    def update_image_display(self, is_before=None):
        """
        更新图像显示
        
        Args:
            is_before: 指定更新哪个图像。True表示前时相，False表示后时相，None表示两者都更新
        """
        try:
            # 更新前时相图像(如果is_before为True或None)
            if (is_before is None or is_before) and self.file_path:
                try:
                    pixmap = QPixmap(self.file_path)
                    if not pixmap.isNull():
                        self.label_before.set_pixmap(pixmap)
                        self.log_message(f"已更新前时相图像显示: {self.file_path}")
                    else:
                        self.log_message(f"无法加载前时相图像: {self.file_path}")
                except Exception as e:
                    self.log_message(f"显示前时相图像时出错: {str(e)}")
            
            # 更新后时相图像(如果is_before为False或None)
            if (is_before is None or is_before is False) and self.file_path_after:
                try:
                    pixmap = QPixmap(self.file_path_after)
                    if not pixmap.isNull():
                        self.label_after.set_pixmap(pixmap)
                        self.log_message(f"已更新后时相图像显示: {self.file_path_after}")
                    else:
                        self.log_message(f"无法加载后时相图像: {self.file_path_after}")
                except Exception as e:
                    self.log_message(f"显示后时相图像时出错: {str(e)}")
        
        except Exception as e:
            self.log_message(f"更新图像显示时出错: {str(e)}")
            import traceback
            self.log_message(traceback.format_exc())

    # 添加显示图像信息的方法
    def show_image_info(self):
        """显示图像的详细信息"""
        self.log_message("\n===== 图像详细信息 =====")
        
        # 显示前时相图像信息
        if self.file_path:
            self.log_message(f"\n前时相图像:")
            self.log_message(f"文件路径: {self.file_path}")
            
            if hasattr(self, 'before_image_original_size') and self.before_image_original_size:
                width, height = self.before_image_original_size
                self.log_message(f"图像尺寸: {width} x {height} 像素")           # 计算文件大小
        else:
            self.log_message("前时相图像未加载")
        
        # 显示后时相图像信息
        if self.file_path_after:
            self.log_message(f"\n后时相图像:")
            self.log_message(f"文件路径: {self.file_path_after}")
                
        else:
            self.log_message("后时相图像未加载")
        
        self.log_message("\n=========================")
        

    