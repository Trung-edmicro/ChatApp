import sys
import json
from views import styles
import uuid
import openai
import google.generativeai as genai
from datetime import datetime
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QLineEdit, QPushButton, QListWidget, QListWidgetItem, QLabel, QSizePolicy, QAction, QMenu
from PyQt5.QtGui import QPalette, QColor, QIcon, QCursor, QFont, QPixmap, QFontMetrics, QClipboard
from PyQt5.QtCore import Qt, QPropertyAnimation, QRect, pyqtSignal, QSize
CHAT_HISTORY_FILE = "ChatApp/data.json"

# Cấu hình AI API
    # OpenAI
client = openai.OpenAI(api_key="")

    # Gemini
api_key = ""
genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-2.0-flash-thinking-exp-01-21')
chat = model.start_chat(history=[])

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

        else:  # **AI Message**
            self.text_edit.setStyleSheet("""
                QTextEdit {
                    border: 1px solid #545454;
                    font-size: 14px;
                    border-radius: 12px;
                    padding: 8px;
                    color: white;
                }
            """)

            main_layout.addLayout(more_layout)
            main_layout.addWidget(self.text_edit)

        doc = self.text_edit.document()
        doc.setTextWidth(self.text_edit.width())
        self.text_edit.setFixedHeight(int(doc.size().height()) + 15)

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
        message_content = self.text_edit.toPlainText()
        if self.chat_app:
            print("in")
            self.chat_app.add_selected_message(message_content)

    def copy_text(self):
        clipboard = QApplication.clipboard()
        clipboard.setText(self.text_edit.toPlainText())

    def copy_markdown(self):
        clipboard = QApplication.clipboard()
        markdown_text = f"```\n{self.text_edit.toPlainText()}\n```"
        clipboard.setText(markdown_text)

class ChatApp(QWidget):
    def __init__(self, app):
        super().__init__()
        self.app = app
        self.initUI()
        self.load_chat_history()
        self.selected_messages_data = []

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
    def load_chat_history(self):
        try:
            with open(CHAT_HISTORY_FILE, "r", encoding="utf-8") as file:
                chat_sessions = json.load(file)
                self.history_list.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
                max_width = self.history_list.width() - 20
                for session in chat_sessions:
                    full_text = session['session_name']

                    metrics = QFontMetrics(self.history_list.font())
                    elided_text = metrics.elidedText(full_text, Qt.ElideRight, max_width)

                    item = QListWidgetItem(elided_text)
                    item.setData(Qt.UserRole, session['session_id'])
                    item.setSizeHint(QSize(self.history_list.width(), 40))
                    self.history_list.addItem(item)
        except FileNotFoundError:
            with open(CHAT_HISTORY_FILE, "w", encoding="utf-8") as file:
                json.dump([], file)

    def load_selected_chat(self, item):
        session_id = item.data(Qt.UserRole)
        try:
            with open(CHAT_HISTORY_FILE, "r", encoding="utf-8") as file:
                chat_sessions = json.load(file)
                for session in chat_sessions:
                    if session['session_id'] == session_id:
                        self.chat_display.clear()

                        for message in session['messages']:
                            sender = "user" if message['sender'] == "user" else "bot"
                            msg_id = message['message_id']
                            msg_text = message['content']

                            # Tạo ChatItem mới
                            msg_widget = ChatItem(msg_id, msg_text, sender=sender, chat_app=self)
                            msg_item = QListWidgetItem()
                            msg_item.setSizeHint(msg_widget.sizeHint())

                            # Thêm vào khung chat
                            self.chat_display.addItem(msg_item)
                            self.chat_display.setItemWidget(msg_item, msg_widget)

            self.chat_display.scrollToBottom()
        except FileNotFoundError:
            pass

    def create_new_session(self):
        """Tạo một phiên chat mới."""
        #Logic tạo session
        session_id = str(uuid.uuid4())
        session_name = f"chat_{datetime.now().strftime('%Y%m%d_%H%M')}"
        new_session = {
            "session_id": session_id,
            "session_name": session_name,
            "messages": [],
            "ai_config": {"model": "gpt-4", "max_tokens": 1024, "response_time": "fast"},
            "created_at": datetime.now().isoformat()
        }

        try:
            with open(CHAT_HISTORY_FILE, "r", encoding="utf-8") as file:
                chat_sessions = json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            chat_sessions = []

        chat_sessions.insert(0, new_session) #Add session to chat_session

        with open(CHAT_HISTORY_FILE, "w", encoding="utf-8") as file:
            json.dump(chat_sessions, file, ensure_ascii=False, indent=4) #Save

        # Cập nhật danh sách hiển thị
        self.history_list.clear()
        self.load_chat_history()
        # Clear chat display and input field
        self.chat_display.clear()
        self.input_field.clear()

    def adjust_input_height(self):
        document_height = self.input_field.document().size().height()
        new_height = min(100, max(styles.INPUT_FIELD_HEIGHT, int(document_height + 10)))
        self.input_field.setFixedHeight(new_height)

    def update_toggle_state(self, state):
        self.is_toggle_on = state

    def send_message(self):
        user_message = self.input_field.toPlainText().strip()
        if not user_message:
            return

        message_id = f"msg_{uuid.uuid4().hex[:6]}"

        user_item = QListWidgetItem()
        user_widget = ChatItem(message_id, user_message, sender="user")
        user_item.setSizeHint(user_widget.sizeHint())

        self.chat_display.addItem(user_item)
        self.chat_display.setItemWidget(user_item, user_widget)
        self.input_field.clear()
        
        try:
            if self.is_toggle_on:
                # GPT
                print("gpt")
                # response = client.chat.completions.create(
                #     model="gpt-4",
                #     messages=[{"role": "user", "content": user_message}]
                # )
                # bot_reply = response.choices[0].message.content.strip()
            else:
                # Gemini
                print("gemini")
                # chat = model.start_chat(history=[])

                # response = chat.send_message(user_message)
                # bot_reply = response.text
        except Exception as e:
            bot_reply = f"Lỗi: {str(e)}"

        bot_reply = "Xin chào! Tôi là OpenAI ChatGPT."
        bot_item = QListWidgetItem()
        bot_widget = ChatItem(message_id, bot_reply, sender="AI")
        bot_item.setSizeHint(bot_widget.sizeHint())

        self.chat_display.addItem(bot_item)
        self.chat_display.setItemWidget(bot_item, bot_widget)

        self.chat_display.scrollToBottom()
        self.save_chat_history(message_id, user_message, bot_reply)

    def save_chat_history(self, message_id, user_message, bot_reply):
        try:
            with open(CHAT_HISTORY_FILE, "r", encoding="utf-8") as file:
                chat_sessions = json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            chat_sessions = []

        if not chat_sessions:
            session = {
                "session_id": str(uuid.uuid4()),
                "session_name": f"chat_{datetime.now().strftime('%Y%m%d_%H%M')}",
                "messages": [],
                "ai_config": {"model": "gpt-4", "max_tokens": 1024, "response_time": "fast"},
                "created_at": datetime.now().isoformat()
            }
            chat_sessions.append(session)
        else:
            session = chat_sessions[0]

        session["messages"].append({
            "message_id": message_id,
            "sender": "user",
            "content": user_message,
            "timestamp": datetime.now().isoformat()
        })
        session["messages"].append({
            "message_id": message_id,
            "sender": "AI",
            "content": bot_reply,
            "timestamp": datetime.now().isoformat()
        })

        with open(CHAT_HISTORY_FILE, "w", encoding="utf-8") as file:
            json.dump(chat_sessions, file, ensure_ascii=False, indent=4)

    def add_selected_message(self, message):
        if message not in self.selected_messages_data:
            self.selected_messages_data.append(message)

            index = self.selected_messages.count() + 1  
            display_text = f"{index}. {message}"  

            max_width = self.selected_messages.width() - 40 
            self.selected_messages.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

            metrics = QFontMetrics(self.selected_messages.font())
            elided_text = metrics.elidedText(display_text, Qt.ElideRight, max_width)  
            
            item = QListWidgetItem(elided_text)
            item.setToolTip(display_text) 

            item.setSizeHint(QSize(max_width, 30))
            self.selected_messages.addItem(item)

    def clear_list_messages(self):
        print("xóa")

    def export_list_messages(self):
        print("Export")


