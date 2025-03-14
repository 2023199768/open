#!/bin/bash

echo "正在启动划词翻译工具..."

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo "错误: 未检测到Python环境，请安装Python 3.8或更高版本。"
    read -p "按任意键继续..." -n1 -s
    exit 1
fi

# 检查依赖是否已安装
echo "检查依赖项..."
if ! python3 -c "import PyQt6, keyboard, mouse, pyperclip" &> /dev/null; then
    echo "安装所需依赖..."
    pip3 install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "错误: 安装依赖失败，请手动运行 pip3 install -r requirements.txt"
        read -p "按任意键继续..." -n1 -s
        exit 1
    fi
fi

# 生成图标
echo "正在准备应用资源..."
python3 icon.py

# 启动应用
echo "启动应用程序..."
python3 main.py &

echo "划词翻译工具已在后台启动。"
echo "您可以在系统托盘中找到应用图标。"
sleep 5 