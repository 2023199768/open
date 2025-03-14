#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import json

class Settings:
    """应用程序设置类"""
    
    def __init__(self):
        """初始化设置"""
        self.settings_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "settings.json")
        self.settings = self.load_settings()
        
    def load_settings(self):
        """从文件加载设置"""
        default_settings = {
            "translation": {
                "default_engine": "百度翻译",
                "available_engines": ["百度翻译", "谷歌翻译", "有道翻译"],
                "auto_detect_language": True,
                "default_source_lang": "auto",
                "default_target_lang": "zh"
            },
            "ui": {
                "toolbar_opacity": 0.9,
                "translation_window_opacity": 0.95,
                "show_toolbar_on_selection": True,
                "toolbar_position_offset_y": 20,
                "translation_window_size": [400, 350]
            },
            "hotkeys": {
                "translate": "ctrl+shift+t",
                "copy": "ctrl+shift+c",
                "hide": "esc"
            },
            "clipboard": {
                "check_interval_ms": 500,
                "use_clipboard_for_detection": True
            },
            "search": {
                "default_search_engine": "百度",
                "available_search_engines": {
                    "百度": "https://www.baidu.com/s?wd={query}",
                    "谷歌": "https://www.google.com/search?q={query}",
                    "必应": "https://www.bing.com/search?q={query}"
                }
            }
        }
        
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                # 合并设置，确保所有默认设置都存在
                self.update_nested_dict(default_settings, settings)
                return default_settings
            else:
                # 如果设置文件不存在，创建默认设置文件
                self.save_settings(default_settings)
                return default_settings
        except Exception as e:
            print(f"加载设置出错: {str(e)}")
            return default_settings
    
    def update_nested_dict(self, d, u):
        """递归更新嵌套字典"""
        import collections.abc
        for k, v in u.items():
            if isinstance(v, collections.abc.Mapping):
                d[k] = self.update_nested_dict(d.get(k, {}), v)
            else:
                d[k] = v
        return d
    
    def save_settings(self, settings=None):
        """保存设置到文件"""
        if settings is None:
            settings = self.settings
            
        try:
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, ensure_ascii=False, indent=4)
            return True
        except Exception as e:
            print(f"保存设置出错: {str(e)}")
            return False
    
    def get(self, section, key, default=None):
        """获取设置值"""
        try:
            return self.settings[section][key]
        except (KeyError, TypeError):
            return default
    
    def set(self, section, key, value):
        """设置值"""
        try:
            if section not in self.settings:
                self.settings[section] = {}
            self.settings[section][key] = value
            return self.save_settings()
        except Exception as e:
            print(f"设置值出错: {str(e)}")
            return False


# 创建全局设置实例
app_settings = Settings() 