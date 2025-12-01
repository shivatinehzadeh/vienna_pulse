

from sqlalchemy import Column, Integer, String, DateTime, Boolean
from datetime import datetime
from setup.database_setup import Base


class Users(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    username = Column(String, unique=True, index=True)
    password = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=True)
    phone_number = Column(String, unique=True, index=True, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.now())
    updated_at = Column(DateTime, nullable=True, onupdate=datetime.now())
    active_status = Column(Boolean, nullable=False, default="True")
    
