from pydantic import BaseModel, EmailStr
from typing import Optional, List
from .models import UserRole

class Status(BaseModel):
    status: str
    phase1_status: str
    phase2_status: str
    phase3_status: str
    phase4_status: str
    phase5_status: str

class Profit(BaseModel):
    total_profit: float
    daily_profit: float
    trades_today: int
    win_rate: float

class Opportunity(BaseModel):
    id: str
    type: str
    pair: str
    profit_potential: float
    exchange_a: Optional[str] = None
    exchange_b: Optional[str] = None
    protocol: Optional[str] = None

class UserBase(BaseModel):
    email: EmailStr
    role: UserRole = UserRole.VIEWER

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int
    is_active: bool

    class Config:
        orm_mode = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[EmailStr] = None
