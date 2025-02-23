from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, ForeignKey,CheckConstraint, func
from sqlalchemy.orm import relationship
from .database import Base

class Session(Base):
    __tablename__ = "sessions"

    session_id = Column(String, primary_key=True, index=True)
    session_name = Column(String)
    ai_model = Column(String)
    ai_max_tokens = Column(Integer)
    ai_response_time = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    messages = relationship("Message", back_populates="session", cascade="all, delete-orphan", order_by="Message.statement_index") # Quan hệ với bảng Message, thêm cascade
    summaries = relationship("Summary", back_populates="session", order_by="Summary.to_statement_index") # Quan hệ với bảng Summary, thêm order_by

    def __repr__(self):
        return f"<Session(session_id='{self.session_id}', session_name='{self.session_name}')>"

class Message(Base):
    __tablename__ = "messages"

    message_id = Column(String, primary_key=True, index=True)
    session_id = Column(String, ForeignKey("sessions.session_id")) # Khóa ngoại đến bảng sessions
    statement_index = Column(Integer, index=True) # Thêm cột statement_index
    sender = Column(String, CheckConstraint("sender IN ('user', 'system')", name='sender_type_check')) # Ràng buộc giá trị sender
    content = Column(Text)
    timestamp = Column(DateTime(timezone=True))
    is_selected = Column(Boolean, default=False) # Thêm trường is_ai_selected, mặc định là False

    session = relationship("Session", back_populates="messages") # Quan hệ với bảng Session

    def __repr__(self):
        return f"<Message(message_id='{self.message_id}', sender='{self.sender}')>"

class Summary(Base):
    __tablename__ = "summaries"

    id = Column(Integer, primary_key=True, index=True) # Thêm ID cho bảng summaries
    session_id = Column(String, ForeignKey("sessions.session_id")) # Khóa ngoại đến bảng sessions
    to_statement_index = Column(Integer) # Chỉ số tin nhắn cuối cùng trong bản tóm tắt
    summary_text = Column(Text)

    session = relationship("Session", back_populates="summaries") # Quan hệ với bảng Session

    def __repr__(self):
        return f"<Summary(id={self.id}, session_id='{self.session_id}', to_statement_index={self.to_statement_index})>"