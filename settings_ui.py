#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, 
                           QLabel, QComboBox, QCheckBox, QSpinBox, QDoubleSpinBox,
                           QPushButton, QGroupBox, QFormLayout, QSlider, QLineEdit,
                           QListWidget, QListWidgetItem, QMessageBox)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QIcon

from settings import app_settings

class SettingsDialog(QDialog):
    """设置对话框"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("设置")
        self.setMinimumSize(500, 400)
        self.setup_ui()
        
    def setup_ui(self):
        """设置用户界面"""
        main_layout = QVBoxLayout()
        
        # 创建选项卡
        tab_widget = QTabWidget(self)
        
        # 创建各个选项卡内容
        general_tab = self.create_general_tab()
        translation_tab = self.create_translation_tab()
        ui_tab = self.create_ui_tab()
        hotkeys_tab = self.create_hotkeys_tab()
        search_tab = self.create_search_tab()
        
        # 添加选项卡
        tab_widget.addTab(general_tab, "基本设置")
        tab_widget.addTab(translation_tab, "翻译设置")
        tab_widget.addTab(ui_tab, "界面设置")
        tab_widget.addTab(hotkeys_tab, "快捷键")
        tab_widget.addTab(search_tab, "搜索引擎")
        
        # 添加按钮
        button_layout = QHBoxLayout()
        
        self.reset_btn = QPushButton("重置默认")
        self.reset_btn.clicked.connect(self.reset_settings)
        
        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.clicked.connect(self.reject)
        
        self.save_btn = QPushButton("保存")
        self.save_btn.clicked.connect(self.save_settings)
        self.save_btn.setDefault(True)
        
        button_layout.addWidget(self.reset_btn)
        button_layout.addStretch()
        button_layout.addWidget(self.cancel_btn)
        button_layout.addWidget(self.save_btn)
        
        # 设置主布局
        main_layout.addWidget(tab_widget)
        main_layout.addLayout(button_layout)
        
        self.setLayout(main_layout)
        
    def create_general_tab(self):
        """创建基本设置选项卡"""
        tab = QWidget()
        layout = QVBoxLayout()
        
        # 剪贴板设置
        clipboard_group = QGroupBox("剪贴板设置")
        clipboard_layout = QFormLayout()
        
        self.use_clipboard_check = QCheckBox()
        self.use_clipboard_check.setChecked(app_settings.get("clipboard", "use_clipboard_for_detection", True))
        clipboard_layout.addRow("使用剪贴板检测选中文本:", self.use_clipboard_check)
        
        self.clipboard_interval = QSpinBox()
        self.clipboard_interval.setRange(100, 2000)
        self.clipboard_interval.setSingleStep(100)
        self.clipboard_interval.setValue(app_settings.get("clipboard", "check_interval_ms", 500))
        self.clipboard_interval.setSuffix(" 毫秒")
        clipboard_layout.addRow("剪贴板检查间隔:", self.clipboard_interval)
        
        clipboard_group.setLayout(clipboard_layout)
        
        # 启动设置
        startup_group = QGroupBox("启动设置")
        startup_layout = QFormLayout()
        
        self.autostart_check = QCheckBox()
        self.autostart_check.setChecked(False)  # TODO: 检查是否已设置自启动
        startup_layout.addRow("开机自启动:", self.autostart_check)
        
        startup_group.setLayout(startup_layout)
        
        # 添加各组到布局
        layout.addWidget(clipboard_group)
        layout.addWidget(startup_group)
        layout.addStretch()
        
        tab.setLayout(layout)
        return tab
        
    def create_translation_tab(self):
        """创建翻译设置选项卡"""
        tab = QWidget()
        layout = QVBoxLayout()
        
        # 翻译引擎设置
        engine_group = QGroupBox("翻译引擎")
        engine_layout = QFormLayout()
        
        self.engine_combo = QComboBox()
        engines = app_settings.get("translation", "available_engines", ["百度翻译", "谷歌翻译", "有道翻译"])
        self.engine_combo.addItems(engines)
        default_engine = app_settings.get("translation", "default_engine", "百度翻译")
        index = self.engine_combo.findText(default_engine)
        if index >= 0:
            self.engine_combo.setCurrentIndex(index)
        engine_layout.addRow("默认翻译引擎:", self.engine_combo)
        
        engine_group.setLayout(engine_layout)
        
        # 语言设置
        language_group = QGroupBox("语言设置")
        language_layout = QFormLayout()
        
        self.auto_detect_check = QCheckBox()
        self.auto_detect_check.setChecked(app_settings.get("translation", "auto_detect_language", True))
        language_layout.addRow("自动检测语言:", self.auto_detect_check)
        
        self.source_lang_combo = QComboBox()
        self.source_lang_combo.addItems(["auto", "zh", "en", "ja", "ko", "fr", "de", "es", "ru"])
        source_lang = app_settings.get("translation", "default_source_lang", "auto")
        index = self.source_lang_combo.findText(source_lang)
        if index >= 0:
            self.source_lang_combo.setCurrentIndex(index)
        language_layout.addRow("默认源语言:", self.source_lang_combo)
        
        self.target_lang_combo = QComboBox()
        self.target_lang_combo.addItems(["zh", "en", "ja", "ko", "fr", "de", "es", "ru"])
        target_lang = app_settings.get("translation", "default_target_lang", "zh")
        index = self.target_lang_combo.findText(target_lang)
        if index >= 0:
            self.target_lang_combo.setCurrentIndex(index)
        language_layout.addRow("默认目标语言:", self.target_lang_combo)
        
        # 当自动检测语言被选中时，禁用源语言选择
        def update_source_lang_state():
            self.source_lang_combo.setEnabled(not self.auto_detect_check.isChecked())
        self.auto_detect_check.stateChanged.connect(update_source_lang_state)
        update_source_lang_state()
        
        language_group.setLayout(language_layout)
        
        # 添加各组到布局
        layout.addWidget(engine_group)
        layout.addWidget(language_group)
        layout.addStretch()
        
        tab.setLayout(layout)
        return tab
    
    def create_ui_tab(self):
        """创建界面设置选项卡"""
        tab = QWidget()
        layout = QVBoxLayout()
        
        # 工具栏设置
        toolbar_group = QGroupBox("工具栏设置")
        toolbar_layout = QFormLayout()
        
        self.toolbar_show_check = QCheckBox()
        self.toolbar_show_check.setChecked(app_settings.get("ui", "show_toolbar_on_selection", True))
        toolbar_layout.addRow("选中文本时自动显示工具栏:", self.toolbar_show_check)
        
        self.toolbar_opacity = QDoubleSpinBox()
        self.toolbar_opacity.setRange(0.1, 1.0)
        self.toolbar_opacity.setSingleStep(0.1)
        self.toolbar_opacity.setDecimals(1)
        self.toolbar_opacity.setValue(app_settings.get("ui", "toolbar_opacity", 0.9))
        toolbar_layout.addRow("工具栏不透明度:", self.toolbar_opacity)
        
        self.toolbar_offset = QSpinBox()
        self.toolbar_offset.setRange(0, 100)
        self.toolbar_offset.setSingleStep(5)
        self.toolbar_offset.setValue(app_settings.get("ui", "toolbar_position_offset_y", 20))
        self.toolbar_offset.setSuffix(" 像素")
        toolbar_layout.addRow("工具栏垂直偏移:", self.toolbar_offset)
        
        toolbar_group.setLayout(toolbar_layout)
        
        # 翻译窗口设置
        window_group = QGroupBox("翻译窗口设置")
        window_layout = QFormLayout()
        
        self.window_opacity = QDoubleSpinBox()
        self.window_opacity.setRange(0.1, 1.0)
        self.window_opacity.setSingleStep(0.1)
        self.window_opacity.setDecimals(1)
        self.window_opacity.setValue(app_settings.get("ui", "translation_window_opacity", 0.95))
        window_layout.addRow("翻译窗口不透明度:", self.window_opacity)
        
        window_width = app_settings.get("ui", "translation_window_size", [400, 350])[0]
        self.window_width = QSpinBox()
        self.window_width.setRange(200, 800)
        self.window_width.setSingleStep(50)
        self.window_width.setValue(window_width)
        self.window_width.setSuffix(" 像素")
        window_layout.addRow("翻译窗口宽度:", self.window_width)
        
        window_height = app_settings.get("ui", "translation_window_size", [400, 350])[1]
        self.window_height = QSpinBox()
        self.window_height.setRange(200, 600)
        self.window_height.setSingleStep(50)
        self.window_height.setValue(window_height)
        self.window_height.setSuffix(" 像素")
        window_layout.addRow("翻译窗口高度:", self.window_height)
        
        window_group.setLayout(window_layout)
        
        # 添加各组到布局
        layout.addWidget(toolbar_group)
        layout.addWidget(window_group)
        layout.addStretch()
        
        tab.setLayout(layout)
        return tab
    
    def create_hotkeys_tab(self):
        """创建快捷键设置选项卡"""
        tab = QWidget()
        layout = QVBoxLayout()
        
        hotkeys_group = QGroupBox("快捷键设置")
        hotkeys_layout = QFormLayout()
        
        self.translate_hotkey = QLineEdit()
        self.translate_hotkey.setText(app_settings.get("hotkeys", "translate", "ctrl+shift+t"))
        hotkeys_layout.addRow("翻译快捷键:", self.translate_hotkey)
        
        self.copy_hotkey = QLineEdit()
        self.copy_hotkey.setText(app_settings.get("hotkeys", "copy", "ctrl+shift+c"))
        hotkeys_layout.addRow("复制快捷键:", self.copy_hotkey)
        
        self.hide_hotkey = QLineEdit()
        self.hide_hotkey.setText(app_settings.get("hotkeys", "hide", "esc"))
        hotkeys_layout.addRow("隐藏工具栏快捷键:", self.hide_hotkey)
        
        hotkeys_group.setLayout(hotkeys_layout)
        
        layout.addWidget(hotkeys_group)
        layout.addWidget(QLabel("注意: 更改快捷键后需要重启应用程序才能生效"))
        layout.addStretch()
        
        tab.setLayout(layout)
        return tab
    
    def create_search_tab(self):
        """创建搜索引擎设置选项卡"""
        tab = QWidget()
        layout = QVBoxLayout()
        
        # 搜索引擎设置
        search_group = QGroupBox("搜索引擎设置")
        search_layout = QFormLayout()
        
        # 获取搜索引擎列表
        search_engines = app_settings.get("search", "available_search_engines", {
            "百度": "https://www.baidu.com/s?wd={query}",
            "谷歌": "https://www.google.com/search?q={query}",
            "必应": "https://www.bing.com/search?q={query}"
        })
        
        self.search_engine_combo = QComboBox()
        self.search_engine_combo.addItems(search_engines.keys())
        default_engine = app_settings.get("search", "default_search_engine", "百度")
        index = self.search_engine_combo.findText(default_engine)
        if index >= 0:
            self.search_engine_combo.setCurrentIndex(index)
        search_layout.addRow("默认搜索引擎:", self.search_engine_combo)
        
        search_group.setLayout(search_layout)
        
        # 搜索引擎列表
        engines_list_group = QGroupBox("已配置的搜索引擎")
        engines_list_layout = QVBoxLayout()
        
        self.engines_list = QListWidget()
        for name, url in search_engines.items():
            item = QListWidgetItem(f"{name}: {url}")
            item.setData(Qt.ItemDataRole.UserRole, {"name": name, "url": url})
            self.engines_list.addItem(item)
            
        engines_list_layout.addWidget(self.engines_list)
        
        engines_list_group.setLayout(engines_list_layout)
        
        # 添加各组到布局
        layout.addWidget(search_group)
        layout.addWidget(engines_list_group)
        
        tab.setLayout(layout)
        return tab
    
    def save_settings(self):
        """保存设置"""
        # 保存剪贴板设置
        app_settings.set("clipboard", "use_clipboard_for_detection", self.use_clipboard_check.isChecked())
        app_settings.set("clipboard", "check_interval_ms", self.clipboard_interval.value())
        
        # 保存翻译引擎设置
        app_settings.set("translation", "default_engine", self.engine_combo.currentText())
        app_settings.set("translation", "auto_detect_language", self.auto_detect_check.isChecked())
        app_settings.set("translation", "default_source_lang", self.source_lang_combo.currentText())
        app_settings.set("translation", "default_target_lang", self.target_lang_combo.currentText())
        
        # 保存界面设置
        app_settings.set("ui", "show_toolbar_on_selection", self.toolbar_show_check.isChecked())
        app_settings.set("ui", "toolbar_opacity", self.toolbar_opacity.value())
        app_settings.set("ui", "toolbar_position_offset_y", self.toolbar_offset.value())
        app_settings.set("ui", "translation_window_opacity", self.window_opacity.value())
        app_settings.set("ui", "translation_window_size", [self.window_width.value(), self.window_height.value()])
        
        # 保存快捷键设置
        app_settings.set("hotkeys", "translate", self.translate_hotkey.text())
        app_settings.set("hotkeys", "copy", self.copy_hotkey.text())
        app_settings.set("hotkeys", "hide", self.hide_hotkey.text())
        
        # 保存搜索引擎设置
        app_settings.set("search", "default_search_engine", self.search_engine_combo.currentText())
        
        QMessageBox.information(self, "设置已保存", "设置已保存，部分设置可能需要重启应用程序才能生效。")
        self.accept()
        
    def reset_settings(self):
        """重置设置为默认值"""
        confirm = QMessageBox.question(
            self, 
            "确认重置", 
            "确定要将所有设置重置为默认值吗？此操作不可撤销。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if confirm == QMessageBox.StandardButton.Yes:
            # 删除设置文件并重新加载
            settings_file = app_settings.settings_file
            if os.path.exists(settings_file):
                os.remove(settings_file)
            
            # 重新加载默认设置
            app_settings.settings = app_settings.load_settings()
            
            # 更新界面
            QMessageBox.information(self, "设置已重置", "所有设置已重置为默认值，请重新启动应用程序以应用更改。")
            self.accept() 