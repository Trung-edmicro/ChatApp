import re
import markdown2

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

# Chuyển Markdown thành HTML có hỗ trợ MathJax
def format_message(message):
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <script>
            window.MathJax = {{
                tex: {{
                    inlineMath: [['$', '$'], ['\\(', '\\)']]
                }},
                svg: {{
                    fontCache: 'global'
                }}
            }};
        </script>
        <script type="text/javascript" async
            src="https://polyfill.io/v3/polyfill.min.js?features=es6">
        </script>
        <script type="text/javascript" async
            src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js">
        </script>
        <style>
            body {{
                font-size: 17px;
                color: white;
                background-color: #2E2E2E;
            }}
            ::-webkit-scrollbar {{
                width: 10px; /* Độ rộng thanh cuộn */
                height: 10px;
            }}
            ::-webkit-scrollbar-track {{
                background: #2E2E2E;
                border-radius: 10px;
            }}
            ::-webkit-scrollbar-thumb {{
                background: #555;
                border-radius: 10px;
                transition: background 0.3s;
            }}
            ::-webkit-scrollbar-thumb:hover {{
                background: #888;
            }}
            .chat-container {{
                display: flex;
                flex-direction: column;
                align-items: flex-start;
                margin-bottom: 10px;
                max-width: 100%;
            }}
            .ai-message {{
                max-width: 100%;
                border-radius: 12px;
                text-align: left;
            }}
        </style>
    </head>
    <body>
        <div class="chat-container">
            <div class="ai-message">
                {markdown2.markdown(message, extras=["fenced-code-blocks", "tables", "strike", "mathjax"])}
            </div>
        </div>
        <script>
            MathJax.typesetPromise();
        </script>
    </body>
    </html>
    """
    return html_content