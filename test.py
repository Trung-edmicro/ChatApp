import google.generativeai as genai
import json
import os

def chat_gemini_with_history(user_message, history_file="chat_history.json"):
    """
    Gửi tin nhắn đến Gemini API và lưu lại lịch sử chat.

    Args:
        user_message (str): Tin nhắn của người dùng.
        history_file (str, optional): Đường dẫn đến file lưu lịch sử chat.
                                       Mặc định là "chat_history.json".

    Returns:
        str: Phản hồi từ Gemini API.
    """
    # Cấu hình API key (Bạn nên thiết lập biến môi trường GOOGLE_API_KEY thay vì hardcode)
    genai.configure(api_key="AIzaSyAUh7P-Zx7TegzSQ31CkpTEWDZzf9_7kcY")

    # Chọn model Gemini (ở đây dùng 'gemini-pro')
    model = genai.GenerativeModel('gemini-2.0-flash-thinking-exp-01-21')

    history = []
    if os.path.exists(history_file):
        try:
            with open(history_file, 'r') as f:
                history_data = json.load(f)
                # Tải lịch sử từ dữ liệu JSON dictionary (đã là định dạng mong muốn)
                history = history_data # Sử dụng trực tiếp history_data
        except Exception as e:
            print(f"Lỗi khi tải lịch sử chat: {e}")
            history = []

    chat = model.start_chat(history [parts {text: "hello"} role: "user", parts {text: "Hello there! How can I help you today? 😊"} role: "model"]) # Sử dụng history là list các dictionaries

    response = chat.send_message(user_message)

    updated_history_raw = chat.history # Lấy history (có thể vẫn là list các đối tượng Content nội bộ)
    updated_history_to_save = []


    try:
        with open(history_file, 'w') as f:
            json.dump(updated_history_to_save, f, indent=4) # Lưu lịch sử dưới dạng list dictionary JSON
    except Exception as e:
        print(f"Lỗi khi lưu lịch sử chat: {e}")

    return response.text

# --- Ví dụ sử dụng ---
if __name__ == "__main__":
    # Đảm bảo bạn đã thiết lập biến môi trường GOOGLE_API_KEY hoặc thay thế trực tiếp API key vào dòng dưới
    # os.environ["GOOGLE_API_KEY"] = "YOUR_API_KEY" # KHÔNG NÊN HARDCODE API KEY TRỰC TIẾP

    # Lần chat đầu tiên (lịch sử sẽ được tạo mới)
    response1 = chat_gemini_with_history("Xin chào Gemini!")
    print("Gemini (lần 1):", response1)

    # Lần chat thứ hai (lịch sử từ file 'chat_history.json' sẽ được tải và tiếp tục)
    response2 = chat_gemini_with_history("Bạn có nhớ tôi đã nói gì trước đó không?", history_file="chat_history.json")
    print("Gemini (lần 2):", response2)

    # Lần chat thứ ba, tiếp tục sử dụng lịch sử cũ
    response3 = chat_gemini_with_history("Hãy tóm tắt lại cuộc trò chuyện của chúng ta.", history_file="chat_history.json")
    print("Gemini (lần 3):", response3)