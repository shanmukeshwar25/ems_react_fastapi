import sys
from pathlib import Path
from sqlalchemy import create_engine, text

# Add backend to path
backend_path = Path(r"d:\EMSfull_python\fullems-main\EmployeeManagementSystem\ems-backend-python")
sys.path.append(str(backend_path))

from core.config import settings
from core.security import verify_password

def check_user_raw():
    SQLALCHEMY_DATABASE_URL = f"postgresql://{settings.db_user}:{settings.db_password}@{settings.db_host}:{settings.db_port}/{settings.db_name}"
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    
    with engine.connect() as conn:
        try:
            result = conn.execute(text("SELECT password, is_user_active FROM users WHERE emp_id = 'TT0001'")).fetchone()
            if not result:
                print("User TT0001 NOT FOUND in users table.")
                # List some users
                users = conn.execute(text("SELECT emp_id FROM users LIMIT 5")).fetchall()
                print("Available emp_ids in users table:")
                for u in users:
                    print(f" - {u[0]}")
            else:
                hashed_pw, active = result
                print(f"User TT0001 found. Active: {active}")
                print(f"Password match 'Mouni@1702': {verify_password('Mouni@1702', hashed_pw)}")
                
        except Exception as e:
            print(f"Error checking DB: {e}")

if __name__ == "__main__":
    check_user_raw()
