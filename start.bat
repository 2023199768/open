@echo off
echo 正在启动划词翻译工具...

rem 检查Python环境
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo 错误: 未检测到Python环境，请安装Python 3.8或更高版本。
    pause
    exit /b 1
)

rem 检查依赖是否已安装
echo 检查依赖项...
python -c "import PyQt6, keyboard, mouse, pyperclip" >nul 2>&1
if %errorlevel% neq 0 (
    echo 安装所需依赖...
    pip install -r requirements.txt
    if %errorlevel% neq 0 (
        echo 错误: 安装依赖失败，请手动运行 pip install -r requirements.txt
        pause
        exit /b 1
    )
)

rem 生成图标
echo 正在准备应用资源...
python icon.py

rem 启动应用
echo 启动应用程序...
start pythonw main.py

echo 划词翻译工具已在后台启动。
echo 您可以在系统托盘中找到应用图标。
timeout /t 5 