import sys
import os
import json
import keyboard
import pyperclip
import mouse
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                           QPushButton, QLabel, QHBoxLayout, QMenu, QSystemTrayIcon,
                           QScrollArea)
from PyQt6.QtCore import Qt, QPoint, QTimer, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QIcon, QAction, QFont, QColor, QPainter, QPainterPath
from translate import Translator

class TranslationWindow(QWidget):
    def __init__(self, parent=None, text="", translation=""):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.initUI(text, translation)
        
    def initUI(self, text, translation):
        self.setFixedSize(300, 120)  # 更小的窗口尺寸
        
        # 创建主容器
        container = QWidget()
        container.setStyleSheet("""
            QWidget {
                background-color: white;
                border-radius: 8px;
                border: 1px solid #E0E0E0;
            }
        """)
        
        layout = QVBoxLayout(container)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)
        
        # 翻译结果
        translation_text = QLabel(translation)
        translation_text.setWordWrap(True)
        translation_text.setStyleSheet("""
            QLabel {
                color: #333;
                font-size: 14px;
                line-height: 1.5;
            }
        """)
        layout.addWidget(translation_text)
        
        # 设置主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(container)

class QuickToolbar(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('AI划词工具栏')
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # 初始化变量
        self.selected_text = ""
        self.translator = Translator(to_lang="zh")
        self.is_visible = False
        self.is_dragging = False
        self.drag_start_pos = None
        self.translation_window = None
        
        # 初始化UI
        self.initUI()
        
        # 创建系统托盘图标
        self.setup_tray_icon()
        
        # 初始化鼠标定时器
        self.mouse_timer = QTimer(self)
        self.mouse_timer.timeout.connect(self.check_clipboard)
        self.mouse_timer.start(500)  # 每500毫秒检查一次
        
        # 监听鼠标事件
        mouse.on_click(self.on_mouse_click)
        
        # 初始隐藏窗口
        self.hide()
        
        # 保存上一次剪贴板内容
        self.last_clipboard = ""
        
    def initUI(self):
        self.setFixedSize(180, 36)  # 更小的窗口尺寸
        
        # 创建主窗口部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建布局
        layout = QHBoxLayout(central_widget)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(4)
        
        # 创建按钮
        self.translate_btn = QPushButton('翻译')
        self.translate_btn.setFixedSize(40, 32)
        self.translate_btn.clicked.connect(self.translate_text)
        layout.addWidget(self.translate_btn)
        
        # 创建搜索按钮
        self.search_btn = QPushButton('搜索')
        self.search_btn.setFixedSize(40, 32)
        self.search_btn.clicked.connect(self.search_text)
        layout.addWidget(self.search_btn)
        
        # 创建复制按钮
        self.copy_btn = QPushButton('复制')
        self.copy_btn.setFixedSize(40, 32)
        self.copy_btn.clicked.connect(self.copy_text)
        layout.addWidget(self.copy_btn)
        
        # 设置按钮样式
        button_style = """
            QPushButton {
                background-color: #2C3E50;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 12px;
                padding: 4px;
            }
            QPushButton:hover {
                background-color: #34495E;
            }
            QPushButton:pressed {
                background-color: #1A252F;
            }
        """
        self.translate_btn.setStyleSheet(button_style)
        self.search_btn.setStyleSheet(button_style)
        self.copy_btn.setStyleSheet(button_style)
        
        # 设置窗口样式
        self.setStyleSheet("""
            QMainWindow {
                background-color: #2C3E50;
                border-radius: 4px;
                border: 1px solid #34495E;
            }
        """)
        
    def setup_tray_icon(self):
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(QIcon("icon.png"))
        
        # 创建托盘菜单
        tray_menu = QMenu()
        show_action = QAction("显示", self)
        show_action.triggered.connect(self.show)
        quit_action = QAction("退出", self)
        quit_action.triggered.connect(self.close)
        
        tray_menu.addAction(show_action)
        tray_menu.addSeparator()
        tray_menu.addAction(quit_action)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()
    
    def check_clipboard(self):
        try:
            # 获取当前剪贴板内容
            current_clipboard = pyperclip.paste()
            
            # 如果剪贴板内容变化且不为空
            if current_clipboard and current_clipboard != self.last_clipboard:
                self.last_clipboard = current_clipboard
                
                # 检查是否是用户选中的文本
                if keyboard.is_pressed('ctrl') or keyboard.is_pressed('shift'):
                    self.selected_text = current_clipboard
                    
                    # 获取鼠标位置
                    x, y = mouse.get_position()
                    
                    # 显示工具栏
                    self.show()
                    self.move(x - self.width() // 2, y - self.height() - 10)
                    self.is_visible = True
                    print(f"Toolbar shown with text: {self.selected_text}")  # Debug
        except Exception as e:
            print(f"Error checking clipboard: {str(e)}")
        
    def on_mouse_click(self, event):
        try:
            # 获取鼠标位置
            x, y = event.x, event.y
            print(f"Mouse clicked at: ({x}, {y})")  # Debug
            
            # 检查是否有文本选择
            selected_text = self.get_selected_text()
            print(f"Selected text: {selected_text}")  # Debug
            
            # 如果选中文本与上次不同，且不为空
            if selected_text and selected_text != self.selected_text:
                self.selected_text = selected_text
                
                # 显示窗口
                self.show()
                self.move(x - self.width() // 2, y - self.height() - 10)
                self.is_visible = True
                print("Toolbar shown.")  # Debug
            else:
                # 检查点击是否在工具栏外部
                if self.is_visible and not self.geometry().contains(QPoint(x, y)):
                    if self.translation_window and not self.translation_window.geometry().contains(QPoint(x, y)):
                        self.hide()  # 如果点击在工具栏和翻译窗口外部，隐藏工具栏
                        print("Toolbar hidden (clicked outside).")  # Debug
                
        except Exception as e:
            print(f"Error on mouse click: {str(e)}")
            
    def get_selected_text(self):
        try:
            # 尝试获取当前选中的文本
            # 首先检查剪贴板
            current_clipboard = pyperclip.paste()
            
            # 模拟Ctrl+C复制操作
            keyboard.press_and_release('ctrl+c')
            
            # 等待一小段时间让剪贴板更新
            QApplication.processEvents()
            
            # 获取复制后的剪贴板内容
            new_clipboard = pyperclip.paste()
            
            # 如果剪贴板内容变化，说明有文本被选中
            if new_clipboard != current_clipboard and new_clipboard.strip():
                return new_clipboard
            
            return ""
        except Exception as e:
            print(f"Error getting selected text: {str(e)}")
            return ""
        
    def translate_text(self):
        if not self.selected_text:
            return
            
        try:
            # 翻译文本
            translation = self.translator.translate(self.selected_text)
            print(f"Translation result: {translation}")  # Debug
            
            # 创建翻译结果窗口
            if self.translation_window:
                self.translation_window.close()
                
            self.translation_window = TranslationWindow(self, self.selected_text, translation)
            self.translation_window.move(self.x(), self.y() + self.height() + 5)
            self.translation_window.show()
            
        except Exception as e:
            print(f"Translation error: {str(e)}")
            
    def search_text(self):
        if not self.selected_text:
            return
            
        try:
            # 默认使用百度搜索
            search_url = 'https://www.baidu.com/s?wd=' + self.selected_text
            os.startfile(search_url)
        except Exception as e:
            print(f"Search error: {str(e)}")
            
    def copy_text(self):
        if self.selected_text:
            pyperclip.copy(self.selected_text)
            print(f"Copied text: {self.selected_text}")  # Debug
            
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_dragging = True
            self.drag_start_pos = event.globalPosition().toPoint()
            print("Mouse drag started.")  # Debug
            
    def mouseMoveEvent(self, event):
        if self.is_dragging:
            delta = event.globalPosition().toPoint() - self.drag_start_pos
            self.move(self.pos() + delta)
            self.drag_start_pos = event.globalPosition().toPoint()
            print(f"Mouse moved to: {self.pos()}")  # Debug
            
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_dragging = False
            print("Mouse drag ended.")  # Debug
            
    def hide(self):
        self.is_visible = False
        if self.translation_window:
            self.translation_window.close()
        super().hide()
        print("Toolbar hidden.")  # Debug
        
    def closeEvent(self, event):
        self.mouse_timer.stop()
        event.accept()
        print("Application closed.")  # Debug

if __name__ == '__main__':
    try:
        app = QApplication(sys.argv)
        toolbar = QuickToolbar()
        sys.exit(app.exec())
    except Exception as e:
        print(f"Error starting application: {str(e)}")
        input("Press Enter to exit...")