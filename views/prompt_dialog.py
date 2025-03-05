# views/prompt_dialog.py
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QTextEdit, QPushButton, QListWidget, QListWidgetItem, QSizePolicy, QWidget, QMessageBox
from PyQt5.QtCore import Qt, pyqtSignal, QSize
from PyQt5.QtGui import QFont, QCursor, QIcon
from views import styles
from internal.db.connection import get_db
from controllers.controllers import *
from views.utils.helpers import show_toast

class PromptDialog(QDialog):
    prompt_selected_signal = pyqtSignal(str, str) # Signal phát ra khi prompt được chọn, truyền cả content và name

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Quản lý Prompts")
        self.setModal(True)
        self.setFixedWidth(1024)
        self.setFixedHeight(768)
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
        self.prompts_list_widget.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.prompts_list_widget.itemClicked.connect(self.prompt_item_clicked)
        self.prompts_list_widget.itemDoubleClicked.connect(self.accept) # Double click chọn prompt
        self.prompts_list_layout.addWidget(self.prompts_list_widget)

        self.create_prompt_button = QPushButton("Tạo Prompt mới")
        self.create_prompt_button.setStyleSheet(f"""
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

        # === Nút XÓA ===
        self.delete_button_ui = QPushButton("Xóa") # Đổi tên biến để phân biệt với nút xóa trong item cũ
        self.delete_button_ui.setStyleSheet("""
            QPushButton {
                background-color: #00a67d;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px;
            }
            QPushButton:hover {
                background-color: #019d76;
            }
        """)
        print(f"Stylesheet nút Xóa: {self.delete_button_ui.styleSheet()}") # <---- THÊM DÒNG NÀY
        self.delete_button_ui.setCursor(QCursor(Qt.PointingHandCursor))
        self.delete_button_ui.clicked.connect(self.delete_prompt_button_clicked) # Kết nối signal clicked với hàm mới
        self.delete_button_ui.setEnabled(False) # **Ban đầu disable nút Xóa**
        self.buttons_layout.addWidget(self.delete_button_ui)
        # === END Nút XÓA ===

        self.prompt_detail_layout.addLayout(self.buttons_layout)

        # === Layout Chính (chia dialog thành 2 cột) ===
        split_layout = QHBoxLayout()
        split_layout.addLayout(self.prompts_list_layout)
        split_layout.addLayout(self.prompt_detail_layout)

        # Thiết lập stretch factors
        split_layout.setStretch(0, 1)  # prompts_list_layout (cột trái) có stretch factor là 1
        split_layout.setStretch(1, 2)  # prompt_detail_layout (cột phải) có stretch factor là 3

        self.main_layout.addLayout(split_layout)

    def load_prompts_from_db(self):
        self.prompts_list_widget.clear()
        db = next(get_db())
        prompts = get_all_prompts_json(db)
        db.close()

        if prompts:
            for prompt_data in prompts:
                item = QListWidgetItem()
                item.setSizeHint(QSize(self.prompts_list_widget.width(), 40)) # Đặt chiều cao item

                # === Tạo WIDGET TÙY CHỈNH cho item ===
                widget = QWidget()
                widget.setStyleSheet("""
                    background-color: transparent;
                """)
                layout = QHBoxLayout()
                layout.setContentsMargins(5, 2, 5, 2) # Thêm margins cho đẹp
                layout.setSpacing(5)

                # Label hiển thị tên prompt
                full_text = prompt_data['name'] # Lấy tên đầy đủ
                max_length = 20 # Độ dài tối đa trước khi cắt
                if len(full_text) > max_length:
                    truncated_text = full_text[:max_length] + "..." # Cắt ngắn và thêm "..."
                    label = QLabel(truncated_text) # Hiển thị tên đã cắt ngắn
                    label.setToolTip(full_text) # Set tooltip là tên đầy đủ (hiện khi hover chuột)
                else:
                    label = QLabel(full_text) # Hiển thị tên đầy đủ
                label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
                label.setStyleSheet("""color: white;""")
                layout.addWidget(label)

                widget.setLayout(layout)
                # === END WIDGET TÙY CHỈNH ===

                item.setData(Qt.UserRole, prompt_data)
                self.prompts_list_widget.addItem(item)
                self.prompts_list_widget.setItemWidget(item, widget)

    def prompt_item_clicked(self, item):
        prompt_data = item.data(Qt.UserRole)
        if prompt_data and prompt_data != "dummy": # Thêm check không phải "dummy"
            self.name_input.setText(prompt_data['name'])
            self.content_input.setText(prompt_data['content'])
            self.selected_prompt_data = prompt_data
            self.delete_button_ui.setEnabled(True) # **Enable nút "Xóa" khi chọn item**
            self.name_input.setEnabled(True) # **Enable khi chọn prompt**
            self.content_input.setEnabled(True) # **Enable khi chọn prompt**

            # === Đổi nút "Hủy" trở lại thành nút "Xóa" ===
            self.delete_button_ui.setText("Xóa") # Đổi text thành "Xóa"
            self.delete_button_ui.disconnect() # Ngắt kết nối signal "Hủy" (nếu có)
            self.delete_button_ui.clicked.connect(self.delete_prompt_button_clicked) # Kết nối lại với hàm "Xóa"

        else:
            self.clear_prompt_detail()
            self.selected_prompt_data = None
            self.delete_button_ui.setEnabled(False) # **Disable nút "Xóa" nếu không có item nào được chọn**
            self.name_input.setEnabled(False) # **Disable khi không chọn prompt**
            self.content_input.setEnabled(False) # **Disable khi không chọn prompt**
            # === Đảm bảo nút là "Xóa" khi không chọn prompt ===
            self.delete_button_ui.setText("Xóa") # Đảm bảo text là "Xóa"
            self.delete_button_ui.disconnect() # Ngắt kết nối signal "Hủy" (nếu có)
            self.delete_button_ui.clicked.connect(self.delete_prompt_button_clicked) # Kết nối lại với hàm "Xóa"

    def clear_prompt_detail(self):
        self.name_input.clear()
        self.content_input.clear()
        self.selected_prompt_data = None # Reset selected_prompt_data khi clear

    def create_prompt(self):
        self.previous_selected_prompt_data = self.selected_prompt_data # Lưu lại selected_prompt_data
        self.clear_prompt_detail()
        self.prompts_list_widget.clearSelection()
        self.selected_prompt_data = None

        # === Tạo "prompt giả" ở cuối danh sách ===
        dummy_prompt_name = "Tạo prompt mới...." # Tên "prompt giả" như yêu cầu
        dummy_item = QListWidgetItem(dummy_prompt_name)
        dummy_item.setData(Qt.UserRole, "dummy") # Đánh dấu là "dummy"
        self.prompts_list_widget.addItem(dummy_item) # **Thêm xuống cuối danh sách**
        self.prompts_list_widget.setCurrentItem(dummy_item) # Chọn item "dummy"
        self.name_input.setFocus() # Focus vào ô tên prompt để nhập liệu

        # === Disable/Enable các UI elements ===
        self.create_prompt_button.setEnabled(False) # Disable nút "Tạo Prompt mới"
        self.delete_button_ui.setEnabled(False) # Disable nút "Xóa"
        self.select_prompt_button.setEnabled(False) # Disable nút "Chọn Prompt"
        self.prompts_list_widget.setEnabled(False) # Disable danh sách prompts

        # Enable các input fields và nút Lưu
        self.name_input.setEnabled(True)
        self.content_input.setEnabled(True)
        self.save_button.setEnabled(True) # Enable nút "Lưu"

        # === Thay đổi nút "Xóa" thành nút "Hủy" ===
        self.delete_button_ui.setText("Hủy") # Đổi text thành "Hủy"
        self.delete_button_ui.disconnect() # Ngắt kết nối signal cũ (nếu có, để chắc chắn)
        self.delete_button_ui.setEnabled(True)
        self.delete_button_ui.clicked.connect(self.cancel_create_prompt_button_clicked) # Kết nối với hàm "Hủy tạo prompt"

    def save_prompt(self):
        db = next(get_db())
        prompt_id = None
        current_item = self.prompts_list_widget.currentItem()
        if current_item:
            prompt_data = current_item.data(Qt.UserRole)
            # Kiểm tra xem prompt_data có phải là dictionary trước khi truy cập 'prompt_id'
            if isinstance(prompt_data, dict):
                if prompt_data:
                    prompt_id = prompt_data['prompt_id']

        name = self.name_input.text().strip()
        content = self.content_input.toPlainText().strip()

        if not name or not content:
            QMessageBox.warning(self, "Lỗi", "Vui lòng nhập đầy đủ Tên Prompt và Nội dung Prompt.")
            return

        if prompt_id: # Trường hợp CẬP NHẬT prompt
            updated_prompt = update_prompt_controller(db, prompt_id, name, content)
            if updated_prompt:
                print(f"Prompt ID {prompt_id} đã được cập nhật.")
                show_toast(self, f"Prompt '{name}' đã được cập nhật thành công!", "success") # Toast thành công
                prompt_to_select_id = prompt_id # Lưu prompt_id để chọn lại sau khi load
            else:
                print(f"Lỗi khi cập nhật Prompt ID {prompt_id}.")
                show_toast(self, f"Lỗi cập nhật prompt '{name}'. Vui lòng thử lại!", "error") # Toast lỗi
                prompt_to_select_id = None # Không chọn lại nếu lỗi
        else: # Trường hợp TẠO MỚI prompt
            new_prompt = create_prompt_controller(db, name, content)
            if new_prompt:
                print(f"Prompt mới '{new_prompt.name}' đã được tạo (ID: {new_prompt.prompt_id}).")
                show_toast(self, f"Prompt '{name}' đã được tạo thành công!", "success") # Toast thành công
                prompt_to_select_id = new_prompt.prompt_id # Lưu prompt_id để chọn sau khi load
                # === Re-enable các UI elements sau khi lưu thành công ===
                self.create_prompt_button.setEnabled(True) # Enable nút "Tạo Prompt mới"
                self.delete_button_ui.setEnabled(False) # Disable nút "Xóa" (chỉ enable khi chọn prompt)
                self.select_prompt_button.setEnabled(True) # Enable nút "Chọn Prompt"
                self.prompts_list_widget.setEnabled(True) # Enable danh sách prompts

            else:
                print(f"Lỗi khi tạo prompt mới.")
                show_toast(self, f"Lỗi tạo prompt '{name}'. Vui lòng thử lại!", "error") # Toast lỗi
                prompt_to_select_id = None # Không chọn lại nếu lỗi
        db.close()
        self.load_prompts_from_db()
        # === Select prompt sau khi lưu (tạo mới hoặc cập nhật) ===
        if prompt_to_select_id: # Kiểm tra nếu có prompt_id để chọn
            for i in range(self.prompts_list_widget.count()):
                item = self.prompts_list_widget.item(i)
                item_data = item.data(Qt.UserRole)
                if isinstance(item_data, dict) and item_data.get('prompt_id') == prompt_to_select_id:
                    self.prompts_list_widget.setCurrentItem(item) # Chọn item
                    break # Thoát vòng lặp sau khi tìm thấy và chọn
            self.delete_button_ui.setText("Xóa") # Đổi text trở lại thành "Xóa"
            self.delete_button_ui.disconnect() # Ngắt kết nối signal "Hủy"
            self.delete_button_ui.setEnabled(True) # Enable nút "Xóa"
            self.delete_button_ui.clicked.connect(self.delete_prompt_button_clicked) # Kết nối lại với hàm "Xóa"       

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

    def delete_prompt_button_clicked(self):
        """Xử lý sự kiện click nút "Xóa" (nút UI, không phải nút trong item)."""
        if not self.selected_prompt_data: # Kiểm tra xem có prompt nào đang được chọn không
            QMessageBox.warning(self, "Lỗi", "Vui lòng chọn một prompt từ danh sách trước khi xóa.")
            return

        prompt_id = self.selected_prompt_data['prompt_id']
        prompt_name = self.selected_prompt_data['name']

        reply = QMessageBox.question(
            self,
            'Xác nhận xóa Prompt',
            f"Bạn có chắc chắn muốn xóa prompt '{prompt_name}' không?\nHành động này không thể hoàn tác!",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            db = next(get_db())
            deleted = delete_prompt_controller(db, prompt_id)
            db.close()

            if deleted:
                print(f"Prompt ID {prompt_id} ('{prompt_name}') đã được xóa.")
                show_toast(self, f"Prompt '{prompt_name}' đã được xóa thành công!", "success") # Toast thành
                self.load_prompts_from_db() # Tải lại danh sách prompts
                self.clear_prompt_detail() # Clear form chi tiết
                self.selected_prompt_data = None # Reset selected_prompt_data
                self.prompts_list_widget.clearSelection() # Bỏ chọn item
                self.delete_button_ui.setEnabled(False) # **Disable nút Xóa sau khi xóa thành công**
            else:
                print(f"Lỗi khi xóa Prompt ID {prompt_id} ('{prompt_name}').")
                show_toast(self, f"Lỗi xóa prompt '{prompt_name}'. Vui lòng thử lại!", "error") # Toast lỗi
        else:
            print(f"Hủy xóa prompt '{prompt_name}'.")

    def cancel_create_prompt_button_clicked(self):
        """Xử lý sự kiện click nút "Hủy" (khi tạo prompt mới)."""
        # === Xóa "prompt giả" nếu có (tìm từ cuối danh sách) ===
        for i in range(self.prompts_list_widget.count() - 1, -1, -1): # Duyệt từ cuối danh sách lên đầu
            item = self.prompts_list_widget.item(i)
            if item and item.data(Qt.UserRole) == "dummy":
                self.prompts_list_widget.takeItem(i) # Xóa item "dummy"
                break # Dừng lại sau khi xóa "dummy" item đầu tiên tìm thấy từ cuối

        # === Khôi phục prompt đã chọn trước đó (nếu có) ===
        if self.previous_selected_prompt_data: # Kiểm tra nếu có prompt đã chọn trước đó
            self.selected_prompt_data = self.previous_selected_prompt_data # Khôi phục selected_prompt_data
            prompt_name = self.selected_prompt_data['name']
            prompt_content = self.selected_prompt_data['content']
            self.name_input.setText(prompt_name) # Set lại tên vào input
            self.content_input.setText(prompt_content) # Set lại nội dung vào input

            # Tìm và chọn lại item trong list
            prompt_to_select_id = self.selected_prompt_data['prompt_id']
            for i in range(self.prompts_list_widget.count()):
                item = self.prompts_list_widget.item(i)
                item_data = item.data(Qt.UserRole)
                if isinstance(item_data, dict) and item_data.get('prompt_id') == prompt_to_select_id:
                    self.prompts_list_widget.setCurrentItem(item) # Chọn item
                    break # Thoát vòng lặp sau khi tìm thấy và chọn
        else: # Nếu không có prompt nào được chọn trước đó, clear form
            self.clear_prompt_detail()

        # === Re-enable các UI elements ===
        self.create_prompt_button.setEnabled(True) # Enable nút "Tạo Prompt mới"
        self.select_prompt_button.setEnabled(True) # Enable nút "Chọn Prompt"
        self.prompts_list_widget.setEnabled(True) # Enable danh sách prompts

        # Disable input fields
        self.name_input.setEnabled(False)
        self.content_input.setEnabled(False)

        # === Đổi nút "Hủy" trở lại thành nút "Xóa" ===
        self.delete_button_ui.setText("Xóa") # Đổi text trở lại thành "Xóa"
        self.delete_button_ui.disconnect() # Ngắt kết nối signal "Hủy"
        self.delete_button_ui.clicked.connect(self.delete_prompt_button_clicked) # Kết nối lại với hàm "Xóa"
        if self.previous_selected_prompt_data:
            self.delete_button_ui.setEnabled(True) # Enable nút "Xóa" sau khi đã chọn prompt
        else:    
            self.delete_button_ui.setEnabled(False) # Disable nút "Xóa" (vì không có prompt nào được chọn)
        self.previous_selected_prompt_data = None # Reset previous_selected_prompt_data sau khi dùng    