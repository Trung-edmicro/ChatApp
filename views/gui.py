import sys
import re
import json
import uuid
import openai
import google.generativeai as genai
from google.generativeai.types import content_types
from datetime import datetime
from PyQt5 import QtCore, QtWidgets
from PyQt5.QtWidgets import QApplication, QCheckBox, QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QMessageBox, QLineEdit, QGraphicsOpacityEffect , QPushButton, QInputDialog, QListWidget, QListWidgetItem, QLabel, QSizePolicy, QAction, QMenu, QMessageBox, QDialog, QScroller
from PyQt5.QtGui import QPalette, QColor, QIcon, QCursor, QFont, QPixmap, QFontMetrics, QClipboard 
from PyQt5.QtCore import Qt, QPropertyAnimation, QRect, pyqtSignal, QSize, QTimer, QEasingCurve, QPoint
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineSettings
from internal.db.connection import get_db
from controllers.controllers import *
from views import styles
from views.export_docx import export_to_docx
from views.prompt_dialog import PromptDialog # Import PromptDialog
from views.utils.helpers import show_toast
from views.utils.contains import format_message, contains_latex
from views.utils.config import set_api_keys

class ToggleSwitch(QWidget):
    toggled_signal = pyqtSignal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(62, 30)

        # Layout chính
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)

        # Background của toggle
        self.bg_label = QLabel(self)
        self.bg_label.setStyleSheet(f"border-radius: 15px; border: 2px solid #3c91d9")
        self.bg_label.setGeometry(0, 0, 62, 30)

        self.sun_icon = QLabel(self)
        self.sun_icon.setPixmap(QPixmap("views/images/gpt_icon.png").scaled(20, 20, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        self.sun_icon.setGeometry(6, 5, 20, 20)

        self.moon_icon = QLabel(self)
        self.moon_icon.setPixmap(QPixmap("views/images/gemini_icon.png").scaled(20, 20, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        self.moon_icon.setGeometry(35, 5, 20, 20)

        # Nút toggle
        self.toggle_button = QPushButton(self)
        self.toggle_button.setCursor(QCursor(Qt.PointingHandCursor))
        self.toggle_button.setStyleSheet("background-color: #3c91d9; border-radius: 12px; border: none;")
        self.toggle_button.setGeometry(3, 3, 24, 24)
        self.toggle_button.clicked.connect(self.toggle)

        # Animation
        self.animation = QPropertyAnimation(self.toggle_button, b"geometry")
        self.animation.setDuration(200)

        self.checked = False

    def toggle(self):
        self.checked = not self.checked
        self.toggled_signal.emit(self.checked)

        if self.checked:
            self.animation.setStartValue(QRect(3, 3, 24, 24))
            self.animation.setEndValue(QRect(35, 3, 24, 24))
            self.bg_label.setStyleSheet(f"border-radius: 15px; border: 2px solid #00a67d")
            self.toggle_button.setStyleSheet("background-color: #00a67d; border-radius: 12px; border: none;")
        else:
            self.animation.setStartValue(QRect(35, 3, 24, 24))
            self.animation.setEndValue(QRect(3, 3, 24, 24))
            self.bg_label.setStyleSheet(f"border-radius: 15px; border: 2px solid #3c91d9")
            self.toggle_button.setStyleSheet("background-color: #3c91d9; border-radius: 12px; border: none;")

        self.animation.start()

class ChatItem(QWidget):
    def __init__(self, message_id, message="", sender="user", parent=None, chat_app=None):
        super().__init__(parent)

        latex_checked = contains_latex(message)
        self.message_id = message_id
        self.chat_app = chat_app 

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        self.main_layout.setSpacing(2)

        # Nút More Options
        self.more_button = QPushButton()
        self.more_button.setIcon(QIcon(QPixmap("views/images/more_icon.png")))
        self.more_button.setIconSize(QSize(20, 20))  
        self.more_button.setFixedSize(24, 24)
        self.more_button.setCursor(QCursor(Qt.PointingHandCursor))
        self.more_button.setStyleSheet("border: none; background-color: transparent;") 
        self.more_button.clicked.connect(self.show_more_menu)

        # Layout chứa nút More Options
        more_layout = QHBoxLayout()
        more_layout.setContentsMargins(0, 0, 0, 0)
        more_layout.addStretch()
        more_layout.addWidget(self.more_button)

        # Khu vực chat
        self.text_edit = QTextEdit()
        self.text_edit.setText(message)
        self.text_edit.setReadOnly(True)
        self.text_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.text_edit.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.text_edit.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        # Web view
        self.web_view = QWebEngineView()
        self.web_view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        if sender == "user":
            font_metrics = QFontMetrics(self.text_edit.font())
            text_width = font_metrics.width(message) + 16
            min_width = 60
            max_width = 500

            self.text_edit.setStyleSheet("""
                QTextEdit {
                    border: none;
                    font-size: 14px;
                    border-radius: 12px;
                    padding: 8px;
                    background-color: #545454; 
                    color: white;
                }
            """)
            self.main_layout.addStretch()
            self.main_layout.addWidget(self.text_edit, 0, Qt.AlignRight)
            self.text_edit.setFixedWidth(min(max_width, max(text_width, min_width)))

        else:
            self.main_layout.addLayout(more_layout) # Luôn thêm more_layout
            if latex_checked:
                # AI message CÓ LaTeX: chỉ hiển thị WebView, ẨN QTextEdit
                self.web_view.setHtml(format_message(message)) # Set HTML vào WebView
                self.text_edit.hide() # ẨN QTextEdit
                self.main_layout.addWidget(self.web_view) # Thêm WebView vào layout
                self.main_layout.setStretch(0, 1) # Stretch layout cho WebView
                self.main_layout.setStretch(1, 3) # Stretch layout cho WebView
            else:
                self.text_edit.setStyleSheet("""
                    QTextEdit {
                        border: 1px solid #545454;
                        font-size: 14px;
                        border-radius: 12px;
                        padding: 5px 0px;
                        color: white;
                    }
                """)
                self.web_view.hide() # ẨN WebView
                self.main_layout.addWidget(self.text_edit)

        doc = self.text_edit.document()
        doc.setTextWidth(self.text_edit.width())
        self.text_edit.setFixedHeight(int(doc.size().height()) + 16)

        # Dùng QTimer để cập nhật MathJax sau khi WebEngine tải xong
        QTimer.singleShot(100, self.update_mathjax)

    def update_mathjax(self):
        """Kích hoạt MathJax sau khi nội dung được load"""
        self.web_view.page().runJavaScript("MathJax.typesetPromise();")

    def show_more_menu(self):
        menu = QMenu(self)
        
        # Tuỳ chỉnh giao diện menu
        menu.setStyleSheet("""
            QMenu {
                background-color: #2a2a2a;
                border-radius: 8px;
                padding: 6px;
            }
            QMenu::item {
                padding: 8px;
                min-width: 130px;
                color: white;
                border-radius: 6px;
                font-size: 14px;
            }
            QMenu::item:selected {
                background-color: #3c3c3c;
            }
        """)

        # Add item
        add_item_action = QAction(QIcon("views/images/copy.png"), "Add Text", self)
        add_item_action.triggered.connect(self.add_text)

        # Hành động Copy Text
        copy_text_action = QAction(QIcon("views/images/copy.png"), "Copy Text", self)
        copy_text_action.triggered.connect(self.copy_text)

        # Hành động Copy Markdown
        copy_markdown_action = QAction(QIcon("views/images/markdown.png"), "Copy Markdown", self)
        copy_markdown_action.triggered.connect(self.copy_markdown)

        # Thêm hành động vào menu
        menu.addAction(add_item_action)
        menu.addAction(copy_text_action)
        menu.addAction(copy_markdown_action)

        # Hiển thị menu ngay tại vị trí của nút
        menu.exec_(self.more_button.mapToGlobal(self.more_button.rect().bottomRight()))

    def add_text(self):
        print("ChatItem.add_text được gọi") # Debug print
        if self.chat_app:
            print("ChatItem.add_text: self.chat_app is NOT None") # Debug print
            print(f"ChatItem.add_text: Thêm message vào danh sách chọn: Message ID = {self.message_id}") # Log
            self.chat_app.add_to_selected_messages(self.message_id)
        else:
            print("ChatItem.add_text: self.chat_app is None!") # Debug print - Kiểm tra xem self.chat_app có bị None không

    def copy_text(self):
        clipboard = QApplication.clipboard()
        clipboard.setText(self.text_edit.toPlainText())

    def copy_markdown(self):
        clipboard = QApplication.clipboard()
        markdown_text = f"```\n{self.text_edit.toPlainText()}\n```"
        clipboard.setText(markdown_text)
    
    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update_text_edit_size()

    def update_text_edit_size(self):
        if not self.text_edit.isHidden():
            doc = self.text_edit.document()
            doc.setTextWidth(self.text_edit.width())  # Cập nhật độ rộng
            new_height = int(doc.size().height()) + 16  # Tính lại chiều cao
            self.text_edit.setFixedHeight(new_height)

            if self.parent() and isinstance(self.parent(), QListWidget):
                list_widget = self.parent()
                item_index = list_widget.indexFromItem(self.parent().itemWidget(self))
                if item_index.isValid():
                    list_widget.item(item_index.row()).setSizeHint(self.sizeHint())

class ChatApp(QWidget):
    checkbox_state_changed_signal = pyqtSignal(str, bool) # Signal phát ra khi checkbox state thay đổi (message_id, is_checked)

    def __init__(self, app, openai_api_key, gemini_api_key):
        super().__init__()
        self.app = app
        self.openai_api_key = openai_api_key # Lưu API keys
        self.gemini_api_key = gemini_api_key # Lưu API keys
        
        # Cấu hình AI API
        # OpenAI
        self.openai_client = openai.OpenAI(api_key=self.openai_api_key)

        # Gemini
        genai.configure(api_key=self.gemini_api_key)
        self.gemini_model = genai.GenerativeModel('gemini-2.0-flash-thinking-exp-01-21')
        self.gemini_chat = self.gemini_model.start_chat(history=[])
        
        self.initUI()
        self.load_sessions_from_db() # Gọi hàm load sessions từ DB
        self.selected_messages_data = []
        self.load_selected_messages_list()
        self.current_session_id = None  # Thêm biến self.current_session_id, khởi tạo là None
        self.checkbox_state_changed_signal.connect(self.update_message_exported_status)

        self.attached_prompt_content = "" # Thêm biến lưu content prompt đính kèm
        self.attached_prompt_name = "" # Thêm biến lưu name prompt đính kèm

        self.dim_effect = QtWidgets.QGraphicsOpacityEffect() # Khởi tạo QGraphicsOpacityEffect
        self.dim_effect.setOpacity(0.5) # Set độ mờ (0.0 - 1.0, 0.5 là mờ vừa phải)

        self.list_messages_widget.setMaximumWidth(250)
    
    def initUI(self):
        app_font = QFont("Inter", 12)
        self.setWindowTitle("ChatApp")
        self.setGeometry(100, 100, 1280, 820)
        self.app.setFont(app_font)
        self.setStyleSheet("background-color: #212121; color: white;")

        self.main_layout = QHBoxLayout()

        # Layout Danh sách lịch sử chat
        history_layout = QVBoxLayout()

            # New session button
        self.button_create_new = QPushButton("Tạo mới", self)
        self.button_create_new.setStyleSheet(f"""
            QPushButton {{
                background-color: {styles.NEW_SESSION_BUTTON_COLOR};
                color: white;
                border: none;
                border-radius: 10px;
                padding: 8px;
                margin: 5px;
            }}
            QPushButton:hover {{
                background-color: {styles.NEW_SESSION_BUTTON_HOVER_COLOR};
            }}
        """)
        self.button_create_new.setCursor(QCursor(Qt.PointingHandCursor))
        self.button_create_new.clicked.connect(self.create_new_session)

        history_layout.addWidget(self.button_create_new)

        self.history_list = QListWidget()
        self.history_list.setFixedWidth(styles.HISTORY_LIST_WIDTH)
        self.history_list.setStyleSheet(f"""
            QListWidget {{
                border: none;
                background-color: {styles.HISTORY_BACKGROUND_COLOR};
                border-radius: {styles.BORDER_RADIUS};
                padding: 5px; 
            }}
            QListWidget::item {{
                color: {styles.HISTORY_TEXT_COLOR};
                background-color: {styles.HISTORY_ITEM_BACKGROUND};
                padding-right: 6px;
                border: none; 
                border-radius: 10px; 
            }}
            QListWidget::item:hover {{
                background-color: {styles.HISTORY_ITEM_HOVER_BACKGROUND};
            }}
            QListWidget::item:selected {{ 
                background-color: {styles.HISTORY_ITEM_HOVER_BACKGROUND};
                outline: none;
            }}
            QListWidget:focus {{
                outline: none;
            }}
        """)
        self.history_list.itemClicked.connect(self.load_selected_chat)
        history_layout.addWidget(self.history_list)

        self.main_layout.addLayout(history_layout) 

        # Layout chat
        chat_layout = QVBoxLayout()
        chat_layout.setContentsMargins(0, 8, 0, 0)

        # Layout chức năng 
        method_layout = QHBoxLayout()
        method_layout.setSpacing(0)
        method_layout.setContentsMargins(0, 0, 0, 0)

            # Toggle AI
        self.toggle_switch = ToggleSwitch()
        method_layout.addWidget(self.toggle_switch)
        
            # Trạng thái toggle
        self.is_toggle_on = False
        self.toggle_switch.toggled_signal.connect(self.update_toggle_state)

        spacer_between_buttons = QWidget()
        spacer_between_buttons.setFixedWidth(10)
        method_layout.addWidget(spacer_between_buttons)

            # Nút thay đổi API
        self.change_button = QPushButton()
        self.change_button.setStyleSheet("background-color: transparent; color: white; padding: 5px;")
        self.change_button.setFixedSize(33, 33)
        self.change_button.setCursor(QCursor(Qt.PointingHandCursor))
        self.change_button.setIcon(QIcon("views/images/rest_api_icon.png"))
        self.change_button.setIconSize(QSize(33,33))
        self.change_button.clicked.connect(self.handle_change_api)

        method_layout.addWidget(self.change_button)

        spacer_left = QWidget()
        spacer_left.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        method_layout.addWidget(spacer_left)

            # Nút ẩn/hiện
        self.toggle_button = QPushButton()
        self.toggle_button.setCheckable(True)
        self.toggle_button.setChecked(True)  # Mặc định hiển thị
        self.toggle_button.setStyleSheet("background-color: #2f2f2f; color: white; border-radius: 4px; font-size: 12px; font-weight: bold; padding: 5px;")
        self.toggle_button.setFixedSize(16, 32)
        self.toggle_button.setCursor(QCursor(Qt.PointingHandCursor))
        self.toggle_button.setIcon(QIcon("views/images/forward_icon.png"))
        self.toggle_button.setIconSize(QSize(16,16))
        self.toggle_button.toggled.connect(self.toggle_list_messages)
        method_layout.addWidget(self.toggle_button)

        chat_layout.addLayout(method_layout)

            # Layout messages
        self.chat_display = QListWidget(self)
        self.chat_display.setStyleSheet(f"""
            QListWidget {{
                border: none;
                background-color: #212121;
            }}
            # QListWidget::item:hover {{
            #     background-color: transparent;
            # }}
            QListWidget::item:selected {{
                background-color: transparent;
                outline: none;
            }}
            QListWidget:focus {{
                outline: none;
            }}
        """)
        scroll_bar = self.chat_display.verticalScrollBar()
        self.chat_display.verticalScrollBar().setSingleStep(50)
        scroll_bar.setStyleSheet(styles.SCROLLBAR_STYLES)
        chat_layout.addWidget(self.chat_display)
        
            # Layout input
        input_container = QVBoxLayout()
        input_container.setContentsMargins(10, 10, 10, 10)
        input_container.setSpacing(5)

        # === Widget hiển thị prompt đính kèm ===
        self.attached_prompt_widget = QWidget()
        self.attached_prompt_layout = QHBoxLayout()
        self.attached_prompt_widget.setLayout(self.attached_prompt_layout)
        self.attached_prompt_widget.setStyleSheet("background-color: #333333; border-radius: 5px; padding: 5px; margin-bottom: 5px;")
        self.attached_prompt_label = QLabel()
        self.attached_prompt_label.setStyleSheet("color: white;")
        self.attached_prompt_close_button = QPushButton("X")
        self.attached_prompt_close_button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 2px 5px;
            }
            QPushButton:hover {
                background-color: #555555;
            }
        """)
        self.attached_prompt_close_button.setFixedSize(20, 20)
        self.attached_prompt_close_button.clicked.connect(self.clear_attached_prompt) # Kết nối nút X
        self.attached_prompt_layout.addWidget(self.attached_prompt_label)
        self.attached_prompt_layout.addStretch()
        self.attached_prompt_layout.addWidget(self.attached_prompt_close_button)
        self.attached_prompt_widget.hide() # Ẩn widget prompt đính kèm ban đầu
        input_container.addWidget(self.attached_prompt_widget) # Thêm widget prompt đính kèm vào input_container
        
            # input
        self.input_field = QTextEdit(self)
        self.input_field.setPlaceholderText("Nhập nội dung...")
        self.input_field.setStyleSheet(
            f"border: none; background-color: {styles.BACKGROUND_COLOR_INPUT}; color: {styles.TEXT_COLOR}; padding: 8px;"
            f"border-radius: {styles.BORDER_RADIUS}; font-size: {styles.FONT_SIZE}; max-height: 100px;"
        )
        self.input_field.setFixedHeight(styles.INPUT_FIELD_HEIGHT)
        self.input_field.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.input_field.textChanged.connect(self.adjust_input_height)
        input_container.addWidget(self.input_field, 1)

        # Attachment button (THÊM ĐOẠN CODE NÀY)
        self.attachment_button = QPushButton(self)
        self.attachment_button.setIcon(QIcon("views/images/attach_icon.png")) # Đặt icon dấu cộng. Cần chuẩn bị file ảnh attach_icon.png
        self.attachment_button.setCursor(QCursor(Qt.PointingHandCursor))
        self.attachment_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {styles.SEND_BUTTON_COLOR};
                color: white;
                border-radius: {20 // 2}px;
                width: {styles.SEND_BUTTON_SIZE}px;
                height: {styles.SEND_BUTTON_SIZE}px;
                border: none; /* Loại bỏ border mặc định nếu có */
                padding-bottom: 5px; /* Tạo khoảng cách dưới để có hiệu ứng "ấn xuống" */
            }}
            QPushButton:hover {{
                background-color: #5ca9e0; /* Màu nền sáng hơn khi hover - tùy chỉnh màu */
                transform: scale(0.95); /* Thu nhỏ kích thước 5% khi hover */
                padding-top: 5px; /* Tạo hiệu ứng "ấn xuống" bằng cách tăng padding top */
                padding-bottom: 0px; /* Giảm padding bottom để bù lại */
            }}
            QPushButton:pressed {{
                background-color: #3c91d9; /* Màu nền khi nhấn - có thể giống màu gốc */
                transform: scale(0.9); /* Thu nhỏ thêm một chút khi nhấn */
                padding-top: 7px; /* Ấn xuống sâu hơn khi nhấn */
                padding-bottom: 0px;
            }}
        """)
        self.attachment_button.setFixedSize(styles.SEND_BUTTON_SIZE, styles.SEND_BUTTON_SIZE) # Đảm bảo kích thước cố định
        self.attachment_button.setToolTip("Thêm tệp đính kèm")
        self.attachment_button.clicked.connect(self.show_attachment_menu) # Kết nối với hàm show_attachment_menu
        input_container.addWidget(self.attachment_button) # Thêm vào input_container trước nút send

            # send button
        self.send_button = QPushButton(self)
        self.send_button.setIcon(QIcon("views/images/send_icon.png"))
        self.send_button.setCursor(QCursor(Qt.PointingHandCursor))
        self.send_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {styles.SEND_BUTTON_COLOR};
                color: white;
                border-radius: {styles.SEND_BUTTON_SIZE // 2}px;
                width: {styles.SEND_BUTTON_SIZE}px;
                height: {styles.SEND_BUTTON_SIZE}px;
                border: none; /* Loại bỏ border mặc định nếu có */
                padding-bottom: 5px; /* Tạo khoảng cách dưới để có hiệu ứng "ấn xuống" */
            }}
            QPushButton:hover {{
                background-color: #5ca9e0; /* Màu nền sáng hơn khi hover - tùy chỉnh màu */
                transform: scale(0.95); /* Thu nhỏ kích thước 5% khi hover */
                padding-top: 5px; /* Tạo hiệu ứng "ấn xuống" bằng cách tăng padding top */
                padding-bottom: 0px; /* Giảm padding bottom để bù lại */
            }}
            QPushButton:pressed {{
                background-color: #3c91d9; /* Màu nền khi nhấn - có thể giống màu gốc */
                transform: scale(0.9); /* Thu nhỏ thêm một chút khi nhấn */
                padding-top: 7px; /* Ấn xuống sâu hơn khi nhấn */
                padding-bottom: 0px;
            }}
        """)
        self.send_button.setToolTip("Ấn để gửi")
        self.send_button.clicked.connect(self.send_message)
        input_container.addWidget(self.send_button)

        input_widget = QWidget()
        input_widget.setStyleSheet(f"background-color: {styles.BACKGROUND_COLOR_INPUT}; border-radius: 20px; padding: 5px; min-height: 30px; max-height: 250px") # Tăng max-height
        input_widget.setLayout(input_container)
        chat_layout.addWidget(input_widget)

        self.main_layout.addLayout(chat_layout)
        
        # Widget chứa danh sách tin nhắn
        self.list_messages_widget = QWidget()
        self.list_messages_widget.setStyleSheet("background-color: #171717; border-radius: 10px;")  
        self.list_messages_widget.setFixedWidth(250)

        # Layout danh sách tin nhắn
        list_messages_layout = QVBoxLayout()
        list_messages_layout.setSpacing(5)  
        list_messages_layout.setContentsMargins(5, 15, 5, 10)

        self.title_label = QLabel("Danh sách các câu đã chọn")
        self.title_label.setStyleSheet("color: white; font-size: 13px; font-weight: bold; padding-bottom: 12px; border-bottom: 1px solid #2f2f2f;")
        self.title_label.setAlignment(Qt.AlignCenter)
        list_messages_layout.addWidget(self.title_label)

        # Danh sách tin nhắn đã chọn
        self.selected_messages = QListWidget()
        self.selected_messages.setFixedWidth(240)
        self.selected_messages.setStyleSheet("""
            QListWidget {
                border: none; 
                background-color: #171717; 
                color: white;
            }
            QListWidget::item {
                background-color: #222222;
                border-radius: 5px;
                padding: 3px;
                margin: 3px 2px;
            }
            QListWidget::item:selected {
                background-color: #333333;
                outline: none;
            }
            QListWidget::item:hover {
                background-color: #333333;
            }
            QListWidget:focus {
                outline: none;
            }
        """)
        list_messages_layout.addWidget(self.selected_messages)

        # Layout chứa 2 nút
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(10)
        buttons_layout.setContentsMargins(0, 0, 0, 0)  

        # Nut xoa tat ca
        self.clear_button = QPushButton("Xóa tất cả")
        self.clear_button.setStyleSheet("background-color: #2f2f2f; color: white; border-radius: 6px; font-size: 12px; font-weight: bold; padding: 5px;")
        self.clear_button.setFixedSize(112, 30)  
        self.clear_button.setCursor(QCursor(Qt.PointingHandCursor))
        self.clear_button.clicked.connect(self.clear_list_messages)
        buttons_layout.addWidget(self.clear_button)

        # Nút "Chọn tất cả / Bỏ chọn tất cả"
        self.select_all_button = QPushButton("Chọn tất cả")
        self.select_all_button.setStyleSheet("background-color: #2f2f2f; color: white; border-radius: 6px; font-size: 12px; font-weight: bold; padding: 5px;")
        self.select_all_button.setFixedSize(112, 30)
        self.select_all_button.setCursor(QCursor(Qt.PointingHandCursor))
        self.select_all_button.setCheckable(True)
        self.select_all_button.toggled.connect(self.toggle_select_all_messages)
        buttons_layout.addWidget(self.select_all_button)

        export_button_layout = QVBoxLayout()
        export_button_layout.setSpacing(5)  
        export_button_layout.setContentsMargins(3, 5, 3, 0)

        self.export_button = QPushButton("Xuất file Docx")
        self.export_button.setStyleSheet("background-color: #00a67d; color: white; border-radius: 6px; font-size: 12px; font-weight: bold; padding: 5px;")
        self.export_button.setFixedSize(234, 30)
        self.export_button.setCursor(QCursor(Qt.PointingHandCursor))
        self.export_button.clicked.connect(self.export_list_messages)
        export_button_layout.addWidget(self.export_button)

        list_messages_layout.addLayout(buttons_layout)
        list_messages_layout.addLayout(export_button_layout)
        self.list_messages_widget.setLayout(list_messages_layout)

        # Animation
        self.animation = QPropertyAnimation(self.list_messages_widget, b"pos")
        self.animation.setDuration(250)  # Thời gian animation (milliseconds)
        self.animation.setEasingCurve(QEasingCurve.OutCubic) # Loại easing (tùy chọn)

        self.main_layout.addWidget(self.list_messages_widget)
        
        self.setLayout(self.main_layout)

        self.original_pos = None  # Initialize as None
        self.hidden_x = 0  # Initialize hidden_x

# === Function ===
    def show_attachment_menu(self):
        """Hiển thị menu attachment khi nút attachment được click."""
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #2a2a2a;
                border-radius: 15px;
                padding: 8px;
            }
            QMenu::item {
                padding: 8px 20px; /* Tăng padding ngang để có khoảng cách với icon */
                min-width: 150px; /* Tăng min-width nếu cần */
                color: white;
                border-radius: 10px;
                font-size: 14px;
            }
            QMenu::item:selected {
                background-color: #3c3c3c;
            }
        """)

        # Hành động "Select Prompt"
        select_prompt_action = QAction(QIcon("views/images/prompt_icon.png"), "Select Prompt", self) # Cần icon upload_icon.png
        select_prompt_action.triggered.connect(self.open_prompt_dialog) # Kết nối với hàm open_prompt_dialog
        menu.addAction(select_prompt_action)

        # Hành động "Upload File"
        upload_file_action = QAction(QIcon("views/images/upload_icon.png"), "Upload File", self) # Cần icon upload_icon.png
        upload_file_action.triggered.connect(self.upload_file)
        menu.addAction(upload_file_action)

        # Hành động "Sample Media"
        sample_media_action = QAction(QIcon("views/images/media_icon.png"), "Sample Media", self) # Cần icon media_icon.png
        sample_media_action.triggered.connect(self.sample_media)
        menu.addAction(sample_media_action)

        # Hiển thị menu ngay dưới nút attachment
        menu.exec_(self.attachment_button.mapToGlobal(self.attachment_button.rect().bottomRight()))

    def upload_file(self):
        """Xử lý hành động "Upload File"."""
        print("Tải lên File...")
        # TODO: Thêm logic tải lên file

    def sample_media(self):
        """Xử lý hành động "Sample Media"."""
        print("Chọn Sample Media...")
        # TODO: Thêm logic chọn sample media

    def open_prompt_dialog(self):
        # """Mở dialog quản lý prompts và làm mờ cửa sổ chính."""
        # self.setGraphicsEffect(self.dim_effect) # Áp dụng hiệu ứng mờ cho cửa sổ chính

        self.prompt_dialog = PromptDialog(self) # Tạo instance PromptDialog
        self.prompt_dialog.prompt_selected_signal.connect(self.handle_prompt_selected) # **CHỈ KẾT NỐI VỚI handle_prompt_selected**
        result = self.prompt_dialog.exec_() # Hiển thị dialog MODAL

        # self.setGraphicsEffect(None) # Loại bỏ hiệu ứng mờ sau khi dialog đóng

    def handle_prompt_selected(self, prompt_content, prompt_name):
        """Xử lý khi prompt được chọn từ PromptDialog."""
        self.attached_prompt_content = prompt_content # Lưu content prompt
        self.attached_prompt_name = prompt_name # Lưu name prompt
        self.attached_prompt_label.setText(f"Prompt: {prompt_name}") # Hiển thị tên prompt
        self.attached_prompt_widget.show() # Hiển thị widget prompt đính kèm

    def clear_attached_prompt(self):
        """Xóa prompt đính kèm khỏi tin nhắn."""
        self.attached_prompt_content = ""
        self.attached_prompt_name = ""
        self.attached_prompt_widget.hide()

    def insert_prompt_to_input(self, prompt_content):
        """Chèn nội dung prompt đã chọn vào input field."""
        current_text = self.input_field.toPlainText() # Lấy nội dung hiện tại trong input field
        new_text = current_text + "\n\n" + prompt_content # Thêm prompt content vào nội dung hiện tại
        self.input_field.setText(new_text) # Set nội dung mới cho input field    

    def toggle_select_all_messages(self, checked):
        """Chọn hoặc bỏ chọn tất cả tin nhắn trong danh sách tin nhắn đã chọn."""
        for i in range(self.selected_messages.count()):
            item = self.selected_messages.item(i)
            widget = self.selected_messages.itemWidget(item)
            if widget:
                checkbox = widget.findChild(QtWidgets.QCheckBox, "message_checkbox") # Tìm checkbox trong widget
                if checkbox:
                    checkbox.setChecked(checked) # Set trạng thái checkbox theo trạng thái nút "Chọn tất cả"

        if checked:
            self.select_all_button.setText("Bỏ chọn tất cả")
        else:
            self.select_all_button.setText("Chọn tất cả")

    def show_session_menu(self, button, item, session_id, session_name):
        """Hiển thị menu tùy chọn cho session."""
        menu = QMenu(self)
        menu.setWindowFlags(Qt.Popup | Qt.FramelessWindowHint | Qt.NoDropShadowWindowHint)
        menu.setAttribute(Qt.WA_TranslucentBackground)
        # Tùy chỉnh giao diện menu (tương tự như menu tin nhắn)
        menu.setStyleSheet("""
            QMenu {
                background-color: #2a2a2a;
                border-radius: 15px;       /* Bo tròn góc menu */
                padding: 8px;
            }
            QMenu::item {
                padding: 8px;
                min-width: 130px;
                color: white;
                border-radius: 10px;
                font-size: 14px;
            }
            QMenu::item:selected {
                background-color: #3c3c3c;
            }
        """)

        # Hành động Rename (ví dụ, placeholder)
        rename_action = QAction(QIcon("views/images/rename_icon.png"), "Rename", self) # Bạn cần icon rename.png
        rename_action.triggered.connect(lambda: self.rename_session(session_id, session_name, item)) # Hàm rename_session cần được implement

        # Hành động Delete (sử dụng lại chức năng xóa session hiện tại)
        delete_action = QAction(QIcon("views/images/trash_icon.png"), "Delete", self)
        delete_action.triggered.connect(lambda: self.delete_selected_session(item, session_id)) # Sử dụng lại hàm delete_selected_session

        # Thêm hành động vào menu
        menu.addAction(rename_action)
        menu.addAction(delete_action)

        # Hiển thị menu ngay tại vị trí của nút
        menu.exec_(QCursor.pos())

# === Handle show/hide list_messages_widget===
    def showEvent(self, event):
        # Store initial position after the widget is shown
        self.update_positions()
        super().showEvent(event)

    def resizeEvent(self, event):
        # Update positions when the widget is resized
        self.update_positions()
        super().resizeEvent(event)

    def update_positions(self):
        #Update positions when widget or window size has changed.
        self.original_pos = self.list_messages_widget.pos()
        self.hidden_x = self.width() # Calculate the X position for the hidden state

    def toggle_list_messages(self, checked):
        if not hasattr(self, "list_animation"):
            self.list_animation = QPropertyAnimation(self.list_messages_widget, b"maximumWidth")

        self.list_animation.stop()  

        # target_width = 250 if checked else 0
        if checked:
            target_width = 250
            self.toggle_button.setIcon(QIcon("views/images/forward_icon.png"))
        else:
            target_width = 0
            self.toggle_button.setIcon(QIcon("views/images/back_icon.png"))

        self.list_messages_widget.setMinimumWidth(0)

        self.list_animation.setDuration(250)
        self.list_animation.setEasingCurve(QEasingCurve.OutCubic)
        self.list_animation.setStartValue(self.list_messages_widget.width())
        self.list_animation.setEndValue(target_width)

        self.list_animation.start()
        self.list_messages_widget.update()

# === Handle change API Key===
    def handle_change_api(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Cấu hình API Key")
        dialog.setFixedSize(450, 250)
        dialog.setStyleSheet("""
            background-color: #2c2f33; 
            border-radius: 10px;
        """)

        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)

        # Tiêu đề
        label = QLabel("🔑 Nhập API Key")
        label.setFont(QFont("Arial", 12, QFont.Bold))
        label.setStyleSheet("color: white; padding: 5px;")
        label.setAlignment(Qt.AlignCenter)
        layout.addWidget(label)

        # Ô nhập API key Gemini
        gemini_input = QLineEdit()
        gemini_input.setPlaceholderText("Nhập API Key của Gemini")
        gemini_input.setStyleSheet("""
            background-color: #40444b; 
            color: white; 
            border-radius: 5px; 
            padding: 8px;
        """)
        layout.addWidget(gemini_input)

        # Ô nhập API key GPT
        gpt_input = QLineEdit()
        gpt_input.setPlaceholderText("Nhập API Key của GPT")
        gpt_input.setStyleSheet("""
            background-color: #40444b; 
            color: white; 
            border-radius: 5px; 
            padding: 8px;
        """)
        layout.addWidget(gpt_input)

        # Layout cho nút
        button_layout = QHBoxLayout()
        button_layout.setAlignment(Qt.AlignCenter)

        # Nút "Hủy"
        cancel_button = QPushButton("Hủy")
        cancel_button.setFixedSize(60, 30)
        cancel_button.setFont(QFont("Arial", 11))
        cancel_button.setStyleSheet("""
            QPushButton {
                background-color: #ff4d4d; 
                color: white; 
                border-radius: 5px; 
                padding: 8px;
            }
            QPushButton:hover {
                background-color: #cc3b3b;
            }
        """)
        cancel_button.clicked.connect(dialog.reject)
        button_layout.addWidget(cancel_button)

        # Nút "Lưu"
        save_button = QPushButton("Lưu")
        save_button.setFixedSize(60, 30)
        save_button.setFont(QFont("Arial", 11))
        save_button.setStyleSheet("""
            QPushButton {
                background-color: #00a67d; 
                color: white; 
                border-radius: 5px; 
                padding: 85px;
            }
            QPushButton:hover {
                background-color: #019d76;
            }
        """)
        save_button.clicked.connect(lambda: self.save_api_keys(gemini_input.text(), gpt_input.text(), dialog))
        button_layout.addWidget(save_button)

        layout.addLayout(button_layout)
        dialog.setLayout(layout)
        dialog.exec_()

    def save_api_keys(parent, gemini_key, gpt_key, dialog):
        result = set_api_keys(gemini_key, gpt_key)
        
        if result=="success":
            show_toast(parent, "Cập nhật thành công !", "success")

        dialog.accept()
    
# === Các hàm placeholder cho menu actions (cần implement logic thực tế) ===
    def rename_session(self, session_id, session_name, item):
        """Đổi tên session."""
        new_name, ok = QInputDialog.getText(self, "Đổi tên Session", "Nhập tên mới:", text=session_name)
        if ok and new_name:
            db = next(get_db())
            if update_session_name(db, session_id, new_name): # Gọi controller update_session_name
                db.close()
                print(f"Session '{session_name}' (ID: {session_id}) đã được đổi tên thành '{new_name}'.")

                # Cập nhật tên hiển thị trên UI (trong history_list)
                widget_item = self.history_list.itemWidget(item) # Lấy widget của item
                layout = widget_item.layout() # Lấy layout của widget
                label = layout.itemAt(0).widget() # Lấy label (widget đầu tiên trong layout)
                if isinstance(label, QLabel):
                    max_width = self.history_list.width() - 40 # Width tối đa cho text label
                    metrics = QFontMetrics(label.font())
                    elided_text = metrics.elidedText(new_name, Qt.ElideRight, max_width) # Tạo elided text nếu cần
                    label.setText(elided_text) # Set text đã elide (nếu cần)
                    label.setToolTip(new_name) # Set tooltip là tên đầy đủ
                    self.load_sessions_from_db()
                else:
                    print("Không tìm thấy QLabel trong item widget để cập nhật tên.")
            else:
                db.close()
                print(f"Lỗi khi đổi tên session '{session_name}' (ID: {session_id}).")
        else:
            print("Hủy đổi tên session hoặc tên mới không hợp lệ.")

    def load_sessions_from_db(self):
        db = next(get_db())
        sessions = get_all_sessions(db)
        db.close()

        if sessions:
            self.history_list.clear()
            self.history_list.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            max_width = self.history_list.width() - 40  # Giảm width để chừa chỗ cho nút "More Options"
            for session_data in sessions:
                full_text = session_data['session_name']
                metrics = QFontMetrics(self.history_list.font())
                elided_text = metrics.elidedText(full_text, Qt.ElideRight, max_width)

                item = QListWidgetItem()
                item.setData(Qt.UserRole, session_data['session_id'])
                item.setSizeHint(QSize(self.history_list.width(), 40))

                # Tạo widget chứa tên session và nút More Options
                widget = QWidget()
                widget.setStyleSheet("""
                        background-color: transparent;
                    """)
                layout = QHBoxLayout()
                layout.setContentsMargins(10, 0, 10, 0) # Tăng margin phải để có khoảng cách với nút
                layout.setSpacing(5)

                # Label hiển thị session name
                label = QLabel(elided_text)
                label.setToolTip(full_text)
                label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
                label.setStyleSheet("color: white;")

                # Nút More Options (icon 3 chấm hoặc icon khác)
                more_options_button = QPushButton()
                more_options_button.setIcon(QIcon("views/images/more_icon.png")) # Sử dụng lại icon more_icon hoặc thay bằng icon 3 chấm
                more_options_button.setIconSize(QSize(18, 18))
                more_options_button.setCursor(QCursor(Qt.PointingHandCursor))
                more_options_button.setFixedSize(24, 24) # Kích thước nút
                more_options_button.setStyleSheet("border: none; background: transparent;")
                more_options_button.clicked.connect(lambda _, item=item, session_id=session_data['session_id'], session_name=session_data['session_name']: self.show_session_menu(more_options_button, item, session_id, session_name)) # Kết nối với hàm show_session_menu

                # Thêm vào layout
                layout.addWidget(label)
                layout.addStretch()
                layout.addWidget(more_options_button)

                widget.setLayout(layout)
                widget.setMinimumHeight(40)

                self.history_list.addItem(item)
                self.history_list.setItemWidget(item, widget)
        else:
            print("Không có session nào trong Database.")

    def load_selected_chat(self, item):
        """Load danh sách messages của session đã chọn, LƯU SUMMARY session trước đó, và LOAD SUMMARY session hiện tại."""
        # === Lưu summary của session HIỆN TẠI (session cũ) ===
        if self.current_session_id: # Kiểm tra nếu có session cũ (không phải lần load session đầu tiên)
            self.save_current_session_summary(self.current_session_id) # Gọi save_current_session_summary với session_id cũ
        # === Xóa history Gemini trước khi load session mới ===
        if not self.is_toggle_on: # Chỉ xóa history Gemini khi AI model là Gemini (toggle OFF)
            self.clear_gemini_history() # Gọi hàm xóa history Gemini
        session_id = item.data(Qt.UserRole)
        self.chat_display.clear() # Clear chat display trước khi load messages mới
        self.current_session_id = session_id # Cập nhật self.current_session_id với session_id mới

        db = next(get_db()) # Lấy database session
        # === Load summary của session mới được chọn từ database ===
        summary_json_string = get_summary_by_session_id_json(db, session_id) # Lấy summary JSON string từ controller
        if summary_json_string:
            try:
                # Deserialize JSON string về history object của Gemini
                self.gemini_chat = self.gemini_model.start_chat(history=json.loads(summary_json_string)) # Khôi phục history cho gemini_chat
                print(f"History đã được load cho session ID: {session_id}") # Log load history
            except json.JSONDecodeError as e:
                print(f"Lỗi giải mã JSON history cho session ID {session_id}: {e}") # Log lỗi JSON decode
                self.gemini_chat = self.gemini_model.start_chat(history=[]) # Nếu lỗi JSON, tạo history rỗng
        else:
            # Nếu không có summary trong database, tạo history rỗng
            self.gemini_chat = self.gemini_model.start_chat(history=[]) # Tạo history rỗng nếu không có summary
            print(f"Không tìm thấy summary cho session ID: {session_id}. Bắt đầu session mới.") # Log no summary
        messages_data = get_messages_by_session_id_json(db, session_id) # Gọi hàm controller để lấy messages JSON
        db.close() # Đóng database session

        if messages_data:
            for message_data in messages_data:
                sender = "user" if message_data['sender'] == "user" else "system" # Sửa thành system nếu bạn đã thống nhất
                msg_id = message_data['message_id']
                msg_text = message_data['content']

                # Tạo ChatItem mới
                print(f"load_selected_chat: Creating ChatItem for message_id={msg_id}, chat_app={self}") # Debug print
                msg_widget = ChatItem(msg_id, msg_text, sender=sender, chat_app=self)
                msg_item = QListWidgetItem()
                msg_item.setSizeHint(msg_widget.sizeHint())

                # Thêm vào khung chat
                self.chat_display.addItem(msg_item)
                self.chat_display.setItemWidget(msg_item, msg_widget)

        self.chat_display.scrollToBottom()

    def create_new_session(self):
        """Tạo một phiên chat mới."""
        # === Lưu summary của session hiện tại (nếu có) ===
        self.save_current_session_summary() # Gọi hàm save summary trước khi tạo session mới
        # === Xóa history Gemini trước khi tạo session mới ===
        if not self.is_toggle_on: # Chỉ xóa history Gemini khi AI model là Gemini (toggle OFF)
            self.clear_gemini_history() # Gọi hàm xóa history Gemini
        # === Tạo session mới trong database ===
        db = next(get_db()) # Lấy database session
        session_name = f"chat_{datetime.now().strftime('%Y%m%d_%H%M')}" # Tạo session name tự động
        if self.is_toggle_on: # Kiểm tra self.is_toggle_on
            ai_model = "gpt" # Hoặc model OpenAI/GPT bạn muốn dùng
            print("Tạo session với OpenAI/GPT") # Log để debug
        else:
            ai_model = "gemini" # Hoặc model Gemini bạn muốn dùng
            print("Tạo session với Gemini") # Log để debug
        ai_max_tokens = 1024
        ai_response_time = "fast"

        new_session = create_session_controller(db, session_name, ai_model, ai_max_tokens, ai_response_time) # Gọi controller để tạo session
        db.close() # Đóng database session

        if new_session:
            print(f"Session mới đã được tạo: {new_session.session_name} (ID: {new_session.session_id})")
            self.load_sessions_from_db() # Load lại sessions và cập nhật history list

            # Tự động chọn session mới
            new_session_id = new_session.session_id # Lấy session_id của session mới tạo
            new_session_item = self.find_session_item_by_id(new_session_id) # Tìm item trong history list
            if new_session_item:
                self.history_list.setCurrentItem(new_session_item) # Chọn session mới
                print(f"Session mới (ID: {new_session_id}) đã được chọn sau khi tạo.")
            else:
                print(f"Không tìm thấy session item cho ID: {new_session_id} sau khi tạo (ở create_new_session).")

            self.chat_display.clear()
            self.input_field.clear()
        else:
            print("Lỗi khi tạo session mới.")

    def delete_selected_session(self, item, session_id):
        """Xóa session hiện tại được chọn."""
        session_name = item.text() # Lấy session name để hiển thị thông báo

        # Hiển thị hộp thoại xác nhận trước khi xóa (tùy chọn, nhưng nên có)
        reply = QMessageBox.question(self, 'Xác nhận xóa Session',
            f"Bạn có chắc chắn muốn xóa session '{session_name}' không?\nHành động này không thể hoàn tác!",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            db = next(get_db())
            deleted = delete_session_controller(db, session_id) # Gọi controller xóa session
            db.close()

            if deleted:
                print(f"Session '{session_name}' (ID: {session_id}) đã được xóa.") # Log xóa thành công

                row = self.history_list.row(item) # Get row index
                self.history_list.takeItem(row) # Remove item from QListWidget

                self.chat_display.clear() # Xóa chat display khi session bị xóa
                self.current_session_id = None # Reset current_session_id
                # self.load_selected_messages_list() # KHÔNG gọi load_selected_messages_list() ở đây nữa

                # === Kiểm tra nếu danh sách session trở nên rỗng sau khi xóa ===
                if self.history_list.count() == 0: # Nếu history_list rỗng sau khi xóa
                    print("Danh sách session đã rỗng sau khi xóa.") # Log
                    self.chat_display.clear() # Đảm bảo chat_display cũng trống
                    self.current_session_id = None # Đảm bảo current_session_id là None
                    self.selected_messages.clear() # Clear selected messages list luôn cho chắc
                    self.selected_messages_data = [] # Clear selected messages data luôn cho chắc
            else:
                print(f"Lỗi khi xóa session '{session_name}' (ID: {session_id}).") # Log lỗi xóa
                
    def save_current_session_summary(self, session_id_to_save=None):
        """Lưu hoặc cập nhật summary của session hiện tại (hoặc session_id được truyền vào)."""
        session_id = session_id_to_save # Sử dụng session_id truyền vào, hoặc session hiện tại nếu không có tham số
        
        if not session_id: # Nếu không có session_id truyền vào, lấy session hiện tại từ history_list
            current_session_item = self.history_list.currentItem()
            if current_session_item:
                session_id = current_session_item.data(Qt.UserRole)
        if session_id: # Kiểm tra lại session_id (có thể vẫn là None nếu không có session nào được chọn)
            db = next(get_db()) # Lấy database session
            # === Lấy statement_index của tin nhắn CUỐI CÙNG trong session ===
            last_message = db.query(models.Message).filter(models.Message.session_id == session_id).order_by(models.Message.statement_index.desc()).first()
            to_statement_index = 0 # Default value nếu không có message nào trong session
            if last_message:
                    to_statement_index = last_message.statement_index # Lấy statement_index của tin nhắn cuối cùng
            # Lấy history từ Gemini chat (hoặc OpenAI nếu dùng OpenAI)
            # === Serialize self.gemini_chat.history to JSON string ===
            history_json_string = ""
            if self.gemini_chat and self.gemini_chat.history:
                history_json_string = json.dumps([
                    {
                        "role": chat_turn.role,
                        "parts": [part.text for part in chat_turn.parts] # Lưu parts dưới dạng list text
                    }
                    for chat_turn in self.gemini_chat.history
                ], ensure_ascii=False)
            if history_json_string:
                summary_text = history_json_string # Lưu JSON string vào summary_text

                existing_summary = db.query(models.Summary).filter(models.Summary.session_id == session_id).first()

                if existing_summary:
                    existing_summary.summary_text = summary_text
                    existing_summary.to_statement_index = to_statement_index
                    db.commit()
                    print(f"Summary (JSON) đã được cập nhật cho session ID: {session_id}") # Log update
                else:
                    create_summary_controller(db, session_id, to_statement_index, summary_text)
                    print(f"Summary (JSON) đã được tạo cho session ID: {session_id}") # Log create
            else:
                print(f"Không có history để lưu summary cho session ID: {session_id}")

            db.close()

    def adjust_input_height(self):
        document_height = self.input_field.document().size().height()
        new_height = min(100, max(styles.INPUT_FIELD_HEIGHT, int(document_height + 10)))
        self.input_field.setFixedHeight(new_height)

    def update_toggle_state(self, state):
        self.is_toggle_on = state

    def send_message(self):
        user_message_text = ""
        if self.attached_prompt_content: # Nếu có prompt đính kèm
            # 1. Xử lý Prompt đính kèm: Thay placeholder trong prompt đính kèm bằng tin nhắn user
            user_message_text = self.attached_prompt_content.replace("{nội dung tin nhắn}", self.input_field.toPlainText().strip())
            print(user_message_text)
        else:    
            user_message_text = self.input_field.toPlainText().strip() # Use user_message_text consistently
        if not user_message_text:
            return

        # === Lấy session_id của session đang hiển thị ===
        current_session_item = self.history_list.currentItem()
        # Kiểm tra nếu không có session nào được chọn
        if not current_session_item:
            print("Không có session được chọn. Tự động tạo session mới...")
            # Tạo session mới và LẤY session_id của session vừa tạo
            new_session_id = self.create_new_session_and_get_id() # Gọi hàm mới để tạo session và lấy ID
            if not new_session_id: # Nếu tạo session không thành công
                print("Lỗi tạo session mới. Không thể gửi tin nhắn.")
                show_toast(self, "Lỗi tạo session mới. Không thể gửi tin nhắn.", "error")
                return # Dừng lại nếu tạo session lỗi
            # Tìm item của session mới trong history list dựa trên session_id
            new_session_item = self.find_session_item_by_id(new_session_id)
            if new_session_item:
                self.history_list.setCurrentItem(new_session_item) # Chọn session mới
                print(f"Session mới (ID: {new_session_id}) đã được tạo và chọn.")
            else:
                print(f"Không tìm thấy session item cho ID: {new_session_id} sau khi tạo.")
                return # Dừng lại nếu không tìm thấy item
        current_session_item = self.history_list.currentItem() # Lấy lại current item sau khi có thể đã tạo mới    
        session_id = current_session_item.data(Qt.UserRole)

        prompt_template = f"""Bạn là một Giáo viên thông minh. Hãy trả lời nội dung dưới đây một cách chi tiết và rõ ràng:
        {user_message_text}
        Kết quả trả về phải bao gồm quy chuẩn bắt buộc sau (đừng trả về các yêu cầu này trong phần trả về):
        - Luôn tách biệt nội dung và công thức toán cách nhau 1 dòng.
        - Các công thức phải trả về mã Latex với điều kiện:
            + Sử dụng $...$ để bọc các công thức thay vì sử dụng \[...\] hay \(...\), không sử dụng \boxed trong công thức.
            + Không được sử dụng \frac, thay vào đó sử dụng \dfrac
        """

        # === Lưu tin nhắn người dùng vào database ===
        db = next(get_db())
        db_user_message = create_message_controller(db, session_id, "user", self.input_field.toPlainText().strip()) # Use user_message_text
        db.close()

        # === Hiển thị tin nhắn người dùng lên GUI ===
        user_item = QListWidgetItem()
        user_widget = ChatItem(db_user_message.message_id, db_user_message.content, sender="user", chat_app=self)
        user_item.setSizeHint(user_widget.sizeHint())
        self.chat_display.addItem(user_item)
        self.chat_display.setItemWidget(user_item, user_widget)
        self.input_field.clear()

        self.input_field.setEnabled(False)
        self.send_button.setEnabled(False)

        bot_reply_text = ""
        ai_sender = "system"

        try:
            if self.is_toggle_on: # Toggle ON: OpenAI/ChatGPT
                print("Gọi OpenAI/ChatGPT API")
                openai_response = self.openai_client.chat.completions.create(
                    model="gpt-4",
                    messages=[{"role": "user", "content": prompt_template}] # **Corrected: user_message_text for OpenAI**
                )
                bot_reply_text = openai_response.choices[0].message.content.strip() # Correctly get text from OpenAI response
                ai_sender = "system"
            else: # Toggle OFF: Gemini
                print("Gọi Gemini API")
                gemini_response = self.gemini_chat.send_message(prompt_template) # **Corrected: user_message_text for Gemini**
                bot_reply_text = gemini_response.text # Correctly get text from Gemini response
                ai_sender = "system"
                # print(f"Gemini history: {self.gemini_chat.history}") 

        except Exception as e:
            bot_reply_text = f"Lỗi khi gọi AI API: {str(e)}"
            show_toast(self, f"{bot_reply_text}", "error")
            ai_sender = "system"

        # === Lưu phản hồi AI vào database ===
        db = next(get_db())
        db_bot_message = create_message_controller(db, session_id, ai_sender, bot_reply_text)
        db.close()

        # === Hiển thị phản hồi AI lên GUI ===
        bot_item = QListWidgetItem()
        bot_widget = ChatItem(db_bot_message.message_id, db_bot_message.content, sender="system", chat_app=self)
        bot_item.setSizeHint(bot_widget.sizeHint())
        self.chat_display.addItem(bot_item)
        self.chat_display.setItemWidget(bot_item, bot_widget)

        self.chat_display.scrollToBottom()

        # Kích hoạt lại input và nút send
        self.input_field.setEnabled(True)
        self.send_button.setEnabled(True)
        self.input_field.setFocus() # Focus lại vào ô input

    def create_new_session_and_get_id(self):
        """Tạo một session mới và trả về session_id của session vừa tạo.
        Trả về None nếu tạo session không thành công."""
        db = next(get_db())
        session_name = f"chat_{datetime.now().strftime('%Y%m%d_%H%M')}"
        ai_model = "gpt" if self.is_toggle_on else "gemini"
        ai_max_tokens = 1024
        ai_response_time = "fast"

        new_session = create_session_controller(db, session_name, ai_model, ai_max_tokens, ai_response_time)
        db.close()

        if new_session:
            print(f"Session mới đã được tạo (trong create_new_session_and_get_id): {new_session.session_name} (ID: {new_session.session_id})")
            self.load_sessions_from_db() # Load lại sessions để cập nhật history list
            return new_session.session_id # TRẢ VỀ session_id của session mới tạo
        else:
            print("Lỗi khi tạo session mới (trong create_new_session_and_get_id).")
            return None # Trả về None nếu tạo session lỗi

    def find_session_item_by_id(self, session_id):
        """Tìm QListWidgetItem trong history_list dựa trên session_id."""
        for index in range(self.history_list.count()):
            item = self.history_list.item(index)
            if item.data(Qt.UserRole) == session_id:
                return item
        return None # Không tìm thấy item nào có session_id tương ứng
    
    def clear_gemini_history(self):
        """Xóa lịch sử chat của Gemini."""
        if self.gemini_model: # Kiểm tra xem gemini_model đã được khởi tạo chưa
            self.gemini_chat = self.gemini_model.start_chat(history=[]) # Tạo một gemini_chat mới, lịch sử sẽ rỗng
            print("Gemini history đã được xóa.") # Log
        else:
            print("Gemini model chưa được khởi tạo.") # Log nếu model chưa khởi tạo

    def add_to_selected_messages(self, message_id):
        """Xử lý việc thêm message vào danh sách tin nhắn đã chọn."""
        print("ChatApp.add_to_selected_messages được gọi, message_id =", message_id) # Debug print
        db = next(get_db())
        selected_message = select_ai_response(db, message_id) # Gọi controller để select message trong DB
        print("ChatApp.add_to_selected_messages: Sau khi gọi select_ai_response, selected_message =", selected_message) # Debug print - Kiểm tra selected_message
        db.close()

        if selected_message:
            print(f"Message ID {message_id} đã được chọn.") # Log
            print(f"Danh sách self.selected_messages_data trước khi load lại gui:\n {self.selected_messages_data}") # Log
            self.load_selected_messages_list() # Gọi hàm load lại danh sách selected messages
            print(f"Danh sách self.selected_messages_data sau khi load lại gui:\n {self.selected_messages_data}") # Log
        else:
            print(f"Không thể chọn Message ID {message_id}.") # Log lỗi

    def load_selected_messages_list(self):
        """Load danh sách các tin nhắn đã chọn từ database và hiển thị ở khung bên phải."""
        self.selected_messages.clear()
        self.selected_messages_data = []
        db = next(get_db())
        selected_messages_data_from_db = get_all_selected_messages_json(db)
        db.close()

        if selected_messages_data_from_db:
            self.selected_messages_data = selected_messages_data_from_db.copy()
            for index, message_data in enumerate(self.selected_messages_data):
                display_text = f"{index + 1}. {message_data['content'][:50]}..."
                item = QListWidgetItem()
                item.setSizeHint(QSize(self.selected_messages.width(), 40))

                # === Tạo WIDGET TÙY CHỈNH cho item (bao gồm Checkbox) ===
                widget = QWidget()
                widget.setStyleSheet("""
                    background-color: transparent;
                """)
                layout = QHBoxLayout()
                layout.setContentsMargins(5, 2, 5, 2)
                layout.setSpacing(5)

                # Checkbox cho mỗi tin nhắn
                checkbox = QCheckBox()
                checkbox.setObjectName("message_checkbox") # Set objectName để tìm checkbox sau này
                checkbox.setChecked(message_data.get('is_exported', False)) # Mặc định là chọn (có thể thay đổi)
                checkbox.stateChanged.connect(lambda state, msg_id=message_data['message_id']: self.checkbox_state_changed_signal.emit(msg_id, state == Qt.Checked)) # Phát signal khi state thay đổi
                layout.addWidget(checkbox)

                # Label hiển thị nội dung
                metrics = QFontMetrics(self.selected_messages.font())
                elided_text = metrics.elidedText(display_text, Qt.ElideRight, self.selected_messages.width() - 70) # Giảm width để chừa chỗ cho checkbox và nút xóa
                label = QLabel(elided_text)
                label.setToolTip(message_data['content'])
                label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
                label.setStyleSheet("""color: white;""")
                label.setAlignment(Qt.AlignVCenter)
                layout.addWidget(label)

                # Nút xóa (icon) (giữ nguyên)
                delete_item_button = QPushButton()
                delete_item_button.setIcon(QIcon("views/images/trash_icon.png"))
                delete_item_button.setCursor(QCursor(Qt.PointingHandCursor))
                delete_item_button.setFixedSize(18, 18)
                delete_item_button.setStyleSheet("border: none; background: transparent;")
                delete_item_button.clicked.connect(lambda _, item=item: self.remove_selected_message(item))
                layout.addWidget(delete_item_button)

                widget.setLayout(layout)
                # === END WIDGET TÙY CHỈNH ===
                item.setData(Qt.UserRole, message_data['message_id'])
                self.selected_messages.addItem(item)
                self.selected_messages.setItemWidget(item, widget)
        else:
            print("Không có tin nhắn nào được chọn.")

    def update_message_exported_status(self, message_id, is_checked):
        """Cập nhật trạng thái is_exported của message trong database khi checkbox thay đổi."""
        db = next(get_db())
        if update_message_is_exported(db, message_id, is_checked): # Gọi controller update_message_is_exported
            db.close()
            print(f"Message ID {message_id} is_exported status updated to: {is_checked}") # Log
        else:
            db.close()
            print(f"Error updating is_exported status for Message ID {message_id}") # Log lỗi
            
    def remove_selected_message(self, item):
        """Bỏ chọn một tin nhắn khỏi danh sách tin nhắn đã chọn (khung bên phải)."""
        message_id = item.data(Qt.UserRole) # Lấy message_id từ item data
        db = next(get_db())
        unselected_message = unselect_ai_response(db, message_id) # Gọi controller unselect message trong DB
        db.close()
        if unselected_message:
            print(f"Message ID {message_id} đã được bỏ chọn.") # Log bỏ chọn thành công
            self.load_selected_messages_list() # Gọi hàm load lại danh sách selected messages (ĐỒNG BỘ GUI và self.selected_messages_data)
        else:
            print(f"Lỗi khi bỏ chọn Message ID {message_id}.") # Log lỗi bỏ chọn

    def clear_list_messages(self):
        """Xóa tất cả các tin nhắn đã chọn khỏi danh sách."""
        db = next(get_db())
        cleared_count = clear_all_selected_messages_controller(db) # Gọi controller để xóa selected messages trong DB
        db.close()

        if cleared_count > 0:
            print(f"{cleared_count} tin nhắn đã được bỏ chọn.") # Log số lượng tin nhắn đã bỏ chọn
        else:
            print("Không có tin nhắn nào được bỏ chọn (có thể chưa có tin nhắn nào được chọn).") # Log nếu không có tin nhắn nào được bỏ chọn
        self.load_selected_messages_list() # Gọi hàm load lại danh sách selected messages (sẽ hiển thị danh sách trống)

    def export_list_messages(self):
        """Xuất danh sách tin nhắn đã chọn ra file Docx."""
        selected_messages_data_for_export = []

        for i in range(self.selected_messages.count()):
            item = self.selected_messages.item(i)
            widget = self.selected_messages.itemWidget(item)
            if widget:
                checkbox = widget.findChild(QtWidgets.QCheckBox, "message_checkbox")
                if checkbox and checkbox.isChecked(): # Kiểm tra checkbox có được tích không
                    message_id = item.data(Qt.UserRole) # Lấy message_id từ item
                    db = next(get_db())
                    message_data_from_db = get_message_by_id_json(db, message_id) # Hàm mới để lấy message theo ID
                    db.close()
                    if message_data_from_db:
                        selected_messages_data_for_export.append(message_data_from_db) # Thêm message data vào list xuất

        print(selected_messages_data_for_export) # Log dữ liệu xuất file (để debug)

        if selected_messages_data_for_export:
            if export_to_docx(selected_messages_data_for_export):
                print("Xuất file thành công!")
            else:
                print("Xuất file thất bại!")
        else:
            print("Danh sách trống, không có gì để xuất.")

    def closeEvent(self, event):
        """Xử lý sự kiện đóng cửa sổ ứng dụng."""
        print("Ứng dụng đang đóng...") # Log
        self.save_current_session_summary() # Lưu summary của session hiện tại trước khi đóng
        event.accept() # Chấp nhận sự kiện đóng cửa sổ, ứng dụng sẽ đóng