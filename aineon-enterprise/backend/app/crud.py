from sqlalchemy.orm import Session
from . import models, schemas, security

def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()

def get_inactive_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.User).filter(models.User.is_active == False).offset(skip).limit(limit).all()

def create_user(db: Session, user: schemas.UserCreate):
    hashed_password = security.get_password_hash(user.password)
    db_user = models.User(
        email=user.email,
        hashed_password=hashed_password,
        role=user.role
    )
    if user.role == models.UserRole.SUPER_ADMIN:
        db_user.is_active = True
        
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def activate_user(db: Session, user_id: int):
    db_user = get_user(db, user_id)
    if db_user:
        db_user.is_active = True
        db.commit()
        db.refresh(db_user)
    return db_user
