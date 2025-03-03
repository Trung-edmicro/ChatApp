# views/prompt_dialog.py
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QTextEdit, QPushButton, QListWidget, QListWidgetItem, QSizePolicy, QWidget, QMessageBox
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QCursor
from views import styles
from internal.db.connection import get_db
from controllers.controllers import *

class PromptDialog(QDialog):
    prompt_selected_signal = pyqtSignal(str, str) # Signal phát ra khi prompt được chọn, truyền cả content và name

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Quản lý Prompts")
        self.setModal(True)
        self.setFixedWidth(700)
        self.setFixedHeight(500)
        self.setStyleSheet("background-color: #212121; color: white;")
        self.selected_prompt_data = None # Thêm biến để lưu prompt data được chọn

        self.initUI()
        self.load_prompts_from_db()

    def initUI(self):
        self.main_layout = QVBoxLayout(self)

        # === Layout Danh sách Prompts (bên trái) ===
        self.prompts_list_layout = QVBoxLayout()
        self.prompts_label = QLabel("Danh sách Prompts")
        self.prompts_label.setStyleSheet("color: white; font-size: 14px; font-weight: bold; padding-bottom: 6px;")
        self.prompts_list_layout.addWidget(self.prompts_label)

        self.prompts_list_widget = QListWidget()
        self.prompts_list_widget.setStyleSheet("""
            QListWidget {
                border: 1px solid #3c91d9;
                border-radius: 5px;
                background-color: #2a2a2a;
                color: white;
                font-size: 14px;
            }
            QListWidget::item {
                padding: 8px;
            }
            QListWidget::item:selected {
                background-color: #3c3c3c;
            }
        """)
        self.prompts_list_widget.itemClicked.connect(self.prompt_item_clicked)
        self.prompts_list_widget.itemDoubleClicked.connect(self.accept) # Double click chọn prompt
        self.prompts_list_layout.addWidget(self.prompts_list_widget)

        self.create_prompt_button = QPushButton("Tạo Prompt mới")
        self.create_prompt_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {styles.SEND_BUTTON_COLOR};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px;
                margin-top: 5px;
            }}
            QPushButton:hover {{
                background-color: {styles.NEW_SESSION_BUTTON_HOVER_COLOR};
            }}
        """)
        self.create_prompt_button.setCursor(QCursor(Qt.PointingHandCursor))
        self.create_prompt_button.clicked.connect(self.create_prompt)
        self.prompts_list_layout.addWidget(self.create_prompt_button)

        # === Layout Chi tiết Prompt (bên phải) ===
        self.prompt_detail_layout = QVBoxLayout()
        self.detail_label = QLabel("Chi tiết Prompt")
        self.detail_label.setStyleSheet("color: white; font-size: 14px; font-weight: bold; padding-bottom: 6px;")
        self.prompt_detail_layout.addWidget(self.detail_label)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Tên Prompt")
        self.name_input.setStyleSheet(f"""
            QLineEdit {{
                border: 1px solid #3c91d9;
                border-radius: 5px;
                padding: 6px;
                background-color: #2a2a2a;
                color: white;
                font-size: 14px;
            }}
        """)
        self.prompt_detail_layout.addWidget(self.name_input)

        self.content_input = QTextEdit()
        self.content_input.setPlaceholderText("Nội dung Prompt")
        self.content_input.setStyleSheet(f"""
            QTextEdit {{
                border: 1px solid #3c91d9;
                border-radius: 5px;
                padding: 6px;
                background-color: #2a2a2a;
                color: white;
                font-size: 14px;
            }}
        """)
        self.prompt_detail_layout.addWidget(self.content_input)

        # === Layout Nút "Lưu", "Chọn Prompt" và "Hủy" ===
        self.buttons_layout = QHBoxLayout()

        self.save_button = QPushButton("Lưu")
        self.save_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {styles.SEND_BUTTON_COLOR};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px;
            }}
            QPushButton:hover {{
                background-color: {styles.NEW_SESSION_BUTTON_HOVER_COLOR};
            }}
        """)
        self.save_button.setCursor(QCursor(Qt.PointingHandCursor))
        self.save_button.clicked.connect(self.save_prompt)
        self.buttons_layout.addWidget(self.save_button)

        self.select_prompt_button = QPushButton("Chọn Prompt") # Nút "Chọn Prompt"
        self.select_prompt_button.setStyleSheet(f"""
            QPushButton {{
                background-color: #00a67d;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px;
            }}
            QPushButton:hover {{
                background-color: #019d76;
            }}
        """)
        self.select_prompt_button.setCursor(QCursor(Qt.PointingHandCursor))
        self.select_prompt_button.clicked.connect(self.accept) # Kết nối với accept()
        self.buttons_layout.addWidget(self.select_prompt_button)


        self.cancel_button = QPushButton("Hủy")
        self.cancel_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {styles.SEND_BUTTON_COLOR};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px;
            }}
            QPushButton:hover {{
                background-color: {styles.NEW_SESSION_BUTTON_HOVER_COLOR};
            }}
        """)
        self.cancel_button.setCursor(QCursor(Qt.PointingHandCursor))
        self.cancel_button.clicked.connect(self.reject)
        self.buttons_layout.addWidget(self.cancel_button)

        self.prompt_detail_layout.addLayout(self.buttons_layout)

        # === Layout Chính (chia dialog thành 2 cột) ===
        split_layout = QHBoxLayout()
        split_layout.addLayout(self.prompts_list_layout)
        split_layout.addLayout(self.prompt_detail_layout)
        self.main_layout.addLayout(split_layout)

    def load_prompts_from_db(self):
        self.prompts_list_widget.clear()
        db = next(get_db())
        prompts = get_all_prompts_json(db)
        db.close()

        if prompts:
            for prompt_data in prompts:
                item = QListWidgetItem(prompt_data['name'])
                item.setData(Qt.UserRole, prompt_data)
                self.prompts_list_widget.addItem(item)

    def prompt_item_clicked(self, item):
        prompt_data = item.data(Qt.UserRole)
        if prompt_data:
            self.name_input.setText(prompt_data['name'])
            self.content_input.setText(prompt_data['content'])
            self.selected_prompt_data = prompt_data # Lưu prompt data khi item được click
        else:
            self.clear_prompt_detail()
            self.selected_prompt_data = None

    def clear_prompt_detail(self):
        self.name_input.clear()
        self.content_input.clear()
        self.selected_prompt_data = None # Reset selected_prompt_data khi clear

    def create_prompt(self):
        self.clear_prompt_detail()
        self.prompts_list_widget.clearSelection()
        self.selected_prompt_data = None # Reset selected_prompt_data khi tạo mới

    def save_prompt(self):
        db = next(get_db())
        prompt_id = None
        current_item = self.prompts_list_widget.currentItem()
        if current_item:
            prompt_data = current_item.data(Qt.UserRole)
            if prompt_data:
                prompt_id = prompt_data['prompt_id']

        name = self.name_input.text().strip()
        content = self.content_input.toPlainText().strip()

        if not name or not content:
            QMessageBox.warning(self, "Lỗi", "Vui lòng nhập đầy đủ Tên Prompt và Nội dung Prompt.")
            return

        if prompt_id:
            updated_prompt = update_prompt_controller(db, prompt_id, name, content)
            if updated_prompt:
                print(f"Prompt ID {prompt_id} đã được cập nhật.")
            else:
                print(f"Lỗi khi cập nhật Prompt ID {prompt_id}.")
        else:
            new_prompt = create_prompt_controller(db, name, content)
            if new_prompt:
                print(f"Prompt mới '{new_prompt.name}' đã được tạo (ID: {new_prompt.prompt_id}).")

        db.close()
        self.load_prompts_from_db()
        self.clear_prompt_detail()
        self.prompts_list_widget.clearSelection()
        self.selected_prompt_data = None # Reset selected_prompt_data sau khi save

    def reject(self):
        self.clear_prompt_detail()
        self.selected_prompt_data = None # Reset selected_prompt_data khi reject
        super().reject()

    def accept(self):
        """Xử lý sự kiện nút "Chọn Prompt" hoặc double-click."""
        if self.selected_prompt_data: # Kiểm tra xem có prompt nào được chọn không
            selected_prompt_content = self.selected_prompt_data['content']
            selected_prompt_name = self.selected_prompt_data['name']
            self.prompt_selected_signal.emit(selected_prompt_content, selected_prompt_name) # Phát tín hiệu với content và name
            super().accept()
        else:
            QMessageBox.warning(self, "Lỗi", "Vui lòng chọn một prompt từ danh sách trước khi chọn.")