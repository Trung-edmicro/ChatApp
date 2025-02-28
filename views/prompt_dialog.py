# views/prompt_dialog.py
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QTextEdit, QPushButton, QListWidget, QListWidgetItem, QSizePolicy, QWidget, QMessageBox
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QCursor
from views import styles
from internal.db.connection import get_db
from controllers.controllers import *

class PromptDialog(QDialog):
    prompt_selected_signal = pyqtSignal(str) # Signal phát ra khi prompt được chọn

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Quản lý Prompts")
        self.setModal(True) # Đặt dialog là modal (chặn tương tác với cửa sổ chính)
        self.setFixedWidth(700) # Kích thước dialog
        self.setFixedHeight(500)
        self.setStyleSheet("background-color: #212121; color: white;")

        self.initUI()
        self.load_prompts_from_db() # Load danh sách prompts khi dialog khởi tạo

    def initUI(self):
        self.main_layout = QVBoxLayout(self)

        # === Layout Danh sách Prompts (bên trái) ===
        self.prompts_list_layout = QVBoxLayout()

        # Label "Danh sách Prompts"
        self.prompts_label = QLabel("Danh sách Prompts")
        self.prompts_label.setStyleSheet("color: white; font-size: 14px; font-weight: bold; padding-bottom: 6px;")
        self.prompts_list_layout.addWidget(self.prompts_label)

        # QListWidget hiển thị danh sách prompts
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
        self.prompts_list_widget.itemClicked.connect(self.prompt_item_clicked) # Kết nối signal itemClicked
        self.prompts_list_layout.addWidget(self.prompts_list_widget)

        # Nút "Tạo Prompt mới"
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
        self.create_prompt_button.clicked.connect(self.create_prompt) # Kết nối signal clicked
        self.prompts_list_layout.addWidget(self.create_prompt_button)


        # === Layout Chi tiết Prompt (bên phải) ===
        self.prompt_detail_layout = QVBoxLayout()

        # Label "Chi tiết Prompt"
        self.detail_label = QLabel("Chi tiết Prompt")
        self.detail_label.setStyleSheet("color: white; font-size: 14px; font-weight: bold; padding-bottom: 6px;")
        self.prompt_detail_layout.addWidget(self.detail_label)

        # Input Name
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

        # Text Editor Content
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

        # Layout Nút "Lưu" và "Hủy"
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
        self.save_button.clicked.connect(self.save_prompt) # Kết nối signal clicked
        self.buttons_layout.addWidget(self.save_button)

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
        self.cancel_button.clicked.connect(self.reject) # reject() là hàm built-in của QDialog để đóng dialog và trả về QDialog.Rejected
        self.buttons_layout.addWidget(self.cancel_button)

        self.prompt_detail_layout.addLayout(self.buttons_layout)

        # === Layout Chính (chia dialog thành 2 cột) ===
        split_layout = QHBoxLayout()
        split_layout.addLayout(self.prompts_list_layout) # Cột bên trái (danh sách prompts)
        split_layout.addLayout(self.prompt_detail_layout) # Cột bên phải (chi tiết prompt)

        self.main_layout.addLayout(split_layout) # Thêm split_layout vào main_layout

    def load_prompts_from_db(self):
        """Load danh sách prompts từ database và hiển thị trong QListWidget."""
        self.prompts_list_widget.clear() # Clear list widget trước khi load
        db = next(get_db())
        prompts = get_all_prompts_json(db) # Gọi controller để lấy danh sách prompts JSON
        db.close()

        if prompts:
            for prompt_data in prompts:
                item = QListWidgetItem(prompt_data['name']) # Hiển thị tên prompt trong list
                item.setData(Qt.UserRole, prompt_data) # Lưu trữ toàn bộ prompt data vào item data
                self.prompts_list_widget.addItem(item)

    def prompt_item_clicked(self, item):
        """Xử lý khi một prompt item được click trong QListWidget."""
        prompt_data = item.data(Qt.UserRole) # Lấy prompt data từ item data
        if prompt_data:
            self.name_input.setText(prompt_data['name']) # Set tên prompt vào input name
            self.content_input.setText(prompt_data['content']) # Set nội dung prompt vào input content
        else:
            self.clear_prompt_detail() # Clear input nếu không có data

    def clear_prompt_detail(self):
        """Xóa nội dung input chi tiết prompt."""
        self.name_input.clear()
        self.content_input.clear()

    def create_prompt(self):
        """Xử lý logic tạo prompt mới."""
        self.clear_prompt_detail() # Xóa input detail trước khi tạo mới
        self.prompts_list_widget.clearSelection() # Bỏ chọn item hiện tại trong list

    def save_prompt(self):
        """Xử lý logic lưu prompt (tạo mới hoặc cập nhật)."""
        db = next(get_db())
        prompt_id = None # Cho trường hợp tạo mới
        current_item = self.prompts_list_widget.currentItem() # Lấy item hiện tại trong list
        if current_item: # Nếu có item được chọn, có thể là update
            prompt_data = current_item.data(Qt.UserRole)
            if prompt_data:
                prompt_id = prompt_data['prompt_id'] # Lấy prompt_id để update

        name = self.name_input.text().strip() # Lấy tên prompt từ input
        content = self.content_input.toPlainText().strip() # Lấy nội dung prompt từ input

        if not name or not content: # Validate input (tên và nội dung không được trống)
            QMessageBox.warning(self, "Lỗi", "Vui lòng nhập đầy đủ Tên Prompt và Nội dung Prompt.")
            return

        if prompt_id:
            # === Update prompt ===
            updated_prompt = self.update_prompt_controller(db, prompt_id, name, content) # Gọi controller update
            if updated_prompt:
                print(f"Prompt ID {prompt_id} đã được cập nhật.") # Log update
            else:
                print(f"Lỗi khi cập nhật Prompt ID {prompt_id}.") # Log lỗi update
        else:
            # === Create new prompt ===
            new_prompt = create_prompt_controller(db, name, content) # Gọi controller create
            if new_prompt:
                print(f"Prompt mới '{new_prompt.name}' đã được tạo (ID: {new_prompt.prompt_id}).") # Log create

        db.close()
        self.load_prompts_from_db() # Load lại danh sách prompts để cập nhật GUI
        self.clear_prompt_detail() # Xóa input detail sau khi lưu
        self.prompts_list_widget.clearSelection() # Bỏ select item sau khi lưu

    def reject(self):
        """Xử lý sự kiện nút "Hủy" (đóng dialog)."""
        self.clear_prompt_detail() # Clear input detail khi hủy
        super().reject() # Gọi reject() của QDialog để đóng dialog và trả về QDialog.Rejected

    def accept(self):
        """Xử lý sự kiện nút "Chọn Prompt" (nếu có nút này)."""
        current_item = self.prompts_list_widget.currentItem() # Lấy item hiện tại được chọn
        if current_item:
            prompt_data = current_item.data(Qt.UserRole) # Lấy prompt data từ item data
            if prompt_data:
                selected_prompt_content = prompt_data['content'] # Lấy content prompt đã chọn
                self.prompt_selected_signal.emit(selected_prompt_content) # Phát tín hiệu prompt_selected_signal và truyền content
                super().accept() # Chấp nhận dialog và trả về QDialog.Accepted
            else:
                QMessageBox.warning(self, "Lỗi", "Không có dữ liệu prompt được chọn.") # Log lỗi nếu không có data
        else:
            QMessageBox.warning(self, "Lỗi", "Vui lòng chọn một prompt từ danh sách.") # Log lỗi nếu chưa chọn prompt