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
    QScrollBar:vertical {
        border: none;
        background: transparent;
        width: 8px;
        margin: 4px 0;
    }
    QScrollBar::handle:vertical {
        background: #555;
        min-height: 30px;
        border-radius: 4px;
    }
    QScrollBar::handle:vertical:hover {
        background: #777;
    }
    QScrollBar::add-line:vertical, 
    QScrollBar::sub-line:vertical {
        background: none;
    }

    QScrollBar:horizontal {
        border: none;
        background: transparent;
        height: 8px;
        margin: 0 4px;
    }
    QScrollBar::handle:horizontal {
        background: #555;
        min-width: 30px;
        border-radius: 4px;
    }
    QScrollBar::handle:horizontal:hover {
        background: #777;
    }
    QScrollBar::add-line:horizontal, 
    QScrollBar::sub-line:horizontal {
        background: none;
    }
"""
