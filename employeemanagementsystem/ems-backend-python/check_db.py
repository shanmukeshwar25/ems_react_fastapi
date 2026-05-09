import sys
import os
from pathlib import Path

# Add backend to path
backend_path = Path(r"d:\EMSfull_python\fullems-main\EmployeeManagementSystem\ems-backend-python")
sys.path.append(str(backend_path))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from core.config import settings
from models.user import User
from models.employee import Employee
from core.security import verify_password

def check_user():
    # Database connection
    SQLALCHEMY_DATABASE_URL = f"postgresql://{settings.db_user}:{settings.db_password}@{settings.db_host}:{settings.db_port}/{settings.db_name}"
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        user = db.query(User).filter(User.emp_id == "TT0001").first()
        if not user:
            print("User TT0001 NOT FOUND in database.")
            # List some users
            users = db.query(User).limit(5).all()
            print("Available users in DB:")
            for u in users:
                print(f" - {u.emp_id}")
        else:
            print(f"User TT0001 found. Active: {user.is_user_active}")
            print(f"Password match 'Mouni@1702': {verify_password('Mouni@1702', user.password)}")
            
    except Exception as e:
        print(f"Error checking DB: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    check_user()
