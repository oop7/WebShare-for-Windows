"""
Fallback icon utilities for WebShare
"""

from PySide6.QtGui import QIcon, QPixmap, QPainter, QColor, QBrush, QPen, QFont
from PySide6.QtCore import Qt, QSize

def create_fallback_icon(size=64):
    """
    Create a simple programmatically generated icon (no PNG loading required)
    
    Args:
        size (int): Size of the icon
        
    Returns:
        QPixmap: A generated icon
    """
    # Create a blank pixmap
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.transparent)
    
    # Create a painter to draw on the pixmap
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    
    # Draw the background circle
    painter.setPen(Qt.NoPen)
    painter.setBrush(QBrush(QColor(44, 62, 80)))  # Dark blue background
    painter.drawEllipse(2, 2, size-4, size-4)
    
    # Draw a network icon (simplified)
    pen = QPen(QColor(255, 255, 255))  # White pen
    pen.setWidth(2)
    painter.setPen(pen)
    
    # Draw connecting lines
    center_x = size // 2
    center_y = size // 2
    
    # Draw connection lines
    painter.drawLine(center_x, center_y - size//4, center_x + size//3, center_y + size//4)
    painter.drawLine(center_x, center_y - size//4, center_x - size//3, center_y + size//4)
    
    # Draw three circles (nodes)
    painter.setBrush(QBrush(QColor(46, 204, 113)))  # Green
    painter.drawEllipse(center_x - size//10, center_y - size//4 - size//10, size//5, size//5)
    
    painter.setBrush(QBrush(QColor(52, 152, 219)))  # Blue
    painter.drawEllipse(center_x + size//3 - size//10, center_y + size//4 - size//10, size//5, size//5)
    
    painter.setBrush(QBrush(QColor(155, 89, 182)))  # Purple
    painter.drawEllipse(center_x - size//3 - size//10, center_y + size//4 - size//10, size//5, size//5)
    
    # Add a letter "W" in the center
    font = QFont("Arial", size//4)
    font.setBold(True)
    painter.setFont(font)
    painter.drawText(center_x - size//8, center_y + size//8, "W")
    
    # End painting
    painter.end()
    
    return pixmap

def get_fallback_icon():
    """
    Get a fallback icon as a QIcon
    
    Returns:
        QIcon: A programmatically generated icon
    """
    icon = QIcon()
    for size in [16, 32, 64, 128]:
        icon.addPixmap(create_fallback_icon(size))
    return icon 