import re

def contains_latex(text):
    # Regex tìm các ký hiệu LaTeX phổ biến
    latex_patterns = [
        r"\$\$(.*?)\$\$",         # Công thức block $$ ... $$
        r"\$(.*?)\$",             # Công thức inline $ ... $
        r"\\\((.*?)\\\)",         # Công thức inline \( ... \)
        r"\\\[(.*?)\\\]",         # Công thức block \[ ... \]
        r"\\frac\{.*?\}\{.*?\}",  # Phân số
        r"\\sqrt\{.*?\}",         # Căn bậc hai
        r"\\sum",                 # Tổng sigma
        r"\\int",                 # Tích phân
        r"\\begin\{align\}"       # Hệ phương trình
    ]
    
    # Kiểm tra nếu có bất kỳ mẫu nào khớp
    for pattern in latex_patterns:
        if re.search(pattern, text, re.DOTALL):
            return True
    return False