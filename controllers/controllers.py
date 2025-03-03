import json
from sqlalchemy.orm import Session
from models import models
from sqlalchemy import func, asc
from datetime import datetime, timezone
import uuid
import json # Đảm bảo import json

# --- Các hàm cho Session ---

def get_all_sessions(db: Session):
    """Lấy danh sách tất cả các sessions, bao gồm cả tin nhắn của mỗi session, trả về cấu trúc JSON."""
    sessions = db.query(models.Session).all()
    session_list = []
    for session in sessions:
        messages_data = []
        for message in session.messages:
            messages_data.append({
                "message_id": message.message_id,
                "sender": message.sender,
                "content": message.content,
                "timestamp": message.timestamp.isoformat() if message.timestamp else None # Format datetime to ISO string
            })

        session_data = {
            "session_id": session.session_id,
            "session_name": session.session_name,
            "messages": messages_data,
            "ai_config": { # Assuming ai_config is static or derived from session, adapt as needed
                "model": session.ai_model,
                "max_tokens": session.ai_max_tokens,
                "response_time": session.ai_response_time
            },
            "created_at": session.created_at.isoformat() if session.created_at else None # Format datetime to ISO string
        }
        session_list.append(session_data)
    return session_list

def get_messages_by_session_id(db: Session, session_id: str):
    """Lấy danh sách messages trong một session cụ thể."""
    return db.query(models.Message).filter(models.Message.session_id == session_id).order_by(models.Message.statement_index).all()

def get_messages_by_session_id_json(db: Session, session_id: str):
    """Lấy danh sách messages trong một session cụ thể và trả về cấu trúc JSON."""
    messages = get_messages_by_session_id(db, session_id) # Gọi hàm get_messages_by_session_id đã có
    messages_data_json = []
    for message in messages:
        messages_data_json.append({
            "message_id": message.message_id,
            "is_selected": message.is_selected, # Thêm trường is_selected
            "sender": message.sender,
            "content": message.content,
            "timestamp": message.timestamp.isoformat() if message.timestamp else None, # Format datetime to ISO string
            "is_exported": message.is_exported
        })
    return messages_data_json

def create_session(db: Session, session_name: str, ai_model: str, ai_max_tokens: int, ai_response_time: str):
    """Tạo một session mới."""
    db_session = models.Session(
        session_id=f"chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}", # Ví dụ tạo session_id tự động
        session_name=session_name,
        ai_model=ai_model,
        ai_max_tokens=ai_max_tokens,
        ai_response_time=ai_response_time
    )
    db.add(db_session)
    db.commit()
    db.refresh(db_session)
    return db_session

def create_session_controller(db: Session, session_name: str, ai_model: str, ai_max_tokens: int, ai_response_time: str):
    """Tạo một session mới thông qua controller."""
    return create_session(db, session_name, ai_model, ai_max_tokens, ai_response_time) # Gọi hàm create_session đã có

def update_session_name(db: Session, session_id: str, new_session_name: str):
    """Cập nhật tên của một session."""
    db_session = db.query(models.Session).filter(models.Session.session_id == session_id).first()
    if db_session:
        db_session.session_name = new_session_name
        db.commit()
        db.refresh(db_session)
        return True  # Cập nhật thành công
    return False  # Session không tồn tại hoặc lỗi

def delete_session(db: Session, session_id: str):
    """Xóa một session và các messages liên quan."""
    db_session = db.query(models.Session).filter(models.Session.session_id == session_id).first()
    if db_session:
        db.delete(db_session)
        db.commit()
        return True # Xóa thành công
    return False # Session không tồn tại hoặc lỗi

def delete_session_controller(db: Session, session_id: str):
    """Xóa một session mới thông qua controller."""
    return delete_session(db, session_id) # Gọi hàm delete_session đã có

def create_message_controller(db: Session, session_id: str, sender: str, content: str):
    """Tạo và lưu một message mới vào database."""
    # Lấy statement_index tiếp theo cho session
    last_message = db.query(models.Message).filter(models.Message.session_id == session_id).order_by(models.Message.statement_index.desc()).first()
    next_statement_index = 1
    if last_message:
        next_statement_index = last_message.statement_index + 1

    db_message = models.Message(
        message_id=f"msg_{uuid.uuid4().hex[:6]}", # Tạo message_id tự động
        session_id=session_id,
        statement_index=next_statement_index,
        sender=sender,
        content=content,
        timestamp=datetime.now(tz=timezone.utc) # Lưu thời gian UTC
    )
    db.add(db_message)
    db.commit()
    db.refresh(db_message)
    return db_message

def get_message_by_id_json(db: Session, message_id: str):
    """Lấy thông tin chi tiết của một message theo message_id và trả về cấu trúc JSON."""
    message = db.query(models.Message).filter(models.Message.message_id == message_id).first()
    if message:
        return {
            "message_id": message.message_id,
            "sender": message.sender,
            "content": message.content,
            "timestamp": message.timestamp.isoformat() if message.timestamp else None,
            "selected_at": message.selected_at.isoformat() if message.selected_at else None
        }
    return None # Trả về None nếu không tìm thấy message

def update_message_is_exported(db: Session, message_id: str, is_exported: bool):
    """Cập nhật trạng thái is_exported của một message."""
    db_message = db.query(models.Message).filter(models.Message.message_id == message_id).first()
    if db_message:
        db_message.is_exported = is_exported
        db.commit()
        db.refresh(db_message)
        return True # Cập nhật thành công
    return False # Message không tồn tại hoặc lỗi

def create_summary_controller(db: Session, session_id: str, to_statement_index: int, summary_text: str):
    """Tạo và lưu một summary mới vào database."""
    db_summary = models.Summary(
        session_id=session_id,
        to_statement_index=to_statement_index, # Chỉ số tin nhắn cuối cùng trong bản tóm tắt
        summary_text=summary_text
    )
    db.add(db_summary)
    db.commit()
    db.refresh(db_summary)
    return db_summary

def get_summary_by_session_id_json(db: Session, session_id: str):
    """Lấy summary của một session cụ thể từ database và trả về cấu trúc JSON."""
    summary = db.query(models.Summary).filter(models.Summary.session_id == session_id).first()
    if summary:
        return summary.summary_text # Trả về summary_text (JSON string)
    return None # Trả về None nếu không tìm thấy summary

# --- Các hàm cho AI-Selected Questions ---

def get_ai_selected_questions(db: Session):
    """Lấy danh sách các câu hỏi AI được lựa chọn."""
    return db.query(models.Message).filter(
        models.Message.sender == 'system',
        models.Message.is_selected == True # Đã đổi tên cột thành is_selected
    ).order_by(asc(models.Message.selected_at)).all() # Sắp xếp theo thời gian mới nhất trước

def get_all_selected_messages_json(db: Session):
    """Lấy danh sách các câu hỏi AI được lựa chọn và trả về cấu trúc JSON, đã sắp xếp theo selected_at."""
    selected_messages = get_ai_selected_questions(db) # Sử dụng hàm get_ai_selected_questions đã có

    messages_data_json = []
    for message in selected_messages:
        messages_data_json.append({
            "message_id": message.message_id,
            "sender": message.sender,
            "content": message.content,
            "timestamp": message.timestamp.isoformat() if message.timestamp else None,
            "selected_at": message.selected_at.isoformat() if message.selected_at else None, # Thêm selected_at vào JSON
            "is_exported": message.is_exported # Thêm is_exported vào JSON
        })
    return messages_data_json

def get_ai_selected_question_detail(db: Session, message_id: str):
    """Xem chi tiết một câu hỏi AI được lựa chọn."""
    return db.query(models.Message).filter(
        models.Message.message_id == message_id,
        models.Message.sender == 'system',
        models.Message.is_selected == True # Đã đổi tên cột thành is_selected
    ).first()

def select_ai_response(db: Session, message_id: str):
    """Chọn một phản hồi AI vào danh sách câu hỏi lựa chọn."""
    db_message = db.query(models.Message).filter(models.Message.message_id == message_id, models.Message.sender == 'system', 
                                                 models.Message.is_selected == False).first()
    if db_message:
        db_message.is_selected = True # Đã đổi tên cột thành is_selected
        db_message.selected_at = datetime.now(tz=timezone.utc) # Set selected_at bằng thời điểm hiện tại (UTC)
        db.commit()
        db.refresh(db_message)
        return db_message
    return None # Message không tồn tại hoặc không phải của AI

def unselect_ai_response(db: Session, message_id: str):
    """Xóa một phản hồi AI khỏi danh sách câu hỏi lựa chọn."""
    db_message = db.query(models.Message).filter(models.Message.message_id == message_id, models.Message.sender == 'system').first()
    if db_message:
        db_message.is_selected = False # Đã đổi tên cột thành is_selected
        db_message.selected_at = None # Xóa giá trị selected_at
        db_message.is_exported = False # Xóa giá trị is_exported
        db.commit()
        db.refresh(db_message)
        return db_message
    return None # Message không tồn tại hoặc không phải của AI

def clear_all_selected_messages_controller(db: Session):
    """Xóa tất cả các tin nhắn AI đã được lựa chọn (đặt is_selected=False và selected_at=None)."""
    selected_messages = db.query(models.Message).filter(models.Message.is_selected == True, models.Message.sender == 'system').all() # Lấy tất cả tin nhắn AI đã chọn
    count = 0
    for message in selected_messages:
        message.is_selected = False
        message.selected_at = None # Xóa giá trị selected_at
        message.is_exported = False
        count += 1
    db.commit()
    return count # Trả về số lượng tin nhắn đã bỏ chọn

def write_sessions_to_json_file(db: Session, filepath: str = "sessions_data.json"):
    """Lấy danh sách sessions và messages, chuyển đổi sang JSON và ghi vào file."""
    sessions_data_json = get_all_sessions(db) # Reuse the function that fetches session data in JSON format

    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(sessions_data_json, f, indent=4, ensure_ascii=False) # Write JSON to file
        print(f"Sessions data written to: {filepath}") # Optional: Print confirmation message
        return True # Indicate success
    except Exception as e:
        print(f"Error writing sessions data to JSON file: {e}") # Print error message
        return False # Indicate failure