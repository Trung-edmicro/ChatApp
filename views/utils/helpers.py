from PyQt5.QtWidgets import QLabel, QHBoxLayout, QWidget, QSpacerItem, QSizePolicy, QPushButton
from PyQt5.QtGui import QPixmap, QFont, QFontMetrics, QIcon
from PyQt5.QtCore import Qt, QTimer


# Thông báo
class ToastMessage(QLabel):
    def __init__(self, message, message_type="info", duration=3000, parent=None):
        super().__init__(message, parent)

        icons = {
            "success": "views/images/success_icon.png",
            "error": "views/images/error_icon.png",
            "warning": "views/images/warning_icon.png",
            "info": "views/images/info_icon.png",
        }
        icon_path = icons.get(message_type, "views/images/info_icon.png")

        self.setStyleSheet(f"""
            background-color: #2f2f2f;
            color: white;
            font-size: 12px;
            padding: 5px;
            border-radius: 5px;
            text-align: center;
        """)

        # Layout chính
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Icon
        icon_button = QPushButton()
        icon_button.setIcon(QIcon(icon_path))
        icon_button.setFixedSize(30, 30)  # Kích thước cố định
        # icon_button.setStyleSheet("border: none; background: transparent;")
        layout.addWidget(icon_button)

        # Nội dung thông báo
        text_label = QLabel(message)
        text_label.setFont(QFont("Arial", 11))
        text_label.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Fixed)
        text_label.setWordWrap(False)
        layout.addWidget(text_label)

        # Tính toán chiều rộng dựa trên nội dung chữ
        font_metrics = QFontMetrics(text_label.font())
        text_width = font_metrics.boundingRect(message).width() + 10
        min_width = 20 + text_width

        self.setLayout(layout)
        self.setFixedSize(min_width, 40)

        # Căn giữa cửa sổ cha (parent)
        if parent:
            parent_width = parent.width()
            self.move((parent_width - self.width()) // 2, 20)

        QTimer.singleShot(duration, self.close)

def show_toast(parent, message, message_type="success", duration=3000):
    """
    :param parent: Cửa sổ cha (QWidget).
    :param message: Nội dung thông báo.
    :param message_type: Loại thông báo ("success", "error", "warning", "info").
    :param duration: Thời gian hiển thị (ms).
    """
    toast = ToastMessage(message, message_type, duration, parent)
    toast.show()

