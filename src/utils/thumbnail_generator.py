import os
from PyQt6.QtGui import QPixmap, QImage, QPainter, QColor, QFont
from PyQt6.QtCore import Qt, QRect
import logging

logger = logging.getLogger(__name__)

class ThumbnailGenerator:
    @staticmethod
    def generate(filepath, size=(160, 90)):
        if not os.path.exists(filepath):
            logger.error(f"Thumbnail generation failed: File not found {filepath}")
            return QPixmap()

        ext = os.path.splitext(filepath)[1].lower()
        logger.info(f"Generating thumbnail for {filepath} with ext {ext}")
        
        # IMAGE HANDLER
        if ext in ['.jpg', '.jpeg', '.png', '.bmp', '.gif']:
            try:
                pixmap = QPixmap(filepath)
                if pixmap.isNull():
                    logger.warning(f"Failed to load image: {filepath}")
                    return ThumbnailGenerator._generate_placeholder(ext, size)
                
                logger.info(f"Image loaded successfully: {filepath}")   
                return pixmap.scaled(size[0], size[1], 
                                   Qt.AspectRatioMode.KeepAspectRatioByExpanding, 
                                   Qt.TransformationMode.SmoothTransformation)
            except Exception as e:
                logger.error(f"Error loading image thumbnail: {e}")
                return ThumbnailGenerator._generate_placeholder(ext, size)
        
        # VIDEO HANDLER (Safe Mode - No OpenCV)
        elif ext in ['.mp4', '.mov', '.mkv', '.avi', '.webm']:
            # Currently using placeholder to avoid DLL conflicts between OpenCV and libmpv/PyQt
            # TODO: Implement mpv-based thumbnailing if needed
            return ThumbnailGenerator._generate_placeholder("VIDEO", size, filepath)
            
        else:
            logger.warning(f"Unsupported format for thumbnail: {ext}")
            return ThumbnailGenerator._generate_placeholder("?", size)

    @staticmethod
    def _generate_placeholder(text, size, filepath=None):
        pixmap = QPixmap(size[0], size[1])
        pixmap.fill(QColor("#333333"))
        
        painter = QPainter(pixmap)
        painter.setPen(QColor("white"))
        
        # Draw border
        painter.drawRect(0, 0, size[0]-1, size[1]-1)
        
        # Draw Text
        font = QFont("Arial", 10)
        font.setBold(True)
        painter.setFont(font)
        
        display_text = text
        if filepath:
            filename = os.path.basename(filepath)
            display_text = f"VIDEO\n{filename[:10]}..."
            
        painter.drawText(QRect(0, 0, size[0], size[1]), 
                        Qt.AlignmentFlag.AlignCenter, 
                        display_text)
        
        painter.end()
        return pixmap
