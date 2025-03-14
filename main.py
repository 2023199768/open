#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import time
import threading
import requests
import pyperclip
import keyboard
import mouse
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                           QHBoxLayout, QPushButton, QLabel, QSystemTrayIcon,
                           QMenu, QDialog, QTextEdit, QComboBox, QCheckBox)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QObject, QPoint, QSize
from PyQt6.QtGui import QIcon, QPixmap, QFont, QAction, QCursor

# 导入设置模块
from settings import app_settings

# 导入图标生成模块
try:
    from icon import create_icon
except ImportError:
    # 创建简单图标的函数
    def create_icon():
        """创建一个简单的图标"""
        from PIL import Image, ImageDraw
        
        # 创建一个32x32的RGBA图像（带透明度）
        icon = Image.new('RGBA', (32, 32), (0, 0, 0, 0))
        draw = ImageDraw.Draw(icon)
        
        # 绘制圆形背景
        draw.ellipse((2, 2, 30, 30), fill=(66, 133, 244, 255))
        
        # 绘制 "T" 字母（白色）
        draw.text((12, 6), "T", fill=(255, 255, 255, 255))
        
        # 保存图标
        icon_path = os.path.join(os.path.dirname(__file__), "icon.png")
        icon.save(icon_path)
        return icon_path


class TranslationEngine:
    """翻译引擎接口类"""
    
    def __init__(self):
        # 支持的翻译引擎及其API配置
        self.engines = {
            "百度翻译": {
                "url": "https://fanyi.baidu.com/#{lang_from}/{lang_to}/{query}",
                "direct": False  # 默认不直接跳转到网页
            },
            "谷歌翻译": {
                "url": "https://translate.google.com/?sl={lang_from}&tl={lang_to}&text={query}",
                "direct": False
            },
            "有道翻译": {
                "url": "https://fanyi.youdao.com/",
                "api_url": "https://fanyi.youdao.com/translate?&doctype=json&type={lang_from}2{lang_to}&i={query}",
                "direct": False
            }
        }
        self.current_engine = app_settings.get("translation", "default_engine", "百度翻译")
        
    def translate(self, text, from_lang="auto", to_lang="zh"):
        """进行文本翻译"""
        if not text or text.isspace():
            return "没有选中文本或文本为空"
            
        engine = self.engines.get(self.current_engine)
        if not engine:
            return "翻译引擎未配置"
        
        # 使用API进行翻译
        try:
            if self.current_engine == "有道翻译":
                api_url = engine["api_url"].format(lang_from=from_lang, lang_to=to_lang, query=text)
                response = requests.get(api_url)
                result = response.json()
                if "translateResult" in result and result["translateResult"]:
                    return result["translateResult"][0][0]["tgt"]
            
            # 如果没有API或API调用失败，返回一个模拟的翻译结果
            if self.current_engine == "百度翻译":
                return f"[百度翻译] {text} → {'英文翻译结果' if from_lang == 'zh' else '中文翻译结果'}"
            elif self.current_engine == "谷歌翻译":
                return f"[谷歌翻译] {text} → {'英文翻译结果' if from_lang == 'zh' else '中文翻译结果'}"
            
            return '正在翻译中...\n\n请稍候，或点击"打开网页"在浏览器中查看完整翻译。'
            
        except Exception as e:
            return f'翻译出错: {str(e)}\n\n您可以点击"打开网页"在浏览器中查看翻译。'
    
    def get_translation_url(self, text, from_lang="auto", to_lang="zh"):
        """获取翻译网页URL"""
        engine = self.engines.get(self.current_engine)
        if not engine:
            return ""
            
        # 编码查询参数
        import urllib.parse
        query = urllib.parse.quote(text)
        return engine["url"].format(lang_from=from_lang, lang_to=to_lang, query=query)
    
    def get_engines(self):
        """获取所有支持的翻译引擎名称"""
        return app_settings.get("translation", "available_engines", list(self.engines.keys()))
    
    def set_engine(self, engine_name):
        """设置当前使用的翻译引擎"""
        if engine_name in self.engines:
            self.current_engine = engine_name
            app_settings.set("translation", "default_engine", engine_name)
            return True
        return False


class ClipboardMonitor(QObject):
    """剪贴板监视器，检测用户选中的文本"""
    text_selected = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.last_text = ""
        self.timer = QTimer()
        
        # 直接设置检查间隔
        self.timer.timeout.connect(self.check_clipboard)
        self.timer.start(500)  # 固定500毫秒间隔
        
    def check_clipboard(self):
        """检查剪贴板变化"""
        try:
            current_text = pyperclip.paste()
            if current_text and current_text != self.last_text:
                self.last_text = current_text
                self.text_selected.emit(current_text)
        except Exception as e:
            print(f"剪贴板检查错误: {str(e)}")


class SelectionDetector(QObject):
    """鼠标选中文本检测器"""
    text_selected = pyqtSignal(str, QPoint)
    hide_toolbar = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.last_text = ""
        self.is_selecting = False
        self.check_enabled = True
        self.last_check_time = time.time()
        self.min_check_interval = 1.0  # 最小检查间隔，秒
        self.stored_clipboard = ""
        
        # 在启动时保存剪贴板内容
        try:
            self.stored_clipboard = pyperclip.paste()
        except:
            pass
            
        # 使用直接定义的热键，避免依赖设置
        try:
            print("注册热键和鼠标事件...")
            # 热键注册
            keyboard.add_hotkey("ctrl+shift+t", self.on_translate_hotkey)
            keyboard.add_hotkey("ctrl+shift+c", self.on_copy_hotkey)
            keyboard.add_hotkey("esc", self.on_escape_hotkey)
            
            # 阻止注册重复的组合键
            if not hasattr(keyboard, '_hotkeys') or 'ctrl+c' not in str(keyboard._hotkeys):
                keyboard.add_hotkey("ctrl+c", self.on_system_copy)
            
            # 鼠标事件注册 - 这里使用库的事件而不是定时器
            mouse.on_click(self.on_mouse_click)
            mouse.on_button(self.on_mouse_button, buttons=('left',), types=('up',))
            
            print("热键和鼠标事件注册成功")
        except Exception as e:
            print(f"注册热键或鼠标事件失败: {str(e)}")
    
    def on_mouse_click(self):
        """处理鼠标点击事件，隐藏工具栏"""
        # 如果点击时没有正在选择文本，则隐藏工具栏
        if not self.is_selecting:
            self.hide_toolbar.emit()
    
    def on_mouse_button(self, event):
        """处理鼠标按钮事件"""
        # 鼠标左键释放时检查是否有选中文本
        if event == mouse.ButtonEvent.up and time.time() - self.last_check_time >= self.min_check_interval:
            self.last_check_time = time.time()
            # 延迟一小段时间再检查，确保系统有时间完成选择
            QTimer.singleShot(100, self.check_selection)
    
    def on_system_copy(self):
        """系统复制事件的处理器"""
        # 当用户按下Ctrl+C时，我们等待一小段时间然后检查剪贴板变化
        QTimer.singleShot(100, self.check_clipboard_change)
    
    def check_clipboard_change(self):
        """检查剪贴板是否发生变化"""
        try:
            current_text = pyperclip.paste()
            if current_text and current_text != self.stored_clipboard and not current_text.isspace():
                self.stored_clipboard = current_text
                cursor_pos = QCursor().pos()
                self.text_selected.emit(current_text, cursor_pos)
                self.is_selecting = True
        except Exception as e:
            print(f"检查剪贴板变化错误: {str(e)}")
    
    def check_selection(self):
        """检查是否有文本被选中，使用单次操作"""
        if not self.check_enabled:
            return
            
        try:
            # 暂时禁用检查以避免递归
            self.check_enabled = False
            
            # 保存原始剪贴板内容
            original_text = pyperclip.paste()
            self.stored_clipboard = original_text
            
            # 模拟一次复制操作
            keyboard.press_and_release('ctrl+c')
            
            # 使用QTimer延迟获取剪贴板，而不是阻塞线程
            QTimer.singleShot(100, lambda: self.finish_check_selection(original_text))
        except Exception as e:
            print(f"开始检查选中文本错误: {str(e)}")
            self.check_enabled = True
    
    def finish_check_selection(self, original_text):
        """完成文本选择检查过程"""
        try:
            # 获取新的剪贴板内容
            new_text = pyperclip.paste()
            
            # 如果有新的文本被选中
            if new_text and new_text != self.last_text and not new_text.isspace() and new_text != original_text:
                self.last_text = new_text
                cursor_pos = QCursor().pos()
                self.text_selected.emit(new_text, cursor_pos)
                self.is_selecting = True
            else:
                self.is_selecting = False
                
            # 如果剪贴板内容被更改，恢复原始内容
            if original_text != new_text:
                pyperclip.copy(original_text)
        except Exception as e:
            print(f"完成检查选中文本错误: {str(e)}")
        finally:
            # 重新启用检查
            self.check_enabled = True
    
    def on_translate_hotkey(self):
        """翻译快捷键响应"""
        self.check_selection()
    
    def on_copy_hotkey(self):
        """复制快捷键响应"""
        # 暂时标记为正在选择
        self.is_selecting = True
        QTimer.singleShot(300, lambda: setattr(self, 'is_selecting', False))
    
    def on_escape_hotkey(self):
        """ESC快捷键响应，发送空文本信号隐藏工具栏"""
        self.hide_toolbar.emit()
        self.text_selected.emit("", QPoint(0, 0))


class TranslationToolbar(QWidget):
    """翻译工具栏窗口"""
    translate_requested = pyqtSignal(str)
    search_requested = pyqtSignal(str)
    explain_requested = pyqtSignal(str)
    copy_requested = pyqtSignal(str)
    color_requested = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.selected_text = ""
        self.last_pos = QPoint(0, 0)
        self.hide_timer = QTimer(self)
        self.hide_timer.setSingleShot(True)
        self.hide_timer.timeout.connect(self.check_should_hide)
        self.initUI()
        
    def initUI(self):
        """初始化用户界面"""
        # 设置无边框窗口
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # 从设置中获取不透明度
        opacity = app_settings.get("ui", "toolbar_opacity", 0.9)
        self.setWindowOpacity(opacity)
        
        # 主布局
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(6)
        
        # 圆形按钮样式
        circle_button_style = """
            QPushButton {
                background-color: white;
                border: 1px solid rgba(0, 0, 0, 0.1);
                border-radius: 16px;
                padding: 2px;
                font-size: 14px;
                color: #333;
                min-width: 32px;
                min-height: 32px;
                max-width: 32px;
                max-height: 32px;
                text-align: center;
            }
            QPushButton:hover {
                background-color: #f0f0f0;
                border: 1px solid rgba(0, 0, 0, 0.2);
            }
            QPushButton:pressed {
                background-color: #e0e0e0;
            }
        """
        
        # 创建按钮容器
        buttons_widget = QWidget()
        buttons_widget.setStyleSheet("""
            background-color: white;
            border-radius: 20px;
            border: 1px solid rgba(0, 0, 0, 0.1);
        """)
        buttons_layout = QHBoxLayout(buttons_widget)
        buttons_layout.setContentsMargins(10, 5, 10, 5)
        buttons_layout.setSpacing(8)
        
        # AI搜索按钮
        self.ai_search_btn = QPushButton("AI搜索")
        self.ai_search_btn.setStyleSheet(circle_button_style)
        self.ai_search_btn.setIcon(self.get_icon_for_button("ai"))
        self.ai_search_btn.clicked.connect(self.on_search_clicked)
        
        # 解读按钮
        self.explain_btn = QPushButton("解读")
        self.explain_btn.setStyleSheet(circle_button_style)
        self.explain_btn.setIcon(self.get_icon_for_button("explain"))
        self.explain_btn.clicked.connect(self.on_explain_clicked)
        
        # 翻译按钮
        self.translate_btn = QPushButton("翻译")
        self.translate_btn.setStyleSheet(circle_button_style)
        self.translate_btn.setIcon(self.get_icon_for_button("translate"))
        self.translate_btn.clicked.connect(self.on_translate_clicked)
        
        # 润色按钮
        self.color_btn = QPushButton("润色")
        self.color_btn.setStyleSheet(circle_button_style)
        self.color_btn.setIcon(self.get_icon_for_button("color"))
        self.color_btn.clicked.connect(self.on_color_clicked)
        
        # 复制按钮
        self.copy_btn = QPushButton("复制")
        self.copy_btn.setStyleSheet(circle_button_style)
        self.copy_btn.setIcon(self.get_icon_for_button("copy"))
        self.copy_btn.clicked.connect(self.on_copy_clicked)
        
        # 发送到手机按钮
        self.send_btn = QPushButton("发送")
        self.send_btn.setStyleSheet(circle_button_style)
        self.send_btn.setIcon(self.get_icon_for_button("send"))
        self.send_btn.clicked.connect(self.on_send_clicked)
        
        # 收藏按钮
        self.favorite_btn = QPushButton("收藏")
        self.favorite_btn.setStyleSheet(circle_button_style)
        self.favorite_btn.setIcon(self.get_icon_for_button("favorite"))
        self.favorite_btn.clicked.connect(self.on_favorite_clicked)
        
        # 添加按钮到布局
        buttons_layout.addWidget(self.ai_search_btn)
        buttons_layout.addWidget(self.explain_btn)
        buttons_layout.addWidget(self.translate_btn)
        buttons_layout.addWidget(self.color_btn)
        buttons_layout.addWidget(self.copy_btn)
        buttons_layout.addWidget(self.send_btn)
        buttons_layout.addWidget(self.favorite_btn)
        
        # 添加更多选项按钮
        self.more_btn = QPushButton("...")
        self.more_btn.setStyleSheet(circle_button_style)
        self.more_btn.clicked.connect(self.on_more_clicked)
        buttons_layout.addWidget(self.more_btn)
        
        main_layout.addWidget(buttons_widget)
        self.setLayout(main_layout)
        self.adjustSize()
    
    def get_icon_for_button(self, icon_type):
        """获取按钮图标"""
        # 这里可以根据需要加载实际的图标
        # 简单实现，返回空图标
        return QIcon()
    
    def show_at_position(self, text, position):
        """在指定位置显示工具栏"""
        if not text or text.isspace():
            self.hide()
            return
            
        self.selected_text = text
        
        # 如果位置接近上次显示位置，不移动工具栏
        if not self.isVisible() or (position - self.last_pos).manhattanLength() > 20:
            # 从设置中获取工具栏位置偏移量
            offset_y = app_settings.get("ui", "toolbar_position_offset_y", 20)
            
            # 调整窗口位置，确保在屏幕内
            screen_geometry = QApplication.primaryScreen().geometry()
            x = min(position.x(), screen_geometry.width() - self.width())
            y = min(position.y() + offset_y, screen_geometry.height() - self.height())
            
            self.move(x, y)
            self.last_pos = position
        
        # 如果已经可见，不需要重新显示
        if not self.isVisible():
            self.show()
            self.raise_()
        
        # 开始隐藏计时器
        self.hide_timer.start(5000)  # 5秒后检查是否应该隐藏
    
    def check_should_hide(self):
        """检查是否应该隐藏工具栏"""
        # 如果鼠标不在工具栏上，隐藏它
        if not self.underMouse():
            self.hide()
    
    def on_translate_clicked(self):
        """处理翻译按钮点击事件"""
        if self.selected_text:
            self.translate_requested.emit(self.selected_text)
    
    def on_copy_clicked(self):
        """处理复制按钮点击事件"""
        if self.selected_text:
            pyperclip.copy(self.selected_text)
            self.copy_requested.emit(self.selected_text)
    
    def on_search_clicked(self):
        """处理搜索按钮点击事件"""
        if self.selected_text:
            self.search_requested.emit(self.selected_text)
    
    def on_explain_clicked(self):
        """处理解读按钮点击事件"""
        if self.selected_text:
            self.explain_requested.emit(self.selected_text)
    
    def on_color_clicked(self):
        """处理润色按钮点击事件"""
        if self.selected_text:
            self.color_requested.emit(self.selected_text)
    
    def on_send_clicked(self):
        """处理发送到手机按钮点击事件"""
        # 提示功能未实现
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.information(self, "功能提示", "发送到手机功能尚未实现")
    
    def on_favorite_clicked(self):
        """处理收藏按钮点击事件"""
        # 提示功能未实现
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.information(self, "功能提示", "收藏功能尚未实现")
    
    def on_more_clicked(self):
        """处理更多按钮点击事件"""
        # 提示功能未实现
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.information(self, "功能提示", "更多功能尚未实现")

    def enterEvent(self, event):
        """鼠标进入事件"""
        # 停止隐藏计时器
        self.hide_timer.stop()
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        """鼠标离开事件"""
        # 启动隐藏计时器
        self.hide_timer.start(2000)  # 2秒后检查是否应该隐藏
        super().leaveEvent(event)


class TranslationWindow(QDialog):
    """翻译结果窗口"""
    
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool | Qt.WindowType.WindowStaysOnTopHint)
        self.source_text_content = ""
        self.from_lang = "auto"
        self.to_lang = "zh"
        self.is_search_mode = False
        self.search_url = ""
        self.hide_timer = QTimer(self)
        self.hide_timer.setSingleShot(True)
        self.hide_timer.timeout.connect(self.check_should_hide)
        self.initUI()
        
    def initUI(self):
        """初始化用户界面"""
        # 从设置中获取不透明度
        opacity = app_settings.get("ui", "translation_window_opacity", 0.95)
        self.setWindowOpacity(opacity)
        
        # 设置窗口样式
        self.setStyleSheet("""
            QDialog {
                background-color: rgba(255, 255, 255, 0.95);
                border: 1px solid rgba(0, 0, 0, 0.1);
                border-radius: 8px;
            }
        """)
        
        # 主布局
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        
        # 标题栏
        title_layout = QHBoxLayout()
        
        self.title_label = QLabel("翻译结果")
        self.title_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        
        self.close_btn = QPushButton("×")
        self.close_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #666;
                font-size: 16px;
                font-weight: bold;
                border: none;
                padding: 0px 5px;
            }
            QPushButton:hover {
                color: #000;
            }
        """)
        self.close_btn.clicked.connect(self.close)
        
        title_layout.addWidget(self.title_label)
        title_layout.addStretch()
        title_layout.addWidget(self.close_btn)
        
        # 原文
        self.source_label = QLabel("原文:")
        self.source_label.setStyleSheet("font-size: 12px; color: #666;")
        
        self.source_text = QTextEdit()
        self.source_text.setReadOnly(True)
        self.source_text.setStyleSheet("""
            QTextEdit {
                background-color: rgba(245, 245, 245, 0.8);
                border: 1px solid rgba(0, 0, 0, 0.1);
                border-radius: 4px;
                padding: 5px;
                font-size: 13px;
            }
        """)
        self.source_text.setMaximumHeight(80)
        
        # 翻译结果
        self.result_label = QLabel("译文:")
        self.result_label.setStyleSheet("font-size: 12px; color: #666;")
        
        self.result_text = QTextEdit()
        self.result_text.setReadOnly(True)
        self.result_text.setStyleSheet("""
            QTextEdit {
                background-color: rgba(245, 245, 245, 0.8);
                border: 1px solid rgba(0, 0, 0, 0.1);
                border-radius: 4px;
                padding: 5px;
                font-size: 13px;
            }
        """)
        
        # 翻译引擎选择
        engine_layout = QHBoxLayout()
        
        self.engine_combo = QComboBox()
        # 从设置中获取可用的翻译引擎
        engines = app_settings.get("translation", "available_engines", ["百度翻译", "谷歌翻译", "有道翻译"])
        self.engine_combo.addItems(engines)
        # 设置默认引擎
        default_engine = app_settings.get("translation", "default_engine", "百度翻译")
        index = self.engine_combo.findText(default_engine)
        if index >= 0:
            self.engine_combo.setCurrentIndex(index)
            
        self.engine_combo.setStyleSheet("""
            QComboBox {
                background-color: rgba(245, 245, 245, 0.8);
                border: 1px solid rgba(0, 0, 0, 0.1);
                border-radius: 4px;
                padding: 3px 10px;
                font-size: 12px;
            }
        """)
        self.engine_combo.currentTextChanged.connect(self.on_engine_changed)
        
        self.lang_toggle = QPushButton("中 ⟷ 英")
        self.lang_toggle.setStyleSheet("""
            QPushButton {
                background-color: rgba(245, 245, 245, 0.8);
                border: 1px solid rgba(0, 0, 0, 0.1);
                border-radius: 4px;
                padding: 3px 10px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: rgba(235, 235, 235, 0.8);
            }
        """)
        self.lang_toggle.clicked.connect(self.on_toggle_language)
        
        engine_layout.addWidget(self.engine_combo)
        engine_layout.addWidget(self.lang_toggle)
        
        # 添加打开网页按钮
        self.open_web_btn = QPushButton("在浏览器中打开")
        self.open_web_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(245, 245, 245, 0.8);
                border: 1px solid rgba(0, 0, 0, 0.1);
                border-radius: 4px;
                padding: 5px 10px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: rgba(235, 235, 235, 0.8);
            }
        """)
        self.open_web_btn.clicked.connect(self.open_in_browser)
        
        # 添加所有组件到主布局
        layout.addLayout(title_layout)
        layout.addWidget(self.source_label)
        layout.addWidget(self.source_text)
        layout.addWidget(self.result_label)
        layout.addWidget(self.result_text)
        layout.addLayout(engine_layout)
        layout.addWidget(self.open_web_btn)
        
        self.setLayout(layout)
        
        # 从设置中获取窗口大小
        size = app_settings.get("ui", "translation_window_size", [400, 350])
        self.resize(size[0], size[1])
        
    def set_translation(self, source_text, translated_text, from_lang="auto", to_lang="zh"):
        """设置翻译内容"""
        self.is_search_mode = False
        self.title_label.setText("翻译结果")
        self.source_label.setText("原文:")
        self.result_label.setText("译文:")
        self.open_web_btn.setText("在浏览器中打开")
        
        self.source_text.setText(source_text)
        self.result_text.setText(translated_text)
        self.source_text_content = source_text
        self.from_lang = from_lang
        self.to_lang = to_lang
        
    def on_engine_changed(self, engine_name):
        """处理翻译引擎更改事件"""
        # 保存用户选择的翻译引擎
        app_settings.set("translation", "default_engine", engine_name)
        
    def on_toggle_language(self):
        """切换翻译语言方向"""
        # 中英文互换
        source_text = self.source_text.toPlainText()
        result_text = self.result_text.toPlainText()
        
        if source_text and result_text:
            self.source_text.setText(result_text)
            self.result_text.setText(source_text)
        
    def open_in_browser(self):
        """在浏览器中打开翻译或搜索结果"""
        if self.is_search_mode and self.search_url:
            import webbrowser
            webbrowser.open(self.search_url)
            return
            
        if not self.source_text_content:
            return
            
        engine_name = self.engine_combo.currentText()
        translation_engine = TranslationEngine()
        translation_engine.set_engine(engine_name)
        url = translation_engine.get_translation_url(self.source_text_content, self.from_lang, self.to_lang)
        
        if url:
            import webbrowser
            webbrowser.open(url)
    
    def set_search_result(self, query, search_engine="百度"):
        """设置搜索内容"""
        self.is_search_mode = True
        self.source_text_content = query
        self.title_label.setText(f"{search_engine}搜索结果")
        self.source_label.setText("搜索词:")
        self.result_label.setText("摘要:")
        self.source_text.setText(query)
        
        # 构建搜索URL
        import urllib.parse
        encoded_query = urllib.parse.quote(query)
        search_engines = app_settings.get("search", "available_search_engines", {
            "百度": "https://www.baidu.com/s?wd={query}",
            "谷歌": "https://www.google.com/search?q={query}",
            "必应": "https://www.bing.com/search?q={query}"
        })
        self.search_url = search_engines.get(search_engine, "https://www.baidu.com/s?wd={query}").format(query=encoded_query)
        
        # 设置摘要文本
        self.result_text.setText(f'正在搜索"{query}"...\n\n点击"在浏览器中打开"查看完整搜索结果。')
        self.open_web_btn.setText("在浏览器中查看搜索结果")
    
    def mousePressEvent(self, event):
        """处理鼠标按下事件，用于拖动窗口"""
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()
            
    def mouseMoveEvent(self, event):
        """处理鼠标移动事件，用于拖动窗口"""
        if event.buttons() & Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()
            
    def resizeEvent(self, event):
        """窗口大小改变事件"""
        # 保存窗口大小到设置
        size = [self.width(), self.height()]
        app_settings.set("ui", "translation_window_size", size)
        super().resizeEvent(event)

    def set_explanation(self, source_text, explanation_text):
        """设置解释内容"""
        self.is_search_mode = False
        self.title_label.setText("文本解释")
        self.source_label.setText("原文:")
        self.result_label.setText("解释:")
        self.open_web_btn.setText("了解更多")
        
        self.source_text.setText(source_text)
        self.result_text.setText(explanation_text)
        self.source_text_content = source_text
    
    def set_polished(self, source_text, polished_text):
        """设置润色内容"""
        self.is_search_mode = False
        self.title_label.setText("文本润色")
        self.source_label.setText("原文:")
        self.result_label.setText("润色后:")
        self.open_web_btn.setText("复制润色结果")
        
        self.source_text.setText(source_text)
        self.result_text.setText(polished_text)
        self.source_text_content = source_text

    def enterEvent(self, event):
        """鼠标进入事件"""
        # 停止隐藏计时器
        self.hide_timer.stop()
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        """鼠标离开事件"""
        # 启动隐藏计时器
        self.hide_timer.start(3000)  # 3秒后检查是否应该隐藏
        super().leaveEvent(event)
    
    def check_should_hide(self):
        """检查是否应该隐藏窗口"""
        # 如果鼠标不在窗口上，隐藏它
        if not self.underMouse():
            self.close()


class SystemTrayApp(QMainWindow):
    """系统托盘应用程序"""
    
    def __init__(self):
        super().__init__()
        # 注意：移除了可能会干扰的剪贴板监视器
        # self.clipboard_monitor = ClipboardMonitor()
        self.selection_detector = SelectionDetector()
        self.translation_engine = TranslationEngine()
        self.toolbar = TranslationToolbar()
        self.translation_window = TranslationWindow()
        
        self.initUI()
        self.connectSignals()
        
    def initUI(self):
        """初始化用户界面"""
        self.setWindowTitle("划词翻译工具")
        self.resize(400, 300)
        
        # 创建系统托盘图标
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setToolTip("划词翻译工具")
        
        # 创建托盘菜单
        tray_menu = QMenu()
        
        self.settings_action = QAction("设置", self)
        self.settings_action.triggered.connect(self.show_settings)
        
        self.about_action = QAction("关于", self)
        self.about_action.triggered.connect(self.show_about)
        
        self.exit_action = QAction("退出", self)
        self.exit_action.triggered.connect(self.close_application)
        
        tray_menu.addAction(self.settings_action)
        tray_menu.addAction(self.about_action)
        tray_menu.addSeparator()
        tray_menu.addAction(self.exit_action)
        
        self.tray_icon.setContextMenu(tray_menu)
        
        # 设置图标
        self.set_tray_icon()
        
        # 显示系统托盘图标
        self.tray_icon.show()
        
        # 保持应用在后台运行，隐藏主窗口
        self.hide()
        
    def set_tray_icon(self):
        """设置系统托盘图标"""
        # 创建一个简单的图标
        icon_path = os.path.join(os.path.dirname(__file__), "icon.png")
        
        # 如果图标不存在，创建一个
        if not os.path.exists(icon_path):
            try:
                icon_path = create_icon()
            except Exception as e:
                print(f"创建图标出错: {str(e)}")
                # 使用默认图标
                self.tray_icon.setIcon(QIcon.fromTheme("accessories-dictionary"))
                return
                
        # 设置图标
        self.tray_icon.setIcon(QIcon(icon_path))
    
    def connectSignals(self):
        """连接信号和槽"""
        # 连接文本选择信号到工具栏显示
        self.selection_detector.text_selected.connect(self.toolbar.show_at_position)
        
        # 连接隐藏工具栏信号
        self.selection_detector.hide_toolbar.connect(self.hide_toolbar)
        
        # 连接翻译和搜索请求信号
        self.toolbar.translate_requested.connect(self.show_translation)
        self.toolbar.search_requested.connect(self.show_search_result)
        self.toolbar.explain_requested.connect(self.show_explanation)
        self.toolbar.color_requested.connect(self.show_polished)
        
        # 连接系统托盘图标的事件
        self.tray_icon.activated.connect(self.on_tray_icon_activated)
        
    def on_tray_icon_activated(self, reason):
        """处理系统托盘图标激活事件"""
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            # 单击托盘图标，显示/隐藏主窗口
            if self.isVisible():
                self.hide()
            else:
                self.show()
                self.raise_()
                self.activateWindow()
        
    def hide_toolbar(self):
        """隐藏工具栏"""
        self.toolbar.hide()
        
    def show_translation(self, text):
        """显示翻译结果窗口"""
        if not text:
            return
            
        # 自动检测源语言
        if app_settings.get("translation", "auto_detect_language", True):
            # 简单判断是否为中文
            is_chinese = any('\u4e00' <= char <= '\u9fff' for char in text)
            from_lang = "zh" if is_chinese else "en"
            to_lang = "en" if is_chinese else "zh"
        else:
            # 使用默认语言设置
            from_lang = app_settings.get("translation", "default_source_lang", "auto")
            to_lang = app_settings.get("translation", "default_target_lang", "zh")
        
        # 调用翻译引擎
        engine_name = self.translation_window.engine_combo.currentText()
        self.translation_engine.set_engine(engine_name)
        
        # 获取翻译结果
        translation_result = self.translation_engine.translate(text, from_lang, to_lang)
        
        # 显示翻译结果在浮动窗口中
        self.translation_window.set_translation(text, translation_result, from_lang, to_lang)
        
        # 定位窗口位置
        cursor_pos = QCursor().pos()
        screen_geometry = QApplication.primaryScreen().geometry()
        window_x = min(cursor_pos.x(), screen_geometry.width() - self.translation_window.width())
        window_y = min(cursor_pos.y() + 30, screen_geometry.height() - self.translation_window.height())
        self.translation_window.move(window_x, window_y)
        
        self.translation_window.show()
        self.translation_window.raise_()
    
    def show_search_result(self, query):
        """显示搜索结果窗口"""
        if not query:
            return
        
        # 获取默认搜索引擎
        default_engine = app_settings.get("search", "default_search_engine", "百度")
        
        # 设置搜索结果
        self.translation_window.set_search_result(query, default_engine)
        
        # 定位窗口位置
        cursor_pos = QCursor().pos()
        screen_geometry = QApplication.primaryScreen().geometry()
        window_x = min(cursor_pos.x(), screen_geometry.width() - self.translation_window.width())
        window_y = min(cursor_pos.y() + 30, screen_geometry.height() - self.translation_window.height())
        self.translation_window.move(window_x, window_y)
        
        self.translation_window.show()
        self.translation_window.raise_()
    
    def show_explanation(self, text):
        """显示文本解释窗口"""
        if not text:
            return
            
        # 设置解释结果
        explanation = f'解释"{text}"\n\n这是一段自动生成的解释内容，用于演示功能。实际应用中可以接入AI解释API。'
        self.translation_window.set_explanation(text, explanation)
        
        # 定位窗口位置
        cursor_pos = QCursor().pos()
        screen_geometry = QApplication.primaryScreen().geometry()
        window_x = min(cursor_pos.x(), screen_geometry.width() - self.translation_window.width())
        window_y = min(cursor_pos.y() + 30, screen_geometry.height() - self.translation_window.height())
        self.translation_window.move(window_x, window_y)
        
        self.translation_window.show()
        self.translation_window.raise_()
    
    def show_polished(self, text):
        """显示润色结果窗口"""
        if not text:
            return
            
        # 设置润色结果
        polished = f'润色"{text}"\n\n这是润色后的内容，用于演示功能。实际应用中可以接入AI润色API。'
        self.translation_window.set_polished(text, polished)
        
        # 定位窗口位置
        cursor_pos = QCursor().pos()
        screen_geometry = QApplication.primaryScreen().geometry()
        window_x = min(cursor_pos.x(), screen_geometry.width() - self.translation_window.width())
        window_y = min(cursor_pos.y() + 30, screen_geometry.height() - self.translation_window.height())
        self.translation_window.move(window_x, window_y)
        
        self.translation_window.show()
        self.translation_window.raise_()
    
    def show_settings(self):
        """显示设置窗口"""
        from settings_ui import SettingsDialog
        settings_dialog = SettingsDialog(self)
        if settings_dialog.exec():
            # 如果用户保存了设置，应用一些可以即时生效的设置
            
            # 更新工具栏不透明度
            opacity = app_settings.get("ui", "toolbar_opacity", 0.9)
            self.toolbar.setWindowOpacity(opacity)
            
            # 更新翻译窗口不透明度
            opacity = app_settings.get("ui", "translation_window_opacity", 0.95)
            self.translation_window.setWindowOpacity(opacity)
            
            # 更新翻译窗口大小
            size = app_settings.get("ui", "translation_window_size", [400, 350])
            self.translation_window.resize(size[0], size[1])
            
            # 更新翻译引擎
            engine = app_settings.get("translation", "default_engine", "百度翻译")
            self.translation_engine.set_engine(engine)
    
    def show_about(self):
        """显示关于窗口"""
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.about(self, "关于划词翻译工具", 
            """<b>划词翻译工具</b> v1.0
            <p>一款跨浏览器、跨软件的划词翻译工具。</p>
            <p>支持翻译、搜索等功能，让您的阅读更加便捷。</p>
            <p>Copyright © 2023</p>""")
    
    def close_application(self):
        """关闭应用程序"""
        try:
            # 停止所有线程和监听器
            print("正在关闭应用...")
            keyboard.unhook_all()
            mouse.unhook_all()
            
            # 确保清理所有资源
            self.selection_detector.check_enabled = False
            self.toolbar.hide()
            self.translation_window.close()
            
            # 关闭应用
            QApplication.quit()
        except Exception as e:
            print(f"关闭应用出错: {str(e)}")
            QApplication.quit()
    
    def closeEvent(self, event):
        """处理窗口关闭事件"""
        # 隐藏窗口而不是关闭应用
        self.hide()
        event.ignore()


def main():
    """主函数"""
    try:
        # 为提高性能，降低动画效果和视觉效果
        os.environ['QT_QUICK_CONTROLS_STYLE'] = 'Basic'
        os.environ['QT_QUICK_CONTROLS_MOBILE'] = '0'
        
        # 检查是否已有实例在运行
        app = QApplication(sys.argv)
        app.setQuitOnLastWindowClosed(False)
        
        # 在PyQt6中，高DPI缩放属性名称已更改，这里移除不兼容的属性设置
        # app.setAttribute(Qt.ApplicationAttribute.AA_DisableHighDpiScaling, True)
        # app.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True)
        
        print("创建应用窗口...")
        # 创建并显示应用
        app_window = SystemTrayApp()
        
        # 设置应用图标
        icon_path = os.path.join(os.path.dirname(__file__), "icon.png")
        if os.path.exists(icon_path):
            print(f"加载图标: {icon_path}")
            app.setWindowIcon(QIcon(icon_path))
        else:
            print("创建默认图标...")
            icon_path = create_icon()
            app.setWindowIcon(QIcon(icon_path))
        
        # 显示一个欢迎消息
        print("显示欢迎消息...")
        app_window.tray_icon.showMessage(
            "划词翻译工具已启动",
            "选择文本后将显示翻译工具栏，按Ctrl+Shift+T快速翻译选中文本。",
            QSystemTrayIcon.MessageIcon.Information,
            3000
        )
        
        print("启动应用主循环...")
        # 执行应用
        sys.exit(app.exec())
    except Exception as e:
        print(f"应用启动失败: {str(e)}")
        import traceback
        traceback.print_exc()
        input("按任意键退出...")


if __name__ == "__main__":
    main() 