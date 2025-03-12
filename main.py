import sys
from PyQt5.QtWidgets import QApplication
from views.gui import ChatApp  # Đảm bảo import đúng đường dẫn
from dotenv import load_dotenv
from PyQt5.QtCore import Qt
import os

load_dotenv()  # Load biến môi trường từ .env

openai_api_key = os.getenv("OPENAI_API_KEY")
gemini_api_key = os.getenv("GEMINI_API_KEY")

if __name__ == "__main__":
    if hasattr(Qt, 'AA_EnableHighDpiScaling'):
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    if hasattr(Qt, 'AA_UseHighDpiPixmaps'):
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    app = QApplication(sys.argv)
    window = ChatApp(app, openai_api_key, gemini_api_key) # Truyền API keys và driver
    window.show()
    sys.exit(app.exec_())