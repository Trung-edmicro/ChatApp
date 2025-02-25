import sys
import re
import json
from views import styles
import uuid
import openai
import google.generativeai as genai
from google.generativeai.types import content_types
from datetime import datetime
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QLineEdit, QPushButton, QListWidget, QListWidgetItem, QLabel, QSizePolicy, QAction, QMenu, QMessageBox
from PyQt5.QtGui import QPalette, QColor, QIcon, QCursor, QFont, QPixmap, QFontMetrics, QClipboard
from PyQt5.QtCore import Qt, QPropertyAnimation, QRect, pyqtSignal, QSize, QTimer
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineSettings
import markdown2
from internal.db.connection import get_db
from controllers.controllers import *
from views.export_docx import export_to_docx

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

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(2)

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

        font_metrics = QFontMetrics(self.text_edit.font())
        text_width = font_metrics.width(message) + 16
        min_width = 60
        max_width = 500
        # Web view
        self.web_view = QWebEngineView()
        self.web_view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        # Chuyển Markdown thành HTML có hỗ trợ MathJax
        def format_message(message):
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <script>
                    window.MathJax = {{
                        tex: {{
                            inlineMath: [['$', '$'], ['\\(', '\\)']]
                        }},
                        svg: {{
                            fontCache: 'global'
                        }}
                    }};
                </script>
                <script type="text/javascript" async
                    src="https://polyfill.io/v3/polyfill.min.js?features=es6">
                </script>
                <script type="text/javascript" async
                    src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js">
                </script>
                <style>
                    body {{
                        font-size: 17px;
                        color: white;
                        background-color: #2E2E2E;
                    }}
                    ::-webkit-scrollbar {{
                        width: 10px; /* Độ rộng thanh cuộn */
                        height: 10px;
                    }}
                    ::-webkit-scrollbar-track {{
                        background: #2E2E2E;
                        border-radius: 10px;
                    }}
                    ::-webkit-scrollbar-thumb {{
                        background: #555;
                        border-radius: 10px;
                        transition: background 0.3s;
                    }}
                    ::-webkit-scrollbar-thumb:hover {{
                        background: #888;
                    }}
                    .chat-container {{
                        display: flex;
                        flex-direction: column;
                        align-items: flex-start;
                        margin-bottom: 10px;
                        max-width: 100%;
                    }}
                    .ai-message {{
                        max-width: 100%;
                        border-radius: 12px;
                        text-align: left;
                    }}
                </style>
            </head>
            <body>
                <div class="chat-container">
                    <div class="ai-message">
                        {markdown2.markdown(message, extras=["fenced-code-blocks", "tables", "strike", "mathjax"])}
                    </div>
                </div>
                <script>
                    MathJax.typesetPromise();
                </script>
            </body>
            </html>
            """
            return html_content
        if sender == "user":
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
            main_layout.addStretch()
            main_layout.addWidget(self.text_edit, 0, Qt.AlignRight)
            self.text_edit.setFixedWidth(min(max_width, max(text_width, min_width)))

        else:
            main_layout.addLayout(more_layout) # Luôn thêm more_layout
            if latex_checked:
                # AI message CÓ LaTeX: chỉ hiển thị WebView, ẨN QTextEdit
                self.web_view.setHtml(format_message(message)) # Set HTML vào WebView
                self.text_edit.hide() # ẨN QTextEdit
                main_layout.addWidget(self.web_view) # Thêm WebView vào layout
                main_layout.setStretch(0, 1) # Stretch layout cho WebView
                main_layout.setStretch(1, 3) # Stretch layout cho WebView
            else:
                self.text_edit.setStyleSheet("""
                    QTextEdit {
                        border: 1px solid #545454;
                        font-size: 14px;
                        border-radius: 12px;
                        padding: 8px;
                        color: white;
                    }
                """)
                self.web_view.hide() # ẨN WebView
                main_layout.addWidget(self.text_edit) # Thêm QTextEdit vào layout
        #     main_layout.addLayout(more_layout)
        #     main_layout.addWidget(self.text_edit)
        # self.web_view.setHtml(format_message(message))
        doc = self.text_edit.document()
        doc.setTextWidth(self.text_edit.width())
        self.text_edit.setFixedHeight(int(doc.size().height()) + 15)
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
        add_item_action = QAction(QIcon("icons/copy.png"), "Add Text", self)
        add_item_action.triggered.connect(self.add_text)

        # Hành động Copy Text
        copy_text_action = QAction(QIcon("icons/copy.png"), "Copy Text", self)
        copy_text_action.triggered.connect(self.copy_text)

        # Hành động Copy Markdown
        copy_markdown_action = QAction(QIcon("icons/markdown.png"), "Copy Markdown", self)
        copy_markdown_action.triggered.connect(self.copy_markdown)

        # Thêm hành động vào menu
        menu.addAction(add_item_action)
        menu.addAction(copy_text_action)
        menu.addAction(copy_markdown_action)

        # Hiển thị menu ngay tại vị trí của nút
        menu.exec_(self.more_button.mapToGlobal(self.more_button.rect().bottomRight()))

    def add_text(self):
        print("ChatItem.add_text được gọi") # Debug print
        message_content = self.text_edit.toPlainText()
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

class ChatApp(QWidget):
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

    def initUI(self):
        app_font = QFont("Inter", 12)
        self.setWindowTitle("ChatApp")
        self.setGeometry(100, 100, 1280, 820)
        self.app.setFont(app_font)
        self.setStyleSheet("background-color: #212121; color: white;")

        main_layout = QHBoxLayout()

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
                padding: {styles.HISTORY_ITEM_PADDING}; 
                border: none; 
                margin-bottom: 5px; 
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

        main_layout.addLayout(history_layout) 

        # Layout chat
        chat_layout = QVBoxLayout()
        chat_layout.setContentsMargins(0, 8, 0, 0)

        # Toggle AI
        self.toggle_switch = ToggleSwitch()
        chat_layout.addWidget(self.toggle_switch)
        
            # Trạng thái toggle
        self.is_toggle_on = False  
        self.toggle_switch.toggled_signal.connect(self.update_toggle_state)

            # Layout messages
        self.chat_display = QListWidget(self)
        self.chat_display.setStyleSheet(f"""
            QListWidget {{
                border: none;
                background-color: #212121;
            }}
            QListWidget::item:hover {{
                background-color: transparent;
            }}
            QListWidget::item:selected {{
                background-color: transparent;
                outline: none;
            }}
            QListWidget:focus {{
                outline: none;
            }}
            {styles.SCROLLBAR_STYLES}
        """)
        chat_layout.addWidget(self.chat_display)
        
            # Layout input
        input_container = QHBoxLayout()
        input_container.setContentsMargins(10, 10, 10, 10)
        input_container.setSpacing(5)
        
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

            # send button
        self.send_button = QPushButton(self)
        self.send_button.setIcon(QIcon("views/images/send_icon.png"))
        self.send_button.setCursor(QCursor(Qt.PointingHandCursor))
        self.send_button.setStyleSheet(
            f"background-color: {styles.SEND_BUTTON_COLOR}; color: white; border-radius: {styles.SEND_BUTTON_SIZE // 2}px;"
            f"width: {styles.SEND_BUTTON_SIZE}px; height: {styles.SEND_BUTTON_SIZE}px;"
        )
        self.send_button.clicked.connect(self.send_message)
        input_container.addWidget(self.send_button)

        input_widget = QWidget()
        input_widget.setStyleSheet(f"background-color: {styles.BACKGROUND_COLOR_INPUT}; border-radius: 20px; padding: 5px; min-height: 30px; max-height: 100px")
        input_widget.setLayout(input_container)
        chat_layout.addWidget(input_widget)

        main_layout.addLayout(chat_layout)
        
        # Widget chứa danh sách tin nhắn
        list_messages_widget = QWidget()
        list_messages_widget.setStyleSheet("background-color: #171717; border-radius: 10px;")  
        list_messages_widget.setFixedWidth(250)  # Giữ kích thước cố định 250px

            # Layout danh sách tin nhắn
        list_messages_layout = QVBoxLayout()
        list_messages_layout.setSpacing(5)  
        list_messages_layout.setContentsMargins(5, 15, 5, 10)  

            # Label
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

        self.clear_button = QPushButton("Xóa tất cả")
        self.clear_button.setStyleSheet("background-color: #2f2f2f; color: white; border-radius: 6px; font-size: 12px; font-weight: bold; padding: 5px;")
        self.clear_button.setFixedSize(112, 30)  
        self.clear_button.setCursor(QCursor(Qt.PointingHandCursor))
        self.clear_button.clicked.connect(self.clear_list_messages)
        buttons_layout.addWidget(self.clear_button)

        self.export_button = QPushButton("Xuất file Docx")
        self.export_button.setStyleSheet("background-color: #00a67d; color: white; border-radius: 6px; font-size: 12px; font-weight: bold; padding: 5px;")
        self.export_button.setFixedSize(112, 30)
        self.export_button.setCursor(QCursor(Qt.PointingHandCursor))
        self.export_button.clicked.connect(self.export_list_messages)
        buttons_layout.addWidget(self.export_button)

        list_messages_layout.addLayout(buttons_layout)

        list_messages_widget.setLayout(list_messages_layout)
        main_layout.addWidget(list_messages_widget)
        
        self.setLayout(main_layout)
        
# === Function ===
    def load_sessions_from_db(self):
        db = next(get_db())
        sessions = get_all_sessions(db)
        db.close()

        if sessions:
            self.history_list.clear() # Clear list trước khi load dữ liệu mới
            max_width = self.history_list.width() - 20
            for session_data in sessions:
                full_text = session_data['session_name']

                metrics = QFontMetrics(self.history_list.font())
                elided_text = metrics.elidedText(full_text, Qt.ElideRight, max_width)

                item = QListWidgetItem()
                item.setData(Qt.UserRole, session_data['session_id'])
                item.setSizeHint(QSize(self.history_list.width(), 40))
                    
                # Tạo widget chứa tên session và nút xóa
                widget = QWidget()
                widget.setStyleSheet("""
                        background-color: transparent;
                    """)
                layout = QHBoxLayout()
                layout.setContentsMargins(10, 0, 10, 0)
                layout.setSpacing(5)

                # Label hiển thị session name
                label = QLabel(elided_text)
                label.setToolTip(full_text)
                label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
                label.setStyleSheet("color: white;")

                # Nút xóa (icon thùng rác)
                delete_button = QPushButton()
                delete_button.setIcon(QIcon("views/images/trash_icon.png"))
                delete_button.setCursor(QCursor(Qt.PointingHandCursor))
                delete_button.setFixedSize(18, 18)
                delete_button.setStyleSheet("border: none; background: transparent;")
                delete_button.clicked.connect(lambda _, item=item, session_id=session_data['session_id']: self.delete_selected_session(item, session_id))

                # Thêm vào layout
                layout.addWidget(label)
                layout.addStretch()
                layout.addWidget(delete_button)

                widget.setLayout(layout)
                widget.setMinimumHeight(40)

                self.history_list.addItem(item)
                self.history_list.setItemWidget(item, widget)
        else:
            print("Không có session nào trong Database.") # Vẫn in log nếu không có session

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

        if new_session: # Kiểm tra nếu session tạo thành công
            print(f"Session mới đã được tạo: {new_session.session_name} (ID: {new_session.session_id})")
            self.load_sessions_from_db() # Gọi lại hàm load_sessions_from_db để cập nhật danh sách session trên GUI
            self.chat_display.clear() # Xóa chat display khi tạo session mới
            self.input_field.clear() # Xóa input field khi tạo session mới
        else:
            print("Lỗi khi tạo session mới.") # Xử lý lỗi nếu không tạo được session

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
                self.load_sessions_from_db() # Load lại danh sách session để cập nhật GUI
                self.chat_display.clear() # Xóa chat display khi session bị xóa
                self.current_session_id = None # Reset current_session_id
                self.load_selected_messages_list()
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
        user_message_text = self.input_field.toPlainText().strip() # Use user_message_text consistently
        if not user_message_text:
            return

        # === Lấy session_id của session đang hiển thị ===
        current_session_item = self.history_list.currentItem()
        if not current_session_item:
            print("Chưa chọn session để gửi tin nhắn.")
            return
        session_id = current_session_item.data(Qt.UserRole)

        # === Lưu tin nhắn người dùng vào database ===
        db = next(get_db())
        db_user_message = create_message_controller(db, session_id, "user", user_message_text) # Use user_message_text
        db.close()

        # === Hiển thị tin nhắn người dùng lên GUI ===
        user_item = QListWidgetItem()
        user_widget = ChatItem(db_user_message.message_id, db_user_message.content, sender="user", chat_app=self)
        user_item.setSizeHint(user_widget.sizeHint())
        self.chat_display.addItem(user_item)
        self.chat_display.setItemWidget(user_item, user_widget)
        self.input_field.clear()

        bot_reply_text = ""
        ai_sender = "system"

        try:
            if self.is_toggle_on: # Toggle ON: OpenAI/ChatGPT
                print("Gọi OpenAI/ChatGPT API")
                openai_response = self.openai_client.chat.completions.create(
                    model="gpt-4",
                    messages=[{"role": "user", "content": user_message_text}] # **Corrected: user_message_text for OpenAI**
                )
                bot_reply_text = openai_response.choices[0].message.content.strip() # Correctly get text from OpenAI response
                ai_sender = "system"
            else: # Toggle OFF: Gemini
                print("Gọi Gemini API")
                gemini_response = self.gemini_chat.send_message(user_message_text) # **Corrected: user_message_text for Gemini**
                bot_reply_text = gemini_response.text # Correctly get text from Gemini response
                ai_sender = "system"
                print(f"Gemini history: {self.gemini_chat.history}") # Debugging Gemini history

        except Exception as e:
            bot_reply_text = f"Lỗi khi gọi AI API: {str(e)}"
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

            # === Thêm dữ liệu tin nhắn đã chọn vào self.selected_messages_data ===
            self.selected_messages_data.append({ # Thêm dictionary vào list
                "message_id": selected_message.message_id,
                "sender": selected_message.sender,
                "content": selected_message.content,
                "timestamp": selected_message.timestamp.isoformat() if selected_message.timestamp else None,
                "selected_at": selected_message.selected_at.isoformat() if selected_message.selected_at else None
            })
            print(f"Danh sách self.selected_messages_data trước khi load lại gui: {self.selected_messages_data}") # Log
            self.load_selected_messages_list() # Gọi hàm load lại danh sách selected messages
            print(f"Danh sách self.selected_messages_data sau khi load lại gui: {self.selected_messages_data}") # Log
        else:
            print(f"Không thể chọn Message ID {message_id}.") # Log lỗi

    def load_selected_messages_list(self):
        """Load danh sách các tin nhắn đã chọn từ database và hiển thị ở khung bên phải."""
        self.selected_messages.clear() # Clear list trước khi load lại
        db = next(get_db())
        selected_messages_data = get_all_selected_messages_json(db) # Lấy danh sách selected messages JSON từ controller
        db.close()

        if selected_messages_data:
            for index, message_data in enumerate(selected_messages_data): # Sử dụng enumerate để lấy index
                display_text = f"{index + 1}. {message_data['content'][:50]}..." # Thêm số thứ tự vào display_text (index + 1)
                item = QListWidgetItem(display_text)
                item.setSizeHint(QSize(self.selected_messages.width(), 40)) # Set Size Hint cho item
                # === Tạo WIDGET TÙY CHỈNH cho item ===
                widget = QWidget()
                widget.setStyleSheet("""
                    background-color: transparent;
                """)
                layout = QHBoxLayout()
                layout.setContentsMargins(5, 2, 5, 2)
                layout.setSpacing(5)

                # Tạo label hiển thị nội dung
                metrics = QFontMetrics(self.selected_messages.font())
                elided_text = metrics.elidedText(display_text, Qt.ElideRight, self.selected_messages.width() - 40) # Tạo elided_text
                label = QLabel(elided_text) # **LỖI CŨ: elided_text chưa được định nghĩa ở đây! CẦN SỬA**
                label = QLabel(elided_text) # Tạo label SAU khi có elided_text
                label.setToolTip(message_data['content'])
                label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
                label.setStyleSheet("""color: white;""")
                label.setAlignment(Qt.AlignVCenter)

                # Nút xóa (icon)
                delete_item_button = QPushButton()
                delete_item_button.setIcon(QIcon("views/images/trash_icon.png")) # Đảm bảo đường dẫn icon đúng
                delete_item_button.setCursor(QCursor(Qt.PointingHandCursor))
                delete_item_button.setFixedSize(18, 18)
                delete_item_button.setStyleSheet("border: none; background: transparent;")
                delete_item_button.clicked.connect(lambda _, item=item: self.remove_selected_message(item)) # Cần implement self.remove_selected_message

                # Thêm label và nút vào layout
                layout.addWidget(label)
                layout.addStretch()
                layout.addWidget(delete_item_button)

                widget.setLayout(layout)
                # === END WIDGET TÙY CHỈNH ===
                item.setData(Qt.UserRole, message_data['message_id']) # Lưu message_id (nếu cần)
                self.selected_messages.addItem(item)
                self.selected_messages.setItemWidget(item, widget)
                if self.selected_messages_data == []:
                    # === Đồng bộ hóa dữ liệu vào self.selected_messages_data ===
                    self.selected_messages_data.append(message_data) # **Thêm message_data (dictionary) vào self.selected_messages_data**
        else:
            print("Không có tin nhắn nào được chọn.") # Log nếu không có selected messages

    def remove_selected_message(self, item):
        """Bỏ chọn một tin nhắn khỏi danh sách tin nhắn đã chọn (khung bên phải)."""
        message_id = item.data(Qt.UserRole) # Lấy message_id từ item data
        db = next(get_db())
        unselected_message = unselect_ai_response(db, message_id) # Gọi controller unselect message trong DB
        db.close()
        if unselected_message:
            print(f"Message ID {message_id} đã được bỏ chọn.") # Log bỏ chọn thành công
            self.load_selected_messages_list() # Load lại danh sách selected messages để cập nhật GUI
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

        self.selected_messages_data = [] # Xóa dữ liệu selected_messages_data (in-memory list)
        self.load_selected_messages_list() # Gọi hàm load lại danh sách selected messages (sẽ hiển thị danh sách trống)

    def export_list_messages(self):
        print(self.selected_messages_data)
        if export_to_docx(self.selected_messages_data):
            print("Xuất file thành công!")
        else:
            print("Xuất file thất bại!")

    def closeEvent(self, event):
        """Xử lý sự kiện đóng cửa sổ ứng dụng."""
        print("Ứng dụng đang đóng...") # Log
        self.save_current_session_summary() # Lưu summary của session hiện tại trước khi đóng
        event.accept() # Chấp nhận sự kiện đóng cửa sổ, ứng dụng sẽ đóng

def contains_latex(text):
    # Regex tìm các ký hiệu LaTeX phổ biến
    latex_patterns = [
        r"\$\$(.*?)\$\$",         # Công thức block $$ ... $$
        r"\$(.*?)\$",             # Công thức inline $ ... $
        r"\\\((.*?)\\\)",         # Công thức inline \( ... \)
        r"\\\[(.*?)\\\]",         # Công thức block \[ ... \]
        r"\\frac\{.*?\}\{.*?\}",  # Phân số
        r"\\sqrt\{.*?\}",         # Căn bậc hai
        r"\\sum",                 # Tổng sigma
        r"\\int",                 # Tích phân
        r"\\begin\{align\}"       # Hệ phương trình
    ]
    
    # Kiểm tra nếu có bất kỳ mẫu nào khớp
    for pattern in latex_patterns:
        if re.search(pattern, text, re.DOTALL):
            return True
    return False