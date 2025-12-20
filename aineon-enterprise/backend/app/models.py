from sqlalchemy import Column, Integer, String, Boolean, Enum
from .db import Base
import enum

class UserRole(str, enum.Enum):
    SUPER_ADMIN = "SUPER_ADMIN"
    ADMIN = "ADMIN"
    TRADER = "TRADER"
    AUDITOR = "AUDITOR"
    VIEWER = "VIEWER"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=False)
    role = Column(Enum(UserRole), default=UserRole.VIEWER)
