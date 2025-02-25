import subprocess

def export_to_docx(selected_messages_data, output_filename="selected_messages.docx"):
    if not selected_messages_data:
        print("Danh sách trống, không có gì để xuất.")
        return False

    # Định dạng nội dung theo thứ tự index
    md_content = "\n\n".join([f"**Câu {i+1}.** {msg["content"]}" for i, msg in enumerate(selected_messages_data)])

    # Tạo file Markdown tạm thời
    md_filename = "selected_messages.md"

    with open(md_filename, "w", encoding="utf-8") as file:
        file.write(md_content)

    # Gọi Pandoc để chuyển đổi sang .docx
    try:
        subprocess.run(["pandoc", md_filename, "--from=markdown+tex_math_dollars", "-o", output_filename], check=True)
        print(f"Đã xuất file {output_filename}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Lỗi khi xuất file: {e}")
        return False