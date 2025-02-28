from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import os
from dotenv import load_dotenv

load_dotenv() # Load biến môi trường từ .env (nếu chưa load ở main.py)

# DB_DRIVER = os.getenv("POSTGRES_DRIVER", "postgresql") # Lấy driver, mặc định là postgresql
# DB_USER = os.getenv("POSTGRES_USER")
# DB_PASSWORD = os.getenv("POSTGRES_PASSWORD")
# DB_HOST = os.getenv("POSTGRES_HOST", "localhost") # Mặc định localhost nếu không có
# DB_PORT = os.getenv("POSTGRES_PORT", "5432")     # Mặc định 5432 nếu không có
# DB_NAME = os.getenv("POSTGRES_DB")

# DATABASE_URL = f"{DB_DRIVER}://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
# Database URL for SQLite (file-based database in the project directory)

DATABASE_URL = f"sqlite:///./chat_history.db" # SQLite database

# engine = create_engine(DATABASE_URL)
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False}) # Add connect_args for PyQt5
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
        print(f"Database connection established: {DATABASE_URL}") # Optional: Print confirmation message
    finally:
        db.close()