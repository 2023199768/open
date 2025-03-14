import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QColor, QFont
from PyQt6.QtCore import Qt, QSize

def create_icon():
    # 创建一个32x32的图标
    pixmap = QPixmap(32, 32)
    pixmap.fill(Qt.GlobalColor.transparent)
    
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    
    # 绘制圆形背景
    painter.setBrush(QColor("#2C3E50"))
    painter.setPen(Qt.PenStyle.NoPen)
    painter.drawEllipse(0, 0, 32, 32)
    
    # 绘制"T"字母
    painter.setPen(QColor("white"))
    painter.setFont(QFont("Arial", 16, QFont.Weight.Bold))
    painter.drawText(8, 24, "T")
    
    painter.end()
    
    return QIcon(pixmap)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    icon = create_icon()
    icon.pixmap(QSize(32, 32)).save("icon.png")
    sys.exit(0) 