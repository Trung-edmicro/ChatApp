# Style
BACKGROUND_COLOR_CHAT = "#212121"
BACKGROUND_COLOR_INPUT = "#303030"
TEXT_COLOR = "white"
BORDER_RADIUS = "10px"
INPUT_FIELD_HEIGHT = 40
SEND_BUTTON_SIZE = 40
SEND_BUTTON_COLOR = "#FFFFFF"
FONT_SIZE = "13px"

HISTORY_LIST_WIDTH = 250

HISTORY_BACKGROUND_COLOR = "#171717"
HISTORY_ITEM_BACKGROUND = "#171717" 
HISTORY_ITEM_HOVER_BACKGROUND = "#2f2f2f"  
HISTORY_TEXT_COLOR = "white"
HISTORY_ITEM_PADDING = "8px" 

NEW_SESSION_BUTTON_COLOR = "#2f2f2f"
NEW_SESSION_BUTTON_HOVER_COLOR = "#545454"

SCROLLBAR_STYLES = """
    /* Style cho thanh cuộn dọc */
    QScrollBar:vertical {
        border: none;
        background: #2C2C2C;
        width: 8px;
        margin: 2px 0 2px 0;
        border-radius: 4px;
    }
    
    /* Style cho phần trượt (handle) */
    QScrollBar::handle:vertical {
        background: #5A5A5A;
        min-height: 20px;
        border-radius: 4px;
    }
    
    /* Hiệu ứng khi hover vào thanh trượt */
    QScrollBar::handle:vertical:hover {
        background: #777;
    }
    
    /* Style cho phần trên/dưới của thanh cuộn */
    QScrollBar::sub-line:vertical, 
    QScrollBar::add-line:vertical {
        background: none;
        height: 0px;
    }
    
    /* Ẩn phần trên/dưới khi không cần */
    QScrollBar::sub-line:vertical:pressed, 
    QScrollBar::add-line:vertical:pressed {
        background: none;
    }
    
    /* Style cho thanh cuộn ngang (nếu có) */
    QScrollBar:horizontal {
        border: none;
        background: #2C2C2C;
        height: 8px;
        margin: 0 2px 0 2px;
        border-radius: 4px;
    }
    
    /* Style cho phần trượt ngang */
    QScrollBar::handle:horizontal {
        background: #5A5A5A;
        min-width: 20px;
        border-radius: 4px;
    }
    
    /* Hiệu ứng hover */
    QScrollBar::handle:horizontal:hover {
        background: #777;
    }
    
    /* Ẩn nút mũi tên (nếu có) */
    QScrollBar::add-page:vertical, 
    QScrollBar::sub-page:vertical, 
    QScrollBar::add-page:horizontal, 
    QScrollBar::sub-page:horizontal {
        background: none;
    }
"""
