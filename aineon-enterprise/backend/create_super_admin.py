import asyncio
import sys
import os
from getpass import getpass
from sqlalchemy.orm import Session

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import crud, schemas
from app.db import SessionLocal, engine, Base
from app.models import UserRole

async def main():
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("Tables created.")

    db: Session = SessionLocal()
    
    print("--- Create Super Admin ---")
    email = input("Email: ")
    password = getpass("Password: ")
    
    user_in = schemas.UserCreate(
        email=email,
        password=password,
        role=UserRole.SUPER_ADMIN
    )
    
    db_user = crud.get_user_by_email(db, email=user_in.email)
    
    if db_user:
        print(f"User with email {email} already exists.")
    else:
        crud.create_user(db=db, user=user_in)
        print(f"Super admin '{email}' created successfully.")
    
    db.close()

if __name__ == "__main__":
    asyncio.run(main())
