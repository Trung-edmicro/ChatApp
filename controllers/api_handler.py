import google.generativeai as genai
from views.utils.helpers import show_toast  # Import show_toast nếu bạn cần dùng ở đây
from PIL import Image # Import Pillow
import docx # Import docx
import PyPDF2 # Import PyPDF2
import base64
import os

def encode_image(image_path):
    """Chuyển đổi ảnh thành chuỗi base64, hỗ trợ nhiều định dạng."""
    try:
        with open(image_path, "rb") as image_file:
            image_data = image_file.read()
            base64_encoded = base64.b64encode(image_data).decode('utf-8')

        # Xác định MIME type dựa trên phần mở rộng của file
        file_extension = os.path.splitext(image_path)[1].lower()
        if file_extension == ".png":
            mime_type = "image/png"
        elif file_extension == ".jpg" or file_extension == ".jpeg":
            mime_type = "image/jpeg"
        elif file_extension == ".gif":
            mime_type = "image/gif"
        elif file_extension == ".bmp":
            mime_type = "image/bmp"
        elif file_extension == ".webp":
            mime_type = "image/webp"
        else:
            raise ValueError(f"Không hỗ trợ định dạng ảnh: {file_extension}")

        return f"data:{mime_type};base64,{base64_encoded}"
    except Exception as e:
        raise Exception(f"Lỗi encode ảnh {image_path}: {e}")


def call_ai_api(user_message_text, is_toggle_on, gemini_chat, openai_client, history=None, image_files=None, document_files=None, parent_widget=None): # Thêm tham số history
    """
    Gọi AI API (OpenAI hoặc Gemini) dựa trên toggle state, hỗ trợ file ảnh và tài liệu cho Gemini (phiên bản dùng biến history trong api_handler).

    """
    bot_reply_text = ""
    ai_sender = "system"
    current_history = history if history is not None else [] # Sử dụng history truyền vào hoặc khởi tạo list rỗng

    try:
        prompt_template = f"""Bạn là một Giáo viên thông minh. Hãy phân tích nội dung sau một cách chi tiết và rõ ràng:
        {user_message_text}
        Kết quả trả về phải bao gồm quy chuẩn bắt buộc sau (đừng trả về các yêu cầu này trong phần trả về):
        - Luôn tách biệt nội dung và công thức toán cách nhau 1 dòng.
        - Các công thức phải trả về mã Latex với điều kiện:
            + Sử dụng $...$ để bọc các công thức thay vì sử dụng \\[...\\] hay \\(...\\), không sử dụng \boxed trong công thức.
            + Không được sử dụng \frac, thay vào đó sử dụng \\dfrac
        """

        if is_toggle_on: # Toggle ON: OpenAI/ChatGPT
            print("Gọi OpenAI/ChatGPT API từ api_handler.py (hỗ trợ file)") # Cập nhật log message
            messages = [{"role": "user", "content": prompt_template}]

            # Xử lý file ảnh
            if image_files:
                for image_file in image_files:
                    try:
                        base64_image_url = encode_image(image_file.filepath)
                        messages.append({
                            "role": "user",
                            "content": [
                                {"type": "text", "text": "Phân tích bức ảnh sau:"},
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": base64_image_url
                                    }
                                },
                            ]
                        })
                    except FileNotFoundError:
                        print(f"Lỗi: Không tìm thấy file ảnh: {image_file}")
                        continue
                    except ValueError as e:
                        print(f"Lỗi định dạng ảnh {image_file}: {e}")
                        continue
                    except Exception as e:
                        print(f"Lỗi đọc file ảnh {image_file}: {e}")
                        continue

            # Xử lý file tài liệu (đọc nội dung và thêm vào prompt)
            if document_files:
                for doc_file in document_files:
                    doc_text = ""
                    try:
                        if doc_file.filepath.lower().endswith(".docx"):
                            doc = docx.Document(doc_file.filepath)
                            for paragraph in doc.paragraphs:
                                doc_text += paragraph.text + "\n"
                        elif doc_file.filepath.lower().endswith(".pdf"):
                            pdf_file = open(doc_file.filepath, 'rb')
                            pdf_reader = PyPDF2.PdfReader(pdf_file)
                            for page_num in range(len(pdf_reader.pages)):
                                page = pdf_reader.pages[page_num]
                                doc_text += page.extract_text()
                            pdf_file.close()
                        else:
                            print(f"Lỗi: Định dạng file document không được hỗ trợ: {doc_file}. Chỉ hỗ trợ .docx và .pdf")
                            continue

                        messages.append({"role": "user", "content": f"File tài liệu đính kèm:\n{doc_text}"})

                    except FileNotFoundError:
                        print(f"Lỗi: Không tìm thấy file document: {doc_file}")
                        continue
                    except Exception as e:
                        print(f"Lỗi đọc file document {doc_file}: {e}")
                        continue

            openai_response = openai_client.chat.completions.create(
                model="gpt-4.5-preview-2025-02-27", # or gpt-4 if you have access
                messages=messages,
                max_tokens=4096,
            )
            bot_reply_text = openai_response.choices[0].message.content.strip()
            ai_sender = "system"

        else: # Toggle OFF: Gemini
            print("Gọi Gemini API từ api_handler.py (có hỗ trợ file - dùng biến history)") # Cập nhật log message
            contents = [] # Danh sách các thành phần nội dung (text, image, document text)

            # Thêm text prompt
            contents.append(prompt_template) # Thêm trực tiếp text prompt vào contents

            # Thêm image objects nếu có
            if image_files:
                for image_file in image_files:
                    try:
                        image = Image.open(image_file.filepath) # Mở ảnh bằng Pillow
                        contents.append(image) # Thêm trực tiếp object Image vào contents
                        print(f"Đã thêm image file (Pillow): {image_file}") # Log
                    except FileNotFoundError:
                        print(f"Lỗi: Không tìm thấy file ảnh: {image_file}")
                        continue # Tiếp tục vòng lặp nếu không tìm thấy file
                    except Exception as e:
                        print(f"Lỗi đọc file ảnh {image_file} (Pillow): {e}") # Log lỗi
                        continue # Tiếp tục vòng lặp nếu lỗi đọc file

            # Thêm document text nếu có
            if document_files:
                for doc_file in document_files:
                    doc_text = ""
                    try:
                        if doc_file.filepath.lower().endswith(".docx"):
                            doc = docx.Document(doc_file.filepath)
                            for paragraph in doc.paragraphs:
                                doc_text += paragraph.text + "\n" # Đọc text từ từng paragraph trong docx
                        elif doc_file.filepath.lower().endswith(".pdf"):
                            pdf_file = open(doc_file.filepath, 'rb')
                            pdf_reader = PyPDF2.PdfReader(pdf_file)
                            for page_num in range(len(pdf_reader.pages)):
                                page = pdf_reader.pages[page_num]
                                doc_text += page.extract_text() # Đọc text từ từng trang trong pdf
                            pdf_file.close()
                        else:
                            print(f"Lỗi: Định dạng file document không được hỗ trợ: {doc_file}. Chỉ hỗ trợ .docx và .pdf")
                            continue # Tiếp tục vòng lặp nếu định dạng không hỗ trợ

                        contents.append(doc_text) # Thêm trực tiếp text nội dung document vào contents
                        print(f"Đã thêm document file (text extracted): {doc_file}") # Log

                    except FileNotFoundError:
                        print(f"Lỗi: Không tìm thấy file document: {doc_file}")
                        continue # Tiếp tục vòng lặp nếu không tìm thấy file
                    except Exception as e:
                        print(f"Lỗi đọc file document {doc_file}: {e}") # Log lỗi
                        continue # Tiếp tục vòng lặp nếu lỗi đọc file


            if not contents: # Kiểm tra nếu không có content nào (text, image, document)
                print("Lỗi: Không có nội dung nào để gửi đến Gemini API.") # Log
                return None # Trả về None nếu không có nội dung

            gemini_response = gemini_chat.send_message(content=contents) # Gọi generate_content() với danh sách contents và history
            bot_reply_text = gemini_response.text
            ai_sender = "system"
            current_history.extend(gemini_chat.history) # Cập nhật history với response history

    except Exception as e:
        bot_reply_text = f"Lỗi khi gọi AI API: {str(e)}"
        print(f"Lỗi API trong api_handler.py: {bot_reply_text}") # Log lỗi ở server-side
        if parent_widget: # Kiểm tra parent_widget trước khi show_toast
            show_toast(parent_widget, f"{bot_reply_text}", "error") # Show toast trên GUI nếu có parent_widget
        return None # Trả về None để báo hiệu lỗi

    return bot_reply_text, ai_sender, current_history # Trả về history cập nhật # Trả về history cập nhật