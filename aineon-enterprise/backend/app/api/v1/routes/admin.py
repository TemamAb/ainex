from fastapi import APIRouter, Depends, HTTPException
from typing import List
from sqlalchemy.orm import Session
from .... import crud, models, schemas
from ....db import get_db
from .auth import get_current_user

router = APIRouter()

def get_current_admin_user(current_user: models.User = Depends(get_current_user)):
    if current_user.role not in [models.UserRole.ADMIN, models.UserRole.SUPER_ADMIN]:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return current_user

@router.get("/admin/users/pending", response_model=List[schemas.User])
def get_pending_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_admin_user)
):
    users = crud.get_inactive_users(db, skip=skip, limit=limit)
    return users

@router.put("/admin/users/{user_id}/approve", response_model=schemas.User)
def approve_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_admin_user)
):
    db_user = crud.activate_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

