import subprocess
import os
import datetime
import platform

def open_directory(path):
    """Mở thư mục trong trình quản lý file mặc định của hệ điều hành."""
    if platform.system() == "Windows":
        os.startfile(path)
    elif platform.system() == "Linux" or platform.system() == "Darwin": # Darwin is macOS
        subprocess.run(["xdg-open", path], check=False)
    else:
        print(f"Không hỗ trợ mở thư mục tự động trên hệ điều hành: {platform.system()}")

def export_to_docx(selected_messages_data):
    """
    Xuất dữ liệu tin nhắn đã chọn ra file Markdown (.md) và Word (.docx)
    trong thư mục 'results', tên file chứa thời gian tạo.

    Args:
        selected_messages_data: Danh sách các tin nhắn đã chọn, mỗi tin nhắn là một dictionary
                                 với khóa 'content' chứa nội dung tin nhắn.

    Returns:
        True nếu xuất file thành công, False nếu có lỗi hoặc danh sách rỗng.
    """
    if not selected_messages_data:
        print("Danh sách trống, không có gì để xuất.")
        return False
    
    # Tạo thư mục 'results' nếu chưa tồn tại
    results_dir = "results"
    os.makedirs(results_dir, exist_ok=True)

    # Tạo timestamp cho tên file
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    base_filename = f"selected_messages_{timestamp}"

    md_filename = os.path.join(results_dir, f"{base_filename}.md")
    docx_filename = os.path.join(results_dir, f"{base_filename}.docx")

    # Định dạng nội dung theo thứ tự index
    md_content = "\n\n".join([f"**Câu {i+1}.** {msg["content"]}" for i, msg in enumerate(selected_messages_data)])

    with open(md_filename, "w", encoding="utf-8") as file:
        file.write(md_content)

    # Gọi Pandoc để chuyển đổi sang .docx
    try:
        subprocess.run(["pandoc", md_filename, "--from=markdown+tex_math_dollars", "-o", docx_filename], check=True)
        print(f"Đã xuất file {docx_filename}")
        open_directory(results_dir)
        os.remove(md_filename)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Lỗi khi xuất file: {e}")
        return False
