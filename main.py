import sys
from PyQt5.QtWidgets import QApplication
from views.gui import ChatApp

if __name__ == "__main__":
    app = QApplication(sys.argv)  # Khởi tạo QApplication ở đây
    window = ChatApp(app)  # Truyền đối tượng app vào ChatApp
    window.show()
    sys.exit(app.exec_())